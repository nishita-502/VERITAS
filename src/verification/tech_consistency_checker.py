"""
Technology Consistency Checker
Verifies consistency between claimed and demonstrated technologies
"""
from typing import Dict, List, Any, Tuple
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class TechConsistencyChecker:
    """Check consistency between claimed and demonstrated tech skills"""
    
    # Technology mappings for grouping related techs
    TECH_GROUPS = {
        "frontend": ["react", "vue", "angular", "svelte", "html", "css", "javascript", "typescript", "next", "nuxt"],
        "backend": ["python", "java", "go", "rust", "cpp", "c++", "node", "nodejs", "express", "django", "flask"],
        "data_science": ["python", "r", "pandas", "numpy", "sklearn", "tensorflow", "keras", "pytorch", "spark"],
        "databases": ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "dynamodb"],
        "cloud": ["aws", "gcp", "azure", "kubernetes", "docker"],
        "ml": ["tensorflow", "pytorch", "keras", "scikit-learn", "xgboost"],
        "devops": ["docker", "kubernetes", "jenkins", "git", "aws", "gcp", "azure"],
    }
    
    TECH_SYNONYMS = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "cpp": "c++",
        "c++": "cpp",
        "nodejs": "node",
        "react.js": "react",
        "vue.js": "vue",
        "django": "python",
        "flask": "python",
        "fastapi": "python",
        "express": "javascript",
        "neural networks": "deep learning",
        "keras": "tensorflow",
        "sklearn": "scikit-learn",
        "tf": "tensorflow",
        "pt": "pytorch",
    }
    
    @staticmethod
    def normalize_tech(tech: str) -> str:
        """Normalize technology name"""
        tech_lower = tech.strip().lower()
        
        # Apply synonyms
        if tech_lower in TechConsistencyChecker.TECH_SYNONYMS:
            return TechConsistencyChecker.TECH_SYNONYMS[tech_lower]
        
        return tech_lower
    
    @staticmethod
    def check_consistency(
        claimed_skills: List[str],
        demonstrated_technologies: Dict[str, int],
        project_technologies: List[str],
        work_technologies: List[str],
    ) -> Dict[str, Any]:
        """Check consistency between claimed and demonstrated skills"""
        logger.info("Checking technology consistency")
        
        # Normalize all inputs
        claimed_normalized = [TechConsistencyChecker.normalize_tech(s) for s in claimed_skills]
        demonstrated_normalized = {
            TechConsistencyChecker.normalize_tech(k): v
            for k, v in demonstrated_technologies.items()
        }
        project_normalized = [TechConsistencyChecker.normalize_tech(t) for t in project_technologies]
        work_normalized = [TechConsistencyChecker.normalize_tech(t) for t in work_technologies]
        
        all_demonstrated = set(demonstrated_normalized.keys()) | set(project_normalized) | set(work_normalized)
        
        consistency_results = {
            "verified_skills": [],
            "partially_verified_skills": [],
            "unverified_skills": [],
            "undeclared_technologies": [],
            "consistency_score": 0.0,
        }
        
        # Check each claimed skill
        for skill in claimed_normalized:
            if skill in all_demonstrated:
                # Check if it's in demonstrated (GitHub)
                if skill in demonstrated_normalized:
                    consistency_results["verified_skills"].append({
                        "skill": skill,
                        "found_in": "github_repos",
                        "repo_count": demonstrated_normalized[skill],
                    })
                # Check if in projects
                elif skill in project_normalized:
                    consistency_results["partially_verified_skills"].append({
                        "skill": skill,
                        "found_in": "projects",
                    })
                # Check if in work
                elif skill in work_normalized:
                    consistency_results["partially_verified_skills"].append({
                        "skill": skill,
                        "found_in": "work_experience",
                    })
            else:
                consistency_results["unverified_skills"].append(skill)
        
        # Check for undeclared technologies
        for tech in all_demonstrated:
            if tech not in claimed_normalized:
                consistency_results["undeclared_technologies"].append(tech)
        
        # Calculate consistency score
        total_claimed = len(claimed_normalized)
        if total_claimed > 0:
            verified = len(consistency_results["verified_skills"])
            partial = len(consistency_results["partially_verified_skills"])
            
            consistency_results["consistency_score"] = (
                (verified * 100 + partial * 70) / (total_claimed * 100)
            )
        
        logger.info(f"Consistency check complete. Score: {consistency_results['consistency_score']:.2f}")
        return consistency_results
    
    @staticmethod
    def detect_red_flags(
        claimed_skills: List[str],
        consistency_report: Dict[str, Any],
        demonstrated_technologies: Dict[str, int],
    ) -> List[Dict[str, str]]:
        """Detect red flags in technology claims"""
        logger.info("Detecting tech consistency red flags")
        
        red_flags = []
        
        # Flag: Expert claim with no GitHub evidence
        unverified_count = len(consistency_report.get("unverified_skills", []))
        if unverified_count > 0:
            unverified_percentage = (unverified_count / len(claimed_skills) * 100) if claimed_skills else 0
            
            if unverified_percentage > 50:
                red_flags.append({
                    "type": "high_unverified_rate",
                    "severity": "high",
                    "description": f"{unverified_percentage:.0f}% of claimed skills have no GitHub evidence",
                    "skills": consistency_report["unverified_skills"],
                })
        
        # Flag: Too many undeclared technologies
        if len(consistency_report.get("undeclared_technologies", [])) > 0:
            red_flags.append({
                "type": "undeclared_technologies",
                "severity": "medium",
                "description": "GitHub shows technologies not mentioned in claims",
                "technologies": consistency_report["undeclared_technologies"][:5],
            })
        
        # Flag: Single repo everything
        if demonstrated_technologies and len(demonstrated_technologies) > 0:
            max_repos = max(demonstrated_technologies.values())
            if max_repos == 1 and len(demonstrated_technologies) == 1:
                red_flags.append({
                    "type": "single_repo_only",
                    "severity": "high",
                    "description": "All GitHub activity in a single repository",
                })
        
        logger.info(f"Found {len(red_flags)} red flags")
        return red_flags
