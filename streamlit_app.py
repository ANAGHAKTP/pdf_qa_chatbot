import os
import re
import tempfile
import datetime
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Lexis — PDF Intelligence",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    color: #1a1a2e;
}

/* Warm off-white background — feels like paper, not a screen */
.stApp { background: #f5f3ef; }

[data-testid="stSidebar"] {
    background: #1a1a2e;
    border-right: none;
}
[data-testid="stSidebar"] * { color: #c8cad8 !important; }

.sidebar-logo {
    padding: 28px 20px 20px;
    border-bottom: 1px solid #252542;
}
.sidebar-logo .wordmark {
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: -0.04em;
    color: #fff !important;
}
.sidebar-logo .wordmark em {
    font-style: normal;
    color: #f59e0b !important;
}
.sidebar-logo .sub {
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4b4d6a !important;
    margin-top: 4px;
}

.sec-head {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4b4d6a !important;
    padding: 20px 20px 6px;
}

.pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 11px;
    border-radius: 20px;
    font-size: 0.71rem;
    font-weight: 600;
    letter-spacing: 0.06em;
}
.pill-ready  { background:#0d2e1f; color:#4ade80 !important; border:1px solid #166534; }
.pill-wait   { background:#1f1f38; color:#818cf8 !important; border:1px solid #3730a3; }

.file-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.73rem;
    color: #f59e0b !important;
    background: #2a1f0a;
    border: 1px solid #78350f;
    padding: 3px 9px;
    border-radius: 4px;
    margin-top: 6px;
    display: inline-block;
}

/* ── Main header ── */
.page-header {
    padding: 36px 0 4px;
    border-bottom: 2px solid #1a1a2e;
    margin-bottom: 0;
}
.page-header h1 {
    font-size: 1.9rem;
    font-weight: 700;
    letter-spacing: -0.04em;
    color: #1a1a2e;
}
.page-header h1 span { color: #f59e0b; }

.doc-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.73rem;
    color: #f59e0b;
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 4px;
    padding: 3px 10px;
}

/* ── Summary card ── */
.summary-card {
    background: #1a1a2e;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 20px 0;
    position: relative;
    overflow: hidden;
}
.summary-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #f59e0b, #fbbf24, #f59e0b);
}
.summary-card .sum-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #f59e0b;
    margin-bottom: 10px;
}
.summary-card .sum-text {
    font-size: 0.9rem;
    line-height: 1.7;
    color: #c8cad8;
}

/* ── Chat ── */
.chat-area { padding: 8px 0; }

.msg-user-wrap { display:flex; justify-content:flex-end; margin: 14px 0 4px; }
.msg-user-bubble {
    background: #1a1a2e;
    color: #e8eaf0;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    max-width: 68%;
    font-size: 0.92rem;
    line-height: 1.6;
}
.msg-user-label {
    text-align: right;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9ca3af;
    margin-bottom: 4px;
}

.msg-ai-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #f59e0b;
    margin-bottom: 4px;
}
.msg-ai-bubble {
    background: #fff;
    border: 1px solid #e5e0d8;
    border-left: 3px solid #f59e0b;
    border-radius: 4px 16px 16px 16px;
    padding: 16px 20px;
    max-width: 86%;
    font-size: 0.92rem;
    line-height: 1.75;
    color: #1a1a2e;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.msg-ai-bubble p { margin: 0 0 10px; }
.msg-ai-bubble p:last-child { margin-bottom: 0; }
.msg-ai-bubble ul, .msg-ai-bubble ol { padding-left: 20px; margin: 8px 0; }
.msg-ai-bubble li { margin: 5px 0; }
.msg-ai-bubble strong { color: #92400e; font-weight: 600; }
.msg-ai-bubble code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82em;
    background: #fef3c7;
    padding: 2px 6px;
    border-radius: 3px;
    color: #78350f;
}

/* Timestamp */
.msg-time {
    font-size: 0.63rem;
    color: #d1d5db;
    margin-top: 4px;
    padding-left: 2px;
}

/* ── Source chips ── */
.src-row { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
.src-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    background: #fef3c7;
    border: 1px solid #f59e0b;
    color: #78350f;
    padding: 2px 8px;
    border-radius: 20px;
    cursor: default;
}

/* ── Empty state ── */
.empty-wrap {
    text-align: center;
    padding: 80px 0;
    color: #9ca3af;
}
.empty-wrap .e-icon { font-size: 2.8rem; opacity: 0.3; margin-bottom: 16px; }
.empty-wrap h3 { font-size: 1rem; font-weight: 500; color: #6b7280; margin-bottom: 6px; }
.empty-wrap p { font-size: 0.83rem; }

/* ── Input ── */
.stTextInput > div > div > input {
    background: #fff !important;
    border: 2px solid #e5e0d8 !important;
    border-radius: 10px !important;
    color: #1a1a2e !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.92rem !important;
    padding: 12px 16px !important;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #f59e0b !important;
    box-shadow: 0 0 0 3px rgba(245,158,11,0.15) !important;
}
.stTextInput > div > div > input::placeholder { color: #bdb8b0 !important; }

/* Buttons */
.stButton > button {
    background: #1a1a2e !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 12px 20px !important;
    transition: background 0.2s !important;
}
.stButton > button:hover { background: #f59e0b !important; color: #1a1a2e !important; }

/* Sidebar buttons override */
[data-testid="stSidebar"] .stButton > button {
    background: #252542 !important;
    color: #c8cad8 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #f59e0b !important;
    color: #1a1a2e !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #252542;
    border: 1.5px dashed #3b3b5c;
    border-radius: 10px;
    padding: 4px;
}

/* Expander */
[data-testid="stExpander"] {
    background: #fafaf8 !important;
    border: 1px solid #e5e0d8 !important;
    border-radius: 8px !important;
}

/* Download button */
.stDownloadButton > button {
    background: #059669 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    padding: 8px 14px !important;
}
.stDownloadButton > button:hover { background: #047857 !important; }

hr { border-color: #e5e0d8 !important; margin: 10px 0 !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* Spinner */
.stSpinner > div { border-top-color: #f59e0b !important; }

/* Suggested questions */
.sq-wrap { display:flex; flex-wrap:wrap; gap:8px; margin: 12px 0 16px; }
.sq-btn {
    background: #fff;
    border: 1px solid #e5e0d8;
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.78rem;
    color: #4b5563;
    cursor: pointer;
    transition: all 0.15s;
    font-family: 'Outfit', sans-serif;
}
.sq-btn:hover { border-color: #f59e0b; color: #92400e; background: #fef3c7; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def md_to_html(text: str) -> str:
    """Convert basic markdown to HTML for display."""
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
    # Inline code
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    # Process lines
    lines = text.split("\n")
    out, in_ul, in_ol = [], False, False
    for line in lines:
        s = line.strip()
        # Numbered list
        num_match = re.match(r'^(\d+)\.\s+(.*)', s)
        if num_match:
            if in_ul: out.append("</ul>"); in_ul = False
            if not in_ol: out.append("<ol>"); in_ol = True
            out.append(f"<li>{num_match.group(2)}</li>")
        # Bullet list
        elif re.match(r'^[-*•]\s+', s):
            if in_ol: out.append("</ol>"); in_ol = False
            if not in_ul: out.append("<ul>"); in_ul = True
            clean_item = re.sub(r'^[-*•]\s+', '', s)
            out.append(f"<li>{clean_item}</li>")
        else:
            if in_ul: out.append("</ul>"); in_ul = False
            if in_ol: out.append("</ol>"); in_ol = False
            if s:
                out.append(f"<p>{s}</p>")
    if in_ul: out.append("</ul>")
    if in_ol: out.append("</ol>")
    return "\n".join(out)


def export_chat_txt(messages, pdf_name: str) -> str:
    lines = [f"Lexis — Chat Export", f"Document: {pdf_name}",
             f"Exported: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", "="*60, ""]
    for m in messages:
        role = "You" if m["role"] == "user" else "Lexis"
        ts = m.get("time", "")
        lines.append(f"[{ts}] {role}:")
        # Strip HTML tags for plain text
        content = re.sub(r'<[^>]+>', '', m["content"])
        lines.append(content)
        lines.append("")
    return "\n".join(lines)


# ── Cached resources ───────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def build_vector_store(pdf_bytes: bytes, filename: str, api_key: str):
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
    from langchain_chroma import Chroma

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    loader = PyPDFLoader(tmp_path)
    documents = loader.load()
    os.unlink(tmp_path)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)

    db_dir = f"chroma_db_{filename.replace('.', '_').replace(' ', '_')}"
    embeddings = NVIDIAEmbeddings(model="nvidia/nv-embedqa-e5-v5", api_key=api_key)

    if os.path.exists(db_dir) and os.listdir(db_dir):
        vs = Chroma(persist_directory=db_dir, embedding_function=embeddings)
    else:
        vs = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_dir)

    return vs, len(chunks), len(documents)


@st.cache_resource(show_spinner=False)
def build_rag_chain(_vectorstore, api_key: str):
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    from langchain_classic.chains import create_retrieval_chain
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate

    retriever = _vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 6, "fetch_k": 20}
    )
    llm = ChatNVIDIA(model="meta/llama-3.1-8b-instruct", api_key=api_key, temperature=0)

    system_prompt = (
        "You are Lexis, a precise document intelligence assistant. "
        "Answer questions strictly from the provided context.\n\n"
        "Formatting rules:\n"
        "- Use **bold** for key terms.\n"
        "- Use bullet points (-) for lists of 3 or more items.\n"
        "- Use numbered lists for steps or sequences.\n"
        "- Keep paragraphs short (2-3 sentences max).\n"
        "- Never start with 'Based on the context' or similar filler.\n"
        "- If unsure, say so clearly.\n\n"
        "Context:\n{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{chat_history}\n\nQuestion: {input}"),
    ])
    qa_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, qa_chain)


@st.cache_resource(show_spinner=False)
def get_summary_and_questions(pdf_bytes: bytes, filename: str, api_key: str):
    """Generate a document summary + 4 suggested questions in one LLM call."""
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    from langchain_community.document_loaders import PyPDFLoader
    import json

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    loader = PyPDFLoader(tmp_path)
    docs = loader.load()
    os.unlink(tmp_path)

    # Use first 3 pages for speed
    sample_text = " ".join([d.page_content for d in docs[:3]])[:3000]

    llm = ChatNVIDIA(model="meta/llama-3.1-8b-instruct", api_key=api_key, temperature=0.1)
    prompt = f"""Given this document excerpt, respond ONLY with valid JSON, no extra text:
{{
  "summary": "2-3 sentence summary of what this document is about",
  "questions": ["question 1", "question 2", "question 3", "question 4"]
}}

Document excerpt:
{sample_text}"""

    try:
        result = llm.invoke(prompt)
        text = result.content if hasattr(result, 'content') else str(result)
        # Extract JSON
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data.get("summary", ""), data.get("questions", [])
    except Exception:
        pass
    return "", []


# ── Session state ──────────────────────────────────────────────────────────────
defaults = {
    "messages": [], "pdf_ready": False, "rag_chain": None,
    "pdf_name": None, "chunk_count": 0, "page_count": 0,
    "summary": "", "suggested_qs": [], "pdf_bytes": None,
    "api_key": "", "pending_question": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="wordmark">Le<em>x</em>is</div>
        <div class="sub">PDF Intelligence · RAG · NVIDIA NIM</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-head">API Key</div>', unsafe_allow_html=True)
    api_key_env = os.getenv("NVIDIA_API_KEY", "")
    api_key = st.text_input(
        "NVIDIA API Key", value=api_key_env, type="password",
        placeholder="nvapi-...", label_visibility="collapsed"
    )
    if api_key:
        st.session_state.api_key = api_key

    st.markdown('<div class="sec-head">Document</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")

    if uploaded and api_key:
        if st.button("⟳  Index document", use_container_width=True):
            with st.spinner("Indexing…"):
                try:
                    pdf_bytes = uploaded.read()
                    vs, n_chunks, n_pages = build_vector_store(pdf_bytes, uploaded.name, api_key)
                    st.session_state.rag_chain = build_rag_chain(vs, api_key)
                    st.session_state.pdf_ready = True
                    st.session_state.pdf_name = uploaded.name
                    st.session_state.chunk_count = n_chunks
                    st.session_state.page_count = n_pages
                    st.session_state.messages = []
                    st.session_state.pdf_bytes = pdf_bytes
                    # Summary + suggested questions
                    with st.spinner("Generating summary…"):
                        summary, qs = get_summary_and_questions(pdf_bytes, uploaded.name, api_key)
                        st.session_state.summary = summary
                        st.session_state.suggested_qs = qs
                    st.success(f"Ready — {n_chunks} chunks, {n_pages} pages")
                except Exception as e:
                    st.error(str(e))
    elif uploaded and not api_key:
        st.caption("Enter API key first ↑")

    st.markdown('<div class="sec-head">Status</div>', unsafe_allow_html=True)
    if st.session_state.pdf_ready:
        st.markdown('<span class="pill pill-ready">● Ready</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="file-chip">{st.session_state.pdf_name}</div>', unsafe_allow_html=True)
        st.caption(f"{st.session_state.page_count}p · {st.session_state.chunk_count} chunks · MMR k=6")
    else:
        st.markdown('<span class="pill pill-wait">○ Awaiting document</span>', unsafe_allow_html=True)

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with c2:
        if st.button("New doc", use_container_width=True):
            for k in ["messages","pdf_ready","rag_chain","pdf_name","chunk_count",
                      "page_count","summary","suggested_qs","pdf_bytes"]:
                st.session_state[k] = defaults[k]
            st.rerun()

    # Export
    if st.session_state.messages:
        st.markdown("---")
        st.markdown('<div class="sec-head">Export</div>', unsafe_allow_html=True)
        export_txt = export_chat_txt(st.session_state.messages, st.session_state.pdf_name or "document")
        st.download_button(
            "⬇ Download chat (.txt)",
            data=export_txt,
            file_name=f"lexis_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )


# ── Main area ──────────────────────────────────────────────────────────────────
h_left, h_right = st.columns([3, 1])
with h_left:
    st.markdown("""
    <div class="page-header">
        <h1>Le<span>x</span>is</h1>
    </div>
    """, unsafe_allow_html=True)
with h_right:
    if st.session_state.pdf_ready:
        st.markdown(
            f'<div style="padding-top:40px;text-align:right">'
            f'<span class="doc-badge">📄 {st.session_state.pdf_name}</span></div>',
            unsafe_allow_html=True
        )

st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

# ── Empty state ────────────────────────────────────────────────────────────────
if not st.session_state.pdf_ready:
    st.markdown("""
    <div class="empty-wrap">
        <div class="e-icon">📖</div>
        <h3>No document loaded</h3>
        <p>Upload a PDF in the sidebar and click <strong>Index document</strong> to start.</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Summary card ────────────────────────────────────────────────────────
    if st.session_state.summary:
        st.markdown(f"""
        <div class="summary-card">
            <div class="sum-label">📋 Document Summary</div>
            <div class="sum-text">{st.session_state.summary}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Suggested questions ──────────────────────────────────────────────────
    if st.session_state.suggested_qs and not st.session_state.messages:
        st.markdown("<div style='font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#9ca3af;margin-bottom:6px'>Suggested questions</div>", unsafe_allow_html=True)
        cols = st.columns(2)
        for i, q in enumerate(st.session_state.suggested_qs[:4]):
            with cols[i % 2]:
                if st.button(q, key=f"sq_{i}", use_container_width=True):
                    st.session_state.pending_question = q
                    st.rerun()

    # ── Chat history ─────────────────────────────────────────────────────────
    st.markdown('<div class="chat-area">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        ts = msg.get("time", "")
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="msg-user-label">You · {ts}</div>
            <div class="msg-user-wrap">
                <div class="msg-user-bubble">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-ai-label">Lexis · {ts}</div>
            <div class="msg-ai-bubble">{msg["content"]}</div>
            """, unsafe_allow_html=True)
            if msg.get("sources"):
                pages = sorted(set(
                    str(s.metadata.get("page", "?")) for s in msg["sources"]
                ))
                chips = "".join(f'<span class="src-chip">p.{p}</span>' for p in pages)
                with st.expander(f"  {len(msg['sources'])} source chunks", expanded=False):
                    st.markdown(f'<div class="src-row">{chips}</div>', unsafe_allow_html=True)
                    for i, src in enumerate(msg["sources"], 1):
                        page = src.metadata.get("page", "?")
                        snippet = src.page_content[:220].replace("\n", " ").strip()
                        st.markdown(
                            f"**Chunk {i} · Page {page}:** {snippet}...",
                            help="Retrieved context chunk"
                        )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Input row ────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_q, col_btn = st.columns([6, 1])
    with col_q:
        question = st.text_input(
            "Ask",
            value=st.session_state.pending_question,
            placeholder="Ask anything about your document…",
            label_visibility="collapsed",
            key="question_box"
        )
    with col_btn:
        ask = st.button("Ask →", use_container_width=True)

    # Handle ask (button or suggested question)
    trigger = (ask and question.strip()) or st.session_state.pending_question
    final_q = st.session_state.pending_question or question.strip()

    if trigger and final_q:
        st.session_state.pending_question = ""
        ts_now = datetime.datetime.now().strftime("%H:%M")

        # Build chat history string for context
        history_lines = []
        for m in st.session_state.messages[-6:]:  # last 3 turns
            role = "User" if m["role"] == "user" else "Assistant"
            clean = re.sub(r'<[^>]+>', '', m["content"])
            history_lines.append(f"{role}: {clean}")
        chat_history = "\n".join(history_lines)

        st.session_state.messages.append({
            "role": "user", "content": final_q, "time": ts_now
        })

        with st.spinner(""):
            try:
                response = st.session_state.rag_chain.invoke({
                    "input": final_q,
                    "chat_history": chat_history
                })
                answer_html = md_to_html(response["answer"])
                sources = response.get("context", [])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer_html,
                    "sources": sources,
                    "time": datetime.datetime.now().strftime("%H:%M")
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"<p style='color:#dc2626'>Error: {e}</p>",
                    "sources": [],
                    "time": datetime.datetime.now().strftime("%H:%M")
                })
        st.rerun()
