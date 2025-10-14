"""
Maximal Marginal Relevance (MMR) 実装
"""
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def mmr_rerank(
    query_embedding: np.ndarray,
    candidate_embeddings: np.ndarray,
    candidate_scores: np.ndarray,
    candidate_indices: np.ndarray,
    lambda_param: float,
    k: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    MMR（Maximal Marginal Relevance）で検索結果を再ランク
    
    Args:
        query_embedding: クエリ埋め込みベクトル
        candidate_embeddings: 候補埋め込みベクトル配列
        candidate_scores: 候補スコア配列
        candidate_indices: 候補インデックス配列
        lambda_param: MMR重みパラメータ（0-1）
        k: 最終的な結果数
    
    Returns:
        (reranked_scores, reranked_indices): 再ランクされたスコアとインデックス
    """
    if lambda_param <= 0 or lambda_param >= 1:
        logger.warning(f"Invalid lambda parameter: {lambda_param}, using default 0.5")
        lambda_param = 0.5
    
    n_candidates = len(candidate_scores)
    if n_candidates == 0:
        return np.array([]), np.array([])
    
    # 結果格納用
    selected_indices = []
    selected_scores = []
    remaining_indices = list(range(n_candidates))
    
    # 最初のアイテムは最高スコアのものを選択
    if n_candidates > 0:
        first_idx = np.argmax(candidate_scores)
        selected_indices.append(first_idx)
        selected_scores.append(candidate_scores[first_idx])
        remaining_indices.remove(first_idx)
    
    # 残りのアイテムをMMRで選択
    while len(selected_indices) < min(k, n_candidates) and remaining_indices:
        best_score = -np.inf
        best_idx = None
        
        for idx in remaining_indices:
            # 関連性スコア（クエリとの類似度）
            relevance_score = candidate_scores[idx]
            
            # 多様性スコア（既選択アイテムとの最大類似度）
            diversity_score = 0.0
            if selected_indices:
                # 既選択アイテムとの類似度を計算
                similarities = []
                for selected_idx in selected_indices:
                    # コサイン類似度を計算
                    similarity = np.dot(
                        candidate_embeddings[idx], 
                        candidate_embeddings[selected_idx]
                    )
                    similarities.append(similarity)
                
                # 最大類似度を多様性スコアとして使用
                diversity_score = max(similarities)
            
            # MMRスコア計算
            mmr_score = lambda_param * relevance_score - (1 - lambda_param) * diversity_score
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx
        
        if best_idx is not None:
            selected_indices.append(best_idx)
            selected_scores.append(candidate_scores[best_idx])
            remaining_indices.remove(best_idx)
        else:
            break
    
    # 結果を配列に変換
    reranked_scores = np.array(selected_scores)
    reranked_indices = np.array([candidate_indices[i] for i in selected_indices])
    
    logger.info(f"MMR reranked {len(selected_indices)} items with lambda={lambda_param}")
    
    return reranked_scores, reranked_indices


def apply_mmr_filtering(
    query_embedding: np.ndarray,
    candidate_embeddings: np.ndarray,
    candidate_scores: np.ndarray,
    candidate_indices: np.ndarray,
    lambda_param: float,
    k: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    MMRフィルタリングを適用（既存の検索結果に対して）
    
    Args:
        query_embedding: クエリ埋め込みベクトル
        candidate_embeddings: 候補埋め込みベクトル配列
        candidate_scores: 候補スコア配列
        candidate_indices: 候補インデックス配列
        lambda_param: MMR重みパラメータ
        k: 最終的な結果数
    
    Returns:
        (filtered_scores, filtered_indices): フィルタリングされたスコアとインデックス
    """
    if lambda_param is None or lambda_param <= 0:
        # MMRを適用しない場合は元の結果を返す
        return candidate_scores[:k], candidate_indices[:k]
    
    return mmr_rerank(
        query_embedding,
        candidate_embeddings,
        candidate_scores,
        candidate_indices,
        lambda_param,
        k
    )

