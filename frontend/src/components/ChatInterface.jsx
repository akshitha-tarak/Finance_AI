import React, { useState, useRef, useEffect } from 'react';

const SUGGESTIONS = [
  "What is the 50/30/20 budgeting rule?",
  "How much did I spend on dining out?",
  "Am I overspending?",
  "Show my spending clusters and personas",
  "How do index funds and compound interest work?",
  "Explain debt snowball vs avalanche"
];

export default function ChatInterface({ apiUrl, onOpenCharts }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: "👋 Hello! I am your **AI-Powered Financial Insights Assistant**.\n\nI can analyze your personal transaction patterns using **Machine Learning (KMeans & anomaly detection)** or answer finance questions using **RAG (Retrieval-Augmented Generation)**.\n\nTry clicking one of the suggested prompts below or ask any question!",
      source: 'system'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (queryText = input) => {
    const textToSend = (typeof queryText === 'string' ? queryText : input).trim();
    if (!textToSend || loading) return;

    // Add user message
    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: textToSend
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: textToSend })
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      const botMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: data.reply,
        source: data.source,
        suggested_actions: data.suggested_actions || []
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      const errorMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: `⚠️ **Connection Error:** Could not reach the backend at \`${apiUrl}\`. Make sure your FastAPI backend is running!`,
        source: 'error'
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: Date.now(),
        sender: 'assistant',
        text: "Conversation cleared. How can I help you with your finances?",
        source: 'system'
      }
    ]);
  };

  // Helper to format basic markdown (bold, lists, code)
  const formatMarkdown = (text) => {
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // Headers
      if (line.startsWith('### ')) {
        return <h3 key={idx} style={{ fontSize: '1.05rem', fontWeight: 700, margin: '8px 0 4px 0', color: '#38bdf8' }}>{line.replace('### ', '')}</h3>;
      }
      if (line.startsWith('#### ')) {
        return <h4 key={idx} style={{ fontSize: '0.95rem', fontWeight: 600, margin: '6px 0 2px 0', color: '#e2e8f0' }}>{line.replace('#### ', '')}</h4>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={idx} style={{ fontSize: '1.15rem', fontWeight: 700, margin: '10px 0 6px 0', color: '#60a5fa' }}>{line.replace('## ', '')}</h2>;
      }
      // Blockquotes
      if (line.startsWith('> ')) {
        return <blockquote key={idx} style={{ borderLeft: '3px solid #38bdf8', paddingLeft: '8px', margin: '6px 0', color: '#94a3b8', fontStyle: 'italic' }}>{line.replace('> ', '')}</blockquote>;
      }
      // Bullet points
      if (line.startsWith('- ')) {
        return (
          <div key={idx} style={{ display: 'flex', gap: '6px', margin: '3px 0' }}>
            <span style={{ color: '#38bdf8' }}>•</span>
            <span>{renderFormattedText(line.replace('- ', ''))}</span>
          </div>
        );
      }
      return <p key={idx} style={{ minHeight: line.trim() ? 'auto' : '8px', margin: '2px 0' }}>{renderFormattedText(line)}</p>;
    });
  };

  const renderFormattedText = (str) => {
    // Process **bold** and `code`
    const parts = str.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} style={{ color: '#fff', fontWeight: 700 }}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i} style={{ background: '#0f172a', padding: '2px 6px', borderRadius: '4px', fontSize: '0.85em', color: '#38bdf8' }}>{part.slice(1, -1)}</code>;
      }
      return part;
    });
  };

  return (
    <div className="chat-card">
      <div className="chat-header">
        <div className="chat-header-title">
          <span>💬</span>
          <span>Assistant Conversation</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {onOpenCharts && (
            <button className="clear-btn" onClick={onOpenCharts} style={{ color: '#38bdf8', borderColor: 'rgba(56, 189, 248, 0.4)' }}>
              📊 View Charts
            </button>
          )}
          <button className="clear-btn" onClick={clearChat} title="Reset chat history">
            Clear
          </button>
        </div>
      </div>

      <div className="chat-messages custom-scroll">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-wrapper ${msg.sender}`}>
            <div className="message-bubble">
              {formatMarkdown(msg.text)}
            </div>
            <div className="message-meta">
              {msg.source && msg.source !== 'system' && (
                <span className={`source-tag ${msg.source}`}>
                  {msg.source === 'ml' ? '🤖 ML Analytics' : msg.source === 'rag' ? '📚 Financial RAG' : msg.source}
                </span>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-wrapper assistant">
            <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="status-dot" style={{ background: '#38bdf8' }}></span>
              <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Analyzing query with ML & RAG...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="suggestions-box custom-scroll">
        {SUGGESTIONS.map((sug, i) => (
          <button key={i} className="suggestion-pill" onClick={() => handleSend(sug)}>
            {sug}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div className="chat-input-bar">
        <input
          type="text"
          className="chat-input"
          placeholder="Ask about your spending or personal finance concepts..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button className="send-btn" onClick={() => handleSend()} disabled={loading || !input.trim()}>
          <span>Send</span>
          <span>→</span>
        </button>
      </div>
    </div>
  );
}
