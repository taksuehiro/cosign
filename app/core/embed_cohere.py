"""
Cohere埋め込み処理
"""
import numpy as np
import logging
from typing import List, Optional
import cohere
from app.config import settings

logger = logging.getLogger(__name__)

# Cohereクライアント（シングルトン）
_cohere_client = None


def get_cohere_client() -> cohere.Client:
    """Cohereクライアントを取得"""
    global _cohere_client
    if _cohere_client is None:
        _cohere_client = cohere.Client(settings.COHERE_API_KEY)
    return _cohere_client


def l2_normalize(embeddings: np.ndarray) -> np.ndarray:
    """L2正規化を実行"""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # ゼロ除算を避ける
    norms = np.where(norms == 0, 1, norms)
    return embeddings / norms


def embed_texts(
    texts: List[str], 
    input_type: str = "search_document",
    model: str = None
) -> np.ndarray:
    """
    テキストを埋め込みベクトルに変換
    
    Args:
        texts: 埋め込み対象のテキストリスト
        input_type: "search_document" または "search_query"
        model: 使用するモデル名
    
    Returns:
        正規化された埋め込みベクトル配列
    """
    if model is None:
        model = settings.COHERE_MODEL
    
    client = get_cohere_client()
    embeddings = []
    
    # バッチ処理
    batch_size = settings.BATCH_SIZE
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        
        try:
            response = client.embed(
                texts=batch_texts,
                model=model,
                input_type=input_type
            )
            
            batch_embeddings = np.array(response.embeddings)
            embeddings.append(batch_embeddings)
            
            logger.info(f"Embedded batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
        except Exception as e:
            logger.error(f"Failed to embed batch {i//batch_size + 1}: {e}")
            raise
    
    # 全バッチを結合
    all_embeddings = np.vstack(embeddings)
    
    # L2正規化
    normalized_embeddings = l2_normalize(all_embeddings)
    
    logger.info(f"Successfully embedded {len(texts)} texts with shape {normalized_embeddings.shape}")
    return normalized_embeddings


def embed_query(query: str, model: str = None) -> np.ndarray:
    """
    クエリを埋め込みベクトルに変換
    
    Args:
        query: 検索クエリ
        model: 使用するモデル名
    
    Returns:
        正規化された埋め込みベクトル
    """
    embeddings = embed_texts([query], input_type="search_query", model=model)
    return embeddings[0]  # 単一クエリなので最初の要素を返す
