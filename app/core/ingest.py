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
    """ベンダー情報からテキストを構築（すべてのフィールドを安全に文字列化）"""
    text_parts = []
    
    # すべてのフィールドを安全に文字列化して処理
    for key, value in vendor.items():
        if value is None:
            continue
            
        if isinstance(value, str):
            # 文字列はそのまま追加
            if value.strip():  # 空文字列は除外
                text_parts.append(value)
        elif isinstance(value, list):
            # リストは要素を結合
            if value:  # 空リストは除外
                list_text = ' '.join(str(item) for item in value if item is not None)
                if list_text.strip():
                    text_parts.append(list_text)
        elif isinstance(value, dict):
            # 辞書は再帰的に処理
            dict_text = _flatten_dict_to_text(value)
            if dict_text.strip():
                text_parts.append(dict_text)
        else:
            # その他の型は文字列化
            text_parts.append(str(value))
    
    return ' '.join(text_parts)


def _flatten_dict_to_text(data: Dict[str, Any], prefix: str = "") -> str:
    """辞書を平坦化してテキストに変換"""
    text_parts = []
    
    for key, value in data.items():
        if value is None:
            continue
            
        if isinstance(value, str):
            if value.strip():
                text_parts.append(value)
        elif isinstance(value, list):
            if value:
                list_text = ' '.join(str(item) for item in value if item is not None)
                if list_text.strip():
                    text_parts.append(list_text)
        elif isinstance(value, dict):
            # 再帰的に処理
            nested_text = _flatten_dict_to_text(value)
            if nested_text.strip():
                text_parts.append(nested_text)
        else:
            text_parts.append(str(value))
    
    return ' '.join(text_parts)


def build_metadata_from_vendor(vendor: Dict[str, Any]) -> Dict[str, Any]:
    """ベンダー情報からメタデータを構築（すべての値を安全に文字列化）"""
    meta = {}
    
    # vendor_id
    if vendor.get('vendor_id'):
        meta['vendor_id'] = str(vendor['vendor_id'])
    
    # name
    if vendor.get('name'):
        meta['name'] = str(vendor['name'])
    
    # type
    if vendor.get('type'):
        meta['type'] = str(vendor['type'])
    
    # corporate.listed
    if vendor.get('corporate', {}).get('listed'):
        meta['listed'] = str(vendor['corporate']['listed'])
    
    # delivery.deployment
    if vendor.get('delivery', {}).get('deployment'):
        meta['deployment'] = str(vendor['delivery']['deployment'])
    
    # 追加のメタデータフィールドも安全に文字列化
    if vendor.get('commercials', {}).get('man_month_jpy'):
        meta['man_month_jpy'] = str(vendor['commercials']['man_month_jpy'])
    
    if vendor.get('corporate', {}).get('employees_band'):
        meta['employees_band'] = str(vendor['corporate']['employees_band'])
    
    return meta


def process_vendors_data(vendors: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """ベンダーデータを処理してテキストとメタデータを生成"""
    texts = []
    metadata = []
    failed_count = 0
    
    for i, vendor in enumerate(vendors):
        try:
            # デバッグ情報
            vendor_id = vendor.get('vendor_id', f'vendor_{i}')
            logger.debug(f"Processing vendor {i+1}/{len(vendors)}: {vendor_id}")
            
            # テキスト生成
            text = build_text_from_vendor(vendor)
            if not text.strip():
                logger.warning(f"Skipping vendor {vendor_id} - empty text")
                continue
            
            # メタデータ生成
            meta = build_metadata_from_vendor(vendor)
            
            texts.append(text)
            metadata.append(meta)
            
            logger.debug(f"Successfully processed vendor {vendor_id}")
            
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to process vendor {vendor.get('vendor_id', f'vendor_{i}')}: {e}")
            logger.error(f"Vendor data sample: {str(vendor)[:200]}...")
            continue
    
    logger.info(f"Processed {len(texts)} vendors successfully, {failed_count} failed")
    return texts, metadata

