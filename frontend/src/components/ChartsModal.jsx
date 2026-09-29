import React, { useEffect, useState } from 'react';

export default function ChartsModal({ isOpen, onClose, apiUrl }) {
  const [charts, setCharts] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetch(`${apiUrl}/charts`)
        .then((res) => res.json())
        .then((data) => {
          setCharts(data);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Error fetching charts:", err);
          setLoading(false);
        });
    }
  }, [isOpen, apiUrl]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content custom-scroll" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
              📈 Visual Financial Analytics
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              High-resolution charts generated directly via Matplotlib backend
            </p>
          </div>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        {loading ? (
          <div style={{ padding: '60px 0', textAlign: 'center', color: '#94a3b8' }}>
            <span className="status-dot" style={{ display: 'inline-block', width: '12px', height: '12px', background: '#38bdf8' }}></span>
            <p style={{ marginTop: '12px', fontSize: '0.9rem' }}>Rendering Matplotlib figures...</p>
          </div>
        ) : (
          <div>
            {charts?.category_chart && (
              <div style={{ marginBottom: '24px' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#38bdf8', marginBottom: '8px', fontWeight: 600 }}>
                  1. Spending Breakdown by Category
                </h4>
                <img
                  src={charts.category_chart}
                  alt="Category Spending Chart"
                  className="chart-img"
                />
              </div>
            )}

            {charts?.cluster_chart && (
              <div>
                <h4 style={{ fontSize: '0.9rem', color: '#a855f7', marginBottom: '8px', fontWeight: 600 }}>
                  2. KMeans Spending Cluster Personas
                </h4>
                <img
                  src={charts.cluster_chart}
                  alt="KMeans Cluster Chart"
                  className="chart-img"
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
