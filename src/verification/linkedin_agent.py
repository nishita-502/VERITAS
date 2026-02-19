"""
LinkedIn Verification Agent
Note: LinkedIn scraping is restricted. This agent provides basic verification only.
"""
import requests
from typing import Dict, Any, Optional
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class LinkedInAgent:
    """Verify LinkedIn claims (limited by LinkedIn's ToS)"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "VERITAS-Resume-Verification",
        }
        logger.warning("LinkedInAgent: LinkedIn API access is restricted. Using basic URL validation only.")
    
    def verify_linkedin_profile(self, linkedin_url: str) -> Dict[str, Any]:
        """Verify LinkedIn profile exists via URL check"""
        logger.info(f"Verifying LinkedIn profile: {linkedin_url}")
        
        try:
            response = requests.head(linkedin_url, headers=self.headers, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                logger.info(f"LinkedIn profile accessible: {linkedin_url}")
                return {
                    "exists": True,
                    "url": linkedin_url,
                    "verified_by": "profile_page_access",
                }
            else:
                logger.warning(f"LinkedIn profile not accessible: {response.status_code}")
                return {
                    "exists": False,
                    "url": linkedin_url,
                    "status_code": response.status_code,
                }
        
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout verifying LinkedIn profile: {linkedin_url}")
            return {
                "exists": None,
                "url": linkedin_url,
                "error": "timeout",
            }
        except Exception as e:
            logger.error(f"Error verifying LinkedIn profile: {str(e)}")
            return {
                "exists": None,
                "url": linkedin_url,
                "error": str(e),
            }
    
    def extract_username(self, linkedin_url: str) -> Optional[str]:
        """Extract LinkedIn username from URL"""
        import re
        
        match = re.search(r"linkedin\.com/in/([a-zA-Z0-9_-]+)", linkedin_url, re.IGNORECASE)
        if match:
            username = match.group(1).lower()
            logger.debug(f"LinkedIn username extracted: {username}")
            return username
        return None
