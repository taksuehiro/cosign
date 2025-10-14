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
        # AWS設定
        self.AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-1")
        self.AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        # Bedrock設定
        self.BEDROCK_EMBEDDINGS_MODEL_ID: str = os.getenv("BEDROCK_EMBEDDINGS_MODEL_ID", "cohere.embed-v4:0")
        self.USE_BEDROCK: bool = os.getenv("USE_BEDROCK", "true").lower() == "true"
        
        # Cohere直API設定（Bedrock不使用時のみ必要）
        self.COHERE_API_KEY: Optional[str] = os.getenv("COHERE_API_KEY")
        
        # S3/FAISS設定
        self.S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME")
        self.S3_PREFIX: str = os.getenv("S3_PREFIX", "faiss/exp")
        self.VECTOR_DIR: str = os.getenv("VECTOR_DIR", "/tmp/vectorstore")
        self.INDEX_NAME: str = os.getenv("INDEX_NAME", "vendor_cohere_v4")
        self.JSON_PATH: str = os.getenv("JSON_PATH", "data/vendors.json")
        
        # 埋め込み設定
        self.COHERE_MODEL: str = "embed-multilingual-v3.0"
        self.BATCH_SIZE: int = 64
        
        # 設定値の検証
        if not self.USE_BEDROCK and not self.COHERE_API_KEY:
            raise ValueError("COHERE_API_KEY is required when USE_BEDROCK is False")
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(self.VECTOR_DIR, exist_ok=True)


# グローバル設定インスタンス
settings = Settings()
