"""
JD Extractor and Skill Matcher
"""
from typing import List, Dict, Any
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.core.config import LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class JDExtractor:
    """Extract structured data from Job Description"""
    
    def __init__(self):
        self.llm = ChatOllama(
            model=LLM_MODEL,
            base_url=LLM_BASE_URL,
            temperature=LLM_TEMPERATURE,
            format="json"
        )
        logger.info("JDExtractor initialized")
    
    async def extract_jd_requirements(self, jd_text: str) -> Dict[str, Any]:
        """Extract structured requirements from JD"""
        logger.info("Extracting JD requirements")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a job description analyzer. Extract structured data from the JD.

Return ONLY valid JSON with this structure:
{
    "job_title": "string",
    "company": "string",
    "required_skills": ["string"],
    "preferred_skills": ["string"],
    "years_of_experience": "number or null",
    "key_responsibilities": ["string"],
    "required_education": "string or null",
    "technologies_mentioned": ["string"],
    "salary_range": "string or null",
    "location": "string or null"
}

Be thorough in extracting all skills and technologies mentioned."""),
            ("human", f"Extract requirements from this JD:\n\n{jd_text}")
        ])
        
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({})
            logger.info(f"Extracted JD: {result.get('job_title')}")
            return result
        except Exception as e:
            logger.error(f"Error extracting JD: {str(e)}")
            return {
                "job_title": "Unknown",
                "company": "Unknown",
                "required_skills": [],
                "preferred_skills": [],
                "technologies_mentioned": [],
            }


class SkillMatcher:
    """Match resume skills against JD requirements"""
    
    @staticmethod
    def match_skills(
        required_skills: List[str],
        resume_skills: List[str],
        resume_technologies: List[str],
    ) -> Dict[str, Any]:
        """Match resume skills against JD requirements"""
        logger.info("Matching skills against JD requirements")
        
        matched = []
        missing = []
        
        for req_skill in required_skills:
            found = False
            requirement_normalized = req_skill.lower().strip()
            
            # Check resume skills
            for res_skill in resume_skills:
                if SkillMatcher._skill_match(requirement_normalized, res_skill.lower()):
                    matched.append({
                        "required": req_skill,
                        "found_in": res_skill,
                        "source": "skills",
                    })
                    found = True
                    break
            
            # Check technologies
            if not found:
                for tech in resume_technologies:
                    if SkillMatcher._skill_match(requirement_normalized, tech.lower()):
                        matched.append({
                            "required": req_skill,
                            "found_in": tech,
                            "source": "technologies",
                        })
                        found = True
                        break
            
            if not found:
                missing.append(req_skill)
        
        match_rate = (len(matched) / len(required_skills) * 100) if required_skills else 0
        
        result = {
            "matched_skills": matched,
            "missing_skills": missing,
            "match_count": len(matched),
            "required_count": len(required_skills),
            "match_percentage": round(match_rate, 1),
        }
        
        logger.info(f"Skill match: {match_rate:.1f}%")
        return result
    
    @staticmethod
    def _skill_match(jd_skill: str, resume_skill: str) -> bool:
        """Check if skills match (flexible matching)"""
        
        if jd_skill == resume_skill:
            return True
        
        if jd_skill in resume_skill or resume_skill in jd_skill:
            return True
        
        # Handle common variations
        skill_variations = {
            "python": ["py", "django", "flask", "fastapi"],
            "javascript": ["js", "node", "nodejs", "react", "vue", "angular"],
            "java": ["spring", "maven"],
            "sql": ["mysql", "postgresql", "postgres", "sqlite"],
            "aws": ["amazon web services"],
            "gcp": ["google cloud"],
            "machine learning": ["ml", "deep learning", "neural networks"],
        }
        
        for key, variations in skill_variations.items():
            if jd_skill == key and resume_skill in variations:
                return True
            if resume_skill == key and jd_skill in variations:
                return True
        
        return False
