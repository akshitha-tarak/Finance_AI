import React, { useEffect, useState } from 'react';

export default function InsightsDashboard({ apiUrl, onOpenCharts }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/analyze`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error("Failed to load insights:", err);
      setError("Could not load insights. Ensure FastAPI is running on " + apiUrl);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysis();
  }, [apiUrl]);

  if (loading) {
    return (
      <div className="panel-card" style={{ alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '300px' }}>
        <span className="status-dot" style={{ width: '12px', height: '12px', background: '#38bdf8' }}></span>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '12px' }}>Computing ML clusters and analytics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="panel-card">
        <p style={{ color: '#f43f5e', fontSize: '0.9rem' }}>⚠️ {error}</p>
        <button className="clear-btn" onClick={fetchAnalysis} style={{ alignSelf: 'flex-start', marginTop: '10px' }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="panel-card custom-scroll" style={{ maxHeight: '680px', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>📊</span>
          <span>Financial Insights & ML</span>
        </h3>
        <button className="clear-btn" onClick={fetchAnalysis} title="Refresh ML calculations">
          ↻ Refresh
        </button>
      </div>

      {/* KPI Stats Grid */}
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-label">Total Spend</div>
          <div className="stat-value">${data.total_spend.toLocaleString()}</div>
          <div className="stat-desc">{data.total_transactions} Transactions</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Top Outflow</div>
          <div className="stat-value" style={{ fontSize: '1.2rem', color: '#38bdf8' }}>{data.top_spending_category}</div>
          <div className="stat-desc">${data.top_spending_amount.toLocaleString()} spent</div>
        </div>
      </div>

      {/* KMeans Behavioral Personas */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: '#94a3b8', fontWeight: 700 }}>
            🧠 KMeans Spending Personas
          </h4>
          {onOpenCharts && (
            <button 
              onClick={onOpenCharts} 
              style={{ background: 'none', border: 'none', color: '#38bdf8', fontSize: '0.75rem', cursor: 'pointer', fontWeight: 600 }}>
              View Chart →
            </button>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {data.clusters.map((cluster) => (
            <div key={cluster.cluster_id} className="cluster-card">
              <div className="cluster-name">
                <span>{cluster.name}</span>
                <span style={{ color: '#38bdf8' }}>${cluster.total_amount.toLocaleString()}</span>
              </div>
              <div className="cluster-progress-bar">
                <div 
                  className="cluster-progress-fill" 
                  style={{ width: `${Math.min(cluster.percentage_of_total, 100)}%` }}
                />
              </div>
              <div className="cluster-meta">
                {cluster.percentage_of_total}% of budget • Avg ${cluster.avg_amount.toFixed(2)} ({cluster.transaction_count} purchases)
              </div>
              <p style={{ fontSize: '0.76rem', color: '#94a3b8', marginTop: '2px' }}>
                {cluster.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Overspending Anomaly Detection Alerts */}
      <div>
        <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: '#94a3b8', fontWeight: 700, marginBottom: '8px' }}>
          ⚠️ Anomaly & Overspending Alerts ({data.overspending_alerts.length})
        </h4>
        {data.overspending_alerts.length === 0 ? (
          <p style={{ fontSize: '0.8rem', color: '#34d399' }}>✓ All transactions are within standard category bounds.</p>
        ) : (
          <div>
            {data.overspending_alerts.map((alert, idx) => (
              <div key={idx} className={`alert-card ${alert.risk_level.toLowerCase()}`}>
                <div className="alert-header">
                  <span style={{ color: '#f8fafc' }}>{alert.merchant} ({alert.category})</span>
                  <span style={{ 
                    color: alert.risk_level === 'HIGH' ? '#f43f5e' : '#f59e0b',
                    fontSize: '0.75rem',
                    fontWeight: 700
                  }}>
                    {alert.spike_factor}x Spike
                  </span>
                </div>
                <div className="alert-message">
                  {alert.message}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
