"""
Structured Resume Data Extractor
Uses Groq structured output for reliable extraction
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, ConfigDict, Field

from src.core.config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE
from src.core.logging_config import get_logger
from src.extraction.privacy import PrivacyScrubber
from src.extraction.regex_fallback import RegexFallback

logger = get_logger(__name__)


class CandidateProject(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    timeline: Optional[str] = None
    impact: Optional[str] = None


class CandidateWorkExperience(BaseModel):
    model_config = ConfigDict(extra="ignore")

    company: Optional[str] = None
    position: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class CandidateEducation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    institution: Optional[str] = None
    degree: Optional[str] = None
    cgpa: Optional[float] = None
    graduation_year: Optional[int] = None
    notes: Optional[str] = None


class CandidateClaim(BaseModel):
    model_config = ConfigDict(extra="ignore")

    claim: Optional[str] = None
    type: Optional[str] = None
    value: Optional[str] = None


class CandidateResume(BaseModel):
    model_config = ConfigDict(extra="ignore")

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    github_username: Optional[str] = None
    kaggle_username: Optional[str] = None
    linkedin_url: Optional[str] = None
    cgpa: Optional[float] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    years_of_experience: Optional[int] = None
    education: List[CandidateEducation] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    projects: List[CandidateProject] = Field(default_factory=list)
    work_experience: List[CandidateWorkExperience] = Field(default_factory=list)
    external_links: List[str] = Field(default_factory=list)
    claims: List[CandidateClaim] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)


class StructuredExtractor:
    """Extract structured JSON from resume text."""

    def __init__(self):
        self.llm = None
        if GROQ_API_KEY:
            try:
                self.llm = ChatGroq(
                    model=GROQ_MODEL,
                    temperature=GROQ_TEMPERATURE,
                    groq_api_key=GROQ_API_KEY,
                )
                logger.info("StructuredExtractor initialized with Groq model: %s", GROQ_MODEL)
            except Exception as exc:
                logger.error("Groq client initialization failed: %s", exc)
        else:
            logger.warning("GROQ_API_KEY is not configured; structured extraction will use regex fallback only")

    async def extract(self, resume_text: str) -> Dict[str, Any]:
        """Extract structured data from resume."""

        logger.info("Starting structured extraction from resume")
        scrubbed_text, redactions = PrivacyScrubber.scrub(resume_text)

        if not self.llm:
            logger.warning("No Groq client available, falling back to regex extraction")
            fallback = self._regex_only_extraction(scrubbed_text)
            fallback["pii_redactions"] = redactions
            return fallback

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a resume data extraction expert. Extract information from the resume and return a strict structured object.

Rules:
1. Return structured data only.
2. Use null for missing scalar fields and empty lists for missing collections.
3. Extract only information explicitly stated in the resume.
4. Preserve flat compatibility fields such as full_name, email, phone, github_username, kaggle_username, linkedin_url, cgpa, university, graduation_year, and years_of_experience.
5. Populate the nested collections for education, skills, technologies, projects, work_experience, external_links, claims, and certifications.
6. Normalize technology names where obvious, but do not invent missing details.
7. If a field is not present, keep it empty rather than guessing.
""",
                ),
                ("human", "Extract structured data from this resume:\n\n{resume_text}"),
            ]
        )

        try:
            chain = prompt | self.llm.with_structured_output(CandidateResume)
            result = chain.invoke({"resume_text": scrubbed_text})

            if isinstance(result, CandidateResume):
                structured = result.model_dump(exclude_none=True)
            elif isinstance(result, dict):
                structured = result
            else:
                structured = CandidateResume.model_validate(result).model_dump(exclude_none=True)

            normalized = self._normalize_result(structured)
            merged = self._merge_with_regex_fallback(scrubbed_text, normalized)
            merged["pii_redactions"] = redactions
            logger.info("Structured extraction successful")
            return merged
        except Exception as exc:
            logger.error("Structured extraction failed: %s", exc)
            logger.info("Falling back to regex extraction")
            fallback = self._regex_only_extraction(scrubbed_text)
            fallback["pii_redactions"] = redactions
            return fallback

    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all expected fields exist and are JSON-serializable."""

        normalized = {
            "full_name": result.get("full_name"),
            "email": result.get("email"),
            "phone": result.get("phone"),
            "github_username": result.get("github_username"),
            "kaggle_username": result.get("kaggle_username"),
            "linkedin_url": result.get("linkedin_url"),
            "cgpa": result.get("cgpa"),
            "university": result.get("university"),
            "graduation_year": result.get("graduation_year"),
            "years_of_experience": result.get("years_of_experience"),
            "education": result.get("education") or [],
            "skills": result.get("skills") or [],
            "technologies": result.get("technologies") or [],
            "projects": result.get("projects") or [],
            "work_experience": result.get("work_experience") or [],
            "external_links": result.get("external_links") or [],
            "claims": result.get("claims") or [],
            "certifications": result.get("certifications") or [],
        }

        if not normalized["external_links"]:
            external_links = []
            for key in ("github_username", "kaggle_username", "linkedin_url"):
                value = normalized.get(key)
                if value:
                    external_links.append(str(value))
            normalized["external_links"] = external_links

        return normalized

    def _merge_with_regex_fallback(self, text: str, llm_result: Dict[str, Any]) -> Dict[str, Any]:
        """Merge LLM extraction with regex fallback for missing fields."""

        logger.info("Merging LLM results with regex fallback")
        regex_data = RegexFallback.extract_all(text)
        result = dict(llm_result)

        if not result.get("github_username") and regex_data.get("github_username"):
            result["github_username"] = regex_data["github_username"]

        if not result.get("kaggle_username") and regex_data.get("kaggle_username"):
            result["kaggle_username"] = regex_data["kaggle_username"]

        if not result.get("linkedin_url") and regex_data.get("linkedin_username"):
            result["linkedin_url"] = f"https://linkedin.com/in/{regex_data['linkedin_username']}"

        if not result.get("email") and regex_data.get("emails"):
            result["email"] = regex_data["emails"][0]

        if not result.get("phone") and regex_data.get("phones"):
            result["phone"] = regex_data["phones"][0]

        if not result.get("cgpa") and regex_data.get("cgpa") is not None:
            result["cgpa"] = regex_data["cgpa"]

        if not result.get("graduation_year") and regex_data.get("graduation_year"):
            result["graduation_year"] = regex_data["graduation_year"]

        if not result.get("years_of_experience") and regex_data.get("years_of_experience"):
            result["years_of_experience"] = regex_data["years_of_experience"]

        claims = list(result.get("claims") or [])
        for claim_type, values in (regex_data.get("numeric_claims") or {}).items():
            for value in values:
                claims.append({"claim": f"Claimed {claim_type}: {value}+", "type": "numeric", "value": str(value)})
        result["claims"] = claims

        if not result.get("external_links"):
            external_links = []
            if result.get("github_username"):
                external_links.append(f"https://github.com/{result['github_username']}")
            if result.get("linkedin_url"):
                external_links.append(result["linkedin_url"])
            if result.get("kaggle_username"):
                external_links.append(f"https://www.kaggle.com/{result['kaggle_username']}")
            result["external_links"] = external_links

        logger.info("Merge completed successfully")
        return self._normalize_result(result)

    def _regex_only_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction using only regex."""

        logger.warning("Using regex-only extraction")
        regex_data = RegexFallback.extract_all(text)

        result = {
            "full_name": None,
            "email": (regex_data.get("emails") or [None])[0],
            "phone": (regex_data.get("phones") or [None])[0],
            "github_username": regex_data.get("github_username"),
            "kaggle_username": regex_data.get("kaggle_username"),
            "linkedin_url": f"https://linkedin.com/in/{regex_data['linkedin_username']}" if regex_data.get("linkedin_username") else None,
            "cgpa": regex_data.get("cgpa"),
            "university": regex_data.get("university"),
            "graduation_year": regex_data.get("graduation_year"),
            "years_of_experience": regex_data.get("years_of_experience"),
            "education": [],
            "skills": [],
            "technologies": [],
            "projects": [],
            "work_experience": [],
            "external_links": [],
            "claims": [
                {"claim": f"Claimed {claim_type}: {value}+", "type": "numeric", "value": str(value)}
                for claim_type, values in regex_data.get("numeric_claims", {}).items()
                for value in values
            ],
            "certifications": [],
        }

        return self._normalize_result(result)
