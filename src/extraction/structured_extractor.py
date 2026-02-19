"""
Structured Resume Data Extractor
Uses LLM with JSON schema for reliable extraction
"""
import json
from typing import Dict, Any, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.core.config import LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE
from src.core.logging_config import get_logger
from src.extraction.regex_fallback import RegexFallback

logger = get_logger(__name__)

class StructuredExtractor:
    """Extract structured JSON from resume text"""
    
    EXTRACTION_SCHEMA = {
        "type": "object",
        "properties": {
            "full_name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "github_username": {"type": "string"},
            "kaggle_username": {"type": "string"},
            "linkedin_url": {"type": "string"},
            "cgpa": {"type": "number"},
            "university": {"type": "string"},
            "graduation_year": {"type": "integer"},
            "years_of_experience": {"type": "integer"},
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "technologies": {"type": "array", "items": {"type": "string"}},
                        "timeline": {"type": "string"},
                        "impact": {"type": "string"},
                    },
                    "required": ["name", "technologies"]
                }
            },
            "skills": {
                "type": "array",
                "items": {"type": "string"}
            },
            "technologies": {
                "type": "array",
                "items": {"type": "string"}
            },
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "type": {"type": "string"},  # skill_match, numeric, timeline, depth
                        "value": {"type": "string"},
                    }
                }
            },
            "work_experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "company": {"type": "string"},
                        "position": {"type": "string"},
                        "start_year": {"type": "integer"},
                        "end_year": {"type": "integer"},
                        "description": {"type": "string"},
                        "technologies": {"type": "array", "items": {"type": "string"}},
                    }
                }
            },
            "certifications": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
    
    def __init__(self):
        """Initialize LLM for structured extraction"""
        self.llm = ChatOllama(
            model=LLM_MODEL,
            base_url=LLM_BASE_URL,
            temperature=LLM_TEMPERATURE,
            format="json"
        )
        logger.info(f"StructuredExtractor initialized with model: {LLM_MODEL}")
    
    async def extract(self, resume_text: str) -> Dict[str, Any]:
        """Extract structured data from resume"""
        logger.info("Starting structured extraction from resume")
        
        # Use ChatPromptTemplate with proper variable placeholder
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a resume data extraction expert. Extract information from the resume and return ONLY valid JSON.

CRITICAL RULES:
1. Return ONLY JSON, no markdown, no explanations
2. For missing fields, use null or empty arrays
3. Extract ALL projects mentioned
4. Extract ALL technologies mentioned
5. Extract ALL claims (skills, numeric facts, timelines)
6. Be strict about accuracy - only include what's explicitly stated
7. Normalize technology names (e.g., "React" not "ReactJS")

Focus on:
- Explicit project names and descriptions
- All technologies used in projects
- Skills explicitly claimed
- Numeric claims (e.g., "solved 500+ problems")
- Work experience with dates
- Educational background

Return ONLY valid JSON with these fields: full_name, email, phone, github_username, kaggle_username, linkedin_url, cgpa, university, graduation_year, years_of_experience, projects (array), skills (array), technologies (array), claims (array), work_experience (array), certifications (array).

For ANY missing data, use null for objects or empty arrays for lists. Do NOT include fields with null values unless they are in the array.
"""),
            ("human", "Extract structured data from this resume:\n\n{resume_text}")
        ])
        
        # Create proper chain with variable binding
        prompt = prompt.partial(resume_text=resume_text)
        
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({})
            logger.info("Structured extraction successful")
            return self._merge_with_regex_fallback(resume_text, result)
        except Exception as e:
            logger.error(f"Structured extraction failed: {str(e)}")
            logger.info("Falling back to regex extraction")
            return self._regex_only_extraction(resume_text)
    
    def _merge_with_regex_fallback(self, text: str, llm_result: Dict[str, Any]) -> Dict[str, Any]:
        """Merge LLM extraction with regex fallback for missing fields"""
        logger.info("Merging LLM results with regex fallback")
        
        regex_data = RegexFallback.extract_all(text)
        
        # Fill null fields from regex results
        if not llm_result.get("github_username") and regex_data.get("github_username"):
            llm_result["github_username"] = regex_data["github_username"]
        
        if not llm_result.get("kaggle_username") and regex_data.get("kaggle_username"):
            llm_result["kaggle_username"] = regex_data["kaggle_username"]
        
        if not llm_result.get("linkedin_url") and regex_data.get("linkedin_username"):
            llm_result["linkedin_url"] = f"https://linkedin.com/in/{regex_data['linkedin_username']}"
        
        if not llm_result.get("email") and regex_data.get("emails"):
            llm_result["email"] = regex_data["emails"][0]
        
        if not llm_result.get("phone") and regex_data.get("phones"):
            llm_result["phone"] = regex_data["phones"][0]
        
        if not llm_result.get("cgpa") and regex_data.get("cgpa"):
            llm_result["cgpa"] = regex_data["cgpa"]
        
        if not llm_result.get("graduation_year") and regex_data.get("graduation_year"):
            llm_result["graduation_year"] = regex_data["graduation_year"]
        
        if not llm_result.get("years_of_experience") and regex_data.get("years_of_experience"):
            llm_result["years_of_experience"] = regex_data["years_of_experience"]
        
        # Add numeric claims to claims list
        if regex_data.get("numeric_claims"):
            if "claims" not in llm_result:
                llm_result["claims"] = []
            
            for claim_type, values in regex_data["numeric_claims"].items():
                for value in values:
                    llm_result["claims"].append({
                        "claim": f"Claimed {claim_type}: {value}+",
                        "type": "numeric",
                        "value": str(value)
                    })
        
        logger.info("Merge completed successfully")
        return llm_result
    
    def _regex_only_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction using only regex"""
        logger.warning("Using regex-only extraction")
        
        regex_data = RegexFallback.extract_all(text)
        
        return {
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
            "projects": [],
            "skills": [],
            "technologies": [],
            "claims": [
                {
                    "claim": f"Claimed {claim_type}: {value}+",
                    "type": "numeric",
                    "value": str(value)
                }
                for claim_type, values in regex_data.get("numeric_claims", {}).items()
                for value in values
            ],
            "work_experience": [],
            "certifications": [],
        }
