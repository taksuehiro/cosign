"""
埋め込み・検索テスト
"""
import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch
from app.core.embed_cohere import embed_texts, embed_query, l2_normalize
from app.core.faiss_store import FAISSStore


def test_l2_normalize():
    """L2正規化テスト"""
    # テストベクトル
    vectors = np.array([[3, 4], [1, 1], [0, 0]])
    
    normalized = l2_normalize(vectors)
    
    # 各ベクトルのノルムが1になることを確認
    norms = np.linalg.norm(normalized, axis=1)
    np.testing.assert_allclose(norms, 1.0, rtol=1e-10)
    
    # ゼロベクトルの処理確認
    zero_vector = np.array([[0, 0]])
    normalized_zero = l2_normalize(zero_vector)
    assert np.allclose(normalized_zero, [[0, 0]])


@patch('app.core.embed_cohere.get_cohere_client')
def test_embed_texts(mock_get_client):
    """埋め込み生成テスト（モック使用）"""
    # モック設定
    mock_client = Mock()
    mock_response = Mock()
    mock_response.embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    mock_client.embed.return_value = mock_response
    mock_get_client.return_value = mock_client
    
    texts = ["テストテキスト1", "テストテキスト2"]
    embeddings = embed_texts(texts)
    
    # 形状確認
    assert embeddings.shape == (2, 3)
    
    # 正規化確認
    norms = np.linalg.norm(embeddings, axis=1)
    np.testing.assert_allclose(norms, 1.0, rtol=1e-10)


@patch('app.core.embed_cohere.get_cohere_client')
def test_embed_query(mock_get_client):
    """クエリ埋め込みテスト（モック使用）"""
    # モック設定
    mock_client = Mock()
    mock_response = Mock()
    mock_response.embeddings = [[0.1, 0.2, 0.3]]
    mock_client.embed.return_value = mock_response
    mock_get_client.return_value = mock_client
    
    query = "テストクエリ"
    embedding = embed_query(query)
    
    # 形状確認
    assert embedding.shape == (3,)
    
    # 正規化確認
    norm = np.linalg.norm(embedding)
    np.testing.assert_allclose(norm, 1.0, rtol=1e-10)


def test_faiss_store():
    """FAISSストアテスト"""
    # テスト用の埋め込みベクトル
    embeddings = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [0.5, 0.5, 0]
    ]).astype('float32')
    
    # 正規化
    embeddings = l2_normalize(embeddings)
    
    # テスト用のメタデータ
    metadata = [
        {"vendor_id": "V-1", "name": "Company 1"},
        {"vendor_id": "V-2", "name": "Company 2"},
        {"vendor_id": "V-3", "name": "Company 3"},
        {"vendor_id": "V-4", "name": "Company 4"}
    ]
    
    # 一時ファイル作成
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index.faiss")
        meta_path = os.path.join(temp_dir, "test_meta.json")
        
        # ストア作成・構築
        store = FAISSStore(index_path, meta_path)
        store.build_index(embeddings)
        store.add_metadata(metadata)
        
        # 保存
        store.save()
        
        # 新しいストアで読み込み
        new_store = FAISSStore(index_path, meta_path)
        new_store.load()
        
        # 検索テスト
        query_vector = np.array([1, 0, 0])  # 最初のベクトルに近い
        scores, indices = new_store.search(query_vector, k=2)
        
        # 結果確認
        assert len(scores) == 2
        assert len(indices) == 2
        assert scores[0] >= scores[1]  # スコア順
        
        # メタデータ取得テスト
        meta_results = new_store.get_metadata_by_indices(indices)
        assert len(meta_results) == 2
        assert meta_results[0]["vendor_id"] == "V-1"  # 最高スコアのアイテム
