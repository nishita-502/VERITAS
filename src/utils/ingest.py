#his script handles the PDF loading, chunking, and persistence. We'll use RecursiveCharacterTextSplitter because it’s "smart"—it tries to keep paragraphs together so the LLM doesn't lose context.

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

def ingest_resume(file_path: str):
    """
    Loads a PDF, splits it into chunks, and stores it in a persistent ChromaDB.
    """
    print(f"--- INGESTING: {file_path} ---")
    
    # 1. Load the PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    # 2. Split into chunks (500 chars with some overlap for context)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, 
        chunk_overlap=50
    )
    splits = text_splitter.split_documents(docs)
    
    # 3. Initialize local embeddings (Nomic is excellent for this)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # 4. Create and Persist the Vector Store
    persist_dir = "./chroma_db"
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="veritas_resumes"
    )
    
    print(f"✅ Ingestion complete. {len(splits)} chunks stored in {persist_dir}")
    return vectorstore

if __name__ == "__main__":
    # Test it by pointing to a resume in your data folder
    sample_resume = "data/nishita_resume.pdf" 
    if os.path.exists(sample_resume):
        ingest_resume(sample_resume)
    else:
        print(f"❌ Error: Place a PDF at {sample_resume} first!")