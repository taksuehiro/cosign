#!/bin/bash
# FAISSインデックス作成スクリプト

echo "🚀 Starting FAISS index creation..."

# 環境変数設定
export AWS_REGION=ap-northeast-1
export BEDROCK_EMBEDDINGS_MODEL_ID=cohere.embed-multilingual-v3
export S3_BUCKET_NAME=cosign-test
export S3_PREFIX=faiss/exp
export INDEX_NAME=vendor_cohere_v3
export JSON_PATH=vendors.json
export VECTOR_DIR=./vectorstore
export USE_BEDROCK=true

echo "📋 Configuration:"
echo "  - Model: $BEDROCK_EMBEDDINGS_MODEL_ID"
echo "  - S3 Bucket: $S3_BUCKET_NAME"
echo "  - S3 Prefix: $S3_PREFIX"
echo "  - Index Name: $INDEX_NAME"
echo "  - JSON Path: $JSON_PATH"
echo ""

# Pythonスクリプト実行
echo "🔧 Creating index..."
python create_index.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Index creation completed successfully!"
    echo "📁 Local files: ./vectorstore/"
    echo "☁️  S3 location: s3://$S3_BUCKET_NAME/$S3_PREFIX/$INDEX_NAME/"
    echo ""
    echo "🧪 Test the index:"
    echo "  curl -X POST 'https://api.3ii.biz/search' \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"q\": \"生成AIとは\"}'"
else
    echo ""
    echo "❌ Index creation failed!"
    exit 1
fi
