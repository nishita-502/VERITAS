"""
Core Configuration Module
Centralized settings for VERITAS Resume Verification System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DB_DIR.mkdir(exist_ok=True)

# LLM Configuration (Ollama Local)
LLM_MODEL = os.getenv("LLM_MODEL", "mistral")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_TEMPERATURE = 0  # Deterministic for structured extraction
LLM_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# GitHub API Configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # Optional, increases rate limit
GITHUB_RATE_LIMIT_REQUESTS = 60 if not GITHUB_TOKEN else 5000
GITHUB_TIMEOUT = 10

# Verification Thresholds
MIN_TRUST_SCORE = 0  # Minimum to be considered verified
PARTIAL_MATCH_THRESHOLD = 70  # Trust score >= this is partial
VERIFIED_THRESHOLD = 85  # Trust score >= this is verified

# ATS Scoring Weights
ATS_WEIGHTS = {
    "jd_skill_match": 0.4,
    "verified_claims": 0.3,
    "resume_completeness": 0.2,
    "timeline_consistency": 0.1,
}

# Chroma DB Configuration
CHROMA_COLLECTION_NAME = "veritas_resumes"
CHROMA_BATCH_SIZE = 5000

# Extraction Configuration
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

# Regex Patterns
GITHUB_REGEX = r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)"
LINKEDIN_REGEX = r"(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)"
KAGGLE_REGEX = r"(?:https?://)?(?:www\.)?kaggle\.com/([a-zA-Z0-9_-]+)"
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
CGPA_REGEX = r"(?:CGPA|GPA|C\.G\.P\.A)[:\s]*([0-9]\.[0-9]{1,2})"
PHONE_REGEX = r"(?:\+?91[\s\-]?)?[0-9]{10}"

# Timeline Configuration
CURRENT_YEAR = 2026

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Feature Flags
ENABLE_GITHUB_VERIFICATION = True
ENABLE_KAGGLE_VERIFICATION = True
ENABLE_LINKEDIN_VERIFICATION = False  # LinkedIn scraping often blocked
ENABLE_TECH_CONSISTENCY_CHECK = True
ENABLE_TIMELINE_VALIDATION = True

print(f"✅ Configuration loaded from {PROJECT_ROOT}")
