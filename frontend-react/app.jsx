const { useState, useEffect, useRef } = React;

// API Base URL
const API_BASE = "http://localhost:8000";

// --- Main App Component ---
function App() {
  const [employeeId, setEmployeeId] = useState("EMP-1042");
  const [activeTab, setActiveTab] = useState("chat");
  const [services, setServices] = useState({
    vpn: { status: "OPERATIONAL", latency: "24ms" },
    wifi: { status: "DEGRADED", latency: "180ms" },
    sap: { status: "MAINTENANCE", latency: "N/A" },
    email: { status: "OPERATIONAL", latency: "42ms" },
  });
  const [backendOnline, setBackendOnline] = useState(true);

  // Check Backend Connectivity
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(res => res.ok ? setBackendOnline(true) : setBackendOnline(false))
      .catch(() => setBackendOnline(false));
  }, []);

  return (
    <div className="app-container">
      {/* Top Navigation Bar */}
      <nav className="navbar">
        <div className="brand">
          <div className="brand-icon">⚡</div>
          <div>
            <div className="brand-title">NexaSupport AI</div>
          </div>
          <span className="brand-badge">React 18</span>
        </div>

        <div className="nav-controls">
          <div className="status-pill">
            <span className="status-dot"></span>
            <span>{backendOnline ? "Backend Connected" : "Connecting..."}</span>
          </div>

          <div className="user-selector">
            <label>Employee ID:</label>
            <input
              type="text"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              placeholder="EMP-1042"
            />
          </div>
        </div>
      </nav>

      {/* Main Workspace Layout */}
      <div className="workspace">
        {/* Left Health Dashboard Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-title">
            <span>IT Services Status</span>
            <button className="refresh-btn" onClick={() => setServices({...services})}>🔄</button>
          </div>

          {Object.entries(services).map(([key, item]) => (
            <div key={key} className="service-card">
              <div className="service-header">
                <span className="service-name">{key.toUpperCase()} Network</span>
                <span className={`badge-${item.status.toLowerCase()}`}>
                  {item.status}
                </span>
              </div>
              <div className="service-details">
                Latency: {item.latency} • Region: US-East
              </div>
            </div>
          ))}
        </aside>

        {/* Main Content View with Tabs */}
        <main className="content-area">
          <div className="tabs-header">
            <button
              className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              💬 AI Support Agent
            </button>
            <button
              className={`tab-btn ${activeTab === 'tickets' ? 'active' : ''}`}
              onClick={() => setActiveTab('tickets')}
            >
              🎫 Incident Tickets
            </button>
            <button
              className={`tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
              onClick={() => setActiveTab('analytics')}
            >
              📊 Satisfaction Analytics
            </button>
          </div>

          {activeTab === 'chat' && <ChatRoom employeeId={employeeId} />}
          {activeTab === 'tickets' && <TicketManager employeeId={employeeId} />}
          {activeTab === 'analytics' && <FeedbackAnalytics />}
        </main>
      </div>
    </div>
  );
}

// --- Chat Room Component ---
function ChatRoom({ employeeId }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: `Hello! I am **NexaSupport AI**, your automated IT incident assistant. How can I help you today?`,
      confidence: 1.0,
      tools: ["knowledge_search"],
      citations: [],
      id: "init-1"
    }
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [ratings, setRatings] = useState({});
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputQuery.trim() || loading) return;

    const userMessage = { role: "user", content: inputQuery, id: Date.now().toString() };
    setMessages((prev) => [...prev, userMessage]);
    setInputQuery("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userMessage.content,
          employee_id: employeeId,
        }),
      });

      if (!response.ok) throw new Error("API error");

      const data = await response.json();
      const botMessage = {
        role: "assistant",
        content: data.answer,
        confidence: data.confidence_score,
        tools: data.tools_executed || [],
        citations: data.sources || [],
        id: (Date.now() + 1).toString(),
        query: userMessage.content,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "❌ Failed to reach NexaSupport AI backend server. Please verify backend is running on `http://localhost:8000`.",
          confidence: 0.0,
          id: Date.now().toString(),
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (msgId, isPositive, query, answer) => {
    setRatings((prev) => ({ ...prev, [msgId]: isPositive ? "up" : "down" }));

    try {
      await fetch(`${API_BASE}/api/v1/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query || "Chat message feedback",
          answer: answer || "",
          rating: isPositive ? "thumbs_up" : "thumbs_down",
          employee_id: employeeId,
        }),
      });
    } catch (e) {
      console.error("Feedback submit error", e);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-history">
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-message ${msg.role}`}>
            <div className={`avatar ${msg.role}`}>
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            
            <div className="message-bubble">
              <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>

              {msg.citations && msg.citations.length > 0 && (
                <div style={{ marginTop: "10px", fontSize: "12px", color: "#9CA3AF" }}>
                  📚 <strong>Sources:</strong> {msg.citations.join(", ")}
                </div>
              )}

              {msg.role === 'assistant' && (
                <div className="meta-bar">
                  {msg.confidence !== undefined && (
                    <span className={`confidence-pill ${msg.confidence > 0.7 ? 'confidence-high' : 'confidence-low'}`}>
                      {(msg.confidence * 100).toFixed(0)}% Confident
                    </span>
                  )}

                  {msg.tools && msg.tools.map((t, idx) => (
                    <span key={idx} className="tool-tag">🔧 {t}</span>
                  ))}

                  {msg.query && (
                    <div className="feedback-actions">
                      <button
                        className={`icon-btn ${ratings[msg.id] === 'up' ? 'selected-up' : ''}`}
                        onClick={() => handleFeedback(msg.id, true, msg.query, msg.content)}
                      >
                        👍 Helpful
                      </button>
                      <button
                        className={`icon-btn ${ratings[msg.id] === 'down' ? 'selected-down' : ''}`}
                        onClick={() => handleFeedback(msg.id, false, msg.query, msg.content)}
                      >
                        👎 Unhelpful
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-message assistant">
            <div className="avatar assistant">🤖</div>
            <div className="message-bubble" style={{ color: "#9CA3AF" }}>
              ⚡ NexaSupport AI is thinking & searching knowledge base...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-bar">
        <form className="input-form" onSubmit={handleSend}>
          <input
            type="text"
            placeholder="Ask IT support a question (e.g., VPN Error 809, WiFi down, SAP access)..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="send-btn" disabled={loading || !inputQuery.trim()}>
            Send Query
          </button>
        </form>
      </div>
    </div>
  );
}

// --- Ticket Manager Component ---
function TicketManager({ employeeId }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    category: "VPN",
    priority: "medium",
    summary: "",
    description: "",
  });

  const fetchTickets = () => {
    setLoading(true);
    fetch(`${API_BASE}/api/v1/tickets`)
      .then((res) => res.json())
      .then((data) => setTickets(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/v1/tickets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: employeeId,
          category: formData.category,
          priority: formData.priority,
          summary: formData.summary,
          description: formData.description,
        }),
      });
      if (res.ok) {
        setShowModal(false);
        setFormData({ category: "VPN", priority: "medium", summary: "", description: "" });
        fetchTickets();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="view-container">
      <div className="view-header">
        <h2 className="view-title">IT Support Incident Tickets</h2>
        <button className="send-btn" onClick={() => setShowModal(true)}>
          + Create Ticket
        </button>
      </div>

      {loading ? (
        <div>Loading tickets from database...</div>
      ) : (
        <table className="ticket-table">
          <thead>
            <tr>
              <th>Ticket ID</th>
              <th>Employee</th>
              <th>Category</th>
              <th>Summary</th>
              <th>Priority</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr key={t.ticket_id}>
                <td style={{ fontWeight: "700", color: "#3B82F6" }}>{t.ticket_id}</td>
                <td>{t.user_id}</td>
                <td>{t.category}</td>
                <td>{t.summary}</td>
                <td style={{ textTransform: "capitalize" }}>{t.priority}</td>
                <td>
                  <span className={`badge-${t.status === 'open' ? 'degraded' : 'operational'}`}>
                    {t.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3 style={{ marginBottom: "16px", fontFamily: "var(--font-heading)" }}>Create IT Incident Ticket</h3>
            <form onSubmit={handleCreateTicket}>
              <div className="form-group">
                <label>Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <option value="VPN">VPN</option>
                  <option value="Email">Email</option>
                  <option value="Password">Password</option>
                  <option value="Network">Network</option>
                  <option value="Hardware">Hardware</option>
                  <option value="Software">Software</option>
                  <option value="Access">Access</option>
                </select>
              </div>

              <div className="form-group">
                <label>Priority</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div className="form-group">
                <label>Summary</label>
                <input
                  type="text"
                  required
                  placeholder="Brief description of the issue..."
                  value={formData.summary}
                  onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Detailed Description</label>
                <textarea
                  rows="4"
                  placeholder="Steps to reproduce, error codes, etc..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", marginTop: "20px" }}>
                <button type="button" className="icon-btn" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="send-btn">
                  Submit Ticket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Feedback Analytics Component ---
function FeedbackAnalytics() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/feedback/stats`)
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch((err) => console.error(err));
  }, []);

  if (!stats) return <div className="view-container">Loading satisfaction analytics...</div>;

  return (
    <div className="view-container">
      <h2 className="view-title" style={{ marginBottom: "20px" }}>AI Response Satisfaction Analytics</h2>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "20px" }}>
        <div className="service-card">
          <div className="service-name">Total Feedback Ratings</div>
          <div style={{ fontSize: "32px", fontWeight: "800", marginTop: "8px" }}>{stats.total}</div>
        </div>

        <div className="service-card">
          <div className="service-name">Satisfaction Rate</div>
          <div style={{ fontSize: "32px", fontWeight: "800", color: "#10B981", marginTop: "8px" }}>
            {stats.satisfaction_rate}%
          </div>
        </div>

        <div className="service-card">
          <div className="service-name">Thumbs Up / Down Breakdown</div>
          <div style={{ fontSize: "20px", fontWeight: "700", marginTop: "8px" }}>
            👍 {stats.thumbs_up} | 👎 {stats.thumbs_down}
          </div>
        </div>
      </div>
    </div>
  );
}

// Render App
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
