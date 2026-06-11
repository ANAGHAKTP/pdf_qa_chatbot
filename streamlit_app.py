import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocMind — PDF Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design tokens ──────────────────────────────────────────────────────────────
# Palette: deep navy base, slate panels, electric indigo accent, warm white text
# Typography: DM Sans for UI, DM Mono for code/sources
# Signature: the answer card uses a left-edge gradient bar that fades from
#            indigo → transparent, giving answers a "document highlight" feel

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #e8eaf0;
}

/* ── App shell ── */
.stApp { background: #0d0f1a; }

[data-testid="stSidebar"] {
    background: #111422;
    border-right: 1px solid #1e2235;
    padding-top: 0;
}

/* ── Sidebar header ── */
.sidebar-brand {
    padding: 24px 20px 16px;
    border-bottom: 1px solid #1e2235;
    margin-bottom: 8px;
}
.sidebar-brand .logo {
    font-size: 1.25rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #fff;
}
.sidebar-brand .logo span { color: #6366f1; }
.sidebar-brand .tagline {
    font-size: 0.72rem;
    color: #4b5270;
    margin-top: 3px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── Section labels ── */
.section-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4b5270;
    padding: 16px 20px 6px;
}

/* ── Status pill ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.pill-ready { background: #0d2e1f; color: #4ade80; border: 1px solid #166534; }
.pill-waiting { background: #1a1d2e; color: #6366f1; border: 1px solid #2d3060; }
.pill-error { background: #2d0f17; color: #f87171; border: 1px solid #7f1d1d; }

.file-tag {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: #6366f1;
    background: #1a1d35;
    padding: 3px 8px;
    border-radius: 4px;
    display: inline-block;
    margin-top: 6px;
}

/* ── Main area ── */
.main-header {
    padding: 40px 0 8px;
}
.main-header h1 {
    font-size: 2rem;
    font-weight: 300;
    letter-spacing: -0.03em;
    color: #fff;
    margin: 0;
}
.main-header h1 strong {
    font-weight: 600;
    color: #818cf8;
}
.active-doc-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.78rem;
    color: #4ade80;
    background: #0d2e1f;
    border: 1px solid #166534;
    border-radius: 20px;
    padding: 3px 12px;
    font-family: 'DM Mono', monospace;
}

/* ── Chat messages ── */
.msg-wrap { margin: 16px 0; }

.msg-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 4px;
}
.msg-user-bubble {
    background: #1e2235;
    border: 1px solid #2a2f4a;
    border-radius: 16px 16px 4px 16px;
    padding: 12px 18px;
    max-width: 72%;
    font-size: 0.92rem;
    line-height: 1.6;
    color: #e8eaf0;
}

.msg-assistant { margin-bottom: 4px; }
.msg-assistant-inner {
    position: relative;
    background: #13162a;
    border: 1px solid #1e2440;
    border-radius: 4px 16px 16px 16px;
    padding: 16px 20px 16px 24px;
    max-width: 88%;
    font-size: 0.92rem;
    line-height: 1.75;
    color: #dde1f0;
    overflow: hidden;
}
/* Signature gradient bar */
.msg-assistant-inner::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, #6366f1 0%, #818cf8 50%, transparent 100%);
    border-radius: 3px 0 0 3px;
}

.msg-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.label-you { color: #4b5270; text-align: right; padding-right: 4px; }
.label-assistant { color: #6366f1; padding-left: 4px; }

/* ── Answer markdown styling ── */
.msg-assistant-inner p { margin: 0 0 10px; }
.msg-assistant-inner p:last-child { margin-bottom: 0; }
.msg-assistant-inner ul, .msg-assistant-inner ol {
    padding-left: 20px;
    margin: 8px 0;
}
.msg-assistant-inner li { margin: 4px 0; }
.msg-assistant-inner strong { color: #c7d2fe; font-weight: 600; }
.msg-assistant-inner code {
    font-family: 'DM Mono', monospace;
    font-size: 0.82em;
    background: #1e2440;
    padding: 2px 6px;
    border-radius: 4px;
    color: #a5b4fc;
}

/* ── Source cards ── */
.source-grid { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.source-card {
    background: #0d0f1a;
    border: 1px solid #1e2235;
    border-radius: 8px;
    padding: 10px 14px;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: #6b7280;
    line-height: 1.5;
}
.source-card .src-meta {
    font-size: 0.68rem;
    color: #4b5270;
    margin-bottom: 4px;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.source-card .src-text { color: #8892aa; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 80px 20px;
    color: #2a2f4a;
}
.empty-state .icon { font-size: 2.5rem; margin-bottom: 16px; opacity: 0.4; }
.empty-state h3 { font-size: 1.1rem; font-weight: 500; color: #3d4466; margin: 0 0 8px; }
.empty-state p { font-size: 0.85rem; color: #2a2f4a; margin: 0; }

/* ── Input row ── */
.stTextInput > div > div > input {
    background: #111422 !important;
    border: 1px solid #1e2235 !important;
    border-radius: 10px !important;
    color: #e8eaf0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    padding: 12px 16px !important;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}
.stTextInput > div > div > input::placeholder { color: #3d4466 !important; }

/* ── Buttons ── */
.stButton > button {
    background: #6366f1 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 12px 20px !important;
    transition: background 0.2s, transform 0.1s !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    background: #4f52d4 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #111422;
    border: 1.5px dashed #1e2235;
    border-radius: 10px;
    padding: 4px;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #6366f1; }

/* ── Password input ── */
[data-testid="stTextInput"] input[type="password"] {
    background: #111422 !important;
    border: 1px solid #1e2235 !important;
    color: #e8eaf0 !important;
    border-radius: 8px !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: transparent !important;
    border: 1px solid #1e2235 !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.78rem !important;
    color: #4b5270 !important;
    font-family: 'DM Mono', monospace !important;
}

/* ── Divider ── */
hr { border-color: #1e2235 !important; margin: 12px 0 !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ── Dependency loader ──────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_deps():
    try:
        from langchain_community.document_loaders import PyPDFLoader          # noqa
        from langchain_text_splitters import RecursiveCharacterTextSplitter   # noqa
        from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA # noqa
        from langchain_chroma import Chroma                                    # noqa
        from langchain_classic.chains import create_retrieval_chain            # noqa
        from langchain_classic.chains.combine_documents import create_stuff_documents_chain # noqa
        from langchain_core.prompts import ChatPromptTemplate                  # noqa
        return True, None
    except ImportError as e:
        return False, str(e)


# ── Vector store ───────────────────────────────────────────────────────────────
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
    embeddings = NVIDIAEmbeddings(
        model="nvidia/nv-embedqa-e5-v5",
        api_key=api_key
    )

    if os.path.exists(db_dir) and os.listdir(db_dir):
        vectorstore = Chroma(persist_directory=db_dir, embedding_function=embeddings)
    else:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=db_dir
        )

    return vectorstore, len(chunks)


# ── RAG chain ──────────────────────────────────────────────────────────────────
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

    llm = ChatNVIDIA(
        model="meta/llama-3.1-8b-instruct",
        api_key=api_key,
        temperature=0
    )

    system_prompt = (
        "You are DocMind, a precise AI assistant that answers questions strictly based on the provided document context.\n\n"
        "Rules:\n"
        "- Answer only from the provided context. If the answer is not in the context, say so clearly.\n"
        "- Structure your answers with clear paragraphs. Use bullet points only when listing multiple distinct items.\n"
        "- Use **bold** to highlight key terms or important phrases.\n"
        "- Be concise but complete. Avoid filler phrases like 'Based on the context...' or 'According to the document...'.\n"
        "- If quoting directly, use quotation marks.\n\n"
        "Context:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    qa_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, qa_chain)


# ── Session state ──────────────────────────────────────────────────────────────
for key, default in [
    ("messages", []),
    ("pdf_ready", False),
    ("rag_chain", None),
    ("pdf_name", None),
    ("chunk_count", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="logo">◈ Doc<span>Mind</span></div>
        <div class="tagline">PDF Intelligence · RAG · NVIDIA NIM</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">API Key</div>', unsafe_allow_html=True)
    api_key_env = os.getenv("NVIDIA_API_KEY", "")
    api_key_input = st.text_input(
        "NVIDIA API Key",
        value=api_key_env,
        type="password",
        placeholder="nvapi-...",
        label_visibility="collapsed"
    )

    st.markdown('<div class="section-label">Document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        label_visibility="collapsed"
    )

    if uploaded_file and api_key_input:
        if st.button("⟳  Index document", use_container_width=True):
            with st.spinner("Embedding document…"):
                try:
                    pdf_bytes = uploaded_file.read()
                    vs, n_chunks = build_vector_store(pdf_bytes, uploaded_file.name, api_key_input)
                    st.session_state.rag_chain = build_rag_chain(vs, api_key_input)
                    st.session_state.pdf_ready = True
                    st.session_state.pdf_name = uploaded_file.name
                    st.session_state.chunk_count = n_chunks
                    st.session_state.messages = []
                    st.success(f"Indexed {n_chunks} chunks")
                except Exception as e:
                    st.error(str(e))
    elif uploaded_file and not api_key_input:
        st.caption("↑ Enter your API key first")

    st.markdown('<div class="section-label">Status</div>', unsafe_allow_html=True)
    if st.session_state.pdf_ready:
        st.markdown(f'<span class="status-pill pill-ready">● Ready</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="file-tag">{st.session_state.pdf_name}</div>', unsafe_allow_html=True)
        st.caption(f"{st.session_state.chunk_count} chunks · MMR retrieval · k=6")
    else:
        st.markdown('<span class="status-pill pill-waiting">○ Awaiting document</span>', unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("New doc", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pdf_ready = False
            st.session_state.rag_chain = None
            st.session_state.pdf_name = None
            st.rerun()


# ── Main ───────────────────────────────────────────────────────────────────────
top_left, top_right = st.columns([3, 1])
with top_left:
    st.markdown("""
    <div class="main-header">
        <h1>Ask your <strong>document</strong> anything</h1>
    </div>
    """, unsafe_allow_html=True)
with top_right:
    if st.session_state.pdf_ready:
        st.markdown(f"""
        <div style="padding-top:44px;text-align:right">
            <span class="active-doc-badge">◈ {st.session_state.pdf_name}</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ── Empty state ────────────────────────────────────────────────────────────────
if not st.session_state.pdf_ready:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">◈</div>
        <h3>No document loaded</h3>
        <p>Upload a PDF in the sidebar and click <strong>Index document</strong> to begin.</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Chat history ──────────────────────────────────────────────────────────
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="msg-wrap">
                <div class="msg-label label-you">You</div>
                <div class="msg-user">
                    <div class="msg-user-bubble">{msg["content"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-wrap">
                <div class="msg-label label-assistant">DocMind</div>
                <div class="msg-assistant">
                    <div class="msg-assistant-inner">{msg["content"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if msg.get("sources"):
                with st.expander(f"  {len(msg['sources'])} source chunks", expanded=False):
                    for i, src in enumerate(msg["sources"], 1):
                        page = src.metadata.get("page", "?")
                        snippet = src.page_content[:200].replace("\n", " ").strip()
                        st.markdown(f"""
                        <div class="source-card">
                            <div class="src-meta">Chunk {i} · Page {page}</div>
                            <div class="src-text">{snippet}…</div>
                        </div>
                        """, unsafe_allow_html=True)

    # ── Input ─────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_q, col_btn = st.columns([6, 1])
    with col_q:
        question = st.text_input(
            "Question",
            placeholder="e.g. What attention mechanism does this paper propose?",
            label_visibility="collapsed",
            key="q"
        )
    with col_btn:
        ask = st.button("Ask →", use_container_width=True)

    if ask and question.strip():
        st.session_state.messages.append({"role": "user", "content": question.strip()})
        with st.spinner(""):
            try:
                response = st.session_state.rag_chain.invoke({"input": question.strip()})
                import re
                raw = response["answer"]
                # Convert markdown to HTML
                # Bold
                answer_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', raw)
                # Bullet lists: lines starting with - or *
                lines = answer_html.split("\n")
                out_lines = []
                in_list = False
                for line in lines:
                    stripped = line.strip()
                    if re.match(r'^[-*]\s+', stripped):
                        if not in_list:
                            out_lines.append("<ul>")
                            in_list = True
                        clean_item = re.sub(r'^[-*]\s+', '', stripped)
                        out_lines.append(f"<li>{clean_item}</li>")
                    else:
                        if in_list:
                            out_lines.append("</ul>")
                            in_list = False
                        if stripped:
                            out_lines.append(f"<p>{stripped}</p>")
                        else:
                            out_lines.append("")
                if in_list:
                    out_lines.append("</ul>")
                answer_html = "\n".join(out_lines)
                sources = response.get("context", [])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer_html,
                    "sources": sources
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"<p style='color:#f87171'>Error: {e}</p>",
                    "sources": []
                })
        st.rerun()
