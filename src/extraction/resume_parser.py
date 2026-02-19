"""
Resume Parser - PDF Loading and Initial Processing
"""
from pathlib import Path
from typing import Dict, Any, List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.core.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class ResumeParser:
    """Parse and process resume PDFs"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
        logger.info(f"ResumeParser initialized with chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
    
    def parse_pdf(self, file_path: str) -> str:
        """Load and extract text from PDF resume"""
        logger.info(f"Parsing resume from: {file_path}")
        
        if not Path(file_path).exists():
            logger.error(f"Resume file not found: {file_path}")
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            
            text = "\n".join([doc.page_content for doc in docs])
            logger.info(f"Successfully parsed PDF: {len(docs)} pages, {len(text)} characters")
            
            return text
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise
    
    def parse_text(self, text: str) -> str:
        """Normalize and clean resume text"""
        logger.info("Normalizing resume text")
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Normalize line breaks
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        logger.info(f"Text normalization complete: {len(text)} characters")
        return text
    
    def chunk_resume(self, text: str) -> List[str]:
        """Split resume into semantic chunks"""
        logger.info("Chunking resume text")
        
        splits = self.text_splitter.split_text(text)
        logger.info(f"Created {len(splits)} chunks")
        
        return splits
    
    def process_resume(self, file_path: str) -> Dict[str, Any]:
        """Complete resume processing pipeline"""
        logger.info(f"Starting complete resume processing: {file_path}")
        
        # Load PDF
        raw_text = self.parse_pdf(file_path)
        
        # Normalize
        normalized_text = self.parse_text(raw_text)
        
        # Chunk
        chunks = self.chunk_resume(normalized_text)
        
        result = {
            "file_path": file_path,
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "chunks": chunks,
            "total_characters": len(normalized_text),
            "total_chunks": len(chunks),
        }
        
        logger.info(f"Resume processing complete: {len(chunks)} chunks created")
        return result
