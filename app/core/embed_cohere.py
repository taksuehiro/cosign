"""
埋め込み処理（Bedrock/Cohere対応, Bedrockのfloat構造対応＋再帰抽出と詳細ログ）
"""
import numpy as np
import logging
from typing import List, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

_embeddings_client = None


def get_embeddings_client():
    global _embeddings_client
    if _embeddings_client is None:
        if settings.USE_BEDROCK:
            from langchain_aws import BedrockEmbeddings
            _embeddings_client = BedrockEmbeddings(
                model_id=settings.BEDROCK_EMBEDDINGS_MODEL_ID,
                region_name=settings.AWS_REGION
            )
            logger.info(f"Initialized Bedrock embeddings with model: {settings.BEDROCK_EMBEDDINGS_MODEL_ID}")
        else:
            import cohere
            if not settings.COHERE_API_KEY:
                raise ValueError("COHERE_API_KEY is required for direct Cohere API usage")
            _embeddings_client = cohere.Client(settings.COHERE_API_KEY)
            logger.info("Initialized Cohere API client")
    return _embeddings_client


def l2_normalize(embeddings: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return embeddings / norms


# ===== 再帰抽出ユーティリティ =====

def _is_number_sequence(seq: Any) -> bool:
    try:
        for x in seq:
            float(x)
        return True
    except Exception:
        return False


def _find_first_float_array(obj: Any) -> Optional[Any]:
    """Bedrockの返却から最初に見つかった数値配列（list[float] or list[list[float]]）を返す。
    見つからない場合はNone。
    優先順: dictの 'embedding'/'embeddings'/'float' → list要素再帰 → dict値再帰。
    """
    # 直接数値配列
    if isinstance(obj, list):
        if len(obj) == 0:
            return obj
        # list[float]
        if not isinstance(obj[0], (list, dict)) and _is_number_sequence(obj):
            return obj
        # list[list[float]]
        if isinstance(obj[0], list) and all(_is_number_sequence(x) for x in obj if isinstance(x, list)):
            return obj
        # list[...] 再帰
        for el in obj:
            cand = _find_first_float_array(el)
            if cand is not None:
                return cand
        return None

    if isinstance(obj, dict):
        for key in ("embedding", "embeddings", "float"):
            if key in obj:
                cand = _find_first_float_array(obj[key])
                if cand is not None:
                    return cand
        # その他のキーも再帰
        for v in obj.values():
            cand = _find_first_float_array(v)
            if cand is not None:
                return cand
        return None

    # それ以外（数値配列ではない）
    return None


def embed_texts(texts: List[str], input_type: str = "search_document", model: str = None) -> np.ndarray:
    """Bedrock/Cohereでテキストを埋め込み。Bedrockの未知構造にも再帰で対応。"""
    client = get_embeddings_client()
    embeddings: List[np.ndarray] = []

    for i in range(0, len(texts), settings.BATCH_SIZE):
        batch = texts[i:i + settings.BATCH_SIZE]
        try:
            if settings.USE_BEDROCK:
                raw = client.embed_documents(batch)

                # 詳細ログ（最初のバッチのみ冗長）
                if i == 0:
                    logger.debug(f"Bedrock raw type: {type(raw)}")
                    if isinstance(raw, list):
                        logger.debug(f"Bedrock raw list length: {len(raw)}")
                        if raw and isinstance(raw[0], dict):
                            logger.debug(f"Bedrock raw[0] keys: {list(raw[0].keys())}")
                    elif isinstance(raw, dict):
                        logger.debug(f"Bedrock raw dict keys: {list(raw.keys())}")
                    elif isinstance(raw, str):
                        logger.error(f"Bedrock raw string head: {raw[:200]}")

                arr = _find_first_float_array(raw)
                if arr is None:
                    raise ValueError("Failed to locate float embeddings in Bedrock response")

                batch_embeddings = np.array(arr, dtype=np.float32)

                # list[float] の場合は (1, dim) に揃える
                if batch_embeddings.ndim == 1:
                    batch_embeddings = batch_embeddings.reshape(1, -1)

                # 期待: (batch, dim)
                if batch_embeddings.shape[0] != len(batch):
                    logger.warning(
                        f"Bedrock embeddings batch size mismatch: got {batch_embeddings.shape[0]} vs expected {len(batch)}"
                    )

            else:
                # Cohere直API
                if model is None:
                    model = settings.COHERE_MODEL
                response = client.embed(texts=batch, model=model, input_type=input_type)
                batch_embeddings = np.array(response.embeddings, dtype=np.float32)

            embeddings.append(batch_embeddings)
            logger.info(f"Embedded batch {i//settings.BATCH_SIZE + 1}")

        except Exception as e:
            logger.error(f"Failed to embed batch {i//settings.BATCH_SIZE + 1}: {e}")
            # 追加の構造ダンプ（安全範囲内）
            logger.error(f"Batch sample: {batch[:2] if batch else 'empty'}")
            raise

    return l2_normalize(np.vstack(embeddings))


def embed_query(query: str, model: str = None) -> np.ndarray:
    client = get_embeddings_client()

    try:
        if settings.USE_BEDROCK:
            raw = client.embed_query(query)

            # 詳細ログ
            logger.debug(f"Bedrock query raw type: {type(raw)}")
            if isinstance(raw, dict):
                logger.debug(f"Bedrock query raw keys: {list(raw.keys())}")
            elif isinstance(raw, list):
                logger.debug(f"Bedrock query raw list length: {len(raw)}")

            arr = _find_first_float_array(raw)
            if arr is None:
                raise ValueError("Failed to locate float embedding in Bedrock query response")

            emb = np.array(arr, dtype=np.float32)
            if emb.ndim == 1:
                emb = emb.reshape(1, -1)
            elif emb.ndim > 2:
                emb = emb.reshape(1, -1)
        else:
            if model is None:
                model = settings.COHERE_MODEL
            response = client.embed(texts=[query], model=model, input_type="search_query")
            emb = np.array(response.embeddings[0], dtype=np.float32).reshape(1, -1)

        return l2_normalize(emb)[0]

    except Exception as e:
        logger.error(f"Failed to embed query: {e}")
        logger.error(f"Query: {query}")
        raise

