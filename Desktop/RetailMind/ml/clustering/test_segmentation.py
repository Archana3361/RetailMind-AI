"""
Focused tests for customer segmentation: RFM calculation, customer inclusion,
cluster-label mapping, insufficient data, degenerate data, and per-customer details.
Run: python -m pytest ml/clustering/test_segmentation.py -v
    or: python ml/clustering/test_segmentation.py
"""
import sys
import os
from datetime import datetime, timezone, timedelta

# Ensure ml package is importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from clustering.customer_segmentation import (
    CustomerSegmentation, segment_customers
)


def _make_sale(customer_id, total, days_ago):
    """Helper: create a sale dict mimicking MongoDB record."""
    return {
        "customer_id": customer_id,
        "total": total,
        "created_at": datetime.now(timezone.utc) - timedelta(days=days_ago)
    }


# ─── RFM Calculation ─────────────────────────────────────

def test_rfm_basic():
    """RFM correctly groups sales by customer and computes recency/freq/monetary."""
    sales = [
        _make_sale("c1", 100, 5),
        _make_sale("c1", 200, 10),   # c1: 2 orders, 300 total, last 5d ago
        _make_sale("c2", 500, 20),   # c2: 1 order, 500 total, 20d ago
    ]
    seg = CustomerSegmentation()
    rfm, ids = seg.calculate_rfm(sales)
    assert set(ids) == {"c1", "c2"}, f"Expected c1,c2 got {ids}"
    c1_idx = ids.index("c1")
    c2_idx = ids.index("c2")
    assert rfm[c1_idx][1] == 2, f"c1 frequency should be 2, got {rfm[c1_idx][1]}"
    assert rfm[c1_idx][2] == 300, f"c1 monetary should be 300, got {rfm[c1_idx][2]}"
    assert rfm[c2_idx][1] == 1, f"c2 frequency should be 1, got {rfm[c2_idx][1]}"
    assert rfm[c2_idx][2] == 500
    # c1 recency should be ~5 days
    assert abs(rfm[c1_idx][0] - 5) <= 1, f"c1 recency ~5, got {rfm[c1_idx][0]}"
    print("  [PASS] test_rfm_basic")


def test_rfm_skips_walk_in_sales():
    """Sales without customer_id (walk-in) are correctly skipped."""
    sales = [
        _make_sale("c1", 100, 5),
        {"customer_id": None, "total": 999, "created_at": datetime.now(timezone.utc)},  # walk-in
        {"total": 50, "created_at": datetime.now(timezone.utc)},  # no customer_id key
    ]
    seg = CustomerSegmentation()
    rfm, ids = seg.calculate_rfm(sales)
    assert ids == ["c1"], f"Only c1 should be included, got {ids}"
    assert len(rfm) == 1
    print("  [PASS] test_rfm_skips_walk_in_sales")


def test_rfm_uses_most_recent_purchase():
    """Recency uses the MOST RECENT purchase, not the first."""
    sales = [
        _make_sale("c1", 100, 30),  # old purchase
        _make_sale("c1", 200, 3),   # recent purchase
    ]
    seg = CustomerSegmentation()
    rfm, ids = seg.calculate_rfm(sales)
    assert ids == ["c1"]
    assert abs(rfm[0][0] - 3) <= 1, f"Recency should be ~3 (most recent), got {rfm[0][0]}"
    assert rfm[0][1] == 2  # frequency = 2
    assert rfm[0][2] == 300  # monetary = 300
    print("  [PASS] test_rfm_uses_most_recent_purchase")


# ─── Customer Inclusion ──────────────────────────────────

def test_only_customers_with_sales_included():
    """Only customers with linked sales appear in segmentation — no fabrication."""
    sales = [
        _make_sale("c1", 100, 5),
        _make_sale("c2", 200, 10),
    ]
    _, summary = segment_customers(sales, n_clusters=4)
    # With only 2 customers, falls into "too few" branch
    details = summary.get("customer_details", [])
    assert len(details) == 2, f"Expected 2 customers, got {len(details)}"
    detail_ids = {d["customer_id"] for d in details}
    assert detail_ids == {"c1", "c2"}
    print("  [PASS] test_only_customers_with_sales_included")


# ─── Cluster Label Uniqueness ────────────────────────────

def test_unique_labels_normal_case():
    """With enough diverse customers, each cluster gets a unique label."""
    sales = []
    # Create 8 customers with varied RFM
    profiles = [
        ("c1", 3000, 2),   # loyal: recent, freq=2, high spend
        ("c2", 2500, 2),
        ("c3", 5, 1),      # new: very recent, 1 order
        ("c4", 15, 1),
        ("c5", 200, 1),    # occasional
        ("c6", 150, 1),
        ("c7", 70, 4),     # at-risk: old, but freq=4
        ("c8", 80, 3),
    ]
    for cid, spend, days_ago in profiles:
        sales.append(_make_sale(cid, spend, days_ago))
    # Add a second order for c1 and c2 to boost frequency
    sales.append(_make_sale("c1", 500, 1))
    sales.append(_make_sale("c2", 600, 2))
    sales.append(_make_sale("c7", 300, 65))
    sales.append(_make_sale("c7", 400, 62))
    sales.append(_make_sale("c8", 200, 61))

    _, summary = segment_customers(sales, n_clusters=4)
    labels = [s["label"] for s in summary["segments"]]
    assert len(labels) == len(set(labels)), f"Duplicate labels found: {labels}"
    print(f"  [PASS] test_unique_labels_normal_case — labels: {labels}")


def test_no_duplicate_labels_target_scenario():
    """The target user scenario (2 customers, both recent) should NOT produce
    duplicate 'New Customers' labels."""
    sales = [
        _make_sale("c1", 139, 3),
        _make_sale("c2", 210, 4),
    ]
    _, summary = segment_customers(sales, n_clusters=4)
    labels = [s["label"] for s in summary["segments"]]
    # With only 2 customers, should be 1 segment (not 2 duplicate ones)
    assert len(summary["segments"]) == 1, f"Expected 1 segment for 2 customers, got {len(summary['segments'])}"
    assert len(labels) == len(set(labels)), f"Duplicate labels: {labels}"
    assert "message" in summary, "Should include explanation message for too-few case"
    print(f"  [PASS] test_no_duplicate_labels_target_scenario — label: {labels[0]}, message present")


# ─── Insufficient Data ───────────────────────────────────

def test_insufficient_no_sales():
    """No sales records → error response."""
    _, summary = segment_customers([], n_clusters=4)
    assert "error" in summary
    assert summary["total_clusters"] == 0
    print("  [PASS] test_insufficient_no_sales")


def test_insufficient_one_customer():
    """Only 1 customer with sales → error (need at least 2)."""
    sales = [_make_sale("c1", 100, 5)]
    _, summary = segment_customers(sales, n_clusters=4)
    assert "error" in summary
    print("  [PASS] test_insufficient_one_customer")


def test_two_customers_single_group():
    """2 customers → single group (not K-Means), with explanation message."""
    sales = [
        _make_sale("c1", 100, 5),
        _make_sale("c2", 200, 10),
    ]
    _, summary = segment_customers(sales, n_clusters=4)
    assert summary["total_clusters"] == 1
    assert "message" in summary
    assert len(summary["customer_details"]) == 2
    print("  [PASS] test_two_customers_single_group")


# ─── Degenerate Data ─────────────────────────────────────

def test_identical_rfm_single_group():
    """All customers with identical RFM → single group, not arbitrary clusters."""
    sales = [
        _make_sale("c1", 100, 10),
        _make_sale("c2", 100, 10),
        _make_sale("c3", 100, 10),
    ]
    _, summary = segment_customers(sales, n_clusters=4)
    assert summary["total_clusters"] == 1, f"Identical RFM should be 1 group, got {summary['total_clusters']}"
    assert "message" in summary
    print("  [PASS] test_identical_rfm_single_group")


# ─── Per-Customer Details ────────────────────────────────

def test_customer_details_structure():
    """customer_details contains all required fields per customer."""
    sales = [
        _make_sale("c1", 500, 5),
        _make_sale("c2", 300, 10),
        _make_sale("c3", 200, 20),
        _make_sale("c4", 100, 30),
    ]
    _, summary = segment_customers(sales, n_clusters=2)
    details = summary.get("customer_details", [])
    assert len(details) == 4
    for d in details:
        assert "customer_id" in d
        assert "segment" in d
        assert "recency_days" in d
        assert "frequency" in d
        assert "monetary" in d
        assert "last_purchase" in d
    print("  [PASS] test_customer_details_structure")


def test_customer_details_segment_consistency():
    """Each customer's segment matches one of the segment labels."""
    sales = [
        _make_sale("c1", 500, 5),
        _make_sale("c2", 300, 10),
        _make_sale("c3", 200, 20),
        _make_sale("c4", 100, 30),
    ]
    _, summary = segment_customers(sales, n_clusters=2)
    segment_labels = {s["label"] for s in summary["segments"]}
    for d in summary["customer_details"]:
        assert d["segment"] in segment_labels, f"Customer {d['customer_id']} has unknown segment {d['segment']}"
    print("  [PASS] test_customer_details_segment_consistency")


# ─── API Response Structure ──────────────────────────────

def test_summary_has_required_keys():
    """Summary dict has all keys needed by the API response."""
    sales = [
        _make_sale("c1", 500, 5),
        _make_sale("c2", 300, 10),
        _make_sale("c3", 200, 20),
    ]
    _, summary = segment_customers(sales, n_clusters=2)
    required = {"total_clusters", "segments", "customer_details"}
    assert required.issubset(summary.keys()), f"Missing keys: {required - set(summary.keys())}"
    for seg in summary["segments"]:
        seg_required = {"label", "customer_count", "avg_recency_days", "avg_purchases", "avg_total_spent"}
        assert seg_required.issubset(seg.keys()), f"Segment missing keys: {seg_required - set(seg.keys())}"
    print("  [PASS] test_summary_has_required_keys")


# ─── Run All ──────────────────────────────────────────────

def run_all():
    tests = [
        test_rfm_basic,
        test_rfm_skips_walk_in_sales,
        test_rfm_uses_most_recent_purchase,
        test_only_customers_with_sales_included,
        test_unique_labels_normal_case,
        test_no_duplicate_labels_target_scenario,
        test_insufficient_no_sales,
        test_insufficient_one_customer,
        test_two_customers_single_group,
        test_identical_rfm_single_group,
        test_customer_details_structure,
        test_customer_details_segment_consistency,
        test_summary_has_required_keys,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {t.__name__}: {e}")
            failed += 1
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
