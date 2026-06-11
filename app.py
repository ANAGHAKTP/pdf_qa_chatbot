import os
import sys
import glob

# Reconfigure stdout/stderr to support UTF-8 encoding (prevents crashes with emojis on Windows)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

# Verify NVIDIA API Key
api_key = os.getenv("NVIDIA_API_KEY")
if not api_key:
    print("=" * 60)
    print("🔑 NVIDIA API Key not found in environment variables.")
    print("=" * 60)
    api_key_input = input("Please enter your NVIDIA API Key: ").strip()
    if not api_key_input:
        print("❌ Error: NVIDIA API Key is required to run this application.")
        sys.exit(1)
    
    # Offer to save it to .env
    save_choice = input("Would you like to save this key to '.env' for future runs? (y/n): ").strip().lower()
    if save_choice == 'y':
        with open(".env", "w") as f:
            f.write(f"NVIDIA_API_KEY={api_key_input}\n")
        print("✅ API Key saved to '.env' (added to .gitignore).")
    
    # Set the variable in memory for this session
    os.environ["NVIDIA_API_KEY"] = api_key_input
    api_key = api_key_input

# Import LangChain libraries after environment configuration
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA
    from langchain_chroma import Chroma
    from langchain_core.prompts import ChatPromptTemplate
    
    # Try modern/legacy import paths dynamically to support both LangChain 0.x and 1.x ecosystems
    try:
        from langchain_classic.chains import create_retrieval_chain
        from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    except ImportError:
        from langchain_classic.chains import create_retrieval_chain
        from langchain_classic.chains.combine_documents import create_stuff_documents_chain
except ImportError as e:
    print(f"❌ Failed to import dependencies: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

def select_pdf():
    """Scan the root directory for PDF files and return the path of the selected PDF."""
    pdf_files = glob.glob("*.pdf")
    
    if not pdf_files:
        print("\n❌ No PDF files found in the current directory.")
        print("👉 Please place a PDF file in this directory and run the application again.")
        print("💡 Hint: You can use 'sample.pdf' or any other PDF file.")
        sys.exit(1)
        
    if len(pdf_files) == 1:
        selected_pdf = pdf_files[0]
        print(f"\n📄 Found PDF file: '{selected_pdf}'")
        return selected_pdf
        
    print("\n📚 Multiple PDF files found:")
    for i, file in enumerate(pdf_files, 1):
        print(f"  [{i}] {file}")
        
    while True:
        try:
            choice = input(f"Select a PDF file (1-{len(pdf_files)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(pdf_files):
                return pdf_files[idx]
        except ValueError:
            pass
        print(f"Invalid choice. Please enter a number between 1 and {len(pdf_files)}.")

def get_vector_store(pdf_path):
    """Retrieve existing vector store from disk or build a new one."""
    # Create a unique database directory based on the PDF filename
    pdf_name = os.path.basename(pdf_path)
    db_name = f"chroma_db_{pdf_name.replace('.', '_')}"
    
    embeddings = NVIDIAEmbeddings(
        model="nvidia/nv-embedqa-e5-v5",
        api_key=os.getenv("NVIDIA_API_KEY")
    )
    
    if os.path.exists(db_name) and os.listdir(db_name):
        print(f"\n📂 Loading existing embeddings from database: '{db_name}'...")
        vectorstore = Chroma(
            persist_directory=db_name,
            embedding_function=embeddings
        )
    else:
        print(f"\n⚙️ Analyzing '{pdf_path}' and creating embeddings...")
        print("📝 Step 1: Loading PDF documents...")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        print("✂️ Step 2: Splitting documents into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(documents)
        
        print(f"📦 Step 3: Storing chunks in ChromaDB (persisted under './{db_name}')...")
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=db_name
        )
        print("✅ Vector database successfully created and persisted!")
        
    return vectorstore

def main():
    print("=" * 60)
    print("🤖 PDF QA Chatbot - Modern LangChain & ChromaDB")
    print("=" * 60)
    
    # 1. Select the PDF file
    pdf_path = select_pdf()
    
    # 2. Setup/Load Vector Store
    vectorstore = get_vector_store(pdf_path)
    
    # 3. Create Retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    # 4. Initialize LLM (gpt-4o-mini is fast, cost-efficient, and capable)
    llm = ChatNVIDIA(
        model="meta/llama-3.1-8b-instruct",
        api_key=os.getenv("NVIDIA_API_KEY"),
        temperature=0
    )
    
    # 5. Define Custom System Prompt
    system_prompt = (
        "You are an expert AI assistant designed to answer questions about the provided PDF document.\n"
        "Use the following pieces of retrieved context to answer the question.\n"
        "If you don't know the answer, state that you do not know. Do not make up answers.\n"
        "Keep the answers concise, clear, and well-structured.\n\n"
        "Context:\n"
        "{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    
    # 6. Create RAG Chain using modern LangChain chains
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    print("\n✨ Chatbot is ready! Ask questions about your PDF document.")
    print("👋 Type 'exit' or 'quit' to close the session.\n")
    print("-" * 60)
    
    # 7. Interactive Prompt Loop
    while True:
        try:
            question = input("\n💬 Question: ").strip()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
            
        if not question:
            continue
            
        if question.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
            
        print("🤖 Thinking...")
        try:
            response = rag_chain.invoke({"input": question})
            # Modern retrieval chain output contains:
            # - 'input': the original question
            # - 'context': list of documents retrieved
            # - 'answer': the generated answer text
            print(f"\n📝 Answer: {response['answer']}")
        except Exception as e:
            print(f"\n❌ Error processing request: {e}")

if __name__ == "__main__":
    main()
