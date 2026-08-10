"""
GitHub Verification Agent
Uses real GitHub REST API to verify claims with caching and targeted repository search
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from src.core.config import GITHUB_API_BASE, GITHUB_TOKEN, GITHUB_TIMEOUT
from src.core.logging_config import get_logger

logger = get_logger(__name__)

CACHE_DIR = Path("cache")
CACHE_EXPIRY_HOURS = 24
MAX_SEARCH_RESULTS = 5


class GitHubAgent:
    """Verify GitHub claims using real API with caching and rate limit optimization."""

    def __init__(self):
        self.base_url = GITHUB_API_BASE.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "VERITAS-Resume-Verification",
            }
        )

        CACHE_DIR.mkdir(exist_ok=True)

        if GITHUB_TOKEN:
            self.session.headers["Authorization"] = f"token {GITHUB_TOKEN}"
            logger.info("GitHub Agent initialized with personal access token")
        else:
            logger.warning("GitHub Agent: No token provided, using public API (rate-limited)")

    @staticmethod
    def sanitize_github_username(username: Optional[str]) -> str:
        """Normalize handles such as @user and https://github.com/user."""

        if not username:
            return ""

        cleaned = username.strip()
        cleaned = re.sub(r"(?i)^https?://(?:www\.)?github\.com/", "", cleaned)
        cleaned = cleaned.split("?")[0].split("#")[0].rstrip("/")
        cleaned = cleaned.lstrip("@").strip()
        cleaned = cleaned.split("/")[0]
        cleaned = re.sub(r"[^A-Za-z0-9_-]", "", cleaned)
        return cleaned

    def _get_cache_path(self, username: str, suffix: str) -> Path:
        return CACHE_DIR / f"github_{username}_{suffix}.json"

    def _load_cache(self, username: str, suffix: str) -> Optional[Dict[str, Any]]:
        cache_path = self._get_cache_path(username, suffix)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as handle:
                cache_data = json.load(handle)

            timestamp = datetime.fromisoformat(cache_data.get("timestamp", ""))
            if datetime.now() - timestamp > timedelta(hours=CACHE_EXPIRY_HOURS):
                return None

            return cache_data.get("data")
        except Exception as exc:
            logger.warning("Error loading cache for %s (%s): %s", username, suffix, exc)
            return None

    def _save_cache(self, username: str, suffix: str, data: Dict[str, Any]) -> None:
        cache_path = self._get_cache_path(username, suffix)
        try:
            cache_data = {"timestamp": datetime.now().isoformat(), "data": data}
            with open(cache_path, "w", encoding="utf-8") as handle:
                json.dump(cache_data, handle, indent=2)
        except Exception as exc:
            logger.warning("Error saving cache for %s (%s): %s", username, suffix, exc)

    def _get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        response = self.session.get(f"{self.base_url}{path}", params=params, timeout=GITHUB_TIMEOUT)
        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            logger.warning("GitHub API rate limit reached")
        return response

    def verify_user_exists(self, username: str) -> Dict[str, Any]:
        """Verify GitHub user exists and get profile info."""

        clean_username = self.sanitize_github_username(username)
        logger.info("Verifying GitHub user: %s -> %s", username, clean_username)

        if not clean_username:
            return {"exists": False, "username": username, "clean_username": ""}

        cached = self._load_cache(clean_username, "profile")
        if cached:
            return cached

        try:
            response = self._get(f"/users/{clean_username}")

            if response.status_code == 200:
                data = response.json()
                result = {
                    "exists": True,
                    "username": clean_username,
                    "clean_username": clean_username,
                    "name": data.get("name"),
                    "bio": data.get("bio"),
                    "location": data.get("location"),
                    "public_repos": data.get("public_repos", 0),
                    "followers": data.get("followers", 0),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "html_url": data.get("html_url"),
                }
                self._save_cache(clean_username, "profile", result)
                return result

            if response.status_code == 404:
                return {"exists": False, "username": clean_username, "clean_username": clean_username}

            return {
                "exists": None,
                "username": clean_username,
                "clean_username": clean_username,
                "error": response.status_code,
            }
        except Exception as exc:
            logger.error("Error verifying GitHub user %s: %s", clean_username, exc)
            return {"exists": None, "username": clean_username, "clean_username": clean_username, "error": str(exc)}

    def search_repositories(self, username: str, project_name: str, max_results: int = MAX_SEARCH_RESULTS) -> List[Dict[str, Any]]:
        """Search repositories owned by a user for a specific project name."""

        clean_username = self.sanitize_github_username(username)
        clean_project = (project_name or "").strip()
        if not clean_username or not clean_project:
            return []

        query = f"user:{clean_username} {clean_project}"
        try:
            response = self._get(
                "/search/repositories",
                params={"q": query, "per_page": max_results, "sort": "updated", "order": "desc"},
            )
            if response.status_code != 200:
                logger.warning("GitHub repository search failed for %s: %s", clean_project, response.status_code)
                return []

            payload = response.json()
            items = payload.get("items", []) if isinstance(payload, dict) else []
            return [
                {
                    "name": item.get("name"),
                    "full_name": item.get("full_name"),
                    "url": item.get("html_url"),
                    "description": item.get("description"),
                    "language": item.get("language"),
                    "languages_url": item.get("languages_url"),
                    "stargazers_count": item.get("stargazers_count", 0),
                    "forks_count": item.get("forks_count", 0),
                    "size": item.get("size", 0),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "pushed_at": item.get("pushed_at"),
                }
                for item in items
            ]
        except Exception as exc:
            logger.error("Error searching repositories for %s/%s: %s", clean_username, clean_project, exc)
            return []

    def get_repo_languages(self, repo_full_name: str) -> Dict[str, int]:
        """Get programming languages used in a repository by full name."""

        if not repo_full_name or "/" not in repo_full_name:
            return {}

        try:
            response = self._get(f"/repos/{repo_full_name}/languages")
            if response.status_code == 200:
                languages = response.json()
                return languages if isinstance(languages, dict) else {}
            return {}
        except Exception as exc:
            logger.error("Error fetching languages for %s: %s", repo_full_name, exc)
            return {}

    def get_repo_commits(self, username: str, repo_name: str) -> List[Dict[str, Any]]:
        """Commit fetching is disabled to avoid expensive API usage."""

        logger.debug("Commit fetching disabled for rate limit optimization (was: %s/%s)", username, repo_name)
        return []

    @staticmethod
    def _is_semantic_match(claimed: str, candidate: str) -> bool:
        claimed_lower = claimed.lower().strip()
        candidate_lower = candidate.lower().strip()
        return claimed_lower == candidate_lower or claimed_lower in candidate_lower or candidate_lower in claimed_lower

    def _best_repo_match(self, project: Dict[str, Any], repositories: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        project_name = (project.get("name") or "").strip().lower()
        project_description = (project.get("description") or "").strip().lower()
        if not project_name:
            return None

        best_repo = None
        best_score = 0.0
        for repo in repositories:
            repo_name = (repo.get("name") or "").lower()
            description = (repo.get("description") or "").lower()
            score = 0.0
            if self._is_semantic_match(project_name, repo_name):
                score += 0.7
            if project_description and project_description[:30] and project_description[:30] in description:
                score += 0.2
            if any(token and token in repo_name for token in project_name.split()):
                score += 0.1

            if score > best_score:
                best_score = score
                best_repo = repo

        if best_score >= 0.35:
            return best_repo
        return None

    def verify_project_claims(self, username: str, claimed_projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify claimed projects using targeted search for each project name."""

        clean_username = self.sanitize_github_username(username)
        logger.info("Verifying %s project claims for %s", len(claimed_projects), clean_username)

        profile = self.verify_user_exists(clean_username)
        result = {
            "username": clean_username,
            "profile": profile,
            "total_claimed": len(claimed_projects),
            "matched_projects": [],
            "unmatched_projects": [],
            "language_footprint": {},
            "search_queries": [],
            "match_rate": 0.0,
            "verification_boost": 0.0,
        }

        if not profile.get("exists"):
            return result

        aggregate_languages: Dict[str, int] = {}
        for project in claimed_projects or []:
            if not isinstance(project, dict):
                continue

            project_name = project.get("name") or project.get("title") or ""
            search_results = self.search_repositories(clean_username, project_name)
            result["search_queries"].append(project_name)

            best_repo = self._best_repo_match(project, search_results)
            if not best_repo:
                result["unmatched_projects"].append(
                    {
                        "claimed_name": project_name,
                        "claimed_technologies": project.get("technologies", []),
                        "search_results": [repo.get("full_name") for repo in search_results[:3]],
                    }
                )
                continue

            languages = self.get_repo_languages(best_repo.get("full_name", ""))
            for language, byte_count in languages.items():
                aggregate_languages[language] = aggregate_languages.get(language, 0) + int(byte_count or 0)

            top_languages = sorted(languages.items(), key=lambda item: item[1], reverse=True)[:5]
            result["matched_projects"].append(
                {
                    "claimed_name": project_name,
                    "repo_name": best_repo.get("name"),
                    "repo_full_name": best_repo.get("full_name"),
                    "repo_url": best_repo.get("url"),
                    "repo_description": best_repo.get("description"),
                    "search_result_count": len(search_results),
                    "match_reason": "targeted_search_match",
                    "top_languages": top_languages,
                    "languages": languages,
                    "stars": best_repo.get("stargazers_count", 0),
                    "forks": best_repo.get("forks_count", 0),
                    "size_kb": best_repo.get("size", 0),
                    "updated": best_repo.get("updated_at"),
                    "pushed": best_repo.get("pushed_at"),
                }
            )

        total = len(claimed_projects) if claimed_projects else 0
        matched = len(result["matched_projects"])
        result["match_rate"] = matched / total if total else 0.0
        result["language_footprint"] = aggregate_languages
        result["verification_boost"] = min(100.0, matched * 20.0)
        return result

    def verify_tech_stack(
        self,
        username: str,
        claimed_skills: List[str],
        project_claims: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Verify claimed technologies against language footprints from targeted project matches."""

        clean_username = self.sanitize_github_username(username)
        logger.info("Verifying tech stack for %s: %s", clean_username, claimed_skills)

        project_verification = self.verify_project_claims(clean_username, project_claims or []) if project_claims else {
            "matched_projects": [],
            "unmatched_projects": [],
            "language_footprint": {},
            "match_rate": 0.0,
            "verification_boost": 0.0,
        }

        language_footprint = project_verification.get("language_footprint", {}) or {}
        verified_skills: List[Dict[str, Any]] = []
        partially_verified_skills: List[Dict[str, Any]] = []
        unverified_skills: List[str] = []

        normalized_languages = list(language_footprint.keys())
        for skill in claimed_skills or []:
            skill_lower = skill.lower().strip()
            matched_language = None
            match_type = None

            for language in normalized_languages:
                language_lower = language.lower().strip()
                if self._is_semantic_match(skill_lower, language_lower):
                    matched_language = language
                    match_type = "direct" if skill_lower == language_lower else "semantic"
                    break

            if matched_language:
                if match_type == "direct":
                    verified_skills.append(
                        {
                            "skill": skill,
                            "matched_language": matched_language,
                            "match_type": match_type,
                            "repo_mentions": language_footprint.get(matched_language, 0),
                        }
                    )
                else:
                    partially_verified_skills.append(
                        {
                            "skill": skill,
                            "matched_language": matched_language,
                            "match_type": match_type,
                            "repo_mentions": language_footprint.get(matched_language, 0),
                        }
                    )
            else:
                unverified_skills.append(skill)

        total_claims = len(claimed_skills) if claimed_skills else 0
        verified_count = len(verified_skills)
        partial_count = len(partially_verified_skills)
        verification_rate = (verified_count + partial_count * 0.75) / total_claims if total_claims else 0.0

        return {
            "username": clean_username,
            "verified_skills": verified_skills,
            "partially_verified_skills": partially_verified_skills,
            "unverified_skills": unverified_skills,
            "verification_rate": verification_rate,
            "language_footprint": language_footprint,
            "project_verification": project_verification,
            "verified_repository_count": len(project_verification.get("matched_projects", [])),
            "verified_language_count": len(language_footprint),
        }

    def get_contribution_percentage(self, username: str, repo_name: str) -> float:
        """Estimate contribution using repository metadata when a specific repo is known."""

        clean_username = self.sanitize_github_username(username)
        if not clean_username or not repo_name:
            return 0.0

        try:
            response = self._get(f"/repos/{clean_username}/{repo_name}")
            if response.status_code != 200:
                return 0.0

            repo = response.json()
            size = repo.get("size", 0)
            estimated_contribution = min(100.0, (size / 1000.0) * 10) if size > 0 else 0.0
            return estimated_contribution
        except Exception as exc:
            logger.error("Error estimating contribution: %s", exc)
            return 0.0
