"""
JD Extractor and Skill Matcher
"""
from typing import List, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser

from src.core.config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class JDExtractor:
    """Extract structured data from Job Description"""

    # Predefined role-to-skill mapping for vague JDs
    ROLE_SKILL_MAPPING = {
        "full stack developer": ["React", "Node.js", "SQL", "REST APIs", "JavaScript", "HTML", "CSS", "Git"],
        "backend developer": ["Python", "Java", "Node.js", "SQL", "REST APIs", "Git", "Docker"],
        "frontend developer": ["React", "JavaScript", "HTML", "CSS", "TypeScript", "Git", "Responsive Design"],
        "ml engineer": ["Python", "TensorFlow", "PyTorch", "Data Science", "Pandas", "NumPy", "Scikit-learn"],
        "data scientist": ["Python", "SQL", "Pandas", "NumPy", "Matplotlib", "Data Analysis", "Statistics"],
        "devops engineer": ["Docker", "Kubernetes", "AWS", "CI/CD", "Git", "Linux", "Terraform"],
        "cloud engineer": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform"],
        "ios developer": ["Swift", "Objective-C", "iOS SDK", "Git"],
        "android developer": ["Java", "Kotlin", "Android SDK", "Git"],
        "python developer": ["Python", "Django", "Flask", "SQL", "Git"],
        "java developer": ["Java", "Spring", "SQL", "Git", "REST APIs"],
        "c++ developer": ["C++", "Git", "Memory Management", "STL"],
        "qa engineer": ["Testing", "Automation", "Selenium", "Git", "JIRA"],
        "devops": ["Docker", "Kubernetes", "AWS", "CI/CD", "Git"],
        "cloud": ["AWS", "Azure", "GCP", "Docker", "Kubernetes"],
        "ai engineer": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Data Science"],
    }
    
    def __init__(self):
        self.llm = None
        if GROQ_API_KEY:
            try:
                self.llm = ChatGroq(
                    model=GROQ_MODEL,
                    temperature=GROQ_TEMPERATURE,
                    groq_api_key=GROQ_API_KEY,
                )
            except Exception as exc:
                logger.error("Groq JD extractor initialization failed: %s", exc)
        else:
            logger.warning("GROQ_API_KEY not configured; JD extraction will use heuristics only")

        logger.info("JDExtractor initialized")
    
    def infer_skills_from_title(self, job_title: str) -> List[str]:
        """Infer required skills from job title if JD is vague"""
        logger.info(f"Inferring skills for job title: {job_title}")
        
        title_lower = job_title.lower().strip()
        
        # Check for direct match in mapping
        for role_pattern, skills in self.ROLE_SKILL_MAPPING.items():
            if role_pattern in title_lower:
                logger.info(f"Found skill mapping for role: {role_pattern}")
                return skills
        
        # If no direct match, try to extract keywords and return default technical skills
        logger.warning(f"No skill mapping found for: {job_title}, using generic technical skills")
        return ["Git", "Problem Solving", "Communication", "Teamwork"]
    
    async def extract_jd_requirements(self, jd_text: str) -> Dict[str, Any]:
        """Extract structured requirements from JD"""
        logger.info("Extracting JD requirements")
        
        if not self.llm:
            logger.warning("No Groq client available, using heuristic JD extraction")
            return {
                "job_title": "Unknown",
                "company": "Unknown",
                "required_skills": [],
                "preferred_skills": [],
                "technologies_mentioned": [],
                "key_responsibilities": [],
                "years_of_experience": None,
                "required_education": None,
                "salary_range": None,
                "location": None,
            }

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a job description analyzer. Extract structured data from the JD.

Return ONLY valid JSON with this structure:
{{
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
}}

Be thorough in extracting all skills and technologies mentioned."""),
            ("human", "Extract requirements from this JD:\n\n{jd_content}")
        ])
        
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({"jd_content": jd_text})
            logger.info(f"Extracted JD: {result.get('job_title')}")
            
            # Ensure required fields exist
            if not result.get("required_skills"):
                result["required_skills"] = []
            if not result.get("technologies_mentioned"):
                result["technologies_mentioned"] = []
            
            # CRITICAL FIX: If no skills extracted, use AI brain to infer from job title
            if len(result.get("required_skills", [])) == 0:
                logger.warning(f"No required skills extracted from JD, inferring from title: {result.get('job_title')}")
                inferred_skills = self.infer_skills_from_title(result.get("job_title", ""))
                result["required_skills"] = inferred_skills
                result["inferred_from_title"] = True
            
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
