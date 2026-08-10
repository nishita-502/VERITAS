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

# Groq LLM Configuration
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0"))

# Backwards-compatible aliases used throughout the codebase
LLM_MODEL = GROQ_MODEL
LLM_TEMPERATURE = GROQ_TEMPERATURE
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# Optional SharpAPI resume parsing
SHARPAPI_BASE_URL = os.getenv("SHARPAPI_BASE_URL", "https://api.sharpapi.ai")
SHARPAPI_API_KEY = os.getenv("SHARPAPI_API_KEY", "")
ENABLE_SHARPAPI_PARSER = os.getenv("ENABLE_SHARPAPI_PARSER", "false").lower() in {"1", "true", "yes"}

# GitHub API Configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_RATE_LIMIT_REQUESTS = 60 if not GITHUB_TOKEN else 5000
GITHUB_TIMEOUT = 10

# Verification Thresholds
MIN_TRUST_SCORE = 0
PARTIAL_MATCH_THRESHOLD = 70
VERIFIED_THRESHOLD = 85

# ATS Scoring Weights - base score only (external evidence acts as a boost)
ATS_WEIGHTS = {
    "jd_requirement_alignment": 0.65,
    "resume_completeness": 0.35,
}

# Detailed ATS Scoring Breakdown (for UI transparency)
ATS_WEIGHTS_DETAILED = {
    "base_alignment": {
        "weight": 1.0,
        "components": {
            "jd_requirement_alignment": 0.65,
            "resume_completeness": 0.35,
        },
    },
    "external_verification": {
        "weight": 0.0,
        "components": {
            "github_verification": 0.0,
            "kaggle_verification": 0.0,
            "competitive_programming": 0.0,
        },
    },
}

# Timeline Configuration - informational only
ENABLE_TIMELINE_VALIDATION = True

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

# Current Year for Validation
CURRENT_YEAR = 2026

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Feature Flags
ENABLE_GITHUB_VERIFICATION = True
ENABLE_KAGGLE_VERIFICATION = True
ENABLE_LINKEDIN_VERIFICATION = False
ENABLE_TECH_CONSISTENCY_CHECK = True

print(f"✅ Configuration loaded from {PROJECT_ROOT}")
