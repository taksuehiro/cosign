"""
評価メトリクス計算
"""
import numpy as np
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def recall_at_k(relevant_items: List[str], retrieved_items: List[str], k: int) -> float:
    """
    Recall@Kを計算
    
    Args:
        relevant_items: 関連アイテムリスト（正解）
        retrieved_items: 検索結果リスト
        k: 評価する上位k件
    
    Returns:
        Recall@K値
    """
    if not relevant_items:
        return 0.0
    
    # 上位k件を取得
    top_k = retrieved_items[:k]
    
    # 関連アイテムのうち、上位k件に含まれる数
    relevant_retrieved = len(set(relevant_items) & set(top_k))
    
    return relevant_retrieved / len(relevant_items)


def mrr_at_k(relevant_items: List[str], retrieved_items: List[str], k: int) -> float:
    """
    MRR@Kを計算
    
    Args:
        relevant_items: 関連アイテムリスト（正解）
        retrieved_items: 検索結果リスト
        k: 評価する上位k件
    
    Returns:
        MRR@K値
    """
    if not relevant_items:
        return 0.0
    
    # 上位k件を取得
    top_k = retrieved_items[:k]
    
    # 最初の関連アイテムの位置を探す
    for i, item in enumerate(top_k):
        if item in relevant_items:
            return 1.0 / (i + 1)
    
    return 0.0


def ndcg_at_k(relevant_items: List[str], retrieved_items: List[str], k: int) -> float:
    """
    nDCG@Kを計算
    
    Args:
        relevant_items: 関連アイテムリスト（正解）
        retrieved_items: 検索結果リスト
        k: 評価する上位k件
    
    Returns:
        nDCG@K値
    """
    if not relevant_items:
        return 0.0
    
    # 上位k件を取得
    top_k = retrieved_items[:k]
    
    # DCG計算
    dcg = 0.0
    for i, item in enumerate(top_k):
        if item in relevant_items:
            dcg += 1.0 / np.log2(i + 2)  # i+2 because log2(1) = 0
    
    # IDCG計算（理想的な順序でのDCG）
    idcg = 0.0
    for i in range(min(len(relevant_items), k)):
        idcg += 1.0 / np.log2(i + 2)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def calculate_metrics(
    query_results: List[Dict[str, Any]], 
    gold_standard: List[Dict[str, Any]], 
    k: int
) -> Tuple[float, float, float]:
    """
    複数クエリの評価メトリクスを計算
    
    Args:
        query_results: クエリ結果リスト [{"q": "...", "results": [{"vendor_id": "...", ...}]}]
        gold_standard: 正解データリスト [{"q": "...", "gold": ["V-...", "V-..."]}]
        k: 評価する上位k件
    
    Returns:
        (recall, mrr, ndcg)のタプル
    """
    if not query_results or not gold_standard:
        return 0.0, 0.0, 0.0
    
    # クエリごとのメトリクスを計算
    recalls = []
    mrrs = []
    ndcgs = []
    
    for i, (result, gold) in enumerate(zip(query_results, gold_standard)):
        # 検索結果のvendor_idリスト
        retrieved_items = [r["vendor_id"] for r in result.get("results", [])]
        
        # 正解のvendor_idリスト
        relevant_items = gold.get("gold", [])
        
        if not relevant_items:
            logger.warning(f"Query {i} has no gold standard items")
            continue
        
        # メトリクス計算
        recall = recall_at_k(relevant_items, retrieved_items, k)
        mrr = mrr_at_k(relevant_items, retrieved_items, k)
        ndcg = ndcg_at_k(relevant_items, retrieved_items, k)
        
        recalls.append(recall)
        mrrs.append(mrr)
        ndcgs.append(ndcg)
        
        logger.debug(f"Query {i}: R@{k}={recall:.3f}, MRR@{k}={mrr:.3f}, nDCG@{k}={ndcg:.3f}")
    
    # 平均値を計算
    avg_recall = np.mean(recalls) if recalls else 0.0
    avg_mrr = np.mean(mrrs) if mrrs else 0.0
    avg_ndcg = np.mean(ndcgs) if ndcgs else 0.0
    
    logger.info(f"Average metrics @{k}: R={avg_recall:.3f}, MRR={avg_mrr:.3f}, nDCG={avg_ndcg:.3f}")
    
    return avg_recall, avg_mrr, avg_ndcg

