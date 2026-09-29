import io
import base64
import pandas as pd

class ChartVisualizer:
    """
    Generates high-resolution matplotlib financial charts
    and encodes them as base64 data URLs for seamless web rendering.
    """
    def __init__(self):
        pass

    def get_category_spending_chart_base64(self, df: pd.DataFrame) -> str:
        """Creates a modern horizontal bar chart of spending by category."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        if df.empty:
            return ""

        cat_spending = df.groupby('category')['amount'].sum().sort_values(ascending=True)

        fig, ax = plt.subplots(figsize=(8, 4.5), facecolor='#111827')
        ax.set_facecolor('#111827')

        # Modern palette
        colors = ['#38bdf8', '#818cf8', '#a78bfa', '#c084fc', '#f472b6', '#fb7185', '#34d399', '#fbbf24']
        bar_colors = (colors * 3)[:len(cat_spending)]

        bars = ax.barh(cat_spending.index, cat_spending.values, color=bar_colors, height=0.65, edgecolor='none')

        # Add values on bars
        for bar in bars:
            width = bar.get_width()
            ax.text(width + (cat_spending.max() * 0.015), bar.get_y() + bar.get_height()/2,
                    f"${width:,.0f}",
                    va='center', ha='left', color='#e2e8f0', fontsize=10, fontweight='bold')

        ax.set_title("Spending Breakdown by Category ($)", color='#f8fafc', fontsize=14, pad=15, fontweight='bold')
        ax.tick_params(colors='#94a3b8', labelsize=10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#334155')
        ax.spines['bottom'].set_color('#334155')
        ax.grid(axis='x', color='#1e293b', linestyle='--', alpha=0.7)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{encoded}"

    def get_cluster_scatter_chart_base64(self, clustered_df: pd.DataFrame) -> str:
        """Visualizes KMeans clusters in an amount vs transaction sequence scatter."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        if clustered_df.empty or 'cluster' not in clustered_df.columns:
            return ""

        fig, ax = plt.subplots(figsize=(8, 4.5), facecolor='#111827')
        ax.set_facecolor('#111827')

        palette = {0: '#38bdf8', 1: '#34d399', 2: '#f43f5e'}
        
        clustered_df = clustered_df.copy()
        clustered_df['idx'] = range(1, len(clustered_df) + 1)

        for cluster_id in sorted(clustered_df['cluster'].unique()):
            subset = clustered_df[clustered_df['cluster'] == cluster_id]
            persona = subset['cluster_persona'].iloc[0] if 'cluster_persona' in subset else f"Cluster {cluster_id}"
            ax.scatter(
                subset['idx'],
                subset['amount'],
                color=palette.get(cluster_id, '#a78bfa'),
                label=persona,
                s=70,
                alpha=0.85,
                edgecolors='white',
                linewidth=0.5
            )

        ax.set_title("KMeans Spending Clusters & Persona Distribution", color='#f8fafc', fontsize=14, pad=15, fontweight='bold')
        ax.set_xlabel("Transaction Sequence (#)", color='#94a3b8', fontsize=11)
        ax.set_ylabel("Transaction Amount ($)", color='#94a3b8', fontsize=11)
        ax.tick_params(colors='#94a3b8', labelsize=10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#334155')
        ax.spines['bottom'].set_color('#334155')
        ax.grid(color='#1e293b', linestyle='--', alpha=0.7)
        
        legend = ax.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=9)
        plt.setp(legend.get_texts(), color='#e2e8f0')

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{encoded}"

visualizer = ChartVisualizer()
