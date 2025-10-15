# RAG Search API アーキテクチャ（最新版）

本ドキュメントは cosign（RAG実験用バックエンド）の最新実装に合わせて更新されています。
対象バージョン: main（Bedrock埋め込み: boto3フォールバック対応後）

## 概要
- 目的: vendors.json の各ベンダーをベクトル化し、FAISS(IndexFlatIP + L2正規化＝コサイン類似)で検索・評価できる最小RAGバックエンド。
- フレームワーク: FastAPI (Python 3.11)
- 埋め込み: Cohere Embed v4 (AWS Bedrock経由) もしくは Cohere直API
- ベクトル検索: FAISS (IndexFlatIP) + L2正規化
- 永続化: ローカル（/tmp/vectorstore）＋ S3（任意）

## ディレクトリ構成（抜粋）
```
app/
  main.py              # FastAPIアプリ
  config.py            # 設定・環境変数
  deps.py              # 依存注入（S3クライアント等）
  schemas.py           # Pydantic v2 スキーマ
  routers/
    indexer.py         # /api/v1/index: 埋め込み生成→FAISS構築→保存
    query.py           # /api/v1/query: 検索（閾値/フィルタ/MMR）
    eval.py            # /api/v1/eval: Recall/MRR/nDCG
  core/
    ingest.py          # vendors.json→テキスト生成・メタ
    embed_cohere.py    # 埋め込み実装（Bedrock→boto3フォールバック含む）
    faiss_store.py     # FAISS管理（build/save/load/search）
    s3_store.py        # S3アップ/ダウンロード
    metrics.py         # 評価メトリクス
  utils/
    mmr.py             # MMR再ランク
```

## 設定・環境変数
`.env` で下記を設定（`env.example` 参照）
- `USE_BEDROCK`（default: true）: Bedrockを使うか
- `BEDROCK_EMBEDDINGS_MODEL_ID`（default: cohere.embed-v4:0）
- `AWS_REGION`（default: ap-northeast-1）
- `COHERE_API_KEY`（任意; USE_BEDROCK=false の場合に必要）
- `S3_BUCKET_NAME`（任意; 指定時のみS3連携有効）
- `S3_PREFIX`（default: faiss/exp）
- `VECTOR_DIR`（default: /tmp/vectorstore）
- `INDEX_NAME`（default: vendor_cohere_v4）
- `JSON_PATH`（default: data/vendors.json）

## データフロー

### 1) インデックス作成 `/api/v1/index`
1. ingest: vendors.json を読み込み
   - テキスト生成: 全フィールドを安全に文字列化（ネスト辞書は再帰展開）。
   - メタ生成: vendor_id, name, type, listed, deployment, 金額等は全て文字列として保持。
2. 埋め込み生成: embed_cohere.py
   - USE_BEDROCK=true の場合:
     - まず `langchain_aws.BedrockEmbeddings` を試行
     - 戻り値が不正（例: ['float'] や dict構造不一致）の場合、boto3直叩きへフォールバック
       - Bedrock Runtime: `invoke_model(modelId=cohere.embed-v4:0, body={"texts": [...]})`
       - レスポンスから `embedding/embeddings` 配下の `float` を再帰抽出
     - 取得した配列を `np.float32` にキャストし、L2正規化
   - USE_BEDROCK=false の場合:
     - Cohere直API (`cohere.Client.embed`) を使用
     - `input_type`: document/query を使い分け
3. FAISS構築: `IndexFlatIP(dim)` に正規化ベクトルを登録
4. 保存: `VECTOR_DIR/INDEX_NAME/{index.faiss, meta.json}`
5. オプション: S3へアップロード

レスポンス: `{ indexed, index_name, saved_local, saved_s3 }`

### 2) 検索 `/api/v1/query`
1. クエリを埋め込み（上記と同じ分岐・正規化）
2. FAISS検索（top-k）。閾値があればスコアでカット
3. フィルタ（listed/type）をメタに対して適用
4. MMR指定時は再ランク（lambdaで関連性/多様性のバランス）

レスポンス: `[{ vendor_id, name, score, meta }]`

### 3) 評価 `/api/v1/eval`
- queries.eval.jsonl（q と gold 配列）を順に /query 実行
- recall@k, mrr@k, ndcg@k を平均算出

## 埋め込み実装の詳細（embed_cohere.py）
- クライアント初期化
  - Bedrock: `langchain_aws.BedrockEmbeddings` を優先
  - boto3: `boto3.client("bedrock-runtime")` を遅延初期化
  - Cohere直API: `cohere.Client`
- 返却構造の正規化
  - 返り値が list / dict / nested のいずれでも、再帰関数で `float` 配列（list[float] or list[list[float]]）を抽出
  - 不正な場合はフォールバック、最終的に `np.array(..., dtype=np.float32)`
- 形状
  - document: `(batch, dim)`
  - query: `(1, dim)`
- 正規化
  - すべて L2 正規化して FAISS(IndexFlatIP) でコサイン類似になるよう統一

## FAISS（faiss_store.py）
- `build_index(embeddings)`: IndexFlatIP(dim) を生成して `float32` ベクトルを `add`
- `search(q, k, threshold)`: `index.search(q, k)` → スコア/インデックス返却（閾値カット）
- `save/load`: `faiss.write_index` / `faiss.read_index`、`meta.json` は orjson

## データ取り込み（ingest.py）
- vendors.json から全フィールドを安全に文字列化してテキスト化（ネストは再帰）
- メタは要件の主要キーを文字列で保持（数値風文字列もそのまま）

## API スキーマ（schemas.py）
- IndexRequest/Response, QueryRequest/Response, EvalRequest/Response を Pydantic v2 で定義
- orjson レスポンスで軽量化

## S3 連携（s3_store.py）
- `s3://{bucket}/{prefix}/{index_name}/index.faiss, meta.json`
- `upload_file` / `download_file` を使用

## 運用・ロギング
- INFO: index_name, counts, timings（埋め込みバッチ数、保存先）
- DEBUG: Bedrockレスポンスの型/keys（先頭バッチのみ）
- WARNING: フォールバック発動時
- ERROR: 抽出失敗、invokeModel バリデーションエラー等の詳細

## エラーハンドリング指針
- 4xx: 入力不備（JSONパス不正、空テキスト等）
- 5xx: 外部依存（埋め込みAPI/S3/FAISS I/O）
- Bedrockのスロットリング/一時失敗は将来的にリトライ投入を検討

## テスト
- ingest: テキスト/メタ生成が期待通り
- embed+FAISS: モック埋め込みで検索順位が正しい
- metrics: 小規模データで既知の値

## 今後の拡張
- リトライ/指数バックオフ、タイムアウト明示化
- 埋め込みキャッシュ（S3 or ローカル）
- ハイブリッド検索（BM25 + ベクトル）
- 評価レポートの詳細化（失敗ケースのサンプル返却）

---
この構成は、Bedrock経由のCohere v4応答仕様の揺らぎに耐えるよう、langchain_aws優先＋boto3フォールバックで堅牢化しています。運用環境では IAM ロールでの認証を推奨します。






読む順番（この通りに辿ると理解が速い）

1,app/main.py

ルータのマウントと起動時処理（S3→/tmp 同期→FAISS.load_local()）を確認。

ここで「どの DI(依存) を注入しているか」「設定（.env）がどこで読まれるか」を掴む。


2,app/routers/query.py（/api/v1/query の本体）

POST /api/v1/query のエンドポイント関数を読む。

受け取った {"q":"LLM導入支援が得意", "k":…} を Pydantic スキーマでバリデート → 埋め込み生成 → FAISS 検索 → レスポンス整形…という呼び出し順がそのまま載っているはず。

フィルタ（例：listed/type）や MMR 再ランクの分岐があればここで分かる。


3,app/schemas.py

QueryRequest / QueryResponse を確認して入力と出力の正確な型を把握。

k, threshold, mmr などパラメータ名とデフォルトをここで確定。


4,app/core/embed_cohere.py（最重要その1）

クエリ文の埋め込み生成の実装。

フロー：

USE_BEDROCK=true なら langchain_aws.BedrockEmbeddings をまず試す

戻り値が不正なら boto3 直叩きにフォールバック

bedrock-runtime.invoke_model(modelId=ENV['BEDROCK_EMBEDDINGS_MODEL_ID'], body={"texts":[q]})

返却の embedding/embeddings から float 配列を抽出

np.float32 にキャストして L2 正規化（クエリは形状 (1, dim)）

ここで cohere.embed-v4:0 を本当に投げているか、"texts" キーを使っているか、ログ(DEBUG) の出力位置も確認。


5,app/core/faiss_store.py（最重要その2）

Index のロード（起動時 or 初回アクセス時）と 検索本体を把握。

IndexFlatIP + L2 正規化 = コサイン類似 で top-k を返却、必要なら threshold でカット。

返ってきたインデックスから meta.json のメタデータを引き当て、score と一緒にレスポンス用の配列へ。


6,（オプション）app/utils/mmr.py

リクエストで MMR が指定されたときの多様性再ランクの計算式とハイパラ（lambda）。


7,（参照）app/config.py & app/core/s3_store.py

.env の読み方（USE_BEDROCK, BEDROCK_EMBEDDINGS_MODEL_ID, VECTOR_DIR, INDEX_NAME など）と

S3 同期の具体メソッド（どのパスに index.faiss / meta.json を置くか）。検索時は基本読み取りだけなので後回しでOK。





実行時の“頭の中トレース”

あなたの cURL（"LLM導入支援が得意"）が来ると…

routers/query.py で JSON → QueryRequest にパース

embed_cohere.py が呼ばれ、cohere.embed-v4:0 を Bedrock Runtime に {"texts":[q]} で投げる

必要に応じて LangChain→boto3 フォールバック

返ったベクトルを L2 正規化

faiss_store.py で /tmp/vectorstore/<INDEX_NAME>/index.faiss をロードし、**IP検索（=コサイン類似）**で top-k

該当行のメタを meta.json から取り出し、[{vendor_id, name, score, meta}] に整形して返却
（MMRやフィルタ指定があればここで適用）



すぐ使える“コードあたりの確認コマンド”

ルータ本体を当てる：
grep -R "post(\"/api/v1/query" -n app/routers

埋め込みの実体（invoke_model を探す）：
grep -R "invoke_model" -n app/core | head

ベクトル検索の核（FAISS呼び出し）：
grep -R "IndexFlatIP\\|faiss\\|search(" -n app/core

スキーマ（入出力型）：
grep -n "class .*Query.*" app/schemas.py




デバッグのコツ

.env の LOG_LEVEL=debug を有効にして Bedrockレスポンスの key/shape ログを出す（実装に DEBUG が仕込まれている想定）。

curl に "k": 1 で投げ、1件だけを追うと追跡しやすい。

ARCHITECTURE

この順でファイルを開けば、1本のクエリがどの関数へ流れて何を返すかを、15分で掴めるはずです。