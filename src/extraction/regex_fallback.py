"""
Regex Fallback Module for Resume Data Extraction
Used when LLM extraction fails or for supplementary information
"""
import re
from typing import List, Dict, Any, Optional
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class RegexFallback:
    """Fallback extraction using regex patterns"""
    
    # Regex patterns
    GITHUB_PATTERN = r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)"
    LINKEDIN_PATTERN = r"(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)"
    KAGGLE_PATTERN = r"(?:https?://)?(?:www\.)?kaggle\.com/([a-zA-Z0-9_-]+)"
    EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    PHONE_PATTERN = r"(?:\+?91[\s\-]?)?[0-9]{10}"
    CGPA_PATTERN = r"(?:(?:C\.?G\.?P\.?A|GPA)[:\s]*)?([0-9]\.[0-9]{1,2})"
    UNIVERSITY_PATTERN = r"(?:B\.?Tech|B\.E|B\.Sc|M\.Tech|B\.A|M\.S|MBA)[^,]*?(?:from|–|-)\s*([A-Za-z\s\.]+?)(?:,|\(|$)"
    GRADUATION_YEAR_PATTERN = r"(?:20\d{2})(?:\s*-\s*20\d{2})?|(?:Graduated|Graduation)\s*:?\s*(20\d{2})"
    YEARS_OF_EXP_PATTERN = r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)"
    
    @staticmethod
    def extract_github(text: str) -> Optional[str]:
        """Extract GitHub username"""
        match = re.search(RegexFallback.GITHUB_PATTERN, text, re.IGNORECASE)
        if match:
            username = match.group(1).lower()
            logger.debug(f"GitHub username extracted: {username}")
            return username
        return None
    
    @staticmethod
    def extract_linkedin(text: str) -> Optional[str]:
        """Extract LinkedIn username"""
        match = re.search(RegexFallback.LINKEDIN_PATTERN, text, re.IGNORECASE)
        if match:
            username = match.group(1).lower()
            logger.debug(f"LinkedIn username extracted: {username}")
            return username
        return None
    
    @staticmethod
    def extract_kaggle(text: str) -> Optional[str]:
        """Extract Kaggle username"""
        match = re.search(RegexFallback.KAGGLE_PATTERN, text, re.IGNORECASE)
        if match:
            username = match.group(1).lower()
            logger.debug(f"Kaggle username extracted: {username}")
            return username
        return None
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract all email addresses"""
        emails = re.findall(RegexFallback.EMAIL_PATTERN, text)
        logger.debug(f"Emails extracted: {len(emails)}")
        return list(set(emails))  # Remove duplicates
    
    @staticmethod
    def extract_phones(text: str) -> List[str]:
        """Extract all phone numbers"""
        phones = re.findall(RegexFallback.PHONE_PATTERN, text)
        logger.debug(f"Phones extracted: {len(phones)}")
        return list(set(phones))
    
    @staticmethod
    def extract_cgpa(text: str) -> Optional[float]:
        """Extract CGPA/GPA score"""
        # First try exact CGPA pattern
        match = re.search(RegexFallback.CGPA_PATTERN, text, re.IGNORECASE)
        if match:
            try:
                cgpa = float(match.group(1))
                if 0 <= cgpa <= 10:  # Valid CGPA range
                    logger.debug(f"CGPA extracted: {cgpa}")
                    return cgpa
            except (ValueError, AttributeError):
                pass
        return None
    
    @staticmethod
    def extract_university(text: str) -> Optional[str]:
        """Extract university name"""
        match = re.search(RegexFallback.UNIVERSITY_PATTERN, text, re.IGNORECASE)
        if match:
            university = match.group(1).strip()
            logger.debug(f"University extracted: {university}")
            return university
        return None
    
    @staticmethod
    def extract_graduation_year(text: str) -> Optional[int]:
        """Extract graduation year"""
        matches = re.findall(RegexFallback.GRADUATION_YEAR_PATTERN, text, re.IGNORECASE)
        if matches:
            # Get the latest year (graduation year should be the most recent)
            years = [int(m) for m in matches if m.isdigit()]
            if years:
                year = max(years)
                logger.debug(f"Graduation year extracted: {year}")
                return year
        return None
    
    @staticmethod
    def extract_years_of_experience(text: str) -> Optional[int]:
        """Extract years of experience"""
        match = re.search(RegexFallback.YEARS_OF_EXP_PATTERN, text, re.IGNORECASE)
        if match:
            try:
                years = int(match.group(1))
                logger.debug(f"Years of experience extracted: {years}")
                return years
            except ValueError:
                pass
        return None
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract all URLs"""
        url_pattern = r"https?://[^\s]+"
        urls = re.findall(url_pattern, text)
        logger.debug(f"URLs extracted: {len(urls)}")
        return list(set(urls))  # Remove duplicates
    
    @staticmethod
    def extract_numeric_claims(text: str) -> Dict[str, List[int]]:
        """Extract numeric claims (e.g., 'solved 500+ problems')"""
        claims = {
            "problems_solved": [],
            "projects_count": [],
            "competitions": [],
            "certifications": [],
        }
        
        # Problems solved
        problems_pattern = r"(?:solved|tackling|tackled)\s+(\d+)\+?\s*(?:problems|questions|leetcode|coding)"
        matches = re.findall(problems_pattern, text, re.IGNORECASE)
        claims["problems_solved"] = [int(m) for m in matches]
        
        # Projects count
        projects_pattern = r"(\d+)\+?\s*(?:projects|portfolios|applications)"
        matches = re.findall(projects_pattern, text, re.IGNORECASE)
        claims["projects_count"] = [int(m) for m in matches]
        
        # Competitions
        competitions_pattern = r"(\d+)\+?\s*(?:competitions|hackathons|contests)"
        matches = re.findall(competitions_pattern, text, re.IGNORECASE)
        claims["competitions"] = [int(m) for m in matches]
        
        # Certifications
        certifications_pattern = r"(\d+)\+?\s*(?:certifications|certificates|certs)"
        matches = re.findall(certifications_pattern, text, re.IGNORECASE)
        claims["certifications"] = [int(m) for m in matches]
        
        logger.debug(f"Numeric claims extracted: {claims}")
        return claims
    
    @staticmethod
    def extract_all(text: str) -> Dict[str, Any]:
        """Extract all available information using regex"""
        return {
            "github_username": RegexFallback.extract_github(text),
            "linkedin_username": RegexFallback.extract_linkedin(text),
            "kaggle_username": RegexFallback.extract_kaggle(text),
            "emails": RegexFallback.extract_emails(text),
            "phones": RegexFallback.extract_phones(text),
            "cgpa": RegexFallback.extract_cgpa(text),
            "university": RegexFallback.extract_university(text),
            "graduation_year": RegexFallback.extract_graduation_year(text),
            "years_of_experience": RegexFallback.extract_years_of_experience(text),
            "urls": RegexFallback.extract_urls(text),
            "numeric_claims": RegexFallback.extract_numeric_claims(text),
        }
