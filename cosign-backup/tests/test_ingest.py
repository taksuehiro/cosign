"""
データ取り込みテスト
"""
import pytest
import json
import tempfile
import os
from app.core.ingest import load_vendors_data, process_vendors_data, build_text_from_vendor, build_metadata_from_vendor


def test_load_vendors_data():
    """vendors.json読み込みテスト"""
    # テスト用のベンダーデータ
    test_vendors = [
        {
            "vendor_id": "V-Test1",
            "name": "Test Company 1",
            "type": "スクラッチ",
            "capabilities": ["AI", "機械学習"],
            "offerings": {
                "description_short": "AI開発支援"
            },
            "corporate": {
                "listed": "未上場"
            },
            "delivery": {
                "deployment": "ハイブリッド"
            },
            "notes": "テスト会社1"
        }
    ]
    
    # 一時ファイル作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_vendors, f, ensure_ascii=False)
        temp_path = f.name
    
    try:
        # データ読み込みテスト
        vendors = load_vendors_data(temp_path)
        assert len(vendors) == 1
        assert vendors[0]["vendor_id"] == "V-Test1"
        assert vendors[0]["name"] == "Test Company 1"
        
    finally:
        os.unlink(temp_path)


def test_build_text_from_vendor():
    """ベンダーからテキスト構築テスト"""
    vendor = {
        "vendor_id": "V-Test1",
        "name": "Test Company 1",
        "type": "スクラッチ",
        "capabilities": ["AI", "機械学習"],
        "offerings": {
            "description_short": "AI開発支援"
        },
        "notes": "テスト会社1"
    }
    
    text = build_text_from_vendor(vendor)
    expected_parts = ["Test Company 1", "スクラッチ", "AI 機械学習", "AI開発支援", "テスト会社1"]
    
    for part in expected_parts:
        assert part in text


def test_build_metadata_from_vendor():
    """ベンダーからメタデータ構築テスト"""
    vendor = {
        "vendor_id": "V-Test1",
        "name": "Test Company 1",
        "type": "スクラッチ",
        "corporate": {
            "listed": "未上場"
        },
        "delivery": {
            "deployment": "ハイブリッド"
        }
    }
    
    meta = build_metadata_from_vendor(vendor)
    
    assert meta["vendor_id"] == "V-Test1"
    assert meta["name"] == "Test Company 1"
    assert meta["type"] == "スクラッチ"
    assert meta["listed"] == "未上場"
    assert meta["deployment"] == "ハイブリッド"


def test_process_vendors_data():
    """ベンダーデータ処理テスト"""
    vendors = [
        {
            "vendor_id": "V-Test1",
            "name": "Test Company 1",
            "type": "スクラッチ",
            "capabilities": ["AI"],
            "offerings": {
                "description_short": "AI開発"
            },
            "corporate": {
                "listed": "未上場"
            },
            "delivery": {
                "deployment": "ハイブリッド"
            },
            "notes": "テスト1"
        },
        {
            "vendor_id": "V-Test2",
            "name": "Test Company 2",
            "type": "SaaS",
            "capabilities": ["RAG"],
            "offerings": {
                "description_short": "RAG支援"
            },
            "corporate": {
                "listed": "上場"
            },
            "delivery": {
                "deployment": "SaaS"
            },
            "notes": "テスト2"
        }
    ]
    
    texts, metadata = process_vendors_data(vendors)
    
    assert len(texts) == 2
    assert len(metadata) == 2
    
    # テキスト内容確認
    assert "Test Company 1" in texts[0]
    assert "AI" in texts[0]
    assert "Test Company 2" in texts[1]
    assert "RAG" in texts[1]
    
    # メタデータ確認
    assert metadata[0]["vendor_id"] == "V-Test1"
    assert metadata[1]["vendor_id"] == "V-Test2"
    assert metadata[0]["listed"] == "未上場"
    assert metadata[1]["listed"] == "上場"
