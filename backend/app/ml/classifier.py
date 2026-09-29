import numpy as np
import pandas as pd
from typing import List, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from ..models.schemas import OverspendingAlert

class OverspendingDetector:
    """
    Classifies transactions into 'Normal' vs 'Overspending / High Risk Spike'
    using category-relative feature engineering and a trained scikit-learn classifier.
    """
    def __init__(self):
        self.model = LogisticRegression(random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.category_baselines = {}

    def _compute_category_baselines(self, df: pd.DataFrame) -> dict:
        """Computes baseline mean and std for each spending category."""
        baselines = {}
        grouped = df.groupby('category')['amount']
        for cat, group in grouped:
            mean_val = float(group.mean())
            std_val = float(group.std()) if len(group) > 1 else (mean_val * 0.25)
            # Avoid zero division
            std_val = max(std_val, 1.0)
            baselines[cat] = {
                "mean": mean_val,
                "std": std_val,
                "count": len(group)
            }
        return baselines

    def _extract_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts feature matrix:
        [amount, category_mean, ratio_to_mean, z_score]
        Generates ground-truth heuristic supervision for training:
        A transaction is an overspending event if:
        ratio_to_mean >= 2.0 and z_score >= 1.75 (and not a recurring fixed bill like Rent).
        """
        X_rows = []
        y_labels = []

        for _, row in df.iterrows():
            cat = row['category']
            amt = float(row['amount'])
            stats = self.category_baselines.get(cat, {"mean": amt, "std": 1.0, "count": 1})
            
            mean_val = stats["mean"]
            std_val = stats["std"]
            
            ratio = amt / (mean_val + 1e-4)
            z_score = (amt - mean_val) / (std_val + 1e-4)

            X_rows.append([amt, mean_val, ratio, z_score])

            # Heuristic ground truth for supervision
            # Fixed expenses like Rent don't trigger overspending unless they suddenly spike
            is_fixed = cat.lower() in ['rent', 'housing']
            is_overspending = (ratio >= 2.0 and z_score >= 1.5) and not is_fixed
            y_labels.append(1 if is_overspending else 0)

        return np.array(X_rows), np.array(y_labels)

    def train(self, df: pd.DataFrame):
        """Trains the Logistic Regression classifier on transaction features."""
        if df.empty or len(df) < 5:
            return

        self.category_baselines = self._compute_category_baselines(df)
        X, y = self._extract_features(df)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Handle class imbalance if needed (ensure both classes exist for training)
        if len(np.unique(y)) < 2:
            # Synthetic anchor to ensure classifier has both classes
            synthetic_normal = [10.0, 15.0, 0.66, -0.5]
            synthetic_spike = [250.0, 30.0, 8.33, 4.2]
            X = np.vstack([X, synthetic_normal, synthetic_spike])
            y = np.append(y, [0, 1])
            X_scaled = self.scaler.fit_transform(X)

        self.model.fit(X_scaled, y)
        self.is_trained = True

    def detect_overspending(self, df: pd.DataFrame) -> List[OverspendingAlert]:
        """
        Predicts overspending probabilities and returns structured alerts
        for anomalous or high-risk transactions.
        """
        if not self.is_trained:
            self.train(df)

        if df.empty:
            return []

        alerts: List[OverspendingAlert] = []

        for _, row in df.iterrows():
            cat = row['category']
            amt = float(row['amount'])
            tx_id = str(row.get('transaction_id', 'unknown'))
            merchant = str(row.get('merchant', 'Unknown Merchant'))
            date_str = pd.to_datetime(row['date']).strftime('%Y-%m-%d')

            stats = self.category_baselines.get(cat, {"mean": amt, "std": 1.0})
            mean_val = stats["mean"]
            std_val = stats["std"]
            
            ratio = amt / (mean_val + 1e-4)
            z_score = (amt - mean_val) / (std_val + 1e-4)

            feat = np.array([[amt, mean_val, ratio, z_score]])
            feat_scaled = self.scaler.transform(feat)
            
            # Predict overspending probability using ML model
            probs = self.model.predict_proba(feat_scaled)[0]
            overspend_prob = float(probs[1]) if len(probs) > 1 else 0.0

            # Classification logic
            if overspend_prob >= 0.65 or (ratio >= 2.2 and z_score >= 1.8 and cat.lower() != 'rent'):
                risk = "HIGH"
                message = f"Significant spending spike detected at {merchant}! ${amt:.2f} is {ratio:.1f}x higher than your ${mean_val:.2f} category average."
                alerts.append(OverspendingAlert(
                    transaction_id=tx_id,
                    date=date_str,
                    category=cat,
                    amount=round(amt, 2),
                    category_avg=round(mean_val, 2),
                    spike_factor=round(ratio, 2),
                    risk_level=risk,
                    merchant=merchant,
                    message=message
                ))
            elif ratio >= 1.6 and z_score >= 1.2 and amt > 60 and cat.lower() != 'rent':
                risk = "MODERATE"
                message = f"Above-average expense at {merchant}. ${amt:.2f} exceeds your usual ${mean_val:.2f} baseline."
                alerts.append(OverspendingAlert(
                    transaction_id=tx_id,
                    date=date_str,
                    category=cat,
                    amount=round(amt, 2),
                    category_avg=round(mean_val, 2),
                    spike_factor=round(ratio, 2),
                    risk_level=risk,
                    merchant=merchant,
                    message=message
                ))

        # Sort alerts by spike factor descending (highest anomalies first)
        alerts.sort(key=lambda a: a.spike_factor, reverse=True)
        return alerts

overspending_detector = OverspendingDetector()
