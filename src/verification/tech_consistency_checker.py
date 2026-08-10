"""
Technology Consistency Checker
Verifies consistency between claimed and demonstrated technologies
"""
from typing import Dict, List, Any, Tuple, Set
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class TechConsistencyChecker:
    """Check consistency between claimed and demonstrated tech skills"""
    
    # Technology mappings for grouping related techs (SEMANTIC ECOSYSTEM GROUPS)
    TECH_GROUPS = {
        "frontend": ["react", "vue", "angular", "svelte", "html", "css", "javascript", "typescript", "next", "nuxt", "webpack", "tailwind"],
        "backend": ["python", "java", "go", "rust", "cpp", "c++", "node", "nodejs", "express", "django", "flask", "fastapi"],
        "data_science": ["python", "r", "pandas", "numpy", "sklearn", "tensorflow", "keras", "pytorch", "spark", "jupyter"],
        "databases": ["sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch", "dynamodb", "sqlite"],
        "cloud": ["aws", "gcp", "google cloud", "azure", "kubernetes", "docker", "terraform"],
        "ml": ["tensorflow", "pytorch", "keras", "scikit-learn", "xgboost", "deep learning", "machine learning"],
        "devops": ["docker", "kubernetes", "jenkins", "git", "aws", "gcp", "azure", "ci/cd"],
        "mobile": ["ios", "android", "swift", "kotlin", "react native", "flutter"],
    }
    
    # Semantic tech mapping - maps framework/tools to their underlying technologies
    TECH_SEMANTIC_MAPPING = {
        # JavaScript ecosystem
        "react": ["javascript", "frontend"],
        "react native": ["javascript", "mobile"],
        "next.js": ["javascript", "react", "frontend"],
        "next": ["javascript", "react", "frontend"],
        "nuxt": ["javascript", "vue", "frontend"],
        "vue": ["javascript", "frontend"],
        "angular": ["javascript", "typescript", "frontend"],
        "svelte": ["javascript", "frontend"],
        "express": ["javascript", "nodejs", "backend"],
        "node.js": ["javascript", "backend"],
        "nodejs": ["javascript", "backend"],
        
        # Python ecosystem
        "django": ["python", "backend"],
        "flask": ["python", "backend"],
        "fastapi": ["python", "backend"],
        "pandas": ["python", "data science"],
        "numpy": ["python", "data science"],
        "scikit-learn": ["python", "machine learning"],
        "sklearn": ["python", "machine learning"],
        "tensorflow": ["python", "machine learning", "deep learning"],
        "pytorch": ["python", "machine learning", "deep learning"],
        "keras": ["python", "tensorflow", "machine learning"],
        "flask": ["python", "backend"],
        "jupyter": ["python", "data science"],
        
        # Java ecosystem
        "spring": ["java", "backend"],
        "spring boot": ["java", "backend"],
        "maven": ["java", "build tool"],
        
        # Databases
        "mysql": ["sql", "database"],
        "postgresql": ["sql", "database"],
        "postgres": ["sql", "database"],
        "mongodb": ["nosql", "database"],
        "redis": ["database", "cache"],
        "dynamodb": ["database", "cloud", "aws"],
        "sqlite": ["sql", "database"],
        
        # Cloud
        "aws": ["cloud", "amazon"],
        "gcp": ["cloud", "google"],
        "google cloud": ["cloud", "google"],
        "azure": ["cloud", "microsoft"],
        "docker": ["containerization", "devops"],
        "kubernetes": ["container orchestration", "devops"],
        
        # Mobile
        "swift": ["ios", "mobile"],
        "kotlin": ["android", "mobile"],
        "flutter": ["mobile", "dart"],
        "ios": ["mobile"],
        "android": ["mobile"],
    }
    
    TECH_SYNONYMS = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "cpp": "c++",
        "c++": "cpp",
        "nodejs": "node.js",
        "node": "node.js",
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
        "ml": "machine learning",
        "dl": "deep learning",
        "postgresql": "postgres",
        "mongo": "mongodb",
        "k8s": "kubernetes",
        "k8": "kubernetes",
    }
    
    @staticmethod
    def normalize_tech(tech: str) -> str:
        """Normalize technology name to standard form"""
        tech_lower = tech.strip().lower()
        
        # Apply synonyms
        if tech_lower in TechConsistencyChecker.TECH_SYNONYMS:
            return TechConsistencyChecker.TECH_SYNONYMS[tech_lower]
        
        return tech_lower
    
    @staticmethod
    def get_tech_ecosystem_group(tech: str) -> str:
        """Get the semantic ecosystem group for a technology"""
        normalized = TechConsistencyChecker.normalize_tech(tech)
        
        for group, techs in TechConsistencyChecker.TECH_GROUPS.items():
            if normalized in techs:
                return group
        
        return None
    
    @staticmethod
    def get_semantic_equivalents(tech: str) -> Set[str]:
        """Get all semantically equivalent technologies for a given tech"""
        normalized = TechConsistencyChecker.normalize_tech(tech)
        
        # Get direct semantic mapping
        direct_equivalents = set(TechConsistencyChecker.TECH_SEMANTIC_MAPPING.get(normalized, [normalized]))
        
        # Also add all techs from the same ecosystem group
        ecosystem = TechConsistencyChecker.get_tech_ecosystem_group(tech)
        if ecosystem:
            ecosystem_techs = set(TechConsistencyChecker.TECH_GROUPS[ecosystem])
            direct_equivalents.update(ecosystem_techs)
        
        return direct_equivalents
    
    @staticmethod
    def skills_semantically_match(skill1: str, skill2: str) -> bool:
        """Check if two skills match semantically (not just literal match)"""
        norm1 = TechConsistencyChecker.normalize_tech(skill1)
        norm2 = TechConsistencyChecker.normalize_tech(skill2)
        
        # Direct match
        if norm1 == norm2:
            return True
        
        # Semantic match through ecosystem
        equiv1 = TechConsistencyChecker.get_semantic_equivalents(skill1)
        equiv2 = TechConsistencyChecker.get_semantic_equivalents(skill2)
        
        # If there's overlap in equivalents, they're semantically related
        if equiv1 & equiv2:
            return True
        
        return False
    
    @staticmethod
    def check_consistency(
        claimed_skills: List[str],
        demonstrated_technologies: Dict[str, int],
        project_technologies: List[str],
        work_technologies: List[str],
    ) -> Dict[str, Any]:
        """Check consistency between claimed and demonstrated skills using SEMANTIC MATCHING"""
        logger.info("Checking technology consistency with semantic matching")
        
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
            "semantic_matches": [],
        }
        
        # Check each claimed skill using SEMANTIC MATCHING
        for skill in claimed_normalized:
            found = False
            semantic_match_info = None
            
            # Check for direct or semantic match in demonstrated technologies
            for demonstrated_tech in demonstrated_normalized.keys():
                if TechConsistencyChecker.skills_semantically_match(skill, demonstrated_tech):
                    if skill == demonstrated_tech:
                        # Direct match
                        consistency_results["verified_skills"].append({
                            "skill": skill,
                            "found_in": "github_repos",
                            "repo_count": demonstrated_normalized[demonstrated_tech],
                            "match_type": "direct",
                        })
                    else:
                        # Semantic match (e.g., React found for JavaScript skill)
                        consistency_results["verified_skills"].append({
                            "skill": skill,
                            "found_in": "github_repos",
                            "repo_count": demonstrated_normalized[demonstrated_tech],
                            "match_type": "semantic",
                            "matched_with": demonstrated_tech,
                        })
                        semantic_match_info = (skill, demonstrated_tech)
                    found = True
                    break
            
            # Check projects for semantic match
            if not found:
                for project_tech in project_normalized:
                    if TechConsistencyChecker.skills_semantically_match(skill, project_tech):
                        consistency_results["partially_verified_skills"].append({
                            "skill": skill,
                            "found_in": "projects",
                            "match_type": "semantic" if skill != project_tech else "direct",
                            "matched_with": project_tech if skill != project_tech else None,
                        })
                        found = True
                        break
            
            # Check work experience for semantic match
            if not found:
                for work_tech in work_normalized:
                    if TechConsistencyChecker.skills_semantically_match(skill, work_tech):
                        consistency_results["partially_verified_skills"].append({
                            "skill": skill,
                            "found_in": "work_experience",
                            "match_type": "semantic" if skill != work_tech else "direct",
                            "matched_with": work_tech if skill != work_tech else None,
                        })
                        found = True
                        break
            
            if not found:
                consistency_results["unverified_skills"].append(skill)
        
        # Check for undeclared technologies
        for tech in all_demonstrated:
            if not any(TechConsistencyChecker.skills_semantically_match(tech, claimed) for claimed in claimed_normalized):
                consistency_results["undeclared_technologies"].append(tech)
        
        # Calculate consistency score (without over-penalizing for ecosystem overlap)
        total_claimed = len(claimed_normalized)
        if total_claimed > 0:
            verified = len(consistency_results["verified_skills"])
            partial = len(consistency_results["partially_verified_skills"])
            
            # Semantic matches get 80-90% of full verification credit
            consistency_results["consistency_score"] = (
                (verified * 100 + partial * 75) / (total_claimed * 100)
            )
        
        logger.info(f"Consistency check complete with semantic matching. Score: {consistency_results['consistency_score']:.2f}")
        return consistency_results
    
    @staticmethod
    def detect_red_flags(
        claimed_skills: List[str],
        consistency_report: Dict[str, Any],
        demonstrated_technologies: Dict[str, int],
    ) -> List[Dict[str, str]]:
        """Detect red flags in technology claims - FAIR AND NON-PUNITIVE"""
        logger.info("Detecting tech consistency red flags (with fairness)")
        
        red_flags = []
        
        # IMPORTANT: Only flag STRONG CONTRADICTIONS, not absences
        # Absence of evidence ≠ Evidence of dishonesty
        
        # Red Flag 1: STRONG contradiction - Claims expert in X but ALL repos use totally different ecosystem
        unverified_count = len(consistency_report.get("unverified_skills", []))
        if unverified_count > 0:
            unverified_percentage = (unverified_count / len(claimed_skills) * 100) if claimed_skills else 0
            
            # ONLY flag if > 80% unverified AND there's GitHub activity (contradiction)
            if unverified_percentage > 80 and demonstrated_technologies:
                red_flags.append({
                    "type": "strong_skill_contradiction",
                    "severity": "medium",  # Downgraded from "high" - this is not necessarily dishonesty
                    "description": f"{unverified_percentage:.0f}% of claimed skills have no GitHub evidence despite active GitHub presence",
                    "recommendation": "Verify these skills in interview or with project links",
                    "skills": consistency_report["unverified_skills"][:5],
                })
        
        # Red Flag 2: Undeclared technologies are NORMAL - don't flag
        # GitHub shows tech not in claims? That's fine. Candidates may not list everything.
        # Remove this harsh flag - it's not a red flag
        
        # Red Flag 3: Single repo only - ONLY if ALL tech from single repo
        if demonstrated_technologies and len(demonstrated_technologies) > 0:
            repo_counts = list(demonstrated_technologies.values())
            max_repos = max(repo_counts)
            total_techs = len(demonstrated_technologies)
            
            # ONLY flag if single repo AND only one technology shown
            if max_repos == 1 and total_techs == 1:
                red_flags.append({
                    "type": "single_repo_all_activity",
                    "severity": "low",  # Low severity, not disqualifying
                    "description": "All GitHub activity concentrated in a single repository with one technology",
                    "recommendation": "Candidate may be early in career. Not necessarily a red flag.",
                })
        
        logger.info(f"Found {len(red_flags)} red flags (fair detection)")
        return red_flags
