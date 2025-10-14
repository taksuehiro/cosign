"""
埋め込み処理（Bedrock/Cohere対応, Bedrockのfloat構造対応＋再帰抽出と詳細ログ＋boto3フォールバック）
"""
import numpy as np
import logging
import json
from typing import List, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

_embeddings_client = None
_bedrock_client = None  # boto3 runtime client


def _get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        import boto3
        _bedrock_client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
        logger.info("Initialized boto3 bedrock-runtime client")
    return _bedrock_client


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
    """Bedrockの返却から最初に見つかった数値配列（list[float] or list[list[float]]）を返す。"""
    if isinstance(obj, list):
        if len(obj) == 0:
            return obj
        if not isinstance(obj[0], (list, dict)) and _is_number_sequence(obj):
            return obj
        if isinstance(obj[0], list) and all(_is_number_sequence(x) for x in obj if isinstance(x, list)):
            return obj
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
        for v in obj.values():
            cand = _find_first_float_array(v)
            if cand is not None:
                return cand
        return None

    return None


# ===== boto3 直叩き =====

def _bedrock_embed_documents_boto3(texts: List[str], input_type: str) -> List[List[float]]:
    client = _get_bedrock_client()
    body = {
        "texts": texts,
        # Cohere v4 は texts キーを要求。input_type は仕様により省略可能だが残す場合は以下行を有効化。
        # "input_type": input_type,
    }
    resp = client.invoke_model(
        modelId=settings.BEDROCK_EMBEDDINGS_MODEL_ID,
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json",
    )
    payload = json.loads(resp["body"].read()) if hasattr(resp.get("body"), "read") else json.loads(resp["body"])  # type: ignore
    arr = _find_first_float_array(payload)
    if arr is None:
        logger.error(f"boto3 bedrock response keys: {list(payload.keys()) if isinstance(payload, dict) else type(payload)}")
        raise ValueError("boto3: Failed to locate float embeddings in response")
    return arr  # type: ignore


def _bedrock_embed_query_boto3(query: str) -> List[float]:
    client = _get_bedrock_client()
    body = {
        "texts": [query],
        # "input_type": "search_query",
    }
    resp = client.invoke_model(
        modelId=settings.BEDROCK_EMBEDDINGS_MODEL_ID,
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json",
    )
    payload = json.loads(resp["body"].read()) if hasattr(resp.get("body"), "read") else json.loads(resp["body"])  # type: ignore
    arr = _find_first_float_array(payload)
    if arr is None:
        logger.error(f"boto3 bedrock query response keys: {list(payload.keys()) if isinstance(payload, dict) else type(payload)}")
        raise ValueError("boto3: Failed to locate float embedding in response")
    if isinstance(arr, list) and len(arr) > 0 and isinstance(arr[0], (int, float)):
        return arr  # type: ignore
    if isinstance(arr, list) and len(arr) > 0 and isinstance(arr[0], list):
        return arr[0]  # type: ignore
    return arr  # type: ignore


def embed_texts(texts: List[str], input_type: str = "search_document", model: str = None) -> np.ndarray:
    """Bedrock/Cohereでテキストを埋め込み。Bedrockはlangchain_aws→失敗時boto3にフォールバック。"""
    client = get_embeddings_client()
    embeddings: List[np.ndarray] = []

    for i in range(0, len(texts), settings.BATCH_SIZE):
        batch = texts[i:i + settings.BATCH_SIZE]
        try:
            if settings.USE_BEDROCK:
                raw = None
                try:
                    raw = client.embed_documents(batch)  # langchain_aws
                except Exception as e:
                    logger.warning(f"langchain_aws embed_documents failed, falling back to boto3: {e}")

                arr = _find_first_float_array(raw) if raw is not None else None
                # フォールバック条件: 数値配列に解決できない/型がstr/['float']など
                if arr is None or (isinstance(raw, list) and raw == ["float"]) or isinstance(raw, str):
                    logger.warning("Falling back to boto3 bedrock-runtime for embeddings")
                    arr = _bedrock_embed_documents_boto3(batch, input_type)

                batch_embeddings = np.array(arr, dtype=np.float32)
                if batch_embeddings.ndim == 1:
                    batch_embeddings = batch_embeddings.reshape(1, -1)
            else:
                if model is None:
                    model = settings.COHERE_MODEL
                response = client.embed(texts=batch, model=model, input_type=input_type)
                batch_embeddings = np.array(response.embeddings, dtype=np.float32)

            embeddings.append(batch_embeddings)
            logger.info(f"Embedded batch {i//settings.BATCH_SIZE + 1}")

        except Exception as e:
            logger.error(f"Failed to embed batch {i//settings.BATCH_SIZE + 1}: {e}")
            logger.error(f"Batch sample: {batch[:2] if batch else 'empty'}")
            raise

    return l2_normalize(np.vstack(embeddings))


def embed_query(query: str, model: str = None) -> np.ndarray:
    client = get_embeddings_client()

    try:
        if settings.USE_BEDROCK:
            raw = None
            try:
                raw = client.embed_query(query)
            except Exception as e:
                logger.warning(f"langchain_aws embed_query failed, falling back to boto3: {e}")

            arr = _find_first_float_array(raw) if raw is not None else None
            if arr is None or isinstance(raw, str):
                logger.warning("Falling back to boto3 bedrock-runtime for query embedding")
                arr = _bedrock_embed_query_boto3(query)

            emb = np.array(arr, dtype=np.float32)
            if emb.ndim == 1:
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

