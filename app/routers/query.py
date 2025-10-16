"""
検索エンドポイント
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from app.schemas import QueryRequest, QueryResponse, SearchResult
from app.core.embed_cohere import embed_query
from app.core.faiss_store import FAISSStore, create_store_paths
from app.utils.mmr import apply_mmr_filtering
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# グローバルストア（シングルトン）
_store: Optional[FAISSStore] = None


def get_store() -> FAISSStore:
    """FAISSストアを取得（シングルトン）"""
    global _store
    if _store is None:
        index_path, meta_path = create_store_paths(settings.VECTOR_DIR, settings.INDEX_NAME)
        _store = FAISSStore(index_path, meta_path)
        try:
            _store.load()
            logger.info("Loaded FAISS store")
        except FileNotFoundError:
            logger.error(f"Index not found: {index_path}")
            raise HTTPException(status_code=404, detail="Index not found. Please create index first.")
        except Exception as e:
            logger.error(f"Failed to load store: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load index: {str(e)}")
    return _store


def apply_filters(results: List[SearchResult], filters: Optional[Dict[str, Any]]) -> List[SearchResult]:
    """メタデータフィルタを適用"""
    if not filters:
        return results
    
    filtered_results = []
    for result in results:
        meta = result.meta
        
        # listed フィルタ
        if filters.get("listed") and meta.get("listed") != filters["listed"]:
            continue
        
        # type フィルタ
        if filters.get("type") and meta.get("type") != filters["type"]:
            continue
        
        filtered_results.append(result)
    
    return filtered_results


@router.post("/query", response_model=QueryResponse)
async def search_vendors(request: QueryRequest):
    """
    ベンダー検索を実行
    """
    try:
        # ストア取得
        store = get_store()
        
        # クエリ埋め込み
        logger.info(f"Embedding query: {request.q[:50]}...")
        query_embedding = embed_query(request.q)
        
        # FAISS検索
        scores, indices = store.search(
            query_embedding, 
            k=request.k * 2,  # MMR用に多めに取得
            threshold=request.threshold
        )
        
        if len(scores) == 0:
            return QueryResponse(results=[])
        
        # メタデータ取得
        metadata = store.get_metadata_by_indices(indices)
        
        # 検索結果構築
        results = []
        for i, (score, idx) in enumerate(zip(scores, indices)):
            if i < len(metadata):
                result = SearchResult(
                    vendor_id=metadata[i].get("vendor_id", ""),
                    name=metadata[i].get("name", ""),
                    score=float(score),
                    meta=metadata[i]
                )
                results.append(result)
        
        # MMR適用（オプション）
        if request.mmr_lambda is not None and len(results) > 1:
            logger.info(f"Applying MMR with lambda={request.mmr_lambda}")
            
            candidate_scores = np.array([r.score for r in results])
            candidate_indices = np.array([i for i in range(len(results))])
            
            reranked_scores, reranked_indices = apply_mmr_filtering(
                query_embedding,
                query_embedding.reshape(1, -1).repeat(len(results), axis=0),
                candidate_scores,
                candidate_indices,
                request.mmr_lambda,
                request.k
            )
            
            reranked_results = [results[i] for i in reranked_indices]
            results = reranked_results[:request.k]
        
        # フィルタ適用
        results = apply_filters(results, request.filters)
        results = results[:request.k]
        
        logger.info(f"Search returned {len(results)} results")
        return QueryResponse(results=results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ✅ /api/v1/search エンドポイントを追加
@router.post("/search", response_model=QueryResponse)
async def search_alias(request: QueryRequest):
    """
    /api/v1/search エイリアス (互換用)
    実体は /api/v1/query と同じ処理
    """
    return await search_vendors(request)