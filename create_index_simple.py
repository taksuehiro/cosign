#!/usr/bin/env python3
"""
シンプルなFAISSインデックス作成スクリプト
"""
import os
import sys
import json
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """シンプルなインデックス作成"""
    try:
        # 1. vendors.jsonの存在確認
        json_path = "vendors.json"
        if not os.path.exists(json_path):
            logger.error(f"❌ {json_path} not found")
            return False
        
        logger.info(f"✅ Found {json_path}")
        
        # 2. データ読み込み
        with open(json_path, 'r', encoding='utf-8') as f:
            vendors = json.load(f)
        
        logger.info(f"✅ Loaded {len(vendors)} vendors")
        
        # 3. 簡単なテキスト生成
        texts = []
        metadata = []
        
        for i, vendor in enumerate(vendors):
            # ベンダー情報からテキストを生成
            text_parts = []
            if vendor.get('name'):
                text_parts.append(f"会社名: {vendor['name']}")
            if vendor.get('description'):
                text_parts.append(f"説明: {vendor['description']}")
            if vendor.get('services'):
                text_parts.append(f"サービス: {', '.join(vendor['services'])}")
            
            text = " | ".join(text_parts)
            texts.append(text)
            
            # メタデータ
            meta = {
                "vendor_id": vendor.get('id', f"vendor_{i}"),
                "name": vendor.get('name', ''),
                "type": vendor.get('type', ''),
                "listed": vendor.get('listed', False)
            }
            metadata.append(meta)
        
        logger.info(f"✅ Generated {len(texts)} texts")
        
        # 4. ローカルディレクトリ作成
        vector_dir = "./vectorstore"
        os.makedirs(vector_dir, exist_ok=True)
        
        # 5. 簡単なインデックスファイル作成（ダミー）
        index_path = os.path.join(vector_dir, "vendor_cohere_v3.index")
        meta_path = os.path.join(vector_dir, "vendor_cohere_v3.meta")
        
        # ダミーファイル作成
        with open(index_path, 'w') as f:
            f.write("dummy_index_file")
        
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Created dummy index files:")
        logger.info(f"  - {index_path}")
        logger.info(f"  - {meta_path}")
        
        # 6. 結果表示
        logger.info("")
        logger.info("🎯 Next steps:")
        logger.info("1. Run the actual index creation on the server:")
        logger.info("   curl -X POST 'https://api.3ii.biz/api/v1/index' \\")
        logger.info("     -H 'Content-Type: application/json' \\")
        logger.info("     -d '{\"index_name\": \"vendor_cohere_v3\", \"save_to_s3\": true}'")
        logger.info("")
        logger.info("2. Test the search:")
        logger.info("   curl -X POST 'https://api.3ii.biz/search' \\")
        logger.info("     -H 'Content-Type: application/json' \\")
        logger.info("     -d '{\"q\": \"生成AIとは\"}'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
