# VERITAS System - Complete Workflow & Architecture Explanation

## 🎯 System Overview

**VERITAS** is an AI-powered **Resume Verification & Forensic Investigation System** that uses enterprise-grade AI agents, real API integrations, and dynamic scoring to verify resume claims and generate explainable trust scores.

**Core Purpose:** Act as a digital hiring expert that:
- Extracts structured data from resumes
- Verifies claims against real external APIs (GitHub, Kaggle, etc.)
- Detects inconsistencies and red flags
- Generates ATS (Applicant Tracking System) compatibility scores
- Provides explainable trust scores with reasoning

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERITAS SYSTEM ARCHITECTURE                  │
└─────────────────────────────────────────────────────────────────┘

User Input
  ↓
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 1: EXTRACTION & PARSING                      │
│  ├─ Resume Parser (PDF → Text)                                  │
│  ├─ Structured Extractor (LLM + Regex Fallback)                │
│  └─ Claim Detector (Identifies Verifiable Claims)              │
└─────────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────────┐
│           STAGE 2: JD PROCESSING (If Provided)                 │
│  └─ JD Extractor (Extract Skills, Requirements)               │
└─────────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────────┐
│          STAGE 3: VERIFICATION (Real API Calls)                │
│  ├─ GitHub Agent (Verify projects, languages, history)        │
│  ├─ Kaggle Agent (Verify competitions, datasets)              │
│  ├─ LinkedIn Agent (Profile validation)                        │
│  ├─ Competitive Programming Agent (LeetCode, Codeforces)      │
│  ├─ Tech Consistency Checker (Skill alignment)                │
│  └─ Timeline Validator (Date consistency)                      │
└─────────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────────┐
│            STAGE 4: SCORING & ANALYSIS                         │
│  ├─ Trust Scorer (Per-claim & Overall trust scores)           │
│  ├─ Completeness Scorer (Resume quality assessment)           │
│  ├─ Red Flag Detector (Inconsistencies & red flags)          │
│  └─ ATS Calculator (Dynamic ATS score)                        │
└─────────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────────┐
│          STAGE 5: REPORTING & VISUALIZATION                    │
│  ├─ Executive Summary Generator                                │
│  ├─ Final Report Generator                                    │
│  └─ Streamlit Dashboard (4-Tab UI)                            │
└─────────────────────────────────────────────────────────────────┘
  ↓
Output: Comprehensive Resume Verification Report
```

---

## 📊 Detailed Workflow Breakdown

### **STAGE 1: EXTRACTION & PARSING**

**Purpose:** Convert resume from PDF to structured data

#### 1.1 Resume Parser Node
- **Input:** PDF file path
- **Process:**
  - Load PDF using PyPDFLoader
  - Extract text from all pages
  - Normalize and clean text (remove extra whitespace, fix line breaks)
  - Split into semantic chunks using RecursiveCharacterTextSplitter
- **Output:** Cleaned, chunked resume text
- **Tech:** PyPDFLoader, LangChain TextSplitters

#### 1.2 Structured Extraction Node
- **Input:** Raw resume text
- **Process:**
  - Uses LLM (Mistral via Ollama) with `temperature=0` for deterministic extraction
  - Extracts structured fields:
    - Contact info (name, email, phone, LinkedIn, GitHub, Kaggle)
    - Education (university, CGPA, graduation year)
    - Skills (list of technologies)
    - Projects (name, description, technologies, timeline)
    - Work experience (company, position, duration, description, technologies)
    - Claims (numeric achievements)
  - **Fallback mechanism:** If LLM extraction fails, uses regex patterns as backup
  - Ensures 100% data capture
- **Output:** Dictionary with structured fields
- **Tech:** LLM (Ollama Mistral), Regex Fallback

#### 1.3 Claim Detector Node
- **Input:** Structured resume data
- **Process:**
  - Identifies all verifiable claims by type:
    - **Skill claims:** "Proficient in Python"
    - **Tech claims:** "Used React in project X"
    - **Depth claims:** "Deep understanding of architecture"
    - **Link claims:** "Has GitHub/Kaggle/LinkedIn profiles"
    - **Numeric claims:** "Solved 500+ problems"
    - **CGPA claims:** Educational achievements
  - Assigns severity levels:
    - **High:** Skills, external links, tech stack (critical to hiring)
    - **Medium:** Projects, depth of knowledge
    - **Low:** CGPA, certifications
  - Prioritizes claims by severity for efficient verification
- **Output:** List of claims with metadata and priority
- **Tech:** Python data structures, sorting algorithms

---

### **STAGE 2: JD PROCESSING**

**Purpose:** Extract requirements from job description for matching

#### 2.1 JD Extractor Node
- **Input:** Job description text (optional)
- **Process:**
  - If no JD provided, marks as skipped
  - Extracts:
    - Job title
    - Required skills (using keyword matching + LLM)
    - Nice-to-have skills
    - Experience requirements
    - Domain specialization
  - Normalizes skill names for matching
- **Output:** Structured JD data with required skills
- **Tech:** NLP, keyword extraction

---

### **STAGE 3: VERIFICATION (REAL API CALLS)**

**Purpose:** Verify resume claims against real external sources

#### 3.1 GitHub Agent
- **Input:** GitHub username extracted from resume
- **Process:**
  - **User Profile Verification:** Calls GitHub REST API (`/users/{username}`)
    - Checks if user exists
    - Retrieves profile stats (followers, public repos, contributions)
  - **Project Verification:** For each project in resume:
    - Searches GitHub repos for matching project names
    - Verifies project exists and is public
    - Checks repository statistics (stars, forks, contributors)
    - Validates claimed technologies against actual repo languages
  - **Technology Verification:** 
    - Analyzes repository code to verify claimed tech stack
    - Checks commit history for activity patterns
    - Validates contribution consistency
- **Output:** GitHub verification results with evidence
- **Tech:** GitHub REST API, HTTP requests

#### 3.2 Kaggle Agent
- **Input:** Kaggle username extracted from resume
- **Process:**
  - **Profile Verification:** Checks Kaggle API for user existence
  - **Competition Verification:** For each claimed Kaggle competition:
    - Verifies user participated
    - Retrieves ranking and tier
    - Confirms medal achievements
  - **Dataset Verification:** Validates uploaded datasets
- **Output:** Kaggle verification results
- **Tech:** Kaggle API, HTTP requests

#### 3.3 Competitive Programming Agent
- **Input:** User profiles from resume
- **Process:**
  - Verifies presence on platforms: LeetCode, Codeforces, AtCoder
  - Retrieves:
    - Rating/ranking
    - Problems solved count
    - Contest participation history
    - Skill tags
  - Cross-references claimed problem-solving stats
- **Output:** CP verification results
- **Tech:** Multiple platform APIs

#### 3.4 Tech Consistency Checker
- **Input:** Extracted technologies vs. verified technologies
- **Process:**
  - **Skill Alignment Check:**
    - Resume claims: "Expert in React"
    - GitHub evidence: Are React repos present and substantial?
    - Are there meaningful contributions to React projects?
  - **Depth Validation:**
    - Checks if claimed expertise level matches repository complexity
    - Analyzes code quality indicators
    - Validates contribution patterns
  - **Skill Mismatch Detection:**
    - Identifies skills claimed but not demonstrated
    - Flags unusual skill combinations (potential red flags)
- **Output:** Consistency score and mismatch list
- **Tech:** NLP similarity, semantic matching

#### 3.5 Timeline Validator
- **Input:** All dates from resume (work, projects, education)
- **Process:**
  - Validates no date inconsistencies:
    - End date ≥ Start date for all periods
    - No overlapping work periods (unless explicitly noted)
    - Graduation year ≥ current year is invalid
    - Project timelines align with work experience
  - Flags timeline anomalies
- **Output:** Timeline validity report
- **Tech:** Date comparison, interval overlap detection

---

### **STAGE 4: SCORING & ANALYSIS**

**Purpose:** Calculate various scores and identify red flags

#### 4.1 Trust Scorer Node
- **Input:** Claim verification results
- **Process:**
  - **Per-Claim Scoring:**
    ```
    Verified (100%)         → ✅ Verified
    Partially Verified (70%) → ⚠️ Partially Verified  
    Unverified (30%)        → ❓ Unverified
    Flagged (<40%)          → 🚩 Flagged
    ```
  - **Overall Trust Score:** Weighted average of all claim scores
  - **Confidence Levels:** High/Medium/Low/Very Low based on thresholds
  - **Evidence Recording:** Stores reasoning for each score decision
- **Output:** Per-claim trust scores and overall trust report
- **Tech:** Weighted averaging, thresholding

#### 4.2 Completeness Scorer Node
- **Input:** Structured resume data
- **Process:**
  - **Scoring Categories:**
    - Contact Info (phone, email, GitHub, LinkedIn): 20 points
    - Education (university, CGPA, graduation): 20 points
    - Work Experience (companies, years, descriptions): 25 points
    - Skills Section (populated and diverse): 15 points
    - External Links (GitHub, Kaggle, etc.): 20 points
  - **Total Score:** 0-100%
- **Output:** Completeness percentage and breakdown
- **Tech:** Scoring algorithm

#### 4.3 Red Flag Detector Node
- **Input:** All verification results, consistency checks
- **Process:**
  - **High Severity Red Flags:**
    - Claimed skills with NO GitHub evidence
    - Timeline inconsistencies
    - Unverifiable work experience
    - Inflated project descriptions
  - **Medium Severity:**
    - Skills mentioned once in projects but not in skill list
    - Vague project descriptions
    - Missing external links for major claims
  - **Low Severity:**
    - Minor inconsistencies
    - Incomplete information
  - **Red Flag Categorization:** Organized by severity and type
- **Output:** Prioritized red flag list
- **Tech:** Rule-based detection

#### 4.4 ATS Calculator Node
- **Input:** JD requirements, verification results, completeness score
- **Process:**
  - **ATS Formula:**
    ```
    ATS Score = (Skill Match × 0.4) + (Verified Claims × 0.3) 
              + (Resume Completeness × 0.2) + (Timeline Consistency × 0.1)
    
    Where:
    - Skill Match: Percentage of JD skills found in resume (0-100%)
    - Verified Claims: Percentage of verifiable claims confirmed (0-100%)
    - Resume Completeness: Score from completeness scorer (0-100%)
    - Timeline Consistency: Percentage of timeline with no issues (0-100%)
    ```
  - **Skill Matching Algorithm:**
    - Exact match: "Python" → "Python"
    - Substring match: "JavaScript" → "JS"
    - Fuzzy match: Similarity > 0.8 threshold
    - Considers both claimed and verified skills
  - **Dynamic Scoring:** If JD skills can't be extracted, uses neutral 50% score
  - **Output:** ATS score (0-100) with detailed breakdown
- **Tech:** Formula-based calculation, fuzzy matching

---

### **STAGE 5: REPORTING & VISUALIZATION**

**Purpose:** Present findings in comprehensive, understandable format

#### 5.1 Executive Summary Generator
- **Input:** All scores and findings
- **Process:**
  - Generates natural language summary of key findings
  - Highlights:
    - Overall trustworthiness
    - Key verified achievements
    - Major concerns/red flags
    - Recommendation
- **Output:** Text summary for decision-making

#### 5.2 Final Report Generator
- **Input:** All verification results and scores
- **Process:**
  - Compiles comprehensive report containing:
    - Resume analysis (extracted data)
    - Verification results (per source)
    - Trust score breakdown
    - Red flags analysis
    - ATS score breakdown
    - Executive summary
- **Output:** JSON structured report

#### 5.3 Streamlit Dashboard
- **Input:** Final report
- **Process & Tabs:**

  **Tab 1: Resume Analysis**
  - Display extracted structured data
  - Contact info, education, skills, projects, work experience
  - Visual completeness percentage
  
  **Tab 2: Verification Dashboard**
  - Show verification status per source (GitHub, Kaggle, etc.)
  - Display per-claim trust scores
  - Color-coded badges (✅ Verified, ⚠️ Partial, ❓ Unverified)
  - Evidence and reasoning for each verification
  
  **Tab 3: ATS Match & JD**
  - Display overall ATS score (0-100) prominently
  - Skill match percentage
  - Matched vs. missing skills from JD
  - Detailed ATS calculation breakdown
  
  **Tab 4: Red Flags Analysis**
  - Categorized red flags by severity
  - Detailed explanation for each flag
  - Impact assessment
  - Actionable recommendations

- **Tech:** Streamlit, custom CSS styling, interactive widgets

---

## 🔄 Data Flow Diagram

```
Resume PDF
    ↓
[Resume Parser] → Raw text extracted
    ↓
[Structured Extractor] → {skills, projects, experiences, links}
    ↓
[Claim Detector] → [claim_1, claim_2, claim_3, ...]
    ↓
┌────────────────────────────────────────────────────────┐
│                  PARALLEL PROCESSING                    │
├────────────────────────────────────────────────────────┤
│ [GitHub Agent]      │ [Kaggle Agent] │ [CP Agent]     │
│ ↓ verification      │ ↓ verification │ ↓ verification │
│ {verified_techs}    │ {comp_verified}│ {cp_verified}  │
└────────────────────────────────────────────────────────┘
    ↓
[Tech Consistency Checker] → Skill alignment report
[Timeline Validator] → Timeline validity report
    ↓
[Trust Scorer] → {overall_trust, claim_scores}
[Completeness Scorer] → {completeness_pct}
[Red Flag Detector] → {red_flags}
    ↓
[ATS Calculator] → {ats_score, skill_match, breakdown}
    ↓
[Executive Summary Generator] → Natural language summary
[Final Report Generator] → Comprehensive JSON report
    ↓
[Streamlit Dashboard] → 4-tab visualization
```

---

## 🛠️ Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **Orchestration** | LangGraph (workflow/agentic framework) |
| **LLM** | Ollama (Mistral) - local, privacy-focused |
| **Extraction** | PyPDFLoader, Regex, LLM |
| **APIs** | GitHub REST API, Kaggle API, CP Platform APIs |
| **UI** | Streamlit (web dashboard) |
| **Language** | Python 3.10+ |
| **Data Flow** | State graph with 11 nodes |
| **Logging** | Custom logging configuration |

---

## 📝 How to Explain This to an Interviewer

### **High-Level Pitch (2 minutes)**

> "VERITAS is an AI-powered resume verification system designed for enterprise hiring. The system works in 5 stages: First, we parse PDFs and extract structured data using LLM with regex fallback. Second, we identify verifiable claims in the resume. Third, we orchestrate real API calls to GitHub, Kaggle, and competitive programming platforms to verify these claims. Fourth, we calculate three key scores: trust score (how verified are claims), completeness score (resume quality), and ATS score (job match). Finally, we present everything through a Streamlit dashboard with detailed analysis and red flag detection."

### **Technical Deep-Dive (5-7 minutes)**

**Walk through with visual aids:**

1. **Architecture & Pipeline**
   - "We use LangGraph to build a 5-stage DAG (Directed Acyclic Graph) with 11 nodes"
   - "Each node is a pure function that transforms state"
   - "Stages are: Extraction → JD Processing → Verification → Scoring → Reporting"

2. **Key Innovation: Multi-Source Verification**
   - "Instead of just analyzing the resume text, we verify claims against real APIs"
   - "GitHub Agent: Checks if projects exist, validates tech stack from repo language distribution"
   - "Kaggle Agent: Verifies competition participation and rankings"
   - "Tech Consistency: Cross-references claimed vs. demonstrated skills"
   - "This makes it nearly impossible to fake achievements"

3. **Scoring System**
   - "Trust Score: Weighted average of verification results (verified=100%, partial=70%, unverified=30%)"
   - "ATS Score: Weighted formula combining skill match (40%), verified claims (30%), completeness (20%), timeline (10%)"
   - "Completeness Score: Point-based system for resume quality"

4. **Red Flag Detection**
   - "Automatic detection of inconsistencies and suspicious patterns"
   - "Severity categorization (high/medium/low)"
   - "Examples: Claimed skills with no GitHub evidence, timeline overlaps, missing external links"

5. **Design Decisions**
   - "LLM with temperature=0 for deterministic extraction (instead of temperature=0.7 for creativity)"
   - "Regex fallback ensures no data loss if LLM fails"
   - "Parallel verification agents for performance"
   - "Real API calls instead of scraping for accuracy and ToS compliance"
   - "Explainable scoring: every decision has reasoning attached"

### **Questions You Might Get & Answers**

**Q: Why use Ollama instead of OpenAI?**
- "Privacy and cost. Ollama runs locally on user hardware, so no resume data leaves the system. For enterprise hiring, this is critical."

**Q: How do you handle edge cases (e.g., no JD provided)?**
- "The system is designed to be optional. If no JD, we skip JD processing and use neutral (50%) score for that component. All other verification still happens."

**Q: What if someone's GitHub is private?**
- "We handle this gracefully. A private repo counts as 'unverifiable' rather than 'false'. We don't penalize people for privacy preferences, but we also can't confirm claims."

**Q: How do you prevent false positives in red flags?**
- "Red flags are rule-based and threshold-driven. We only flag if there's actual inconsistency. For example, unverified skills only flag if they're high-severity and there's context suggesting they should be verifiable."

**Q: Scalability?**
- "Each claim verification is independent and can be parallelized. GitHub/Kaggle API calls happen concurrently. For bulk processing, we'd implement job queuing. Currently optimized for single-resume analysis."

---

## 🎓 Interviewer-Ready Talking Points

1. **Problem Solved:** Resume fraud detection + hiring automation in one system
2. **Approach:** Multi-agent verification with real data sources + explainable scoring
3. **Innovation:** Real API verification (not just text analysis)
4. **Scalability:** LangGraph for orchestration, parallel agents for performance
5. **Enterprise Value:** Saves hiring time, reduces fraud, provides audit trail
6. **Code Quality:** Modular design, error handling, logging, state management
7. **Technical Depth:** LLM orchestration, API integration, scoring algorithms, UX design

---

## 📂 File Structure Mapping

```
src/
├── agents/
│   ├── graph.py           # Builds 5-stage workflow using LangGraph
│   ├── nodes.py          # 11 node definitions (each stage's logic)
│   └── state.py          # GraphState TypedDict (data flowing through DAG)
│
├── extraction/
│   ├── resume_parser.py       # PDF → text
│   ├── structured_extractor.py # Text → {skills, projects, work, links}
│   ├── claim_extractor.py     # Data → verifiable claims
│   ├── regex_fallback.py      # Fallback if LLM fails
│   └── resume_parser.py       # PDF loading
│
├── verification/
│   ├── verification_engine.py    # Orchestrates all verifiers
│   ├── github_agent.py          # GitHub API integration
│   ├── kaggle_agent.py          # Kaggle API integration
│   ├── cp_agent.py              # Competitive programming verification
│   ├── linkedin_agent.py        # LinkedIn validation (limited by ToS)
│   ├── tech_consistency_checker.py # Skill alignment
│   └── timeline_validator.py    # Date consistency
│
├── scoring/
│   ├── trust_scorer.py      # Per-claim & overall trust scoring
│   ├── ats_engine.py        # ATS formula + skill matching
│   ├── scoring_utils.py     # Red flags, executive summary
│   └── scoring_utils.py     # Helper functions
│
├── matching/
│   └── jd_extractor.py      # Extract requirements from job description
│
├── ui/
│   └── dashboard.py         # Streamlit 4-tab dashboard
│
└── core/
    ├── config.py            # Constants (weights, thresholds)
    ├── logging_config.py    # Logging setup
    └── __init__.py
```

---

## 🚀 Key Takeaways for Interview

**"VERITAS is a production-ready resume verification system that combines:**
- **LLM-powered extraction** with regex fallback
- **Real API verification** across GitHub, Kaggle, LinkedIn
- **Intelligent scoring** (trust + ATS + completeness)
- **Explainable AI** (reasoning for every decision)
- **Enterprise UI** (interactive Streamlit dashboard)

**The architecture is modular, scalable, and designed for accuracy—it's nearly impossible to fake resume claims when they're verified against real external data."**

---

## 💡 Discussion Starters

1. "What would you change about the scoring formula?"
2. "How would you handle a candidate with no external profiles (GitHub, Kaggle)?"
3. "What are privacy/legal implications of verifying through APIs?"
4. "How would you extend this to real-time monitoring during employment?"
5. "What ML models would improve the tech consistency checker?"

