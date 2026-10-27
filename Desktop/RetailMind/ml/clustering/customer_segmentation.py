"""
Customer Segmentation using K-Means Clustering with RFM Analysis

RFM Features:
- Recency: Days since last purchase
- Frequency: Number of purchases in the period
- Monetary: Total money spent

Segment Labels (data-driven, not hardcoded):
- Loyal Customers: High frequency, high monetary, recent purchases
- Regular Customers: Moderate frequency and monetary
- Occasional Customers: Low frequency but recent activity
- At-Risk Customers: High recency (long time since last purchase)
- New Customers: Recent first purchase with limited history

The segment labels are assigned based on actual cluster characteristics,
not predefined assumptions.
"""

import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import logging

logger = logging.getLogger(__name__)


class CustomerSegmentation:
    """
    K-Means customer segmentation based on RFM (Recency, Frequency, Monetary) analysis.
    """
    
    def __init__(self, n_clusters: int = 4, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = None
        self.cluster_profiles = {}
    
    def calculate_rfm(
        self,
        sales_records: List[Dict[str, Any]],
        reference_date: Optional[datetime] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Calculate RFM features from sales records.
        
        Args:
            sales_records: List of sale documents with customer_id, total, created_at
            reference_date: Date to calculate recency from (defaults to now)
        
        Returns:
            Tuple of (RFM matrix, customer_ids list)
        """
        if reference_date is None:
            reference_date = datetime.now(timezone.utc)
        
        # Group sales by customer
        customer_data = {}
        
        for sale in sales_records:
            customer_id = sale.get("customer_id")
            if not customer_id:
                continue
            
            customer_id = str(customer_id)
            total = float(sale.get("total", 0))
            created_at = sale.get("created_at")
            
            if customer_id not in customer_data:
                customer_data[customer_id] = {
                    "last_purchase": created_at,
                    "purchase_count": 0,
                    "total_spent": 0.0
                }
            
            customer_data[customer_id]["purchase_count"] += 1
            customer_data[customer_id]["total_spent"] += total
            
            # Update last purchase if more recent
            if created_at:
                if customer_data[customer_id]["last_purchase"] is None or created_at > customer_data[customer_id]["last_purchase"]:
                    customer_data[customer_id]["last_purchase"] = created_at
        
        if not customer_data:
            return np.array([]), []
        
        # Build RFM matrix
        customer_ids = []
        rfm_data = []
        
        for customer_id, data in customer_data.items():
            # Recency: days since last purchase
            if data["last_purchase"]:
                if isinstance(data["last_purchase"], str):
                    last_purchase = datetime.fromisoformat(data["last_purchase"].replace("Z", "+00:00"))
                else:
                    last_purchase = data["last_purchase"]
                
                if last_purchase.tzinfo is None:
                    last_purchase = last_purchase.replace(tzinfo=timezone.utc)
                
                recency = (reference_date - last_purchase).days
            else:
                recency = 999  # No purchases - very high recency
            
            # Frequency: number of purchases
            frequency = data["purchase_count"]
            
            # Monetary: total spent
            monetary = data["total_spent"]
            
            customer_ids.append(customer_id)
            rfm_data.append([recency, frequency, monetary])
        
        return np.array(rfm_data), customer_ids
    
    def fit(self, rfm_matrix: np.ndarray) -> 'CustomerSegmentation':
        """
        Fit K-Means model on RFM data.
        
        Args:
            rfm_matrix: Numpy array of shape (n_customers, 3) with [recency, frequency, monetary]
        
        Returns:
            self
        """
        if len(rfm_matrix) < self.n_clusters:
            logger.warning(
                f"Not enough customers ({len(rfm_matrix)}) for {self.n_clusters} clusters. "
                f"Reducing to {max(2, len(rfm_matrix))} clusters."
            )
            self.n_clusters = max(2, len(rfm_matrix))
        
        if len(rfm_matrix) < 2:
            raise ValueError("Need at least 2 customers for segmentation")
        
        # Scale RFM features
        rfm_scaled = self.scaler.fit_transform(rfm_matrix)
        
        # Fit K-Means
        self.model = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10,
            max_iter=300
        )
        self.model.fit(rfm_scaled)
        
        # Calculate cluster profiles (mean RFM values per cluster)
        self._calculate_cluster_profiles(rfm_matrix)

        # Assign unique labels based on relative cluster ranking
        self._assign_unique_labels(rfm_matrix)

        return self
    
    def _calculate_cluster_profiles(self, rfm_matrix: np.ndarray):
        """
        Calculate mean RFM values for each cluster (without assigning labels).
        Labels are assigned separately by _assign_unique_labels to ensure uniqueness.
        """
        labels = self.model.labels_

        for cluster_id in range(self.n_clusters):
            mask = labels == cluster_id
            cluster_data = rfm_matrix[mask]

            if len(cluster_data) == 0:
                continue

            mean_recency = np.mean(cluster_data[:, 0])
            mean_frequency = np.mean(cluster_data[:, 1])
            mean_monetary = np.mean(cluster_data[:, 2])

            self.cluster_profiles[cluster_id] = {
                "mean_recency": mean_recency,
                "mean_frequency": mean_frequency,
                "mean_monetary": mean_monetary,
                "customer_count": len(cluster_data),
            }

    def _assign_unique_labels(self, rfm_matrix: np.ndarray):
        """
        Assign UNIQUE, descriptive labels to clusters based on relative ranking.

        Clusters are ranked by a composite RFM score (lower recency, higher
        frequency, higher monetary = better). Each rank gets a distinct base
        label so no two clusters share the same label. The best and worst
        clusters may get characteristic-based overrides (e.g., "Loyal Customers",
        "At-Risk Customers", "New Customers").

        This fixes the original bug where multiple clusters with similar RFM
        characteristics all received the same absolute-threshold label.
        """
        if not self.cluster_profiles:
            return

        # Gather per-cluster stats for normalization
        all_recencies = [p["mean_recency"] for p in self.cluster_profiles.values()]
        all_frequencies = [p["mean_frequency"] for p in self.cluster_profiles.values()]
        all_monetaries = [p["mean_monetary"] for p in self.cluster_profiles.values()]

        r_min, r_max = min(all_recencies), max(all_recencies)
        f_min, f_max = min(all_frequencies), max(all_frequencies)
        m_min, m_max = min(all_monetaries), max(all_monetaries)

        r_range = (r_max - r_min) if r_max != r_min else 1.0
        f_range = (f_max - f_min) if f_max != f_min else 1.0
        m_range = (m_max - m_min) if m_max != m_min else 1.0

        # Composite score: lower recency = higher score, higher freq/monetary = higher score
        for profile in self.cluster_profiles.values():
            r_score = (r_max - profile["mean_recency"]) / r_range
            f_score = (profile["mean_frequency"] - f_min) / f_range
            m_score = (profile["mean_monetary"] - m_min) / m_range
            profile["score"] = r_score + f_score + m_score

        # Rank clusters by score (best first)
        ranked = sorted(self.cluster_profiles.items(), key=lambda x: -x[1]["score"])

        # Base labels by rank — guaranteed unique since each rank gets a different base
        base_labels = ["Top Customers", "Regular Customers", "Occasional Customers", "Lapsed Customers"]

        assigned = []
        n = len(ranked)
        for rank, (cluster_id, profile) in enumerate(ranked):
            label = base_labels[rank] if rank < len(base_labels) else f"Segment {rank + 1}"

            # Override best cluster if it clearly qualifies as loyal
            if rank == 0 and profile["mean_frequency"] >= 3 and profile["mean_recency"] < 30:
                label = "Loyal Customers"

            # Override worst cluster based on actual behavior
            if rank == n - 1 and rank != 0:
                if profile["mean_recency"] > 60:
                    label = "At-Risk Customers"
                elif profile["mean_frequency"] <= 2 and profile["mean_recency"] < 14:
                    label = "New Customers"

            # Safety: ensure uniqueness (shouldn't trigger with rank-based bases, but guards overrides)
            base_label = label
            counter = 2
            while label in assigned:
                label = f"{base_label} (Group {counter})"
                counter += 1

            assigned.append(label)
            self.cluster_profiles[cluster_id]["label"] = label
    
    def predict(self, rfm_matrix: np.ndarray) -> np.ndarray:
        """
        Predict cluster labels for RFM data.
        
        Args:
            rfm_matrix: Numpy array of shape (n_customers, 3)
        
        Returns:
            Array of cluster labels
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        rfm_scaled = self.scaler.transform(rfm_matrix)
        return self.model.predict(rfm_scaled)
    
    def get_segment_label(self, cluster_id: int) -> str:
        """
        Get human-readable label for a cluster.
        """
        if cluster_id in self.cluster_profiles:
            return self.cluster_profiles[cluster_id]["label"]
        return f"Segment {cluster_id}"
    
    def get_cluster_summary(self) -> Dict[str, Any]:
        """
        Get summary of all clusters.
        """
        summary = {
            "total_clusters": self.n_clusters,
            "segments": []
        }
        
        for cluster_id, profile in sorted(self.cluster_profiles.items()):
            summary["segments"].append({
                "cluster_id": cluster_id,
                "label": profile["label"],
                "customer_count": profile["customer_count"],
                "avg_recency_days": round(profile["mean_recency"], 1),
                "avg_purchases": round(profile["mean_frequency"], 1),
                "avg_total_spent": round(profile["mean_monetary"], 2)
            })
        
        # Sort by customer count descending
        summary["segments"].sort(key=lambda x: x["customer_count"], reverse=True)
        
        return summary


def segment_customers(
    sales_records: List[Dict[str, Any]],
    n_clusters: int = 4,
    reference_date: Optional[datetime] = None
) -> Tuple[Dict[str, str], Dict[str, Any]]:
    """
    Segment customers from sales records using RFM analysis and K-Means clustering.

    Returns:
        Tuple of (customer_segment_mapping, summary_dict)

    The summary_dict contains:
        - total_clusters: number of segments
        - segments: list of per-segment summaries with unique labels
        - customer_details: per-customer data (id, segment, recency, frequency, monetary, last_purchase)
        - message: explanation when clustering is not meaningful (optional)

    Edge cases handled:
        - < 3 customers: single group, no K-Means (clustering requires >= 3)
        - identical RFM values: single group (no variance to cluster on)
        - < 2 customers: error
    """
    if not sales_records or len(sales_records) < 2:
        return {}, {
            "error": "Insufficient sales data for segmentation",
            "total_customers": 0,
            "total_clusters": 0,
            "segments": [],
            "customer_details": []
        }

    segmentation = CustomerSegmentation(n_clusters=n_clusters)

    # Calculate RFM
    rfm_matrix, customer_ids = segmentation.calculate_rfm(sales_records, reference_date)

    if len(customer_ids) < 2:
        return {}, {
            "error": "Need at least 2 customers with purchases for segmentation",
            "total_customers": len(customer_ids),
            "total_clusters": 0,
            "segments": [],
            "customer_details": []
        }

    # Compute last purchase date per customer (for UI display)
    customer_last_purchase: Dict[str, Any] = {}
    for sale in sales_records:
        cid = sale.get("customer_id")
        if not cid:
            continue
        cid = str(cid)
        created_at = sale.get("created_at")
        if created_at and (
            cid not in customer_last_purchase
            or customer_last_purchase[cid] is None
            or created_at > customer_last_purchase[cid]
        ):
            customer_last_purchase[cid] = created_at

    def build_customer_details(ids, matrix, cluster_labels, label_map):
        """Build per-customer detail records from RFM data and cluster assignments."""
        details = []
        for cid, row, clabel in zip(ids, matrix, cluster_labels):
            seg_label = label_map.get(clabel, f"Segment {clabel}")
            details.append({
                "customer_id": cid,
                "segment": seg_label,
                "recency_days": float(row[0]),
                "frequency": int(row[1]),
                "monetary": float(row[2]),
                "last_purchase": customer_last_purchase.get(cid),
            })
        return details

    n = len(customer_ids)

    # --- Edge case: too few customers for meaningful K-Means clustering ---
    if n < 3:
        all_recency = rfm_matrix[:, 0]
        all_freq = rfm_matrix[:, 1]

        if np.all(all_recency < 14) and np.all(all_freq <= 2):
            label = "New Customers"
        elif np.all(all_recency > 60):
            label = "At-Risk Customers"
        else:
            label = "Active Customers"

        customer_segments = {cid: label for cid in customer_ids}
        customer_details = build_customer_details(
            customer_ids, rfm_matrix, [0] * n, {0: label}
        )

        summary = {
            "total_clusters": 1,
            "segments": [{
                "cluster_id": 0,
                "label": label,
                "customer_count": n,
                "avg_recency_days": round(float(np.mean(rfm_matrix[:, 0])), 1),
                "avg_purchases": round(float(np.mean(rfm_matrix[:, 1])), 1),
                "avg_total_spent": round(float(np.mean(rfm_matrix[:, 2])), 2),
            }],
            "customer_details": customer_details,
            "message": (
                f"Only {n} customer(s) have purchase history. K-Means clustering requires "
                f"at least 3 customers for meaningful segmentation. All eligible customers "
                f"are grouped together."
            )
        }
        return customer_segments, summary

    # --- Edge case: degenerate data (all customers have identical RFM values) ---
    if np.allclose(rfm_matrix, rfm_matrix[0]):
        label = "Active Customers"
        customer_segments = {cid: label for cid in customer_ids}
        customer_details = build_customer_details(
            customer_ids, rfm_matrix, [0] * n, {0: label}
        )
        summary = {
            "total_clusters": 1,
            "segments": [{
                "cluster_id": 0,
                "label": label,
                "customer_count": n,
                "avg_recency_days": round(float(rfm_matrix[0, 0]), 1),
                "avg_purchases": round(float(rfm_matrix[0, 1]), 1),
                "avg_total_spent": round(float(rfm_matrix[0, 2]), 2),
            }],
            "customer_details": customer_details,
            "message": (
                "All customers have identical purchasing patterns (same recency, "
                "frequency, and monetary value). No meaningful segments can be identified."
            )
        }
        return customer_segments, summary

    # --- Normal case: enough customers with variance for K-Means clustering ---
    try:
        # Adjust n_clusters: at most n//2 clusters, at least 2
        effective_clusters = min(n_clusters, max(2, n // 2))
        segmentation.n_clusters = effective_clusters
        segmentation.fit(rfm_matrix)

        labels = segmentation.model.labels_

        # Build cluster_id -> label map
        label_map = {
            cid: segmentation.get_segment_label(cid)
            for cid in range(segmentation.n_clusters)
        }

        # Map customer_id to segment label
        customer_segments = {}
        for cid, label in zip(customer_ids, labels):
            customer_segments[cid] = segmentation.get_segment_label(label)

        # Build per-customer details
        customer_details = build_customer_details(
            customer_ids, rfm_matrix, labels, label_map
        )

        summary = segmentation.get_cluster_summary()
        summary["customer_details"] = customer_details

        return customer_segments, summary

    except Exception as e:
        logger.error(f"Error in customer segmentation: {e}")
        return {}, {
            "error": str(e),
            "total_customers": n,
            "total_clusters": 0,
            "segments": [],
            "customer_details": []
        }
