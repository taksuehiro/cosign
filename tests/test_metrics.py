"""
評価メトリクステスト
"""
import pytest
import numpy as np
from app.core.metrics import recall_at_k, mrr_at_k, ndcg_at_k, calculate_metrics


def test_recall_at_k():
    """Recall@Kテスト"""
    # 基本ケース
    relevant = ["A", "B", "C"]
    retrieved = ["A", "D", "B", "E", "C"]
    
    # Recall@1: 1/3 = 0.333
    assert recall_at_k(relevant, retrieved, 1) == pytest.approx(1/3, rel=1e-3)
    
    # Recall@3: 2/3 = 0.667
    assert recall_at_k(relevant, retrieved, 3) == pytest.approx(2/3, rel=1e-3)
    
    # Recall@5: 3/3 = 1.0
    assert recall_at_k(relevant, retrieved, 5) == pytest.approx(1.0, rel=1e-3)
    
    # 空の関連アイテム
    assert recall_at_k([], retrieved, 3) == 0.0
    
    # 空の検索結果
    assert recall_at_k(relevant, [], 3) == 0.0


def test_mrr_at_k():
    """MRR@Kテスト"""
    # 基本ケース
    relevant = ["A", "B", "C"]
    retrieved = ["D", "A", "E", "B", "F"]
    
    # MRR@3: 最初の関連アイテムAは位置2なので 1/2 = 0.5
    assert mrr_at_k(relevant, retrieved, 3) == pytest.approx(0.5, rel=1e-3)
    
    # MRR@5: 最初の関連アイテムAは位置2なので 1/2 = 0.5
    assert mrr_at_k(relevant, retrieved, 5) == pytest.approx(0.5, rel=1e-3)
    
    # 最初のアイテムが関連
    retrieved_first = ["A", "D", "E", "B", "F"]
    assert mrr_at_k(relevant, retrieved_first, 3) == pytest.approx(1.0, rel=1e-3)
    
    # 関連アイテムなし
    retrieved_no_relevant = ["D", "E", "F"]
    assert mrr_at_k(relevant, retrieved_no_relevant, 3) == 0.0
    
    # 空の関連アイテム
    assert mrr_at_k([], retrieved, 3) == 0.0


def test_ndcg_at_k():
    """nDCG@Kテスト"""
    # 基本ケース
    relevant = ["A", "B", "C"]
    retrieved = ["A", "D", "B", "E", "C"]
    
    # nDCG@3: A(位置1), B(位置3)が関連
    # DCG = 1/log2(2) + 1/log2(4) = 1 + 0.5 = 1.5
    # IDCG = 1/log2(2) + 1/log2(3) + 1/log2(4) = 1 + 0.631 + 0.5 = 2.131
    # nDCG = 1.5 / 2.131 ≈ 0.704
    ndcg_3 = ndcg_at_k(relevant, retrieved, 3)
    assert ndcg_3 == pytest.approx(0.704, rel=1e-2)
    
    # nDCG@5: A(位置1), B(位置3), C(位置5)が関連
    # DCG = 1/log2(2) + 1/log2(4) + 1/log2(6) = 1 + 0.5 + 0.387 = 1.887
    # IDCG = 1/log2(2) + 1/log2(3) + 1/log2(4) = 1 + 0.631 + 0.5 = 2.131
    # nDCG = 1.887 / 2.131 ≈ 0.885
    ndcg_5 = ndcg_at_k(relevant, retrieved, 5)
    assert ndcg_5 == pytest.approx(0.885, rel=1e-2)
    
    # 空の関連アイテム
    assert ndcg_at_k([], retrieved, 3) == 0.0


def test_calculate_metrics():
    """複数クエリのメトリクス計算テスト"""
    # テストデータ
    query_results = [
        {
            "q": "query1",
            "results": [
                {"vendor_id": "V-A", "name": "Company A"},
                {"vendor_id": "V-B", "name": "Company B"},
                {"vendor_id": "V-C", "name": "Company C"}
            ]
        },
        {
            "q": "query2", 
            "results": [
                {"vendor_id": "V-D", "name": "Company D"},
                {"vendor_id": "V-A", "name": "Company A"},
                {"vendor_id": "V-E", "name": "Company E"}
            ]
        }
    ]
    
    gold_standard = [
        {
            "q": "query1",
            "gold": ["V-A", "V-B"]
        },
        {
            "q": "query2",
            "gold": ["V-A", "V-D"]
        }
    ]
    
    # メトリクス計算
    recall, mrr, ndcg = calculate_metrics(query_results, gold_standard, k=3)
    
    # 期待値計算
    # Query 1: R@3=1.0, MRR@3=1.0, nDCG@3=1.0
    # Query 2: R@3=1.0, MRR@3=0.5, nDCG@3≈0.885
    # Average: R=1.0, MRR=0.75, nDCG≈0.943
    
    assert recall == pytest.approx(1.0, rel=1e-3)
    assert mrr == pytest.approx(0.75, rel=1e-3)
    assert ndcg == pytest.approx(0.943, rel=1e-2)


def test_edge_cases():
    """エッジケーステスト"""
    # 空の結果
    query_results = []
    gold_standard = []
    
    recall, mrr, ndcg = calculate_metrics(query_results, gold_standard, k=3)
    assert recall == 0.0
    assert mrr == 0.0
    assert ndcg == 0.0
    
    # 結果はあるが正解なし
    query_results = [
        {
            "q": "query1",
            "results": [{"vendor_id": "V-A", "name": "Company A"}]
        }
    ]
    gold_standard = [
        {
            "q": "query1",
            "gold": []
        }
    ]
    
    recall, mrr, ndcg = calculate_metrics(query_results, gold_standard, k=3)
    assert recall == 0.0
    assert mrr == 0.0
    assert ndcg == 0.0
