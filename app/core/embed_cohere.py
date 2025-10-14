"""
埋め込み処理（Bedrock/Cohere対応, Bedrockのfloat構造対応版）
"""
import numpy as np
import logging
from typing import List
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


def embed_texts(texts: List[str], input_type: str = "search_document", model: str = None) -> np.ndarray:
    """Bedrock/Cohereでテキストを埋め込み。Bedrockのfloat構造に厳密対応。"""
    client = get_embeddings_client()
    embeddings: List[np.ndarray] = []

    for i in range(0, len(texts), settings.BATCH_SIZE):
        batch = texts[i:i + settings.BATCH_SIZE]
        try:
            if settings.USE_BEDROCK:
                batch_embeddings = client.embed_documents(batch)

                # Bedrockからの返り値が [{"embedding": {"float": [...]}}] の場合に対応
                if isinstance(batch_embeddings, list) and batch_embeddings and isinstance(batch_embeddings[0], dict):
                    new_embeddings = []
                    for item in batch_embeddings:
                        if "embedding" in item and isinstance(item["embedding"], dict):
                            floats = item["embedding"].get("float")
                            if floats is not None:
                                new_embeddings.append(floats)
                        elif "embeddings" in item and isinstance(item["embeddings"], dict):
                            floats = item["embeddings"].get("float")
                            if floats is not None:
                                new_embeddings.append(floats)
                        elif "float" in item:
                            new_embeddings.append(item["float"])
                        else:
                            # 想定外: そのまま追加（後段のnp.arrayで失敗し、ログに出る）
                            new_embeddings.append(item)
                    batch_embeddings = new_embeddings

                elif isinstance(batch_embeddings, dict):
                    if "embedding" in batch_embeddings and isinstance(batch_embeddings["embedding"], dict) and "float" in batch_embeddings["embedding"]:
                        batch_embeddings = batch_embeddings["embedding"]["float"]
                    elif "embeddings" in batch_embeddings and isinstance(batch_embeddings["embeddings"], dict) and "float" in batch_embeddings["embeddings"]:
                        batch_embeddings = batch_embeddings["embeddings"]["float"]
                    elif "float" in batch_embeddings:
                        batch_embeddings = batch_embeddings["float"]

                # 最終的にfloat32へ
                batch_embeddings = np.array(batch_embeddings, dtype=np.float32)

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
            logger.error(f"Batch sample: {batch[:2] if batch else 'empty'}")
            raise

    return l2_normalize(np.vstack(embeddings))


def embed_query(query: str, model: str = None) -> np.ndarray:
    client = get_embeddings_client()

    if settings.USE_BEDROCK:
        embedding = client.embed_query(query)
        if isinstance(embedding, dict):
            if "embedding" in embedding and isinstance(embedding["embedding"], dict) and "float" in embedding["embedding"]:
                embedding = embedding["embedding"]["float"]
            elif "embeddings" in embedding and isinstance(embedding["embeddings"], dict) and "float" in embedding["embeddings"]:
                embedding = embedding["embeddings"]["float"]
            elif "float" in embedding:
                embedding = embedding["float"]
        embedding = np.array(embedding, dtype=np.float32)
    else:
        if model is None:
            model = settings.COHERE_MODEL
        response = client.embed(texts=[query], model=model, input_type="search_query")
        embedding = np.array(response.embeddings[0], dtype=np.float32)

    return l2_normalize(embedding.reshape(1, -1))[0]

