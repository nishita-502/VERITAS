"""
Competitive Programming Agent - Real Verification
Verifies claims on LeetCode, GeeksforGeeks, Codeforces, CodeChef
Uses real APIs and web scraping with proper error handling
"""
import requests
import re
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Cache directory for CP profiles
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_EXPIRY_HOURS = 24


class CPAgentReal:
    """Real competitive programming verification with API integration"""
    
    # Platform configurations
    PLATFORMS = {
        "leetcode": {
            "name": "LeetCode",
            "url": "https://leetcode.com",
            "api_url": "https://leetcode.com/graphql",
            "username_patterns": [
                # PRIMARY: "username: XXX" pattern (from resume format)
                r"LeetCode\s*\([^)]*username\s*:\s*([a-zA-Z0-9_-]+)",
                # Secondary: Direct URL
                r"(?:https?://)?(?:www\.)?leetcode\.com/(?:u/|user/)?([a-zA-Z0-9_-]+)",
                # Tertiary: Other colon patterns
                r"(?:LeetCode|leetcode)\s*:\s*([a-zA-Z0-9_-]+)",
            ],
            "timeout": 10,
        },
        "geeksforgeeks": {
            "name": "GeeksforGeeks",
            "url": "https://www.geeksforgeeks.org",
            "api_url": "https://www.geeksforgeeks.org/user",
            "username_patterns": [
                # PRIMARY: "username: XXX" pattern
                r"GeeksforGeeks\s*\([^)]*username\s*:\s*([a-zA-Z0-9_-]+)",
                # Secondary: Direct URL
                r"(?:https?://)?(?:www\.)?geeksforgeeks\.org/user/([a-zA-Z0-9_-]+)",
                # Tertiary: Other colon patterns
                r"(?:GeeksforGeeks|geeksforgeeks)\s*:\s*([a-zA-Z0-9_-]+)",
            ],
            "timeout": 10,
        },
        "codeforces": {
            "name": "Codeforces",
            "url": "https://codeforces.com",
            "api_url": "https://codeforces.com/api/user.info",
            "username_patterns": [
                # PRIMARY: "username: XXX" pattern
                r"Codeforces\s*\([^)]*username\s*:\s*([a-zA-Z0-9_-]+)",
                # Secondary: Direct URL
                r"(?:https?://)?(?:www\.)?codeforces\.com/profile/([a-zA-Z0-9_-]+)",
                # Tertiary: Other colon patterns
                r"(?:Codeforces|codeforces)\s*:\s*([a-zA-Z0-9_-]+)",
            ],
            "timeout": 10,
        },
        "codechef": {
            "name": "CodeChef",
            "url": "https://www.codechef.com",
            "api_url": "https://www.codechef.com/api/users",
            "username_patterns": [
                # PRIMARY: "username: XXX" pattern
                r"CodeChef\s*\([^)]*username\s*:\s*([a-zA-Z0-9_-]+)",
                # Secondary: Direct URL
                r"(?:https?://)?(?:www\.)?codechef\.com/users/([a-zA-Z0-9_-]+)",
                # Tertiary: Other colon patterns
                r"(?:CodeChef|codechef)\s*:\s*([a-zA-Z0-9_-]+)",
            ],
            "timeout": 10,
        },
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "VERITAS-Resume-Verification/1.0"
        })
        logger.info("CPAgentReal initialized with real API integration")
    
    def _get_cache_path(self, platform: str, username: str) -> Path:
        """Get cache file path for a CP profile"""
        return CACHE_DIR / f"cp_{platform}_{username}.json"
    
    def _load_cache(self, platform: str, username: str) -> Optional[Dict[str, Any]]:
        """Load cached CP data if valid"""
        cache_path = self._get_cache_path(platform, username)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            timestamp = datetime.fromisoformat(cache_data.get("timestamp", ""))
            if datetime.now() - timestamp > timedelta(hours=CACHE_EXPIRY_HOURS):
                logger.debug(f"Cache for {platform}/{username} expired")
                return None
            
            logger.debug(f"Loaded cached CP data for {platform}/{username}")
            return cache_data["data"]
        
        except Exception as e:
            logger.warning(f"Error loading cache for {platform}/{username}: {str(e)}")
            return None
    
    def _save_cache(self, platform: str, username: str, data: Dict[str, Any]) -> None:
        """Save CP data to cache"""
        cache_path = self._get_cache_path(platform, username)
        
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Cached CP data for {platform}/{username}")
        
        except Exception as e:
            logger.warning(f"Error saving cache for {platform}/{username}: {str(e)}")
    def extract_usernames(self, resume_text: str) -> Dict[str, Optional[str]]:
        """Extract CP platform usernames from resume text
        Tries multiple patterns: URLs, text mentions (e.g. "username: xyz")
        """
        logger.info("Extracting competitive programming usernames from resume")
        logger.debug(f"Resume text length: {len(resume_text)} characters")
        
        usernames = {}
        
        for platform_key, platform_info in self.PLATFORMS.items():
            patterns = platform_info.get("username_patterns", [])
            logger.debug(f"Trying {len(patterns)} patterns for {platform_key}")
            
            # Try each pattern until we find a match
            for pattern_idx, pattern in enumerate(patterns):
                try:
                    matches = re.findall(pattern, resume_text, re.IGNORECASE)
                    
                    if matches:
                        logger.debug(f"{platform_key} pattern {pattern_idx} matched: {matches}")
                        
                        for username_candidate in matches:
                            username_candidate = username_candidate.strip()
                            
                            # Filter out junk matches (numbers only, very short strings)
                            if not re.match(r"^\d+\+?$", username_candidate) and len(username_candidate) > 2:
                                usernames[platform_key] = username_candidate
                                logger.info(f"✅ Found {platform_key} username: {username_candidate}")
                                break  # Stop after first valid match for this platform
                        
                        if platform_key in usernames:
                            break  # Move to next platform
                    else:
                        logger.debug(f"{platform_key} pattern {pattern_idx} no match: {pattern[:50]}...")
                
                except Exception as e:
                    logger.debug(f"Error with {platform_key} pattern {pattern_idx}: {str(e)}")
                    continue
        
        if not usernames:
            logger.warning("❌ No competitive programming usernames found in resume")
            logger.debug(f"Resume text sample: {resume_text[:500]}...")
        else:
            logger.info(f"✅ Extracted usernames: {usernames}")
        
        return usernames
    
    def extract_claimed_problems(self, resume_text: str) -> Dict[str, Optional[int]]:
        """Extract claimed problem counts from resume text
        Looks for patterns like "LeetCode (300+ problems, username: ...)"
        """
        logger.info("Extracting claimed problem counts from resume")
        
        claimed = {}
        
        # LeetCode: "LeetCode (300+ problems..."
        match = re.search(r"LeetCode\s*\(\s*(\d+)\+?\s*(?:problems|solved)", resume_text, re.IGNORECASE)
        if match:
            claimed["leetcode"] = int(match.group(1))
            logger.info(f"✅ Found LeetCode claimed: {claimed['leetcode']}")
        
        # GeeksforGeeks: "GeeksforGeeks (140+ problems..."
        match = re.search(r"GeeksforGeeks\s*\(\s*(\d+)\+?\s*(?:problems|solved)", resume_text, re.IGNORECASE)
        if match:
            claimed["geeksforgeeks"] = int(match.group(1))
            logger.info(f"✅ Found GeeksforGeeks claimed: {claimed['geeksforgeeks']}")
        
        # Codeforces: "Codeforces (XXX problems..."
        match = re.search(r"Codeforces\s*\(\s*(\d+)\+?\s*(?:problems|solved)", resume_text, re.IGNORECASE)
        if match:
            claimed["codeforces"] = int(match.group(1))
            logger.info(f"✅ Found Codeforces claimed: {claimed['codeforces']}")
        
        # CodeChef: "CodeChef (XXX problems..."
        match = re.search(r"CodeChef\s*\(\s*(\d+)\+?\s*(?:problems|solved)", resume_text, re.IGNORECASE)
        if match:
            claimed["codechef"] = int(match.group(1))
            logger.info(f"✅ Found CodeChef claimed: {claimed['codechef']}")
        
        if not claimed:
            logger.info("No claimed problem counts found in resume")
        
        return claimed
    
    def verify_leetcode(self, username: str) -> Dict[str, Any]:
        """Verify LeetCode profile using GraphQL API"""
        logger.info(f"Verifying LeetCode profile: {username}")
        
        # Check cache first
        cached = self._load_cache("leetcode", username)
        if cached:
            return cached
        
        try:
            query = """
                query getUserProfile($username: String!) {
                    allQuestionsCount {
                        difficulty
                        count
                    }
                    matchedUser(username: $username) {
                        username
                        profile {
                            realName
                            userAvatar
                        }
                        submitStats {
                            totalSubmissionNum {
                                difficulty
                                count
                            }
                            acSubmissionNum {
                                difficulty
                                count
                            }
                        }
                    }
                }
            """
            
            response = self.session.post(
                self.PLATFORMS["leetcode"]["api_url"],
                json={"query": query, "variables": {"username": username}},
                timeout=self.PLATFORMS["leetcode"]["timeout"]
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"].get("matchedUser"):
                    matched_user = data["data"]["matchedUser"]
                    
                    # Calculate total solved from AC submissions
                    ac_submissions = matched_user.get("submitStats", {}).get("acSubmissionNum", [])
                    total_solved = sum(item.get("count", 0) for item in ac_submissions)
                    
                    result = {
                        "verified": True,
                        "platform": "leetcode",
                        "username": username,
                        "actual": total_solved,
                        "profile_url": f"https://leetcode.com/u/{username}",
                        "real_name": matched_user.get("profile", {}).get("realName"),
                    }
                    
                    self._save_cache("leetcode", username, result)
                    logger.info(f"LeetCode verified: {username} ({total_solved} problems solved)")
                    return result
            
            logger.warning(f"LeetCode profile not found or API error: {username}")
            result = {"verified": False, "platform": "leetcode", "username": username}
            self._save_cache("leetcode", username, result)
            return result
        
        except requests.Timeout:
            logger.error(f"LeetCode API timeout for {username}")
            return {"verified": False, "platform": "leetcode", "username": username, "error": "timeout"}
        except Exception as e:
            logger.error(f"Error verifying LeetCode profile {username}: {str(e)}")
            return {"verified": False, "platform": "leetcode", "username": username, "error": str(e)}
    
    def verify_codeforces(self, username: str) -> Dict[str, Any]:
        """Verify Codeforces profile using official API"""
        logger.info(f"Verifying Codeforces profile: {username}")
        
        # Check cache first
        cached = self._load_cache("codeforces", username)
        if cached:
            return cached
        
        try:
            # Get user info
            response = self.session.get(
                f"{self.PLATFORMS['codeforces']['api_url']}?handles={username}",
                timeout=self.PLATFORMS["codeforces"]["timeout"]
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "OK" and data.get("result"):
                    user_info = data["result"][0]
                    
                    # Get solved count from submissions
                    submissions_response = self.session.get(
                        f"https://codeforces.com/api/user.status?handle={username}&from=1&count=1",
                        timeout=self.PLATFORMS["codeforces"]["timeout"]
                    )
                    
                    solved_count = 0
                    if submissions_response.status_code == 200:
                        submissions_data = submissions_response.json()
                        if submissions_data.get("status") == "OK":
                            # Count unique accepted problems
                            accepted_problems = set()
                            for submission in submissions_data.get("result", []):
                                if submission.get("verdict") == "OK":
                                    accepted_problems.add(submission.get("problem", {}).get("name", ""))
                            solved_count = len(accepted_problems)
                    
                    result = {
                        "verified": True,
                        "platform": "codeforces",
                        "username": username,
                        "actual": solved_count if solved_count > 0 else user_info.get("problemsSolved", 0),
                        "rating": user_info.get("rating", 0),
                        "max_rating": user_info.get("maxRating", 0),
                        "profile_url": f"https://codeforces.com/profile/{username}",
                    }
                    
                    self._save_cache("codeforces", username, result)
                    logger.info(f"Codeforces verified: {username} (rating: {result['rating']})")
                    return result
            
            logger.warning(f"Codeforces profile not found: {username}")
            result = {"verified": False, "platform": "codeforces", "username": username}
            self._save_cache("codeforces", username, result)
            return result
        
        except requests.Timeout:
            logger.error(f"Codeforces API timeout for {username}")
            return {"verified": False, "platform": "codeforces", "username": username, "error": "timeout"}
        except Exception as e:
            logger.error(f"Error verifying Codeforces profile {username}: {str(e)}")
            return {"verified": False, "platform": "codeforces", "username": username, "error": str(e)}
    
    def verify_geeksforgeeks(self, username: str) -> Dict[str, Any]:
        """Verify GeeksforGeeks profile by scraping"""
        logger.info(f"Verifying GeeksforGeeks profile: {username}")
        
        # Check cache first
        cached = self._load_cache("geeksforgeeks", username)
        if cached:
            return cached
        
        try:
            # Scrape GeeksforGeeks profile
            profile_url = f"https://www.geeksforgeeks.org/user/{username}"
            response = self.session.get(profile_url, timeout=self.PLATFORMS["geeksforgeeks"]["timeout"])
            
            if response.status_code == 200:
                # Extract problems solved count from HTML
                # Pattern: "Problems Solved" followed by number
                match = re.search(r'Problems?\s*Solved[:\s]*(\d+)', response.text, re.IGNORECASE)
                
                if match:
                    problems_solved = int(match.group(1))
                    
                    result = {
                        "verified": True,
                        "platform": "geeksforgeeks",
                        "username": username,
                        "actual": problems_solved,
                        "profile_url": profile_url,
                    }
                    
                    self._save_cache("geeksforgeeks", username, result)
                    logger.info(f"GeeksforGeeks verified: {username} ({problems_solved} problems)")
                    return result
            
            logger.warning(f"GeeksforGeeks profile not found or parse failed: {username}")
            result = {"verified": False, "platform": "geeksforgeeks", "username": username}
            self._save_cache("geeksforgeeks", username, result)
            return result
        
        except requests.Timeout:
            logger.error(f"GeeksforGeeks request timeout for {username}")
            return {"verified": False, "platform": "geeksforgeeks", "username": username, "error": "timeout"}
        except Exception as e:
            logger.error(f"Error verifying GeeksforGeeks profile {username}: {str(e)}")
            return {"verified": False, "platform": "geeksforgeeks", "username": username, "error": str(e)}
    
    def verify_codechef(self, username: str) -> Dict[str, Any]:
        """Verify CodeChef profile by scraping"""
        logger.info(f"Verifying CodeChef profile: {username}")
        
        # Check cache first
        cached = self._load_cache("codechef", username)
        if cached:
            return cached
        
        try:
            # Scrape CodeChef profile
            profile_url = f"https://www.codechef.com/users/{username}"
            response = self.session.get(profile_url, timeout=self.PLATFORMS["codechef"]["timeout"])
            
            if response.status_code == 200:
                # Extract problems solved count from HTML
                # Look for rating or problems solved
                match = re.search(r'Problems?\s*Solved[:\s]*(\d+)', response.text, re.IGNORECASE)
                
                if not match:
                    match = re.search(r'<strong>(\d+)</strong>.*?problems', response.text, re.IGNORECASE | re.DOTALL)
                
                if match:
                    problems_solved = int(match.group(1))
                    
                    result = {
                        "verified": True,
                        "platform": "codechef",
                        "username": username,
                        "actual": problems_solved,
                        "profile_url": profile_url,
                    }
                    
                    self._save_cache("codechef", username, result)
                    logger.info(f"CodeChef verified: {username} ({problems_solved} problems)")
                    return result
            
            logger.warning(f"CodeChef profile not found or parse failed: {username}")
            result = {"verified": False, "platform": "codechef", "username": username}
            self._save_cache("codechef", username, result)
            return result
        
        except requests.Timeout:
            logger.error(f"CodeChef request timeout for {username}")
            return {"verified": False, "platform": "codechef", "username": username, "error": "timeout"}
        except Exception as e:
            logger.error(f"Error verifying CodeChef profile {username}: {str(e)}")
            return {"verified": False, "platform": "codechef", "username": username, "error": str(e)}
    
    def compare_claimed_vs_actual(
        self,
        platform: str,
        actual_data: Dict[str, Any],
        claimed_count: Optional[int] = None
    ) -> Tuple[str, float]:
        """
        Compare claimed problems vs actual problems
        Returns (status, confidence_score)
        """
        if not actual_data.get("verified"):
            return "UNVERIFIED", 0.0
        
        actual = actual_data.get("actual", 0)
        
        # If no claimed count provided, just mark as verified
        if claimed_count is None:
            return "VERIFIED", 0.8  # Default confidence if no claim
        
        # Calculate difference
        difference = abs(actual - claimed_count)
        percentage_diff = (difference / claimed_count * 100) if claimed_count > 0 else 0
        
        if actual >= claimed_count:
            # Actual >= claimed, so it's verified
            confidence = 1.0 - (percentage_diff / 100)
            return "VERIFIED", max(0.7, confidence)
        elif percentage_diff <= 10:
            # Within 10%, minor mismatch
            confidence = 0.9 - (percentage_diff / 100)
            return "MINOR_MISMATCH", confidence
        else:
            # Major mismatch
            confidence = max(0.2, 0.8 - (percentage_diff / 100))
            return "MAJOR_MISMATCH", confidence
    
    async def verify_all_platforms(
        self,
        extracted_data: Dict[str, Any],
        claimed_problems: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Verify all competitive programming platforms
        
        claimed_problems: Dict mapping platform -> claimed problem count
        Example: {"leetcode": 300, "codeforces": 250}
        If not provided, will be extracted from resume text automatically.
        """
        logger.info("Starting competitive programming verification")
        
        resume_text = extracted_data.get("raw_text", "")
        
        # Extract usernames
        usernames = self.extract_usernames(resume_text)
        
        # Extract claimed problems if not provided
        if claimed_problems is None:
            claimed_problems = self.extract_claimed_problems(resume_text)
        
        if not usernames:
            logger.info("No competitive programming usernames found in resume")
            return {
                "platforms_verified": {},
                "total_verified": 0,
                "verification_summary": [],
            }
        
        verification_results = {}
        verification_summary = []
        
        # Verify each platform
        if "leetcode" in usernames and usernames["leetcode"]:
            actual_data = self.verify_leetcode(usernames["leetcode"])
            status, confidence = self.compare_claimed_vs_actual(
                "leetcode",
                actual_data,
                claimed_problems.get("leetcode") if claimed_problems else None
            )
            
            result = {
                "platform": "leetcode",
                "username": usernames["leetcode"],
                "claimed": claimed_problems.get("leetcode") if claimed_problems else None,
                "actual": actual_data.get("actual"),
                "status": status,
                "confidence_score": round(confidence, 2),
                "verified": actual_data.get("verified", False),
                "profile_url": actual_data.get("profile_url"),
            }
            verification_results["leetcode"] = result
            verification_summary.append(result)
        
        if "codeforces" in usernames and usernames["codeforces"]:
            actual_data = self.verify_codeforces(usernames["codeforces"])
            status, confidence = self.compare_claimed_vs_actual(
                "codeforces",
                actual_data,
                claimed_problems.get("codeforces") if claimed_problems else None
            )
            
            result = {
                "platform": "codeforces",
                "username": usernames["codeforces"],
                "claimed": claimed_problems.get("codeforces") if claimed_problems else None,
                "actual": actual_data.get("actual"),
                "status": status,
                "confidence_score": round(confidence, 2),
                "verified": actual_data.get("verified", False),
                "rating": actual_data.get("rating", 0),
                "profile_url": actual_data.get("profile_url"),
            }
            verification_results["codeforces"] = result
            verification_summary.append(result)
        
        if "geeksforgeeks" in usernames and usernames["geeksforgeeks"]:
            actual_data = self.verify_geeksforgeeks(usernames["geeksforgeeks"])
            status, confidence = self.compare_claimed_vs_actual(
                "geeksforgeeks",
                actual_data,
                claimed_problems.get("geeksforgeeks") if claimed_problems else None
            )
            
            result = {
                "platform": "geeksforgeeks",
                "username": usernames["geeksforgeeks"],
                "claimed": claimed_problems.get("geeksforgeeks") if claimed_problems else None,
                "actual": actual_data.get("actual"),
                "status": status,
                "confidence_score": round(confidence, 2),
                "verified": actual_data.get("verified", False),
                "profile_url": actual_data.get("profile_url"),
            }
            verification_results["geeksforgeeks"] = result
            verification_summary.append(result)
        
        if "codechef" in usernames and usernames["codechef"]:
            actual_data = self.verify_codechef(usernames["codechef"])
            status, confidence = self.compare_claimed_vs_actual(
                "codechef",
                actual_data,
                claimed_problems.get("codechef") if claimed_problems else None
            )
            
            result = {
                "platform": "codechef",
                "username": usernames["codechef"],
                "claimed": claimed_problems.get("codechef") if claimed_problems else None,
                "actual": actual_data.get("actual"),
                "status": status,
                "confidence_score": round(confidence, 2),
                "verified": actual_data.get("verified", False),
                "profile_url": actual_data.get("profile_url"),
            }
            verification_results["codechef"] = result
            verification_summary.append(result)
        
        # Calculate overall verification score
        verified_count = sum(1 for r in verification_summary if r.get("verified"))
        avg_confidence = (
            sum(r.get("confidence_score", 0) for r in verification_summary) / len(verification_summary)
            if verification_summary else 0
        )
        
        return {
            "platforms_verified": verification_results,
            "total_verified": verified_count,
            "total_platforms_checked": len(verification_summary),
            "average_confidence": round(avg_confidence, 2),
            "verification_summary": verification_summary,
        }
