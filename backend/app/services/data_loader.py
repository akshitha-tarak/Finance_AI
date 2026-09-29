import pandas as pd
from typing import Dict, Any, List
from pathlib import Path
from ..config import settings

class TransactionDataLoader:
    """
    Loads, cleans, and analyzes user financial transactions using pandas.
    """
    def __init__(self, file_path: Path = None):
        self.file_path = file_path or settings.DATA_PATH
        self.df: pd.DataFrame = pd.DataFrame()
        self.load_data()

    def load_data(self) -> pd.DataFrame:
        """Loads and formats the CSV transactions dataset."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Transactions file not found at: {self.file_path}")
        
        # Load CSV into pandas DataFrame
        df = pd.read_csv(self.file_path)
        
        # Clean and type-cast columns
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
        df['date'] = pd.to_datetime(df['date'])
        df['category'] = df['category'].astype(str).str.strip()
        df['merchant'] = df['merchant'].astype(str).str.strip()
        
        self.df = df
        return self.df

    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculates global statistical summaries."""
        if self.df.empty:
            self.load_data()
            
        total_spend = float(self.df['amount'].sum())
        total_tx = int(len(self.df))
        avg_tx = float(self.df['amount'].mean()) if total_tx > 0 else 0.0
        
        min_date = self.df['date'].min().strftime('%b %d, %Y')
        max_date = self.df['date'].max().strftime('%b %d, %Y')
        date_range_str = f"{min_date} to {max_date}"
        
        # Category breakdown
        category_spend = self.df.groupby('category')['amount'].sum().sort_values(ascending=False)
        top_category = category_spend.index[0] if not category_spend.empty else "N/A"
        top_category_amount = float(category_spend.iloc[0]) if not category_spend.empty else 0.0
        
        return {
            "total_spend": round(total_spend, 2),
            "total_transactions": total_tx,
            "average_transaction": round(avg_tx, 2),
            "date_range": date_range_str,
            "top_spending_category": top_category,
            "top_spending_amount": round(top_category_amount, 2),
            "category_breakdown": {k: round(float(v), 2) for k, v in category_spend.to_dict().items()}
        }

    def get_category_details(self, category_name: str) -> Dict[str, Any]:
        """Provides deep-dive stats for a specific category."""
        if self.df.empty:
            self.load_data()
            
        matches = self.df[self.df['category'].str.lower() == category_name.lower()]
        if matches.empty:
            return {
                "found": False,
                "category": category_name,
                "message": f"No transactions found under category '{category_name}'."
            }
            
        total_spend = float(matches['amount'].sum())
        tx_count = len(matches)
        avg_spend = float(matches['amount'].mean())
        max_spend = float(matches['amount'].max())
        
        return {
            "found": True,
            "category": category_name,
            "total_spend": round(total_spend, 2),
            "transaction_count": tx_count,
            "average_transaction": round(avg_spend, 2),
            "max_transaction": round(max_spend, 2),
            "recent_merchants": matches['merchant'].unique().tolist()[:5]
        }

    def search_by_keyword(self, query: str) -> List[Dict[str, Any]]:
        """Searches transactions matching a merchant or description."""
        if self.df.empty:
            self.load_data()
            
        q = query.lower()
        mask = (
            self.df['merchant'].str.lower().str.contains(q, na=False) |
            self.df['description'].str.lower().str.contains(q, na=False) |
            self.df['category'].str.lower().str.contains(q, na=False)
        )
        results = self.df[mask].copy()
        results['date'] = results['date'].dt.strftime('%Y-%m-%d')
        return results.to_dict(orient='records')

# Singleton instance
data_loader = TransactionDataLoader()
