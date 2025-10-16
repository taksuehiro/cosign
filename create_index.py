#!/usr/bin/env python3
"""
ローカル環境でFAISSインデックスを作成してS3にアップロードするスクリプト
"""
import os
import sys
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "app"))

# 直接インポート
try:
    from app.core.ingest import load_vendors_data, process_vendors_data
    from app.core.embed_cohere import embed_texts
    from app.core.faiss_store import FAISSStore, create_store_paths
    from app.core.s3_store import S3Store
    from app.config import settings
except ImportError:
    # 相対インポートを試す
    from core.ingest import load_vendors_data, process_vendors_data
    from core.embed_cohere import embed_texts
    from core.faiss_store import FAISSStore, create_store_paths
    from core.s3_store import S3Store
    from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """FAISSインデックスを作成してS3にアップロード"""
    try:
        # 1. データ読み込み
        logger.info("Loading vendors data...")
        vendors = load_vendors_data(settings.JSON_PATH)
        if not vendors:
            raise ValueError("No vendors data found")
        
        logger.info(f"Loaded {len(vendors)} vendors")
        
        # 2. テキストとメタデータ生成
        logger.info("Processing vendors data...")
        texts, metadata = process_vendors_data(vendors)
        if not texts:
            raise ValueError("No valid texts generated")
        
        logger.info(f"Generated {len(texts)} texts for embedding")
        
        # 3. 埋め込み生成
        logger.info("Generating embeddings...")
        embeddings = embed_texts(texts, input_type="search_document")
        
        logger.info(f"Generated embeddings shape: {embeddings.shape}")
        
        # 4. FAISSインデックス構築
        logger.info("Building FAISS index...")
        index_path, meta_path = create_store_paths("./vectorstore", settings.INDEX_NAME)
        
        # ディレクトリ作成
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        store = FAISSStore(index_path, meta_path)
        store.build_index(embeddings)
        store.add_metadata(metadata)
        store.save()
        
        logger.info(f"Saved index locally: {index_path}")
        
        # 5. S3アップロード
        logger.info("Uploading to S3...")
        s3_store = S3Store(settings.S3_BUCKET_NAME, settings.S3_PREFIX)
        success = s3_store.upload_index(settings.INDEX_NAME, index_path, meta_path)
        
        if success:
            logger.info("✅ Index successfully uploaded to S3")
            logger.info(f"S3 location: s3://{settings.S3_BUCKET_NAME}/{settings.S3_PREFIX}/{settings.INDEX_NAME}/")
        else:
            logger.error("❌ Failed to upload index to S3")
            sys.exit(1)
            
        # 6. 検索テスト（オプション）
        logger.info("Testing search functionality...")
        test_query = "生成AIとは"
        test_embedding = embed_texts([test_query], input_type="search_query")[0]
        scores, indices = store.search(test_embedding, k=3)
        
        if len(scores) > 0:
            logger.info(f"✅ Search test successful: found {len(scores)} results")
            for i, (score, idx) in enumerate(zip(scores, indices)):
                logger.info(f"  Result {i+1}: score={score:.4f}, index={idx}")
        else:
            logger.warning("⚠️ Search test returned no results")
            
    except Exception as e:
        logger.error(f"❌ Index creation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
