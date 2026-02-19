"""
GitHub Verification Agent
Uses real GitHub REST API to verify claims with caching and rate limit optimization
"""
import requests
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from src.core.config import GITHUB_API_BASE, GITHUB_TOKEN, GITHUB_TIMEOUT
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Configuration for API optimization
MAX_REPOS = 10  # Only fetch top 10 most recent repos
MAX_CONTRIBUTOR_REPOS = 2  # Only fetch contributors for top 2 repos
CACHE_DIR = Path("cache")
CACHE_EXPIRY_HOURS = 24

class GitHubAgent:
    """Verify GitHub claims using real API with caching and rate limit optimization"""
    
    def __init__(self):
        self.base_url = GITHUB_API_BASE
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "VERITAS-Resume-Verification",
        }
        
        # Create cache directory if it doesn't exist
        CACHE_DIR.mkdir(exist_ok=True)
        
        if GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {GITHUB_TOKEN}"
            logger.info("GitHub Agent initialized with personal access token")
        else:
            logger.warning("GitHub Agent: No token provided, using public API (rate-limited)")
    
    def _get_cache_path(self, username: str) -> Path:
        """Get cache file path for a GitHub user"""
        return CACHE_DIR / f"github_{username}.json"
    
    def _load_cache(self, username: str) -> Optional[Dict[str, Any]]:
        """Load cached GitHub data if valid"""
        cache_path = self._get_cache_path(username)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            timestamp = datetime.fromisoformat(cache_data.get("timestamp", ""))
            if datetime.now() - timestamp > timedelta(hours=CACHE_EXPIRY_HOURS):
                logger.info(f"Cache for {username} expired, will refresh")
                return None
            
            logger.info(f"Loaded cached GitHub data for {username}")
            return cache_data["data"]
        
        except Exception as e:
            logger.warning(f"Error loading cache for {username}: {str(e)}")
            return None
    
    def _save_cache(self, username: str, data: Dict[str, Any]) -> None:
        """Save GitHub data to cache"""
        cache_path = self._get_cache_path(username)
        
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Cached GitHub data for {username}")
        
        except Exception as e:
            logger.warning(f"Error saving cache for {username}: {str(e)}")
    
    def verify_user_exists(self, username: str) -> Dict[str, Any]:
        """Verify GitHub user exists and get profile info (with caching)"""
        logger.info(f"Verifying GitHub user: {username}")
        
        try:
            url = f"{self.base_url}/users/{username}"
            response = requests.get(url, headers=self.headers, timeout=GITHUB_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"GitHub user verified: {username}")
                
                return {
                    "exists": True,
                    "username": username,
                    "name": data.get("name"),
                    "bio": data.get("bio"),
                    "location": data.get("location"),
                    "public_repos": data.get("public_repos", 0),
                    "followers": data.get("followers", 0),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                }
            elif response.status_code == 404:
                logger.warning(f"GitHub user not found: {username}")
                return {"exists": False, "username": username}
            else:
                logger.error(f"GitHub API error: {response.status_code}")
                return {"exists": None, "username": username, "error": response.status_code}
        
        except Exception as e:
            logger.error(f"Error verifying GitHub user {username}: {str(e)}")
            return {"exists": None, "username": username, "error": str(e)}
    
    def get_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Get top N recently updated repositories for a user (optimized for API rate limits)"""
        logger.info(f"Fetching top {MAX_REPOS} repositories for: {username}")
        
        try:
            # Use sort=pushed to get most recently updated repos, limit to MAX_REPOS
            url = f"{self.base_url}/users/{username}/repos?per_page={MAX_REPOS}&sort=pushed&order=desc"
            response = requests.get(url, headers=self.headers, timeout=GITHUB_TIMEOUT)
            
            if response.status_code == 200:
                repos = response.json()
                logger.info(f"Found {len(repos)} repositories for {username} (limited to {MAX_REPOS})")
                
                return [{
                    "name": repo.get("name"),
                    "url": repo.get("html_url"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "stargazers_count": repo.get("stargazers_count", 0),
                    "forks_count": repo.get("forks_count", 0),
                    "size": repo.get("size", 0),
                    "created_at": repo.get("created_at"),
                    "updated_at": repo.get("updated_at"),
                    "pushed_at": repo.get("pushed_at"),
                } for repo in repos]
            else:
                logger.error(f"Error fetching repos: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error fetching repositories for {username}: {str(e)}")
            return []
    
    def get_repo_languages(self, username: str, repo_name: str) -> Dict[str, int]:
        """Get programming languages used in a repository"""
        logger.info(f"Fetching languages for: {username}/{repo_name}")
        
        try:
            url = f"{self.base_url}/repos/{username}/{repo_name}/languages"
            response = requests.get(url, headers=self.headers, timeout=GITHUB_TIMEOUT)
            
            if response.status_code == 200:
                languages = response.json()
                logger.info(f"Found {len(languages)} languages in {username}/{repo_name}")
                return languages
            else:
                logger.error(f"Error fetching languages: {response.status_code}")
                return {}
        
        except Exception as e:
            logger.error(f"Error fetching languages: {str(e)}")
            return {}
    
    def get_repo_commits(self, username: str, repo_name: str) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Avoid expensive commit API calls.
        Use repository metadata instead (size, updated_at, pushed_at).
        Returns empty list to maintain interface compatibility.
        """
        logger.debug(f"Commit fetching disabled for rate limit optimization (was: {username}/{repo_name})")
        return []
    
    def verify_tech_stack(self, username: str, claimed_skills: List[str]) -> Dict[str, Any]:
        """Verify claimed technologies appear in user's repositories (optimized)"""
        logger.info(f"Verifying tech stack for {username}: {claimed_skills}")
        
        repos = self.get_repositories(username)  # Already limited to MAX_REPOS
        found_techs = {}
        
        # Only fetch languages for top MAX_REPOS (already limited)
        for i, repo in enumerate(repos):
            if i >= MAX_REPOS:
                break
            
            languages = self.get_repo_languages(username, repo["name"])
            for lang in languages:
                if lang not in found_techs:
                    found_techs[lang] = 0
                found_techs[lang] += 1
        
        verified_skills = []
        unverified_skills = []
        
        for skill in claimed_skills:
            # Normalize skill names
            skill_lower = skill.lower()
            found = False
            
            for tech in found_techs:
                if skill_lower in tech.lower() or tech.lower() in skill_lower:
                    verified_skills.append({
                        "claimed": skill,
                        "found": tech,
                        "count": found_techs[tech],
                    })
                    found = True
                    break
            
            if not found:
                unverified_skills.append(skill)
        
        result = {
            "username": username,
            "verified_skills": verified_skills,
            "unverified_skills": unverified_skills,
            "verification_rate": len(verified_skills) / len(claimed_skills) if claimed_skills else 0,
            "all_found_technologies": found_techs,
        }
        
        logger.info(f"Tech verification complete: {len(verified_skills)}/{len(claimed_skills)} verified")
        return result
    
    def verify_project_claims(self, username: str, claimed_projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify claimed projects exist on GitHub (optimized - no commit calls)"""
        logger.info(f"Verifying {len(claimed_projects)} project claims for {username}")
        
        repos = self.get_repositories(username)  # Already limited to MAX_REPOS
        repo_names = [r["name"].lower() for r in repos]
        
        verification_results = {
            "username": username,
            "total_claimed": len(claimed_projects),
            "total_repos": len(repos),
            "matched_projects": [],
            "unmatched_projects": [],
        }
        
        for project in claimed_projects:
            project_name = project.get("name", "").lower()
            matched = False
            
            for repo in repos:
                if project_name in repo["name"].lower() or repo["name"].lower() in project_name:
                    # Found matching repo - use metadata instead of commit calls
                    languages = self.get_repo_languages(username, repo["name"])
                    
                    verification_results["matched_projects"].append({
                        "claimed_name": project.get("name"),
                        "repo_name": repo["name"],
                        "repo_url": repo["url"],
                        "description_match": project.get("description"),
                        "languages": languages,
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "size_kb": repo["size"],
                        "updated": repo["updated_at"],
                        "pushed": repo["pushed_at"],
                    })
                    matched = True
                    break
            
            if not matched:
                verification_results["unmatched_projects"].append({
                    "claimed_name": project.get("name"),
                    "claimed_technologies": project.get("technologies", []),
                })
        
        verification_results["match_rate"] = len(verification_results["matched_projects"]) / len(claimed_projects) if claimed_projects else 0
        
        logger.info(f"Project verification complete: {len(verification_results['matched_projects'])}/{len(claimed_projects)} matched")
        return verification_results
    
    def get_contribution_percentage(self, username: str, repo_name: str) -> float:
        """
        Estimate user's contribution to a repository using metadata.
        DEPRECATED: Commit API calls are disabled for rate limit optimization.
        Uses repository size as a proxy metric.
        """
        logger.info(f"Estimating contribution for {username} in {repo_name}")
        
        try:
            # Get repo metadata
            url = f"{self.base_url}/repos/{username}/{repo_name}"
            response = requests.get(url, headers=self.headers, timeout=GITHUB_TIMEOUT)
            
            if response.status_code == 200:
                repo = response.json()
                # Use repository size as a proxy for contribution
                # Larger repos = more substantial contribution
                size = repo.get("size", 0)
                forks = repo.get("forks_count", 0)
                
                # Simple heuristic: if user is owner and repo is substantial, assume high contribution
                estimated_contribution = min(100.0, (size / 1000.0) * 10) if size > 0 else 0.0
                
                logger.info(f"Estimated contribution: {estimated_contribution:.2f}%")
                return estimated_contribution
            else:
                return 0.0
        
        except Exception as e:
            logger.error(f"Error estimating contribution: {str(e)}")
            return 0.0
