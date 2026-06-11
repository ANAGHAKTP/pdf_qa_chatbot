import os
import sys
import tempfile
import streamlit as st
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PDF QA Chatbot",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main background */
    .stApp {
        background-color: #0f1117;
        color: #e2e8f0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1d27;
        border-right: 1px solid #2d3148;
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #a78bfa;
    }

    /* Chat messages */
    .user-message {
        background: #1e2235;
        border: 1px solid #2d3148;
        border-radius: 12px 12px 4px 12px;
        padding: 12px 16px;
        margin: 8px 0;
        margin-left: 15%;
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    .assistant-message {
        background: #16213e;
        border: 1px solid #1e3a5f;
        border-left: 3px solid #60a5fa;
        border-radius: 4px 12px 12px 12px;
        padding: 12px 16px;
        margin: 8px 0;
        margin-right: 15%;
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    .message-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .user-label { color: #a78bfa; }
    .assistant-label { color: #60a5fa; }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .badge-ready { background: #064e3b; color: #6ee7b7; }
    .badge-loading { background: #1e3a5f; color: #93c5fd; }
    .badge-error { background: #4c0519; color: #fda4af; }

    /* Source cards */
    .source-card {
        background: #1a1d27;
        border: 1px solid #2d3148;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 4px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #94a3b8;
    }

    /* Input area */
    .stTextInput input {
        background-color: #1e2235 !important;
        border: 1px solid #2d3148 !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.5rem 1.2rem;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: #1a1d27;
        border: 2px dashed #2d3148;
        border-radius: 12px;
        padding: 8px;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }

    /* Divider */
    hr { border-color: #2d3148; }

    /* Scrollable chat area */
    .chat-container {
        max-height: 62vh;
        overflow-y: auto;
        padding-right: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ── Lazy imports with error handling ──────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_dependencies():
    try:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA
        from langchain_chroma import Chroma
        from langchain.chains import create_retrieval_chain
        from langchain.chains.combine_documents import create_stuff_documents_chain
        from langchain_core.prompts import ChatPromptTemplate
        return True, None
    except ImportError as e:
        return False, str(e)


# ── Vector store builder ───────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def build_vector_store(pdf_bytes: bytes, filename: str, api_key: str):
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
    from langchain_chroma import Chroma

    os.environ["NVIDIA_API_KEY"] = api_key

    # Write to temp file (PyPDFLoader needs a file path)
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


# ── RAG chain builder ──────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def build_rag_chain(_vectorstore, api_key: str):
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    from langchain_classic.chains import create_retrieval_chain
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate

    os.environ["NVIDIA_API_KEY"] = api_key

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
        "You are an expert AI assistant designed to answer questions about the provided PDF document.\n"
        "Use the following pieces of retrieved context to answer the question.\n"
        "If you don't know the answer based on the context, say so clearly. Do not make up answers.\n"
        "Keep answers concise, clear, and well-structured.\n\n"
        "Context:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    qa_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, qa_chain)
    return rag_chain


# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = False
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📄 PDF QA Chatbot")
    st.markdown("---")

    # API Key
    st.markdown("### 🔑 API Key")
    api_key_env = os.getenv("NVIDIA_API_KEY", "")
    api_key_input = st.text_input(
        "NVIDIA API Key",
        value=api_key_env,
        type="password",
        placeholder="nvapi-...",
        help="Your key is never stored beyond this session."
    )

    st.markdown("---")

    # PDF Upload
    st.markdown("### 📂 Upload PDF")
    uploaded_file = st.file_uploader(
        "Drop a PDF here",
        type=["pdf"],
        help="Upload any PDF to start asking questions about it."
    )

    if uploaded_file and api_key_input:
        if st.button("⚙️ Process PDF", use_container_width=True):
            with st.spinner("Embedding your PDF..."):
                try:
                    vectorstore, chunk_count = build_vector_store(
                        uploaded_file.read(),
                        uploaded_file.name,
                        api_key_input
                    )
                    st.session_state.rag_chain = build_rag_chain(vectorstore, api_key_input)
                    st.session_state.pdf_ready = True
                    st.session_state.pdf_name = uploaded_file.name
                    st.session_state.messages = []
                    st.success(f"✅ Ready! {chunk_count} chunks indexed.")
                except Exception as e:
                    st.error(f"❌ {e}")

    elif uploaded_file and not api_key_input:
        st.warning("Enter your API key first.")

    st.markdown("---")

    # Status
    st.markdown("### 📊 Status")
    if st.session_state.pdf_ready:
        st.markdown(f'<span class="status-badge badge-ready">● READY</span>', unsafe_allow_html=True)
        st.markdown(f"**File:** `{st.session_state.pdf_name}`")
    else:
        st.markdown('<span class="status-badge badge-loading">○ Awaiting PDF</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Clear chat
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.72rem;color:#475569;text-align:center;">Built with LangChain · ChromaDB · NVIDIA Llama-3.1-8b</div>',
        unsafe_allow_html=True
    )


# ── Main area ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("## Ask your PDF anything")
with col2:
    if st.session_state.pdf_ready:
        st.markdown(
            f'<div style="text-align:right;padding-top:8px"><span class="status-badge badge-ready">● {st.session_state.pdf_name}</span></div>',
            unsafe_allow_html=True
        )

st.markdown("---")

# Welcome state
if not st.session_state.pdf_ready:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;color:#475569;">
        <div style="font-size:3rem;margin-bottom:16px;">📄</div>
        <div style="font-size:1.1rem;font-weight:600;color:#94a3b8;margin-bottom:8px;">No PDF loaded yet</div>
        <div style="font-size:0.9rem;">Upload a PDF in the sidebar and click <strong>Process PDF</strong> to begin.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Chat history
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <div class="message-label user-label">You</div>
                {msg["content"]}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="assistant-message">
                <div class="message-label assistant-label">Assistant</div>
                {msg["content"]}
            </div>""", unsafe_allow_html=True)
            if msg.get("sources"):
                with st.expander("📎 Source chunks", expanded=False):
                    for i, src in enumerate(msg["sources"], 1):
                        page = src.metadata.get("page", "?")
                        snippet = src.page_content[:180].replace("\n", " ")
                        st.markdown(
                            f'<div class="source-card">Chunk {i} · Page {page}<br>{snippet}…</div>',
                            unsafe_allow_html=True
                        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Question input
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            question = st.text_input(
                "Your question",
                placeholder="e.g. What is the main contribution of this paper?",
                label_visibility="collapsed",
                key="question_input"
            )
        with col_btn:
            ask = st.button("Ask →", use_container_width=True)

    if ask and question.strip():
        st.session_state.messages.append({"role": "user", "content": question.strip()})
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.rag_chain.invoke({"input": question.strip()})
                answer = response["answer"]
                sources = response.get("context", [])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: {e}",
                    "sources": []
                })
        st.rerun()
