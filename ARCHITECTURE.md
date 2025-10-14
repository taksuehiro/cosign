# RAG Search API アーキテクチャ

## 概要

本システムは、Cohere Embed v3とFAISSを使用したベンダー検索APIです。ベンダー情報をベクトル化し、セマンティック検索を実現するRAG（Retrieval-Augmented Generation）システムです。

## システム構成

### 技術スタック
- **フレームワーク**: FastAPI (Python 3.11)
- **埋め込み**: Cohere Embed v3 (multilingual)
- **ベクトル検索**: FAISS (IndexFlatIP + L2正規化)
- **ストレージ**: ローカル + S3（オプション）
- **型安全性**: Pydantic v2, mypy対応

### ディレクトリ構成
```
cosign/
├── app/
│   ├── main.py              # FastAPIアプリケーション
│   ├── config.py            # 設定管理
│   ├── deps.py              # 依存関係注入
│   ├── schemas.py           # Pydanticスキーマ
│   ├── routers/             # APIルーター
│   │   ├── indexer.py       # インデックス作成
│   │   ├── query.py         # 検索
│   │   └── eval.py          # 評価
│   ├── core/                # コア機能
│   │   ├── ingest.py        # データ取り込み
│   │   ├── embed_cohere.py  # Cohere埋め込み
│   │   ├── faiss_store.py   # FAISS管理
│   │   ├── s3_store.py      # S3管理
│   │   └── metrics.py       # 評価メトリクス
│   └── utils/               # ユーティリティ
│       └── mmr.py           # MMR実装
├── data/
│   ├── vendors.json         # ベンダーデータ
│   └── queries.eval.jsonl   # 評価クエリ
├── tests/                   # テストファイル
└── requirements.txt         # 依存関係
```

## アーキテクチャ詳細

### 1. データフロー

#### インデックス作成フロー
```
vendors.json → テキスト生成 → Cohere埋め込み → L2正規化 → FAISS構築 → 保存
```

1. **データ取り込み** (`ingest.py`)
   - vendors.jsonを読み込み
   - テキスト生成: `name + type + capabilities + description_short + notes`
   - メタデータ生成: `vendor_id, name, type, listed, deployment`

2. **埋め込み生成** (`embed_cohere.py`)
   - Cohere Embed v3 (multilingual) を使用
   - バッチ処理（64件ずつ）
   - L2正規化でコサイン類似度を実現

3. **インデックス構築** (`faiss_store.py`)
   - FAISS IndexFlatIP（内積）を使用
   - ベクトルとメタデータを保存

#### 検索フロー
```
クエリ → Cohere埋め込み → L2正規化 → FAISS検索 → フィルタリング → MMR → 結果返却
```

1. **クエリ処理** (`query.py`)
   - クエリをCohereで埋め込み
   - FAISSで検索実行
   - 閾値フィルタリング
   - メタデータフィルタリング
   - MMR（Maximal Marginal Relevance）適用

### 2. コアコンポーネント

#### 埋め込み処理 (`embed_cohere.py`)
```python
def embed_texts(texts: List[str], input_type: str) -> np.ndarray:
    # Cohere API呼び出し
    # バッチ処理
    # L2正規化
    return normalized_embeddings
```

#### FAISS管理 (`faiss_store.py`)
```python
class FAISSStore:
    def build_index(self, embeddings: np.ndarray)
    def search(self, query_embedding: np.ndarray, k: int)
    def save(self) / load(self)
```

#### S3連携 (`s3_store.py`)
```python
class S3Store:
    def upload_index(self, index_name: str)
    def download_index(self, index_name: str)
```

### 3. APIエンドポイント

#### POST /api/v1/index
- **機能**: ベンダーデータからインデックス作成
- **入力**: `{index_name, json_path, save_to_s3}`
- **出力**: `{indexed, index_name, saved_local, saved_s3}`

#### POST /api/v1/query
- **機能**: ベクトル検索
- **入力**: `{q, k, threshold, mmr_lambda, filters}`
- **出力**: `[{vendor_id, name, score, meta}]`

#### POST /api/v1/eval
- **機能**: 検索性能評価
- **入力**: `{queries_path, k, threshold, mmr_lambda}`
- **出力**: `{total_queries, metrics: {recall_at_k, mrr_at_k, ndcg_at_k}}`

### 4. 評価メトリクス

#### Recall@K
- 関連アイテムのうち、上位K件に含まれる割合
- 検索の網羅性を測定

#### MRR@K (Mean Reciprocal Rank)
- 最初の関連アイテムの順位の逆数
- 検索の精度を測定

#### nDCG@K (Normalized Discounted Cumulative Gain)
- 順位を考慮した累積利得
- 検索の品質を測定

### 5. 高度な機能

#### MMR (Maximal Marginal Relevance)
```python
def mmr_rerank(query_embedding, candidates, lambda_param):
    # 関連性と多様性のバランス
    # lambda * relevance - (1-lambda) * diversity
```

#### フィルタリング
- メタデータベースの前後段フィルタ
- 閾値ベースのスコアフィルタ

#### バッチ処理
- 埋め込み生成時の効率化
- メモリ使用量の最適化

## 設計思想

### 1. 型安全性
- Pydantic v2による厳密な型チェック
- mypy対応による静的型解析

### 2. エラーハンドリング
- HTTP例外の適切なマッピング
- 構造化ログによる問題追跡

### 3. スケーラビリティ
- S3連携による分散ストレージ
- バッチ処理による効率化

### 4. テスト可能性
- モック対応の設計
- 単体テストと統合テストの分離

## 運用考慮事項

### 1. 環境変数
```bash
COHERE_API_KEY=your_api_key
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=your_bucket
VECTOR_DIR=/tmp/vectorstore
```

### 2. パフォーマンス
- 埋め込み生成: バッチサイズ64
- 検索: FAISS IndexFlatIP（高速）
- メモリ: L2正規化による効率化

### 3. セキュリティ
- APIキーの環境変数管理
- S3アクセス権限の適切な設定

### 4. 監視
- 構造化ログによる運用監視
- メトリクスによる性能測定

## 拡張可能性

### 1. 埋め込みモデル
- 他の埋め込みモデルへの対応
- マルチモーダル対応

### 2. 検索アルゴリズム
- ハイブリッド検索（キーワード + ベクトル）
- 再ランキングアルゴリズムの改善

### 3. ストレージ
- 他のベクトルDB（Pinecone、Weaviate等）への対応
- 分散インデックスの実装

### 4. API機能
- リアルタイム更新
- バッチ処理API
- 管理画面の追加

## まとめ

本システムは、現代的なRAGアーキテクチャのベストプラクティスを実装した、スケーラブルで保守性の高い検索APIです。型安全性、テスト可能性、運用性を重視した設計により、本番環境での安定運用が可能です。

