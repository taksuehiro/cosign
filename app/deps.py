"""
共有依存関係（DI）
"""
import boto3
from typing import Optional
from functools import lru_cache
from app.config import settings


@lru_cache()
def get_s3_client():
    """S3クライアントを取得（シングルトン）"""
    if not settings.S3_BUCKET_NAME:
        return None
    
    return boto3.client(
        's3',
        region_name=settings.AWS_REGION
    )


def get_s3_bucket_name() -> Optional[str]:
    """S3バケット名を取得"""
    return settings.S3_BUCKET_NAME


def get_s3_prefix() -> str:
    """S3プレフィックスを取得"""
    return settings.S3_PREFIX

