"""
Resume Parser - PDF Loading and Initial Processing
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

import requests
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from src.core.config import CHUNK_SIZE, CHUNK_OVERLAP, ENABLE_SHARPAPI_PARSER, SHARPAPI_API_KEY, SHARPAPI_BASE_URL
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ResumeParser:
    """Parse and process resume PDFs."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""],
        )
        logger.info("ResumeParser initialized with chunk_size=%s, overlap=%s", CHUNK_SIZE, CHUNK_OVERLAP)

    def parse_pdf(self, file_path: str) -> str:
        """Load and extract text from PDF resume."""

        logger.info("Parsing resume from: %s", file_path)

        if not Path(file_path).exists():
            logger.error("Resume file not found: %s", file_path)
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            text = "\n".join(doc.page_content for doc in docs)
            logger.info("Successfully parsed PDF: %s pages, %s characters", len(docs), len(text))
            return text
        except Exception as exc:
            logger.error("Error parsing PDF: %s", exc)
            raise

    def parse_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text directly from raw PDF bytes."""

        logger.info("Parsing resume from raw PDF bytes")

        if not pdf_bytes:
            return ""

        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
            logger.info("Successfully parsed raw PDF bytes: %s pages, %s characters", len(reader.pages), len(text))
            return text
        except Exception as exc:
            logger.error("Error parsing raw PDF bytes: %s", exc)
            raise

    def parse_with_sharpapi(self, pdf_bytes: bytes, filename: str = "resume.pdf") -> Optional[str]:
        """Optional SharpAPI-based parsing for raw PDF bytes."""

        if not ENABLE_SHARPAPI_PARSER or not SHARPAPI_API_KEY or not pdf_bytes:
            return None

        logger.info("Attempting SharpAPI parsing for %s", filename)

        try:
            response = requests.post(
                f"{SHARPAPI_BASE_URL.rstrip('/')}/api/v1/hr/parse_resume",
                headers={"Authorization": f"Bearer {SHARPAPI_API_KEY}"},
                files={"file": (filename, pdf_bytes, "application/pdf")},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()

            for key in ("text", "resume_text", "content", "data"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value

            if isinstance(payload.get("result"), dict):
                nested = payload["result"]
                for key in ("text", "resume_text", "content"):
                    value = nested.get(key)
                    if isinstance(value, str) and value.strip():
                        return value

            logger.warning("SharpAPI response did not contain usable text")
            return None
        except Exception as exc:
            logger.warning("SharpAPI parsing failed, falling back locally: %s", exc)
            return None

    def parse_text(self, text: str) -> str:
        """Normalize and clean resume text."""

        logger.info("Normalizing resume text")

        if not text:
            return ""

        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+\n", "\n", text)

        logger.info("Text normalization complete: %s characters", len(text))
        return text.strip()

    def chunk_resume(self, text: str) -> List[str]:
        """Split resume into semantic chunks."""

        logger.info("Chunking resume text")

        if not text:
            return []

        splits = self.text_splitter.split_text(text)
        logger.info("Created %s chunks", len(splits))
        return splits

    def process_resume(self, file_path: Optional[str] = None, pdf_bytes: Optional[bytes] = None) -> Dict[str, Any]:
        """Complete resume processing pipeline."""

        logger.info("Starting complete resume processing")

        raw_text = ""
        source = "unknown"

        if pdf_bytes:
            raw_text = self.parse_with_sharpapi(pdf_bytes, filename=Path(file_path).name if file_path else "resume.pdf") or ""
            if not raw_text:
                raw_text = self.parse_pdf_bytes(pdf_bytes)
            source = "sharpapi" if ENABLE_SHARPAPI_PARSER and raw_text else "raw_bytes"
        elif file_path:
            raw_text = self.parse_pdf(file_path)
            source = "local_pdf"
        else:
            raise ValueError("Either file_path or pdf_bytes must be provided")

        normalized_text = self.parse_text(raw_text)
        chunks = self.chunk_resume(normalized_text)

        result = {
            "file_path": file_path,
            "source": source,
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "chunks": chunks,
            "total_characters": len(normalized_text),
            "total_chunks": len(chunks),
        }

        logger.info("Resume processing complete: %s chunks created", len(chunks))
        return result
