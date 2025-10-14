"""
評価エンドポイント
"""
import json
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.schemas import EvalRequest, EvalResponse, EvalMetrics
from app.core.metrics import calculate_metrics
from app.routers.query import search_vendors, QueryRequest
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def load_eval_queries(queries_path: str) -> List[Dict[str, Any]]:
    """評価クエリを読み込み"""
    try:
        queries = []
        with open(queries_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    query_data = json.loads(line)
                    queries.append(query_data)
        
        logger.info(f"Loaded {len(queries)} evaluation queries from {queries_path}")
        return queries
        
    except Exception as e:
        logger.error(f"Failed to load evaluation queries: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to load queries: {str(e)}")


async def run_evaluation_query(query_data: Dict[str, Any], k: int, threshold: float = None, mmr_lambda: float = None) -> Dict[str, Any]:
    """単一クエリの評価を実行"""
    try:
        # 検索実行
        query_request = QueryRequest(
            q=query_data["q"],
            k=k,
            threshold=threshold,
            mmr_lambda=mmr_lambda
        )
        
        search_response = await search_vendors(query_request)
        
        # 結果を構築
        results = []
        for result in search_response.results:
            results.append({
                "vendor_id": result.vendor_id,
                "name": result.name,
                "score": result.score,
                "meta": result.meta
            })
        
        return {
            "q": query_data["q"],
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to evaluate query '{query_data.get('q', 'unknown')}': {e}")
        return {
            "q": query_data.get("q", "unknown"),
            "results": [],
            "error": str(e)
        }


@router.post("/eval", response_model=EvalResponse)
async def evaluate_search(request: EvalRequest):
    """
    検索性能を評価
    
    Args:
        request: 評価リクエスト
    
    Returns:
        評価結果
    """
    try:
        # 評価クエリ読み込み
        queries = load_eval_queries(request.queries_path)
        if not queries:
            raise HTTPException(status_code=400, detail="No evaluation queries found")
        
        logger.info(f"Starting evaluation with {len(queries)} queries")
        
        # 各クエリを評価
        query_results = []
        failed_cases = []
        
        for i, query_data in enumerate(queries):
            logger.info(f"Evaluating query {i+1}/{len(queries)}: {query_data.get('q', 'unknown')[:50]}...")
            
            result = await run_evaluation_query(
                query_data, 
                request.k, 
                request.threshold, 
                request.mmr_lambda
            )
            
            if "error" in result:
                failed_cases.append({
                    "query": query_data.get("q", "unknown"),
                    "error": result["error"]
                })
            else:
                query_results.append(result)
        
        # メトリクス計算
        if query_results:
            recall, mrr, ndcg = calculate_metrics(query_results, queries, request.k)
            metrics = EvalMetrics(
                recall_at_k=recall,
                mrr_at_k=mrr,
                ndcg_at_k=ndcg
            )
        else:
            metrics = EvalMetrics(
                recall_at_k=0.0,
                mrr_at_k=0.0,
                ndcg_at_k=0.0
            )
        
        logger.info(f"Evaluation completed: R@{request.k}={metrics.recall_at_k:.3f}, "
                   f"MRR@{request.k}={metrics.mrr_at_k:.3f}, nDCG@{request.k}={metrics.ndcg_at_k:.3f}")
        
        return EvalResponse(
            total_queries=len(queries),
            successful_queries=len(query_results),
            failed_queries=len(failed_cases),
            metrics=metrics,
            failed_cases=failed_cases
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
