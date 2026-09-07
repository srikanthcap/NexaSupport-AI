# =============================================================
# NexaSupport AI — Streamlit Frontend
# =============================================================
# PURPOSE:
#   Full enterprise-style UI for the NexaSupport AI system.
#   Employee Portal: Chat with AI, view sources, create tickets.
#   IT Admin Dashboard: Ticket stats, recent incidents.
#
# HOW TO RUN:
#   streamlit run frontend/streamlit_app.py
#
# REQUIRES:
#   FastAPI backend running at http://localhost:8000
#   Run: uvicorn app.main:app --reload (in a separate terminal)
# =============================================================

import httpx
import streamlit as st

# ── Page Configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NexaSupport AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://localhost:8000"

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d6efd 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    /* Chat bubbles */
    .chat-user {
        background: #e8f0fe;
        border-left: 4px solid #0d6efd;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .chat-ai {
        background: #f0f9f0;
        border-left: 4px solid #198754;
        padding: 0.75rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    /* Source citation cards */
    .source-card {
        background: #fff8e1;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
        margin: 0.25rem 0;
        font-size: 0.85em;
    }
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        border-top: 4px solid #0d6efd;
    }
    /* Confidence badge */
    .badge-high { color: #198754; font-weight: bold; }
    .badge-med  { color: #fd7e14; font-weight: bold; }
    .badge-low  { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ───────────────────────────────────────────────────────────

def check_backend() -> bool:
    """Check if the FastAPI backend is reachable."""
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


def ask_ai(query: str, top_k: int = 5, history: list = None) -> dict | None:
    """Send a question to the RAG pipeline and return the response."""
    try:
        payload = {
            "query": query,
            "top_k": top_k,
            "conversation_history": history or [],
        }
        r = httpx.post(f"{API_BASE}/api/v1/chat", json=payload, timeout=30.0)
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"API error {r.status_code}: {r.text}")
            return None
    except httpx.ConnectError:
        st.error("❌ Cannot reach backend. Is `uvicorn app.main:app --reload` running?")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def create_ticket(user_id: str, category: str, priority: str, summary: str) -> dict | None:
    """Create an IT support ticket via the API."""
    try:
        payload = {
            "user_id": user_id,
            "category": category,
            "priority": priority,
            "summary": summary,
        }
        r = httpx.post(f"{API_BASE}/api/v1/tickets", json=payload, timeout=10.0)
        if r.status_code == 201:
            return r.json()
        return None
    except Exception:
        return None


def get_ticket_stats() -> dict | None:
    """Fetch ticket stats from the API."""
    try:
        r = httpx.get(f"{API_BASE}/api/v1/tickets/stats", timeout=5.0)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def get_recent_tickets(limit: int = 10) -> list:
    """Fetch recent tickets from the API."""
    try:
        r = httpx.get(f"{API_BASE}/api/v1/tickets?limit={limit}", timeout=5.0)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def confidence_badge(score: float) -> str:
    """Return a colored confidence label."""
    if score >= 0.7:
        return f'<span class="badge-high">🟢 {score:.0%} High Confidence</span>'
    elif score >= 0.4:
        return f'<span class="badge-med">🟡 {score:.0%} Medium Confidence</span>'
    else:
        return f'<span class="badge-low">🔴 {score:.0%} Low Confidence</span>'


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/it-support.png", width=64)
    st.markdown("## 🛡️ NexaSupport AI")
    st.markdown("*Enterprise IT Support Assistant*")
    st.divider()

    # Navigation
    page = st.radio(
        "Navigation",
        ["💬 Employee Chat", "🎫 My Tickets", "📊 Admin Dashboard"],
        label_visibility="collapsed",
    )
    st.divider()

    # Backend status
    backend_ok = check_backend()
    if backend_ok:
        st.success("🟢 Backend: Online")
    else:
        st.error("🔴 Backend: Offline")

    # Settings
    st.subheader("⚙️ Settings")
    employee_id = st.text_input("Employee ID", value="EMP-1042", help="Your employee ID")
    top_k = st.slider("Sources to retrieve", 1, 10, 5, help="More sources = more context for the AI")

    st.divider()
    st.caption("NexaSupport AI v1.0 | Phases 2–7")


# ── Initialize session state ───────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # List of {"role": ..., "content": ..., "meta": ...}


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EMPLOYEE CHAT
# ══════════════════════════════════════════════════════════════════════════════
if page == "💬 Employee Chat":

    # Header
    st.markdown("""
    <div class="main-header">
        <h2 style="margin:0">🛡️ NexaSupport AI — Employee IT Support</h2>
        <p style="margin:0.25rem 0 0; opacity:0.85">Ask any IT question — VPN, email, password, software, network, and more.</p>
    </div>
    """, unsafe_allow_html=True)

    if not backend_ok:
        st.warning("⚠️ The AI backend is not running. Start it with:\n```\nuvicorn app.main:app --reload\n```")

    # Chat history display
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">👤 <b>You:</b> {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown(f'<div class="chat-ai">🤖 <b>NexaSupport AI:</b></div>', unsafe_allow_html=True)
                st.markdown(msg["content"])
                meta = msg.get("meta", {})
                if meta:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(confidence_badge(meta.get("confidence", 0)), unsafe_allow_html=True)
                    with col2:
                        st.caption(f"📚 {meta.get('retrieval_count', 0)} sources used")
                    with col3:
                        st.caption(f"⏱️ {meta.get('latency_ms', 0):.0f}ms")

                    # Sources
                    sources = meta.get("sources", [])
                    if sources:
                        with st.expander(f"📄 View {len(sources)} source(s)", expanded=False):
                            for src in sources:
                                st.markdown(
                                    f'<div class="source-card">'
                                    f'<b>{src["citation_label"]}</b>: {src["title"]} '
                                    f'— {src["source_file"]} (Section {src["chunk_index"]+1}) '
                                    f'| Relevance: {src["similarity_score"]:.0%}'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )

                    # Escalation warning
                    if meta.get("needs_escalation"):
                        st.warning("⚠️ Low confidence — consider creating a support ticket below.")

    # Chat input
    st.divider()
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_area(
                "Your IT question:",
                placeholder="e.g. My VPN shows Error 809 and cannot connect. What should I do?",
                height=80,
                label_visibility="collapsed",
            )
        with col2:
            st.write("")
            st.write("")
            submit = st.form_submit_button("Send 📤", use_container_width=True)

    if submit and user_input.strip():
        if not backend_ok:
            st.error("Backend is offline. Cannot send messages.")
        else:
            with st.spinner("🤖 AI is thinking..."):
                # Build conversation history for context
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_history[-6:]
                    if m["role"] in ("user", "assistant")
                ]

                response = ask_ai(user_input.strip(), top_k=top_k, history=history)

            if response:
                # Store user message
                st.session_state.chat_history.append(
                    {"role": "user", "content": user_input.strip()}
                )
                # Store AI response with metadata
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "meta": {
                        "confidence": response.get("confidence", 0),
                        "sources": response.get("sources", []),
                        "retrieval_count": response.get("retrieval_count", 0),
                        "latency_ms": response.get("latency_ms", 0),
                        "needs_escalation": response.get("needs_escalation", False),
                    },
                })
                st.rerun()

    # Ticket creation form
    if st.session_state.chat_history:
        with st.expander("🎫 Create a Support Ticket for this Issue"):
            with st.form(key="ticket_form"):
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    t_category = st.selectbox(
                        "Category",
                        ["VPN", "Email", "Password", "Network", "Software", "Hardware", "Access", "Other"],
                    )
                with t_col2:
                    t_priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])
                t_summary = st.text_area("Issue Summary", height=80)
                t_submit = st.form_submit_button("Create Ticket 🎫")

            if t_submit and t_summary.strip():
                ticket = create_ticket(employee_id, t_category, t_priority, t_summary.strip())
                if ticket:
                    st.success(f"✅ Ticket **{ticket['ticket_id']}** created successfully! Status: {ticket['status']}")
                else:
                    st.error("Failed to create ticket. Check backend connection.")

    # Clear chat
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Conversation"):
            st.session_state.chat_history = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MY TICKETS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎫 My Tickets":
    st.markdown(f"""
    <div class="main-header">
        <h2 style="margin:0">🎫 My IT Support Tickets</h2>
        <p style="margin:0.25rem 0 0; opacity:0.85">Employee: {employee_id}</p>
    </div>
    """, unsafe_allow_html=True)

    tickets = get_recent_tickets(limit=50)
    my_tickets = [t for t in tickets if t.get("user_id") == employee_id]

    if not my_tickets:
        st.info(f"No tickets found for {employee_id}. Try creating one from the Chat page.")
    else:
        st.success(f"Found {len(my_tickets)} ticket(s)")
        for t in my_tickets:
            status_icon = {"open": "🔵", "in_progress": "🟡", "resolved": "🟢", "escalated": "🔴", "closed": "⚫"}.get(t["status"], "⚪")
            priority_color = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(t["priority"], "⚪")
            with st.expander(f"{status_icon} {t['ticket_id']} — {t['summary'][:60]}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Status", t["status"].replace("_", " ").title())
                col2.metric("Priority", f"{priority_color} {t['priority'].title()}")
                col3.metric("Category", t["category"])
                if t.get("description"):
                    st.markdown(f"**Description:** {t['description']}")
                if t.get("resolution"):
                    st.success(f"✅ **Resolution:** {t['resolution']}")
                st.caption(f"Created: {t['created_at'][:10]}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Admin Dashboard":
    st.markdown("""
    <div class="main-header">
        <h2 style="margin:0">📊 IT Admin Dashboard</h2>
        <p style="margin:0.25rem 0 0; opacity:0.85">Real-time IT support metrics and incident overview</p>
    </div>
    """, unsafe_allow_html=True)

    stats = get_ticket_stats()
    if stats:
        # KPI metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📋 Total Tickets", stats.get("total_tickets", 0))
        col2.metric("🔵 Open", stats.get("open", 0))
        col3.metric("🟡 In Progress", stats.get("in_progress", 0))
        col4.metric("✅ Resolved", stats.get("resolved", 0))
        col5.metric("🔴 Escalated", stats.get("escalated", 0))

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            rate = stats.get("resolution_rate", 0)
            st.metric("📈 Resolution Rate", f"{rate}%")
            st.progress(rate / 100)
        with col_b:
            escalated = stats.get("escalated", 0)
            total = max(stats.get("total_tickets", 1), 1)
            esc_rate = round(escalated / total * 100, 1)
            st.metric("🔼 Escalation Rate", f"{esc_rate}%")
            st.progress(esc_rate / 100)
    else:
        st.warning("Could not load stats. Is the backend running?")

    # Recent tickets table
    st.subheader("📋 Recent Incidents")
    tickets = get_recent_tickets(limit=20)
    if tickets:
        import pandas as pd
        df = pd.DataFrame([{
            "Ticket ID": t["ticket_id"],
            "Employee": t["user_id"],
            "Category": t["category"],
            "Priority": t["priority"].title(),
            "Status": t["status"].replace("_", " ").title(),
            "Summary": t["summary"][:60] + ("…" if len(t["summary"]) > 60 else ""),
            "Created": t["created_at"][:10],
        } for t in tickets])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No tickets found or backend is offline.")

    # Search historical incidents
    st.subheader("🔍 Search Historical Incidents")
    search_q = st.text_input("Search keyword", placeholder="e.g. VPN Error 809")
    if search_q and len(search_q) >= 3:
        try:
            r = httpx.get(f"{API_BASE}/api/v1/tickets/search?q={search_q}&limit=5", timeout=5.0)
            if r.status_code == 200:
                results = r.json()
                if results:
                    st.success(f"Found {len(results)} similar incident(s):")
                    for t in results:
                        with st.expander(f"[{t['ticket_id']}] {t['summary'][:70]}"):
                            if t.get("resolution"):
                                st.success(f"**Resolution:** {t['resolution']}")
                            st.caption(f"Category: {t['category']} | Status: {t['status']} | Resolved: {t.get('resolved_at', 'N/A')}")
                else:
                    st.info("No similar incidents found.")
        except Exception as e:
            st.error(f"Search failed: {e}")

