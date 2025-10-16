# FAISSインデックス作成ガイド

## 🎯 概要

ローカル環境でFAISSインデックスを作成してS3にアップロードする手順です。

## 📋 前提条件

- Python環境がセットアップ済み
- AWS認証情報が設定済み
- Bedrock APIへのアクセス権限
- S3バケット `cosign-test` への書き込み権限

## 🚀 実行方法

### Windows (PowerShell)
```powershell
.\run_create_index.ps1
```

### Linux/Mac (Bash)
```bash
./run_create_index.sh
```

### 手動実行
```bash
# 環境変数設定
export AWS_REGION=ap-northeast-1
export BEDROCK_EMBEDDINGS_MODEL_ID=cohere.embed-multilingual-v3
export S3_BUCKET_NAME=cosign-test
export S3_PREFIX=faiss/exp
export INDEX_NAME=vendor_cohere_v3
export JSON_PATH=vendors.json
export VECTOR_DIR=./vectorstore
export USE_BEDROCK=true

# インデックス作成
python create_index.py
```

## 📁 生成されるファイル

### ローカル
```
./vectorstore/
├── vendor_cohere_v3.index
└── vendor_cohere_v3.meta
```

### S3
```
s3://cosign-test/faiss/exp/vendor_cohere_v3/
├── index.faiss
└── metadata.json
```

## 🧪 動作確認

### 1. ローカルテスト
```bash
python -c "
from app.core.faiss_store import FAISSStore
store = FAISSStore('./vectorstore/vendor_cohere_v3.index', './vectorstore/vendor_cohere_v3.meta')
store.load()
print('Index loaded successfully')
"
```

### 2. APIテスト
```bash
curl -X POST "https://api.3ii.biz/search" \
  -H "Content-Type: application/json" \
  -d '{"q": "生成AIとは"}'
```

## 🔧 トラブルシューティング

### エラー: "No vendors data found"
- `vendors.json` ファイルが存在するか確認
- ファイルパスが正しいか確認

### エラー: "Failed to upload to S3"
- AWS認証情報を確認
- S3バケットの権限を確認
- ネットワーク接続を確認

### エラー: "Bedrock API error"
- Bedrock APIの利用権限を確認
- リージョン設定を確認
- API制限に達していないか確認

## 📊 実行時間の目安

- 小規模データ（100件）: 2-3分
- 中規模データ（1000件）: 10-15分
- 大規模データ（10000件）: 1-2時間

## 🎯 次のステップ

1. インデックス作成完了後、ECSサービスを再起動
2. APIエンドポイントで検索テスト
3. 必要に応じてインデックス更新
