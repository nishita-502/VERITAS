"""
Timeline Validator
Validates timeline consistency in resume claims
"""
from typing import Dict, List, Any, Tuple
from datetime import datetime
from src.core.config import CURRENT_YEAR
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class TimelineValidator:
    """Validate consistency of timelines in resume"""
    
    @staticmethod
    def parse_timeline(timeline_str: str) -> Tuple[int, int]:
        """Parse timeline string to (start_year, end_year)"""
        if not timeline_str:
            return None, None
        
        try:
            # Handle formats like "2021-2022", "2021 - 2022", "2021–2022"
            timeline_str = timeline_str.strip()
            
            # Split by various separators
            for sep in ["-", "–", "—"]:
                if sep in timeline_str:
                    parts = timeline_str.split(sep)
                    if len(parts) >= 2:
                        try:
                            start = int(parts[0].strip()[-4:])  # Get last 4 chars as year
                            end = int(parts[1].strip()[:4])    # Get first 4 chars as year
                            return start, end
                        except ValueError:
                            pass
            
            # Try to extract 4-digit year
            import re
            years = re.findall(r"20\d{2}", timeline_str)
            if len(years) >= 2:
                return int(years[0]), int(years[1])
            elif len(years) == 1:
                return int(years[0]), CURRENT_YEAR
        
        except Exception as e:
            logger.debug(f"Error parsing timeline '{timeline_str}': {str(e)}")
        
        return None, None
    
    @staticmethod
    def validate_project_timeline(
        project_name: str,
        claimed_timeline: str,
        github_repos: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Validate project timeline against GitHub history"""
        logger.info(f"Validating timeline for project: {project_name}")
        
        start, end = TimelineValidator.parse_timeline(claimed_timeline)
        
        if not start or not end:
            logger.warning(f"Could not parse timeline: {claimed_timeline}")
            return {
                "project": project_name,
                "claimed_timeline": claimed_timeline,
                "status": "unparseable",
                "verified": False,
            }
        
        # Find matching repo
        matching_repo = None
        for repo in github_repos:
            repo_name = repo.get("name", "").lower()
            project_lower = project_name.lower()
            
            if project_lower in repo_name or repo_name in project_lower:
                matching_repo = repo
                break
        
        if not matching_repo:
            logger.warning(f"No matching GitHub repo found for project: {project_name}")
            return {
                "project": project_name,
                "claimed_timeline": claimed_timeline,
                "status": "no_matching_repo",
                "verified": False,
            }
        
        # Check if creation date matches
        created_at = matching_repo.get("created_at", "")
        try:
            created_year = int(created_at.split("-")[0])
            
            timeline_match = (start - 1 <= created_year <= start + 1)  # Allow 1 year tolerance
            
            result = {
                "project": project_name,
                "claimed_timeline": f"{start}-{end}",
                "repo_created": created_at,
                "created_year": created_year,
                "status": "verified" if timeline_match else "mismatch",
                "verified": timeline_match,
                "timeline_match": timeline_match,
            }
            
            logger.info(f"Timeline validation result: {result['status']}")
            return result
        
        except Exception as e:
            logger.error(f"Error validating timeline: {str(e)}")
            return {
                "project": project_name,
                "claimed_timeline": claimed_timeline,
                "status": "error",
                "verified": False,
                "error": str(e),
            }
    
    @staticmethod
    def validate_work_experience_timeline(
        position: str,
        company: str,
        start_year: int,
        end_year: int,
        github_activity: Dict[str, int],
    ) -> Dict[str, Any]:
        """Validate work experience timeline against GitHub activity"""
        logger.info(f"Validating work experience: {position} at {company} ({start_year}-{end_year})")
        
        if not start_year or not end_year:
            logger.warning(f"Invalid timeline for {company} work experience")
            return {
                "company": company,
                "position": position,
                "timeline": f"{start_year}-{end_year}",
                "status": "invalid_timeline",
                "verified": False,
            }
        
        # Check if GitHub has commits during claimed employment period
        relevant_activity = 0
        
        if github_activity and isinstance(github_activity, dict):
            for year_str, count in github_activity.items():
                try:
                    year = int(year_str)
                    if start_year <= year <= end_year:
                        relevant_activity += count
                except (ValueError, TypeError):
                    pass
        
        has_activity = relevant_activity > 0
        
        result = {
            "company": company,
            "position": position,
            "claimed_timeline": f"{start_year}-{end_year}",
            "github_activity_during_period": relevant_activity,
            "status": "verified" if has_activity else "no_evidence",
            "verified": has_activity,
        }
        
        logger.info(f"Work timeline validation: {result['status']}")
        return result
    
    @staticmethod
    def validate_overall_consistency(
        projects: List[Dict[str, Any]],
        work_experiences: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Validate overall timeline consistency (no overlaps, logical order)"""
        logger.info("Validating overall timeline consistency")
        
        all_timelines = []
        
        # Add project timelines
        for project in projects:
            if project.get("timeline"):
                start, end = TimelineValidator.parse_timeline(project["timeline"])
                if start and end:
                    all_timelines.append({
                        "type": "project",
                        "name": project.get("name", "Unknown"),
                        "start": start,
                        "end": end,
                    })
        
        # Add work experience timelines
        for work in work_experiences:
            if work.get("start_year"):
                all_timelines.append({
                    "type": "work",
                    "name": work.get("company", "Unknown"),
                    "start": work.get("start_year"),
                    "end": work.get("end_year", CURRENT_YEAR),
                })
        
        # Check for overlaps with warnings
        overlaps = []
        for i, timeline1 in enumerate(all_timelines):
            for timeline2 in all_timelines[i + 1:]:
                if (timeline1["start"] <= timeline2["end"] and timeline2["start"] <= timeline1["end"]):
                    overlaps.append({
                        "type1": f"{timeline1['type']}: {timeline1['name']}",
                        "type2": f"{timeline2['type']}: {timeline2['name']}",
                        "period": f"{max(timeline1['start'], timeline2['start'])}-{min(timeline1['end'], timeline2['end'])}",
                    })
        
        # Check if timelines are chronological
        sorted_timelines = sorted(all_timelines, key=lambda x: x["start"])
        is_chronological = sorted_timelines == all_timelines
        
        result = {
            "total_timeline_entries": len(all_timelines),
            "overlapping_periods": overlaps,
            "is_chronological": is_chronological,
            "consistency_score": 100 - (len(overlaps) * 10),  # Deduct points for overlaps
        }
        
        result["consistency_score"] = max(0, result["consistency_score"])
        
        logger.info(f"Overall consistency: {len(overlaps)} overlaps found, chronological: {is_chronological}")
        return result
