# FAISSインデックス作成スクリプト (PowerShell版)

Write-Host "🚀 Starting FAISS index creation..." -ForegroundColor Green

# 環境変数設定
$env:AWS_REGION = "ap-northeast-1"
$env:BEDROCK_EMBEDDINGS_MODEL_ID = "cohere.embed-multilingual-v3"
$env:S3_BUCKET_NAME = "cosign-test"
$env:S3_PREFIX = "faiss/exp"
$env:INDEX_NAME = "vendor_cohere_v3"
$env:JSON_PATH = "vendors.json"
$env:VECTOR_DIR = "./vectorstore"
$env:USE_BEDROCK = "true"

Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "  - Model: $env:BEDROCK_EMBEDDINGS_MODEL_ID"
Write-Host "  - S3 Bucket: $env:S3_BUCKET_NAME"
Write-Host "  - S3 Prefix: $env:S3_PREFIX"
Write-Host "  - Index Name: $env:INDEX_NAME"
Write-Host "  - JSON Path: $env:JSON_PATH"
Write-Host ""

# Pythonスクリプト実行
Write-Host "🔧 Creating index..." -ForegroundColor Blue
python create_index.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Index creation completed successfully!" -ForegroundColor Green
    Write-Host "📁 Local files: ./vectorstore/"
    Write-Host "☁️  S3 location: s3://$env:S3_BUCKET_NAME/$env:S3_PREFIX/$env:INDEX_NAME/"
    Write-Host ""
    Write-Host "🧪 Test the index:" -ForegroundColor Cyan
    Write-Host "  curl -X POST 'https://api.3ii.biz/search' \"
    Write-Host "    -H 'Content-Type: application/json' \"
    Write-Host "    -d '{\"q\": \"生成AIとは\"}'"
} else {
    Write-Host ""
    Write-Host "❌ Index creation failed!" -ForegroundColor Red
    exit 1
}
