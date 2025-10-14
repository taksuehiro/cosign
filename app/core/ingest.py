"""
ベンダーデータの取り込みとテキスト生成
"""
import json
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


def load_vendors_data(json_path: str) -> List[Dict[str, Any]]:
    """vendors.jsonを読み込み"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} vendors from {json_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load vendors data from {json_path}: {e}")
        raise


def build_text_from_vendor(vendor: Dict[str, Any]) -> str:
    """ベンダー情報からテキストを構築"""
    text_parts = []
    
    # name
    if vendor.get('name'):
        text_parts.append(vendor['name'])
    
    # type
    if vendor.get('type'):
        text_parts.append(vendor['type'])
    
    # capabilities
    if vendor.get('capabilities') and isinstance(vendor['capabilities'], list):
        capabilities_text = ' '.join(vendor['capabilities'])
        text_parts.append(capabilities_text)
    
    # offerings.description_short
    if vendor.get('offerings', {}).get('description_short'):
        text_parts.append(vendor['offerings']['description_short'])
    
    # notes
    if vendor.get('notes'):
        text_parts.append(vendor['notes'])
    
    return ' '.join(text_parts)


def build_metadata_from_vendor(vendor: Dict[str, Any]) -> Dict[str, Any]:
    """ベンダー情報からメタデータを構築"""
    meta = {}
    
    # vendor_id
    if vendor.get('vendor_id'):
        meta['vendor_id'] = vendor['vendor_id']
    
    # name
    if vendor.get('name'):
        meta['name'] = vendor['name']
    
    # type
    if vendor.get('type'):
        meta['type'] = vendor['type']
    
    # corporate.listed
    if vendor.get('corporate', {}).get('listed'):
        meta['listed'] = vendor['corporate']['listed']
    
    # delivery.deployment
    if vendor.get('delivery', {}).get('deployment'):
        meta['deployment'] = vendor['delivery']['deployment']
    
    return meta


def process_vendors_data(vendors: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """ベンダーデータを処理してテキストとメタデータを生成"""
    texts = []
    metadata = []
    
    for vendor in vendors:
        try:
            # テキスト生成
            text = build_text_from_vendor(vendor)
            if not text.strip():
                logger.warning(f"Skipping vendor {vendor.get('vendor_id', 'unknown')} - empty text")
                continue
            
            # メタデータ生成
            meta = build_metadata_from_vendor(vendor)
            
            texts.append(text)
            metadata.append(meta)
            
        except Exception as e:
            logger.error(f"Failed to process vendor {vendor.get('vendor_id', 'unknown')}: {e}")
            continue
    
    logger.info(f"Processed {len(texts)} vendors successfully")
    return texts, metadata

