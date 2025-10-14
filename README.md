# RAG Search API

Cohere Embed v3 + FAISS を使用したベンダー検索APIです。

## 概要

- **フレームワーク**: FastAPI
- **埋め込み**: Cohere Embed v3 (multilingual)
- **ベクトル検索**: FAISS (IndexFlatIP + L2正規化)
- **ストレージ**: ローカル + S3（オプション）

## 機能

- `/index`: ベンダーデータからインデックス作成
- `/query`: ベクトル検索（閾値・フィルタ・MMR対応）
- `/eval`: 検索性能評価（Recall@K, MRR@K, nDCG@K）

## セットアップ

### 1. 依存関係インストール

```bash
# Python 3.11が必要
pip install -r requirements.txt
```

### 2. 環境変数設定

```bash
# .envファイルを作成
cp env.example .env

# Bedrock使用時（推奨）
USE_BEDROCK=true
BEDROCK_EMBEDDINGS_MODEL_ID=cohere.embed-v4:0
AWS_REGION=ap-northeast-1

# Cohere直API使用時
# USE_BEDROCK=false
# COHERE_API_KEY=your_actual_api_key_here
```

### 3. データ準備

`data/vendors.json` にベンダーデータが配置されていることを確認してください。

## 使用方法

### 開発サーバー起動

```bash
# 方法1: Makefile使用
make run

# 方法2: 直接実行
uvicorn app.main:app --reload --port 8080
```

### API使用例

#### 1. インデックス作成

```bash
curl -X POST http://localhost:8080/api/v1/index \
  -H "Content-Type: application/json" \
  -d '{"save_to_s3": false}'
```

#### 2. 検索実行

```bash
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"q":"LLM導入支援","k":10}'
```

#### 3. 評価実行

```bash
curl -X POST http://localhost:8080/api/v1/eval \
  -H "Content-Type: application/json" \
  -d '{"queries_path":"data/queries.eval.jsonl","k":10}'
```

### Docker使用

```bash
# イメージビルド
make docker-build

# コンテナ実行
make docker-run
```

## テスト

```bash
# 全テスト実行
make test

# 個別テスト実行
pytest tests/test_ingest.py -v
pytest tests/test_embed_search.py -v
pytest tests/test_metrics.py -v
```

## API仕様

### エンドポイント

- `GET /health`: ヘルスチェック
- `POST /api/v1/index`: インデックス作成
- `POST /api/v1/query`: ベンダー検索
- `POST /api/v1/eval`: 検索性能評価

### リクエスト/レスポンス形式

詳細は `/docs` エンドポイントでSwagger UIを確認してください。

## 設定

### 環境変数

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|------------|------|
| `USE_BEDROCK` | - | true | Bedrock使用フラグ |
| `BEDROCK_EMBEDDINGS_MODEL_ID` | - | cohere.embed-v4:0 | Bedrock埋め込みモデルID |
| `AWS_REGION` | - | ap-northeast-1 | AWSリージョン |
| `COHERE_API_KEY` | USE_BEDROCK=false時 | - | Cohere APIキー |
| `S3_BUCKET_NAME` | - | - | S3バケット名（S3連携時） |
| `S3_PREFIX` | - | faiss/exp | S3プレフィックス |
| `VECTOR_DIR` | - | /tmp/vectorstore | ベクトルストアディレクトリ |
| `INDEX_NAME` | - | vendor_cohere_v4 | インデックス名 |
| `JSON_PATH` | - | data/vendors.json | ベンダーデータパス |

### S3連携

S3_BUCKET_NAMEが設定されている場合、インデックス作成時にS3へのアップロードが有効になります。

## アーキテクチャ

```
app/
├── main.py              # FastAPIアプリケーション
├── config.py            # 設定管理
├── deps.py              # 依存関係注入
├── schemas.py           # Pydanticスキーマ
├── routers/             # APIルーター
│   ├── indexer.py       # インデックス作成
│   ├── query.py         # 検索
│   └── eval.py          # 評価
├── core/                # コア機能
│   ├── ingest.py        # データ取り込み
│   ├── embed_cohere.py  # Cohere埋め込み
│   ├── faiss_store.py   # FAISS管理
│   ├── s3_store.py      # S3管理
│   └── metrics.py       # 評価メトリクス
└── utils/               # ユーティリティ
    └── mmr.py           # MMR実装
```

## トラブルシューティング

### よくある問題

1. **Cohere APIキーエラー**
   - `.env`ファイルでAPIキーが正しく設定されているか確認

2. **インデックスが見つからない**
   - 先に `/index` エンドポイントでインデックスを作成

3. **S3接続エラー**
   - AWS認証情報が正しく設定されているか確認
   - S3_BUCKET_NAMEが設定されているか確認

### ログ確認

```bash
# アプリケーションログを確認
tail -f /tmp/vectorstore/*.log
```

## ライセンス

MIT License

