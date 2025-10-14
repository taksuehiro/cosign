"""
インデックス作成エンドポイント
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from app.schemas import IndexRequest, IndexResponse
from app.core.ingest import load_vendors_data, process_vendors_data
from app.core.embed_cohere import embed_texts
from app.core.faiss_store import FAISSStore, create_store_paths
from app.core.s3_store import S3Store
from app.config import settings
from app.deps import get_s3_client, get_s3_bucket_name, get_s3_prefix

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/index", response_model=IndexResponse)
async def create_index(request: IndexRequest):
    """
    ベンダーデータからインデックスを作成
    
    Args:
        request: インデックス作成リクエスト
    
    Returns:
        インデックス作成結果
    """
    try:
        # パラメータ設定
        index_name = request.index_name or settings.INDEX_NAME
        json_path = request.json_path or settings.JSON_PATH
        save_to_s3 = request.save_to_s3
        
        logger.info(f"Starting index creation: {index_name}")
        
        # 1. ベンダーデータ読み込み
        vendors = load_vendors_data(json_path)
        if not vendors:
            raise HTTPException(status_code=400, detail="No vendors data found")
        
        # 2. テキストとメタデータ生成
        texts, metadata = process_vendors_data(vendors)
        if not texts:
            raise HTTPException(status_code=400, detail="No valid texts generated")
        
        # 3. 埋め込み生成
        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = embed_texts(texts, input_type="search_document")
        
        # 4. FAISSインデックス構築
        index_path, meta_path = create_store_paths(settings.VECTOR_DIR, index_name)
        store = FAISSStore(index_path, meta_path)
        store.build_index(embeddings)
        store.add_metadata(metadata)
        
        # 5. ローカル保存
        store.save()
        saved_local = True
        logger.info(f"Saved index locally: {index_path}")
        
        # 6. S3保存（オプション）
        saved_s3 = False
        if save_to_s3:
            s3_client = get_s3_client()
            s3_bucket = get_s3_bucket_name()
            s3_prefix = get_s3_prefix()
            
            if s3_client and s3_bucket:
                s3_store = S3Store(s3_bucket, s3_prefix)
                saved_s3 = s3_store.upload_index(index_name, index_path, meta_path)
                if saved_s3:
                    logger.info(f"Uploaded index to S3: {s3_bucket}/{s3_prefix}/{index_name}")
                else:
                    logger.warning("Failed to upload index to S3")
            else:
                logger.warning("S3 not configured, skipping upload")
        
        return IndexResponse(
            indexed=len(texts),
            index_name=index_name,
            saved_local=saved_local,
            saved_s3=saved_s3
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Index creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Index creation failed: {str(e)}")

