"""
FastAPIメインアプリケーション
"""
import logging
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import HealthResponse
from app.routers import indexer, query, eval
from app.config import settings

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション作成
app = FastAPI(
    title="RAG Search API",
    description="Cohere + FAISS ベースのベンダー検索API",
    version="1.0.0",
    default_response_class=ORJSONResponse
)

# CORS設定
origins = [
    "https://main.d30qmyqyqcxjp3.amplifyapp.com",
    "https://api.3ii.biz",
    "http://localhost:3000",  # ローカル開発用
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(indexer.router, prefix="/api/v1", tags=["index"])
app.include_router(query.router, prefix="/api/v1", tags=["search"])
app.include_router(eval.router, prefix="/api/v1", tags=["evaluation"])

# デバッグ用: 登録されたルートを確認
@app.get("/debug/routes")
async def debug_routes():
    """デバッグ用: 登録されたルート一覧"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    return {"routes": routes}

# ルートレベルの検索エンドポイント（フロントエンド互換用）
from app.schemas import QueryRequest, QueryResponse
from app.routers.query import search_vendors

@app.post("/search", response_model=QueryResponse)
async def root_search(request: QueryRequest):
    """
    ルートレベルの検索エンドポイント（フロントエンド互換用）
    """
    return await search_vendors(request)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェックエンドポイント"""
    return HealthResponse(
        status="healthy",
        message="RAG Search API is running"
    )


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "RAG Search API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )