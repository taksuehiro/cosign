# RAG Search API Makefile

.PHONY: help install run test clean docker-build docker-run

# デフォルトターゲット
help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  run         - Run development server"
	@echo "  test        - Run tests"
	@echo "  clean       - Clean temporary files"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"

# 依存関係インストール
install:
	pip install -r requirements.txt

# 開発サーバー起動
run:
	uvicorn app.main:app --reload --port 8080

# テスト実行
test:
	pytest -v

# 一時ファイルクリーンアップ
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf /tmp/vectorstore

# Dockerイメージビルド
docker-build:
	docker build -t rag-search-api .

# Dockerコンテナ実行
docker-run:
	docker run -p 8080:8080 --env-file .env rag-search-api

# インデックス作成（ローカル）
create-index:
	curl -X POST http://localhost:8080/api/v1/index \
		-H "Content-Type: application/json" \
		-d '{"save_to_s3": false}'

# 検索テスト
test-search:
	curl -X POST http://localhost:8080/api/v1/query \
		-H "Content-Type: application/json" \
		-d '{"q":"LLM導入支援","k":5}'

# 評価実行
run-eval:
	curl -X POST http://localhost:8080/api/v1/eval \
		-H "Content-Type: application/json" \
		-d '{"queries_path":"data/queries.eval.jsonl","k":10}'
