"""
埋め込み処理（Bedrock/Cohere対応）
"""
import numpy as np
import logging
from typing import List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# 埋め込みクライアント（シングルトン）
_embeddings_client = None


def get_embeddings_client():
    """設定に基づいて適切な埋め込みクライアントを取得"""
    global _embeddings_client
    if _embeddings_client is None:
        if settings.USE_BEDROCK:
            try:
                from langchain_aws import BedrockEmbeddings
                _embeddings_client = BedrockEmbeddings(
                    model_id=settings.BEDROCK_EMBEDDINGS_MODEL_ID,
                    region_name=settings.AWS_REGION
                )
                logger.info(f"Initialized Bedrock embeddings with model: {settings.BEDROCK_EMBEDDINGS_MODEL_ID}")
            except ImportError:
                raise ImportError("langchain_aws is required for Bedrock support. Install with: pip install langchain-aws")
        else:
            try:
                import cohere
                if not settings.COHERE_API_KEY:
                    raise ValueError("COHERE_API_KEY is required for direct Cohere API usage")
                _embeddings_client = cohere.Client(settings.COHERE_API_KEY)
                logger.info("Initialized Cohere direct API client")
            except ImportError:
                raise ImportError("cohere is required for direct API usage. Install with: pip install cohere")
    return _embeddings_client


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
    client = get_embeddings_client()
    embeddings = []
    
    # バッチ処理
    batch_size = settings.BATCH_SIZE
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        
        try:
            if settings.USE_BEDROCK:
                # Bedrock経由
                batch_embeddings = client.embed_documents(batch_texts)
                batch_embeddings = np.array(batch_embeddings)
            else:
                # Cohere直API
                if model is None:
                    model = settings.COHERE_MODEL
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
    client = get_embeddings_client()
    
    try:
        if settings.USE_BEDROCK:
            # Bedrock経由
            embedding = client.embed_query(query)
            embedding = np.array(embedding)
        else:
            # Cohere直API
            if model is None:
                model = settings.COHERE_MODEL
            response = client.embed(
                texts=[query],
                model=model,
                input_type="search_query"
            )
            embedding = np.array(response.embeddings[0])
        
        # L2正規化
        normalized_embedding = l2_normalize(embedding.reshape(1, -1))
        return normalized_embedding[0]
        
    except Exception as e:
        logger.error(f"Failed to embed query: {e}")
        raise

