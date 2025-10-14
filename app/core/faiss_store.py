"""
FAISSベクトルストア管理
"""
import os
import json
import logging
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import orjson

logger = logging.getLogger(__name__)


class FAISSStore:
    """FAISSベクトルストア管理クラス"""
    
    def __init__(self, index_path: str, meta_path: str):
        self.index_path = index_path
        self.meta_path = meta_path
        self.index = None
        self.metadata = []
    
    def build_index(self, embeddings: np.ndarray) -> None:
        """FAISSインデックスを構築"""
        dimension = embeddings.shape[1]
        
        # IndexFlatIP（内積）を使用
        self.index = faiss.IndexFlatIP(dimension)
        
        # ベクトルを追加
        self.index.add(embeddings.astype('float32'))
        
        logger.info(f"Built FAISS index with {self.index.ntotal} vectors, dimension {dimension}")
    
    def add_metadata(self, metadata: List[Dict[str, Any]]) -> None:
        """メタデータを追加"""
        self.metadata = metadata
        logger.info(f"Added {len(metadata)} metadata entries")
    
    def save(self) -> None:
        """インデックスとメタデータを保存"""
        if self.index is None:
            raise ValueError("Index not built yet")
        
        # ディレクトリ作成
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # FAISSインデックス保存
        faiss.write_index(self.index, self.index_path)
        
        # メタデータ保存
        with open(self.meta_path, 'wb') as f:
            f.write(orjson.dumps(self.metadata))
        
        logger.info(f"Saved index to {self.index_path} and metadata to {self.meta_path}")
    
    def load(self) -> None:
        """インデックスとメタデータを読み込み"""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"Index file not found: {self.index_path}")
        
        if not os.path.exists(self.meta_path):
            raise FileNotFoundError(f"Metadata file not found: {self.meta_path}")
        
        # FAISSインデックス読み込み
        self.index = faiss.read_index(self.index_path)
        
        # メタデータ読み込み
        with open(self.meta_path, 'rb') as f:
            self.metadata = orjson.loads(f.read())
        
        logger.info(f"Loaded index with {self.index.ntotal} vectors and {len(self.metadata)} metadata entries")
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        k: int = 10,
        threshold: Optional[float] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        ベクトル検索を実行
        
        Args:
            query_embedding: クエリ埋め込みベクトル
            k: 検索結果数
            threshold: スコア閾値
        
        Returns:
            (scores, indices): スコアとインデックスのタプル
        """
        if self.index is None:
            raise ValueError("Index not loaded")
        
        # 検索実行
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1).astype('float32'), 
            k
        )
        
        scores = scores[0]  # バッチサイズ1なので最初の要素
        indices = indices[0]
        
        # 閾値フィルタリング
        if threshold is not None:
            valid_mask = scores >= threshold
            scores = scores[valid_mask]
            indices = indices[valid_mask]
        
        logger.info(f"Search returned {len(scores)} results")
        return scores, indices
    
    def get_metadata_by_indices(self, indices: np.ndarray) -> List[Dict[str, Any]]:
        """インデックスに対応するメタデータを取得"""
        return [self.metadata[i] for i in indices if i < len(self.metadata)]
    
    def is_loaded(self) -> bool:
        """インデックスが読み込まれているかチェック"""
        return self.index is not None and len(self.metadata) > 0


def create_store_paths(base_dir: str, index_name: str) -> Tuple[str, str]:
    """ストアパスを生成"""
    index_dir = os.path.join(base_dir, index_name)
    index_path = os.path.join(index_dir, "index.faiss")
    meta_path = os.path.join(index_dir, "meta.json")
    return index_path, meta_path

