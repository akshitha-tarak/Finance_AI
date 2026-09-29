import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import InsightsDashboard from './components/InsightsDashboard';
import ChartsModal from './components/ChartsModal';
import './index.css';

// Backend API URL: uses Vite env var in production or relative URL / localhost:8000 in dev
const API_URL = import.meta.env?.VITE_API_URL || (
  typeof window !== 'undefined' && (window.location.protocol === 'file:' || window.location.port === '3000' || window.location.port === '5173')
    ? 'http://localhost:8000'
    : ''
);

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [isChartsOpen, setIsChartsOpen] = useState(false);
  const [serverOnline, setServerOnline] = useState(false);

  // Check backend server status
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_URL}/health`);
        if (res.ok) setServerOnline(true);
      } catch (e) {
        setServerOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <nav className="navbar">
        <div className="brand">
          <div className="brand-icon">💎</div>
          <div>
            <h1 className="brand-title">AI-Powered Financial Insights Assistant</h1>
            <p className="brand-subtitle">Machine Learning &bull; LangChain RAG &bull; FastAPI &bull; React</p>
          </div>
        </div>

        <div className="nav-controls">
          <div className="status-badge" style={{
            background: serverOnline ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
            borderColor: serverOnline ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)',
            color: serverOnline ? '#34d399' : '#fb7185'
          }}>
            <span className="status-dot" style={{
              backgroundColor: serverOnline ? '#10b981' : '#f43f5e'
            }}></span>
            <span>{serverOnline ? 'Backend Online' : 'Backend Disconnected'}</span>
          </div>

          <button 
            className="send-btn" 
            style={{ padding: '8px 16px', fontSize: '0.85rem' }}
            onClick={() => setIsChartsOpen(true)}
          >
            📊 Matplotlib Charts
          </button>
        </div>
      </nav>

      {/* Tab Navigation for smaller screens or focused views */}
      <div className="tabs-header">
        <button 
          className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          💬 AI Assistant & Split View
        </button>
        <button 
          className={`tab-btn ${activeTab === 'insights' ? 'active' : ''}`}
          onClick={() => setActiveTab('insights')}
        >
          📊 Deep ML Analytics
        </button>
      </div>

      {/* Main Grid Content */}
      {activeTab === 'chat' ? (
        <div className="main-grid split-view">
          <ChatInterface apiUrl={API_URL} onOpenCharts={() => setIsChartsOpen(true)} />
          <InsightsDashboard apiUrl={API_URL} onOpenCharts={() => setIsChartsOpen(true)} />
        </div>
      ) : (
        <div className="main-grid">
          <InsightsDashboard apiUrl={API_URL} onOpenCharts={() => setIsChartsOpen(true)} />
        </div>
      )}

      {/* Matplotlib Charts Modal */}
      <ChartsModal
        isOpen={isChartsOpen}
        onClose={() => setIsChartsOpen(false)}
        apiUrl={API_URL}
      />
    </div>
  );
}
