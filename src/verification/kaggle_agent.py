"""
Kaggle Verification Agent
Verifies Kaggle profile claims
"""
import requests
from typing import Dict, Any, Optional
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class KaggleAgent:
    """Verify Kaggle claims using public API"""
    
    def __init__(self):
        self.base_url = "https://www.kaggle.com/api/v1"
        self.headers = {
            "User-Agent": "VERITAS-Resume-Verification",
        }
        logger.info("KaggleAgent initialized")
    
    def verify_user_exists(self, username: str) -> Dict[str, Any]:
        """Verify Kaggle user exists"""
        logger.info(f"Verifying Kaggle user: {username}")
        
        try:
            # Kaggle public API endpoint for user profiles
            url = f"https://www.kaggle.com/api/v1/users/{username}/profile"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Kaggle user verified: {username}")
                
                return {
                    "exists": True,
                    "username": username,
                    "display_name": data.get("displayName"),
                    "medals": data.get("medals", {}),
                    "tier": data.get("tier"),
                }
            elif response.status_code == 404:
                logger.warning(f"Kaggle user not found: {username}")
                return {"exists": False, "username": username}
            else:
                logger.warning(f"Kaggle API returned {response.status_code}")
                # Try alternative endpoint
                return self._verify_via_html_parsing(username)
        
        except Exception as e:
            logger.error(f"Error verifying Kaggle user {username}: {str(e)}")
            return {"exists": None, "username": username, "error": str(e)}
    
    def _verify_via_html_parsing(self, username: str) -> Dict[str, Any]:
        """Fallback: Verify user via simple HTML check"""
        logger.info(f"Attempting HTML-based verification for Kaggle user: {username}")
        
        try:
            url = f"https://www.kaggle.com/{username}"
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                logger.info(f"Kaggle user profile accessible: {username}")
                return {
                    "exists": True,
                    "username": username,
                    "verified_by": "profile_page_access",
                }
            else:
                logger.warning(f"Kaggle user profile not accessible: {username}")
                return {"exists": False, "username": username}
        
        except Exception as e:
            logger.error(f"Error in HTML verification: {str(e)}")
            return {"exists": None, "username": username, "error": str(e)}
    
    def get_competitions_participated(self, username: str) -> Dict[str, Any]:
        """Get competitions user participated in"""
        logger.info(f"Fetching competitions for Kaggle user: {username}")
        
        try:
            url = f"https://www.kaggle.com/api/v1/users/{username}/competitions"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                competitions = response.json()
                logger.info(f"Found {len(competitions)} competitions")
                
                return {
                    "username": username,
                    "competitions": competitions,
                    "total_count": len(competitions),
                }
            else:
                logger.warning(f"Could not fetch competitions: {response.status_code}")
                return {"username": username, "competitions": [], "total_count": 0, "error": response.status_code}
        
        except Exception as e:
            logger.error(f"Error fetching competitions: {str(e)}")
            return {"username": username, "competitions": [], "total_count": 0, "error": str(e)}
    
    def get_datasets_contributed(self, username: str) -> Dict[str, Any]:
        """Get datasets contributed by user"""
        logger.info(f"Fetching datasets for Kaggle user: {username}")
        
        try:
            url = f"https://www.kaggle.com/api/v1/users/{username}/datasets"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                datasets = response.json()
                logger.info(f"Found {len(datasets)} datasets")
                
                return {
                    "username": username,
                    "datasets": datasets,
                    "total_count": len(datasets),
                }
            else:
                logger.warning(f"Could not fetch datasets: {response.status_code}")
                return {"username": username, "datasets": [], "total_count": 0, "error": response.status_code}
        
        except Exception as e:
            logger.error(f"Error fetching datasets: {str(e)}")
            return {"username": username, "datasets": [], "total_count": 0, "error": str(e)}
    
    def verify_competitive_claims(self, username: str, claimed_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Verify competitive programming claims"""
        logger.info(f"Verifying Kaggle metrics for {username}")
        
        profile = self.verify_user_exists(username)
        
        if not profile.get("exists"):
            logger.warning(f"Cannot verify metrics: user {username} not found")
            return {
                "username": username,
                "verified": False,
                "reason": "User not found",
            }
        
        result = {
            "username": username,
            "verified": True,
            "profile_info": profile,
            "claimed_metrics": claimed_metrics,
            "actual_metrics": {},
            "verification_status": {},
        }
        
        # Verify competitions count if claimed
        if "competitions" in claimed_metrics:
            try:
                comps = self.get_competitions_participated(username)
                actual_count = comps.get("total_count", 0)
                claimed_count = claimed_metrics.get("competitions")
                
                result["actual_metrics"]["competitions"] = actual_count
                result["verification_status"]["competitions"] = {
                    "claimed": claimed_count,
                    "actual": actual_count,
                    "verified": actual_count >= claimed_count,
                }
            except:
                pass
        
        # Verify datasets count if claimed
        if "datasets" in claimed_metrics:
            try:
                datasets = self.get_datasets_contributed(username)
                actual_count = datasets.get("total_count", 0)
                claimed_count = claimed_metrics.get("datasets")
                
                result["actual_metrics"]["datasets"] = actual_count
                result["verification_status"]["datasets"] = {
                    "claimed": claimed_count,
                    "actual": actual_count,
                    "verified": actual_count >= claimed_count,
                }
            except:
                pass
        
        logger.info(f"Kaggle metric verification complete for {username}")
        return result
