# 🕵️‍♂️ VERITAS - Enterprise Resume Verification System

**Version 2.0** - Production-Grade Architecture

VERITAS is an AI-powered forensic resume investigator that acts as a digital hiring expert, verifying claims through real APIs, detecting inconsistencies, and providing explainable trust scores and ATS matching.

## 🎯 Core Features

### ✨ Structured Extraction Engine
- **Full JSON extraction** from resumes using LLM with fallback to regex
- Extracts: projects, skills, technologies, GitHub/Kaggle usernames, CGPA, work experience
- Temperature = 0 for deterministic, reliable extraction
- Regex fallback ensures no data loss

### 🔍 Real Verification Agents
- **GitHub Verification**: Uses GitHub REST API to verify projects, languages, commit history
- **Kaggle Verification**: Validates Kaggle competitions and datasets
- **LinkedIn Verification**: Basic profile validation (limited by ToS)
- **Tech Consistency Checker**: Detects mismatches between claimed and demonstrated skills
- **Timeline Validator**: Validates timeline consistency and detects overlaps

### 📊 Comprehensive Scoring
- **Trust Score**: Per-claim and overall trust scoring with reasoning
- **ATS Engine**: Dynamic ATS calculation using formula:
  ```
  ATS = (JD Skill Match % × 0.4) + (Verified Claims % × 0.3) 
        + (Resume Completeness % × 0.2) + (Timeline Consistency % × 0.1)
  ```
- **Resume Completeness**: Scores based on contact info, education, experience, skills, links

### 🚨 Red Flag Detection
- Identifies unverified skills without GitHub evidence
- Detects timeline inconsistencies and overlaps
- Flags missing external verification links
- Highlights inconsistencies between claims and demonstrated work

### 🖥️ Enterprise UI
- **Streamlit Dashboard** with 4 main tabs:
  1. Resume Analysis: Extracted data visualization
  2. Verification Dashboard: Claim verification status & breakdown
  3. ATS Match & JD: Dynamic ATS scoring with detailed breakdown
  4. Red Flags: Severity-categorized red flag analysis
- Real-time progress tracking
- Explainable AI: Shows reasoning for each decision

## 🏗️ Architecture

### Modular Design
```
src/
├── core/              # Configuration & logging
├── extraction/        # Resume parsing & claim detection
├── verification/      # API-based verification agents
├── scoring/          # Trust & ATS scoring engines
├── matching/         # JD extraction & skill matching
├── agents/           # LangGraph workflow orchestration
└── ui/               # Streamlit dashboard
```

### Agent Graph Flow
```
Resume Upload
    ↓
Resume Parser → Structured Extraction → Claim Detector
    ↓                                      ↓
Resume Completeness Scorer ← ← ← Skill Matcher ← JD Extractor
    ↓
Verification Orchestrator (GitHub, Kaggle, LinkedIn)
    ↓ (parallel)
Trust Scorer, Red Flag Detector, Tech Consistency Checker
    ↓
ATS Calculator
    ↓
Executive Summary Generator
    ↓
Final Report Generator
```

## 📦 Installation

### Prerequisites
- Python 3.10+
- Ollama running locally (`http://localhost:11434`)
  - Models: `mistral`, `nomic-embed-text`

### Setup
```bash
# Clone/Setup Project
cd VERITAS

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Run Ollama (Required)
```bash
ollama serve
# In another terminal:
ollama pull mistral
ollama pull nomic-embed-text
```

## 🚀 Usage

### Web UI (Recommended)
```bash
streamlit run app.py
# Opens at http://localhost:8501
```

### CLI
```bash
python main.py
```

## 📋 Input Requirements

### Resume
- **Format**: PDF
- **Content**: Standard resume with:
  - Contact information
  - Skills section
  - Projects/Portfolio
  - Work experience
  - Education

### Job Description (Optional)
- **Format**: Plain text
- **Content**: Job requirements, desired skills, technologies
- **Usage**: Enables ATS scoring and skill matching

## 📊 Output Report

### Executive Summary
- Recommendation: Strong/Moderate/Weak/Not Recommended
- Reasoning and confidence metrics

### Trust Score Report
- Overall trust score (0-100)
- Per-claim verification status
- Confidence levels and evidence

### ATS Score Report
```json
{
  "ats_score": 78,
  "breakdown": {
    "jd_skill_match": 85%,
    "verified_claims": 60%,
    "resume_completeness": 90%,
    "timeline_consistency": 70%
  }
}
```

### Verification Results
- GitHub: Projects found, languages verified, commit history
- Kaggle: Profile validation, competitions, datasets
- Tech Stack: Consistency analysis between claimed and demonstrated
- Timeline: Validity and overlap checks

### Red Flags
- Severity-categorized (High/Medium/Low)
- Actionable descriptions
- Evidence-based flagging

## 🔐 Privacy & Security

✅ **100% Local Execution**
- LLM runs via Ollama (local)
- No data sent to external APIs except:
  - GitHub (public read-only)
  - Kaggle (public read-only)

✅ **No External LLM Costs**
- Mistral 7B via Ollama (free)
- Nomic embeddings (free)

## ⚙️ Configuration

Edit `src/core/config.py` or `.env`:

```python
# LLM
LLM_MODEL = "mistral"
LLM_TEMPERATURE = 0  # Deterministic

# Thresholds
VERIFIED_THRESHOLD = 85
PARTIAL_MATCH_THRESHOLD = 70

# GitHub API (optional token for higher limits)
GITHUB_TOKEN = ""

# ATS Weights
ATS_WEIGHTS = {
    "jd_skill_match": 0.4,
    "verified_claims": 0.3,
    "resume_completeness": 0.2,
    "timeline_consistency": 0.1,
}
```

## 📚 Example Verification Flow

### Input
- Resume: software_engineer.pdf
- JD: "Senior Python Developer - AWS, FastAPI"

### Processing Stages
1. ✅ Parse PDF → 5 pages, 2500 characters
2. ✅ Extract structure → 8 projects, 12 skills
3. ✅ Detect claims → 24 verifiable claims
4. ✅ Extract JD → 6 required skills
5. ✅ Verify GitHub → 5 repos, Python confirmed
6. ✅ Check consistency → 10/12 skills verified
7. ✅ Calculate scores → 78 ATS, 82 trust
8. ✅ Detect red flags → Timeline overlap, 1 unverified skill

### Output
```
RECOMMENDATION: ✅ STRONG RECOMMEND - Proceed to interview
TRUST SCORE: 82/100
ATS SCORE: 78/100 (Moderate Match)
RED FLAGS: 1 (Timeline overlap in projects)
```

## 🛠️ Development

### Add New Verification Agent
```python
# src/verification/new_agent.py
class NewAgent:
    async def verify_claims(self, data):
        # Implement verification logic
        pass

# Add to src/verification/verification_engine.py
```

### Extend Scoring Logic
Edit `src/scoring/trust_scorer.py` or `src/scoring/ats_engine.py`

### Modify Graph Flow
Edit `src/agents/graph.py` - add/modify nodes and edges

## 📝 Logging

Logs stored in `logs/` directory:
- `src_agents_nodes.log` - Agent execution logs
- `src_verification_github_agent.log` - GitHub API interactions
- Each module has its own log file

Enable DEBUG logging:
```bash
LOG_LEVEL=DEBUG python main.py
```

## 🤝 Contributing

1. Follow existing module structure
2. Add comprehensive logging
3. Write docstrings for all functions
4. Test with sample resumes

## 📄 License

Proprietary - Enterprise Use Only

## 🙋 Support

For issues or questions:
- Check logs in `logs/`
- Verify Ollama is running on port 11434
- Ensure all dependencies are installed
- Review `.env.example` for configuration

---

**VERITAS Version 2.0** | Last Updated: February 2026
