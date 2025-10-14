"""
環境変数設定
"""
import os
from typing import Optional
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


class Settings:
    """アプリケーション設定"""
    
    def __init__(self):
        # Cohere API設定
        self.COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
        
        # AWS設定
        self.AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-1")
        self.S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME")
        self.S3_PREFIX: str = os.getenv("S3_PREFIX", "faiss/exp")
        
        # ベクトルストア設定
        self.VECTOR_DIR: str = os.getenv("VECTOR_DIR", "/tmp/vectorstore")
        self.INDEX_NAME: str = os.getenv("INDEX_NAME", "vendor_cohere_v1")
        self.JSON_PATH: str = os.getenv("JSON_PATH", "data/vendors.json")
        
        # Cohere設定
        self.COHERE_MODEL: str = "embed-multilingual-v3.0"
        self.BATCH_SIZE: int = 64
        
        # 設定値の検証
        if not self.COHERE_API_KEY:
            raise ValueError("COHERE_API_KEY is required")
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(self.VECTOR_DIR, exist_ok=True)


# グローバル設定インスタンス
settings = Settings()
