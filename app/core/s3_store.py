"""
S3ストレージ管理
"""
import os
import logging
from typing import Optional, Tuple
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class S3Store:
    """S3ストレージ管理クラス"""
    
    def __init__(self, bucket_name: str, prefix: str, region: str = "ap-northeast-1"):
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.region = region
        self.client = None
        
        if bucket_name:
            try:
                self.client = boto3.client('s3', region_name=region)
                logger.info(f"Initialized S3 client for bucket: {bucket_name}")
            except NoCredentialsError:
                logger.warning("AWS credentials not found, S3 operations will be disabled")
                self.client = None
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self.client = None
    
    def upload_index(self, index_name: str, local_index_path: str, local_meta_path: str) -> bool:
        """
        インデックスとメタデータをS3にアップロード
        
        Args:
            index_name: インデックス名
            local_index_path: ローカルインデックスファイルパス
            local_meta_path: ローカルメタデータファイルパス
        
        Returns:
            アップロード成功フラグ
        """
        if not self.client:
            logger.warning("S3 client not available, skipping upload")
            return False
        
        try:
            # S3キー生成
            s3_index_key = f"{self.prefix}/{index_name}/index.faiss"
            s3_meta_key = f"{self.prefix}/{index_name}/meta.json"
            
            # インデックスファイルアップロード
            self.client.upload_file(local_index_path, self.bucket_name, s3_index_key)
            logger.info(f"Uploaded index to s3://{self.bucket_name}/{s3_index_key}")
            
            # メタデータファイルアップロード
            self.client.upload_file(local_meta_path, self.bucket_name, s3_meta_key)
            logger.info(f"Uploaded metadata to s3://{self.bucket_name}/{s3_meta_key}")
            
            return True
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            return False
    
    def download_index(self, index_name: str, local_index_path: str, local_meta_path: str) -> bool:
        """
        インデックスとメタデータをS3からダウンロード
        
        Args:
            index_name: インデックス名
            local_index_path: ローカルインデックスファイルパス
            local_meta_path: ローカルメタデータファイルパス
        
        Returns:
            ダウンロード成功フラグ
        """
        if not self.client:
            logger.warning("S3 client not available, skipping download")
            return False
        
        try:
            # S3キー生成
            s3_index_key = f"{self.prefix}/{index_name}/index.faiss"
            s3_meta_key = f"{self.prefix}/{index_name}/meta.json"
            
            # ローカルディレクトリ作成
            os.makedirs(os.path.dirname(local_index_path), exist_ok=True)
            
            # インデックスファイルダウンロード
            self.client.download_file(self.bucket_name, s3_index_key, local_index_path)
            logger.info(f"Downloaded index from s3://{self.bucket_name}/{s3_index_key}")
            
            # メタデータファイルダウンロード
            self.client.download_file(self.bucket_name, s3_meta_key, local_meta_path)
            logger.info(f"Downloaded metadata from s3://{self.bucket_name}/{s3_meta_key}")
            
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Index {index_name} not found in S3")
            else:
                logger.error(f"S3 download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 download: {e}")
            return False
    
    def index_exists(self, index_name: str) -> bool:
        """
        インデックスがS3に存在するかチェック
        
        Args:
            index_name: インデックス名
        
        Returns:
            存在フラグ
        """
        if not self.client:
            return False
        
        try:
            s3_index_key = f"{self.prefix}/{index_name}/index.faiss"
            self.client.head_object(Bucket=self.bucket_name, Key=s3_index_key)
            return True
        except ClientError:
            return False

