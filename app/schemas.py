"""
Pydanticスキーマ定義
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


# インデックス作成リクエスト
class IndexRequest(BaseModel):
    index_name: Optional[str] = None
    json_path: Optional[str] = None
    save_to_s3: bool = False


# インデックス作成レスポンス
class IndexResponse(BaseModel):
    indexed: int
    index_name: str
    saved_local: bool
    saved_s3: bool


# 検索リクエスト
class QueryRequest(BaseModel):
    q: str = Field(..., description="検索クエリ")
    k: int = Field(10, ge=1, le=100, description="検索結果数")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="スコア閾値")
    mmr_lambda: Optional[float] = Field(None, ge=0.0, le=1.0, description="MMR重み")
    filters: Optional[Dict[str, Any]] = Field(None, description="メタデータフィルタ")


# 検索結果アイテム
class SearchResult(BaseModel):
    vendor_id: str
    name: str
    score: float
    meta: Dict[str, Any]


# 検索レスポンス
class QueryResponse(BaseModel):
    results: List[SearchResult]


# 評価リクエスト
class EvalRequest(BaseModel):
    queries_path: str = "data/queries.eval.jsonl"
    k: int = Field(10, ge=1, le=100)
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    mmr_lambda: Optional[float] = Field(None, ge=0.0, le=1.0)


# 評価結果
class EvalMetrics(BaseModel):
    recall_at_k: float
    mrr_at_k: float
    ndcg_at_k: float


# 評価レスポンス
class EvalResponse(BaseModel):
    total_queries: int
    successful_queries: int
    failed_queries: int
    metrics: EvalMetrics
    failed_cases: List[Dict[str, Any]]


# ヘルスチェックレスポンス
class HealthResponse(BaseModel):
    status: str
    message: str

