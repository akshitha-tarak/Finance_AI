from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    query: str = Field(..., description="User query or financial question", min_length=1)

class ChatResponse(BaseModel):
    query: str
    reply: str
    source: str = Field(..., description="Query handler source: 'ml' (transaction analytics), 'rag' (knowledge retrieval), or 'hybrid'")
    suggested_actions: Optional[List[str]] = Field(default_factory=list, description="Contextual quick suggestions")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional debug/analytics context")

class ClusterSummary(BaseModel):
    cluster_id: int
    name: str
    transaction_count: int
    avg_amount: float
    total_amount: float
    percentage_of_total: float
    top_categories: List[str]
    description: str

class OverspendingAlert(BaseModel):
    transaction_id: str
    date: str
    category: str
    amount: float
    category_avg: float
    spike_factor: float
    risk_level: str  # "HIGH", "MODERATE", "NORMAL"
    merchant: str
    message: str

class AnalysisResponse(BaseModel):
    total_spend: float
    total_transactions: int
    date_range: str
    top_spending_category: str
    top_spending_amount: float
    category_breakdown: Dict[str, float]
    clusters: List[ClusterSummary]
    overspending_alerts: List[OverspendingAlert]
    summary_narrative: str
