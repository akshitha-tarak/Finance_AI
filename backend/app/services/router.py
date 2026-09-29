import re
from typing import Dict, Any, List
from .data_loader import data_loader
from ..ml.clustering import spending_clusterer
from ..ml.classifier import overspending_detector
from ..rag.rag_engine import rag_engine
from ..models.schemas import ChatResponse

class QueryRouter:
    """
    Intelligent Query Router.
    Routes user prompts to either:
    1. ML & Transaction Analytics Engine (for personal spending questions)
    2. RAG Knowledge Pipeline (for general financial literacy and concepts)
    3. Hybrid synthesizer (when both personal data and principles apply)
    """
    def __init__(self):
        # Intent detection keyword dictionaries
        self.spending_keywords = {
            "spend", "spent", "spending", "bought", "buy", "purchase", "purchases",
            "cost", "total", "category", "categories", "cluster", "clusters",
            "overspend", "overspending", "alert", "alerts", "expense", "expenses",
            "transaction", "transactions", "groceries", "dining", "coffee", "rent",
            "utilities", "shopping", "travel", "amazon", "starbucks", "uber",
            "how much did i", "my balance", "breakdown", "pattern", "patterns"
        }

        self.rag_keywords = {
            "rule", "50/30/20", "invest", "investing", "investment", "stock", "stocks",
            "index fund", "etf", "401k", "ira", "roth", "compound interest", "interest",
            "emergency fund", "hysa", "savings account", "debt", "avalanche", "snowball",
            "credit score", "credit", "utilization", "what is", "how to invest",
            "explain", "passive income", "inflation", "wealth", "definition", "how does"
        }

    def route_query(self, query: str) -> ChatResponse:
        """Determines intent and delegates to the appropriate engine."""
        q_lower = query.lower()
        q_tokens = set(re.findall(r'\b[a-zA-Z0-9\/\-]{2,}\b', q_lower))

        spending_score = len(q_tokens.intersection(self.spending_keywords))
        rag_score = len(q_tokens.intersection(self.rag_keywords))

        # Check for phrase matches
        if any(phrase in q_lower for phrase in ["how much", "my spending", "did i overspend", "spending clusters", "transaction"]):
            spending_score += 3
        if any(phrase in q_lower for phrase in ["50/30/20", "compound interest", "debt snowball", "emergency fund", "index fund"]):
            rag_score += 3

        # Intent Decision
        if spending_score > 0 and spending_score >= rag_score:
            return self._handle_spending_intent(query, q_lower)
        else:
            return self._handle_rag_intent(query)

    def _handle_spending_intent(self, raw_query: str, q_lower: str) -> ChatResponse:
        """Processes questions regarding user transactions and ML insights."""
        df = data_loader.load_data()
        stats = data_loader.get_summary_stats()
        
        # Fit ML models
        clustered_df = spending_clusterer.fit_and_cluster(df)
        cluster_summaries = spending_clusterer.get_summaries(clustered_df)
        alerts = overspending_detector.detect_overspending(df)

        # Check if query is about clusters / spending behavior
        if any(w in q_lower for w in ["cluster", "behavior", "pattern", "persona"]):
            lines = [
                "### 🎯 Machine Learning Spending Persona Clusters (KMeans)",
                "We analyzed your spending behavior across 3 distinct behavioral clusters:\n"
            ]
            for c in cluster_summaries:
                lines.append(f"**{c.name}**")
                lines.append(f"- **Total Spend:** ${c.total_amount:,.2f} ({c.percentage_of_total}% of budget)")
                lines.append(f"- **Avg Transaction:** ${c.avg_amount:,.2f} ({c.transaction_count} purchases)")
                lines.append(f"- **Key Categories:** {', '.join(c.top_categories)}")
                lines.append(f"- *{c.description}*\n")
            
            return ChatResponse(
                query=raw_query,
                reply="\n".join(lines),
                source="ml",
                suggested_actions=["Am I overspending?", "What is the 50/30/20 rule?", "Show category breakdown"]
            )

        # Check if query is about overspending or anomalies
        if any(w in q_lower for w in ["overspend", "overspending", "alert", "anomaly", "too much", "spike"]):
            if not alerts:
                reply = "Good news! Our classification model did not detect any high-risk overspending anomalies in your recent transactions."
            else:
                lines = [
                    f"### ⚠️ Overspending Anomaly Detection ({len(alerts)} Spikes Detected)",
                    "Our ML classifier detected the following abnormal spending spikes compared to your historical averages:\n"
                ]
                for a in alerts[:4]:
                    risk_badge = "🔴 High Risk" if a.risk_level == "HIGH" else "🟡 Moderate Risk"
                    lines.append(f"- **{a.merchant}** ({a.category}) on {a.date}: **${a.amount:.2f}**")
                    lines.append(f"  *Baseline Average:* ${a.category_avg:.2f} ({a.spike_factor:.1f}x higher than normal)")
                    lines.append(f"  *Status:* {risk_badge}")
                lines.append("\n💡 *Actionable Tip: Discretionary expenses over 2x your baseline are prime opportunities for rapid budget savings.*")
                reply = "\n".join(lines)

            return ChatResponse(
                query=raw_query,
                reply=reply,
                source="ml",
                suggested_actions=["What is the 50/30/20 rule?", "Show my total spending", "Spending clusters"]
            )

        # Check if query asks for a specific category (e.g. dining, groceries, coffee, rent)
        categories = df['category'].unique()
        for cat in categories:
            cat_words = [w.lower() for w in cat.split() if len(w) > 3]
            if cat.lower() in q_lower or any(w in q_lower for w in cat_words):
                detail = data_loader.get_category_details(cat)
                lines = [
                    f"### 📊 Spending Breakdown for **{cat}**",
                    f"- **Total Spent:** ${detail['total_spend']:,.2f}",
                    f"- **Transaction Count:** {detail['transaction_count']}",
                    f"- **Average per Purchase:** ${detail['average_transaction']:,.2f}",
                    f"- **Largest Single Purchase:** ${detail['max_transaction']:,.2f}",
                    f"- **Frequent Merchants:** {', '.join(detail['recent_merchants'])}"
                ]
                return ChatResponse(
                    query=raw_query,
                    reply="\n".join(lines),
                    source="ml",
                    suggested_actions=[f"Did I overspend on {cat.lower()}?", "Show my total spending", "What is the 50/30/20 rule?"]
                )

        # General spending summary
        lines = [
            "### 💳 Overall Financial Snapshot",
            f"- **Total Spend:** ${stats['total_spend']:,.2f}",
            f"- **Total Transactions:** {stats['total_transactions']}",
            f"- **Average Transaction Size:** ${stats['average_transaction']:,.2f}",
            f"- **Date Range:** {stats['date_range']}",
            f"- **Top Expense Category:** **{stats['top_spending_category']}** (${stats['top_spending_amount']:,.2f})",
            "",
            "#### Category Breakdown:",
        ]
        for cat, amt in list(stats['category_breakdown'].items())[:5]:
            pct = (amt / stats['total_spend']) * 100
            lines.append(f"- **{cat}:** ${amt:,.2f} ({pct:.1f}%)")

        lines.append(f"\n💡 *You have {len(alerts)} flagged overspending spikes. Ask 'Am I overspending?' to review them.*")

        return ChatResponse(
            query=raw_query,
            reply="\n".join(lines),
            source="ml",
            suggested_actions=["Am I overspending?", "Explain spending clusters", "What is the 50/30/20 rule?"]
        )

    def _handle_rag_intent(self, query: str) -> ChatResponse:
        """Processes financial literacy and concepts using RAG."""
        result = rag_engine.answer_query(query)
        return ChatResponse(
            query=query,
            reply=result["reply"],
            source="rag",
            suggested_actions=["Analyze my spending patterns", "Am I overspending?", "How do index funds work?"],
            metadata={"sources": result.get("sources", []), "engine": result.get("engine", "")}
        )

router = QueryRouter()
