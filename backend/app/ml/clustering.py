import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from ..models.schemas import ClusterSummary

class SpendingClusterer:
    """
    Groups user financial transactions into distinct spending behavioral personas
    using scikit-learn's KMeans clustering algorithm.
    """
    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.scaler = StandardScaler()
        self.fitted = False
        self.cluster_labels_map = {}

    def fit_and_cluster(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts features, standardizes them, and trains KMeans clustering.
        Returns the DataFrame enriched with cluster IDs and human-readable personas.
        """
        if df.empty or len(df) < self.n_clusters:
            df['cluster'] = 0
            df['cluster_persona'] = "General Spending"
            return df

        df = df.copy()

        # Feature Engineering:
        # 1. Log-transformed amount (to handle skewed financial distributions)
        # 2. Raw amount
        # 3. Day of week (capturing weekday vs weekend habit patterns)
        df['log_amount'] = np.log1p(df['amount'])
        df['day_of_week'] = df['date'].dt.dayofweek

        features = df[['amount', 'log_amount', 'day_of_week']].values
        scaled_features = self.scaler.fit_transform(features)

        # Fit KMeans
        clusters = self.kmeans.fit_predict(scaled_features)
        df['cluster'] = clusters

        # Determine persona titles dynamically by cluster average transaction size
        cluster_means = df.groupby('cluster')['amount'].mean().sort_values()
        
        # Sort cluster IDs from lowest average spend to highest
        sorted_clusters = cluster_means.index.tolist()
        
        # Mapping: Lowest -> Daily Micro-Habits, Middle -> Discretionary & Living, Highest -> Big-Ticket / Commitments
        persona_names = [
            "Routine Micro-Habits & Daily Essentials",
            "Discretionary Living & Balanced Expenses",
            "Big-Ticket Commitments & Major Outliers"
        ]
        
        self.cluster_labels_map = {}
        for rank, cluster_id in enumerate(sorted_clusters):
            self.cluster_labels_map[cluster_id] = persona_names[min(rank, len(persona_names) - 1)]

        df['cluster_persona'] = df['cluster'].map(self.cluster_labels_map)
        self.fitted = True
        return df

    def get_summaries(self, clustered_df: pd.DataFrame) -> List[ClusterSummary]:
        """
        Generates human-interpretable statistical profiles for each KMeans cluster.
        """
        if clustered_df.empty or 'cluster' not in clustered_df.columns:
            return []

        total_overall_spend = clustered_df['amount'].sum()
        summaries: List[ClusterSummary] = []

        for cluster_id, persona_name in self.cluster_labels_map.items():
            cluster_subset = clustered_df[clustered_df['cluster'] == cluster_id]
            if cluster_subset.empty:
                continue

            count = len(cluster_subset)
            total = float(cluster_subset['amount'].sum())
            avg = float(cluster_subset['amount'].mean())
            pct = round((total / total_overall_spend * 100), 1) if total_overall_spend > 0 else 0.0

            top_cats = cluster_subset['category'].value_counts().head(3).index.tolist()

            # Dynamic narrative description
            if "Micro-Habits" in persona_name:
                desc = f"Frequent, smaller purchases (avg ${avg:.2f}). Mostly daily routines like {', '.join(top_cats)}."
            elif "Big-Ticket" in persona_name:
                desc = f"Heavy financial commitments (avg ${avg:.2f}). Major outflows such as {', '.join(top_cats)}."
            else:
                desc = f"Moderate lifestyle expenses (avg ${avg:.2f}). Includes regular living costs like {', '.join(top_cats)}."

            summaries.append(ClusterSummary(
                cluster_id=int(cluster_id),
                name=persona_name,
                transaction_count=count,
                avg_amount=round(avg, 2),
                total_amount=round(total, 2),
                percentage_of_total=pct,
                top_categories=top_cats,
                description=desc
            ))

        # Sort summary by average amount for clear visual progression
        summaries.sort(key=lambda s: s.avg_amount)
        return summaries

spending_clusterer = SpendingClusterer()
