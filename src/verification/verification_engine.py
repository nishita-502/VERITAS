"""
Verification Engine
Orchestrates all verification agents and combines results
"""
from typing import Dict, Any, List

from src.core.logging_config import get_logger
from src.verification.github_agent import GitHubAgent
from src.verification.kaggle_agent import KaggleAgent
from src.verification.tech_consistency_checker import TechConsistencyChecker
from src.verification.timeline_validator import TimelineValidator
from src.verification.cp_agent import CPAgentReal

logger = get_logger(__name__)


class VerificationEngine:
    """Orchestrate verification across all sources"""
    
    def __init__(self):
        self.github = GitHubAgent()
        self.kaggle = KaggleAgent()
        self.tech_checker = TechConsistencyChecker()
        self.timeline_validator = TimelineValidator()
        self.cp_agent = CPAgentReal()
        logger.info("VerificationEngine initialized")
    
    async def verify_all_claims(
        self,
        extracted_data: Dict[str, Any],
        claims: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run comprehensive verification on all claims"""
        logger.info("Starting comprehensive claim verification")
        
        verification_results = {
            "github_verification": None,
            "kaggle_verification": None,
            "tech_consistency": None,
            "competitive_programming": None,
            "all_claim_results": [],
            "red_flags": [],
        }
        
        # GitHub Verification
        if extracted_data.get("github_username"):
            logger.info(f"Running GitHub verification for {extracted_data['github_username']}")
            verification_results["github_verification"] = await self._verify_github(
                extracted_data
            )
        
        # Kaggle Verification
        if extracted_data.get("kaggle_username"):
            logger.info(f"Running Kaggle verification for {extracted_data['kaggle_username']}")
            verification_results["kaggle_verification"] = await self._verify_kaggle(
                extracted_data
            )
        
        # Tech Consistency Check
        if extracted_data.get("skills") or extracted_data.get("projects"):
            logger.info("Running tech consistency check")
            verification_results["tech_consistency"] = await self._check_tech_consistency(
                extracted_data,
                verification_results.get("github_verification", {}),
            )
        
        # TIMELINE VALIDATION REMOVED - Timeline is not part of ATS scoring
        # (Only used for informational purposes, not penalization)
        
        # Competitive Programming Verification (DSA/LeetCode/Codeforces/etc)
        logger.info("Running competitive programming verification")
        verification_results["competitive_programming"] = await self.cp_agent.verify_all_platforms(
            extracted_data
        )
        
        # Comprehensive claim evaluation
        verification_results["all_claim_results"] = await self._evaluate_all_claims(
            extracted_data,
            claims,
            verification_results,
        )
        
        logger.info("Comprehensive verification complete")
        return verification_results
    
    async def _verify_github(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run GitHub verification"""
        username = extracted_data.get("github_username")
        
        clean_username = self.github.sanitize_github_username(username)
        result = {
            "username": clean_username,
            "stage": "github_verification",
            "user_profile": self.github.verify_user_exists(clean_username),
            "projects_verified": {},
            "tech_verification": {},
            "language_footprint": {},
        }

        if result["user_profile"].get("exists"):
            project_verification = self.github.verify_project_claims(
                clean_username,
                extracted_data.get("projects", []),
            )
            result["projects_verified"] = project_verification
            result["language_footprint"] = project_verification.get("language_footprint", {})

            if extracted_data.get("skills"):
                result["tech_verification"] = self.github.verify_tech_stack(
                    clean_username,
                    extracted_data["skills"],
                    project_claims=extracted_data.get("projects", []),
                )
        
        return result
    
    async def _verify_kaggle(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Kaggle verification"""
        username = extracted_data.get("kaggle_username")
        
        result = {
            "username": username,
            "stage": "kaggle_verification",
            "user_profile": self.kaggle.verify_user_exists(username),
        }
        
        if result["user_profile"].get("exists"):
            result["competitions"] = self.kaggle.get_competitions_participated(username)
            result["datasets"] = self.kaggle.get_datasets_contributed(username)
        
        return result
    
    async def _check_tech_consistency(
        self,
        extracted_data: Dict[str, Any],
        github_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check technology consistency"""
        all_languages = {}
        if extracted_data.get("github_username"):
            all_languages = (
                (github_result or {}).get("language_footprint")
                or ((github_result or {}).get("projects_verified") or {}).get("language_footprint")
                or {}
            )
        
        consistency = self.tech_checker.check_consistency(
            claimed_skills=extracted_data.get("skills", []),
            demonstrated_technologies=all_languages,
            project_technologies=self._extract_project_techs(extracted_data),
            work_technologies=self._extract_work_techs(extracted_data),
        )
        
        red_flags = self.tech_checker.detect_red_flags(
            claimed_skills=extracted_data.get("skills", []),
            consistency_report=consistency,
            demonstrated_technologies=all_languages,
        )
        
        return {
            "stage": "tech_consistency",
            "consistency_report": consistency,
            "red_flags": red_flags,
        }
    
    async def _validate_timelines(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate timelines"""
        github_repos = []
        if extracted_data.get("github_username"):
            github_repos = self.github.get_repositories(extracted_data["github_username"])
        
        project_validations = []
        for project in extracted_data.get("projects", []):
            validation = self.timeline_validator.validate_project_timeline(
                project.get("name", ""),
                project.get("timeline", ""),
                github_repos
            )
            project_validations.append(validation)
        
        work_validations = []
        for work in extracted_data.get("work_experience", []):
            validation = self.timeline_validator.validate_work_experience_timeline(
                work.get("position", ""),
                work.get("company", ""),
                work.get("start_year"),
                work.get("end_year"),
                {},
            )
            work_validations.append(validation)
        
        overall = self.timeline_validator.validate_overall_consistency(
            extracted_data.get("projects", []),
            extracted_data.get("work_experience", []),
        )
        
        return {
            "stage": "timeline_validation",
            "project_timelines": project_validations,
            "work_timelines": work_validations,
            "overall_consistency": overall,
        }
    
    async def _evaluate_all_claims(
        self,
        extracted_data: Dict[str, Any],
        claims: List[Dict[str, Any]],
        verification_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Evaluate each claim individually"""
        claim_results = []
        
        for claim in claims:
            claim_result = self._evaluate_single_claim(
                claim,
                extracted_data,
                verification_results,
            )
            claim_results.append(claim_result)
        
        return claim_results
    
    def _evaluate_single_claim(
        self,
        claim: Dict[str, Any],
        extracted_data: Dict[str, Any],
        verification_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate a single claim"""
        claim_type = claim.get("claim_type", "unknown")
        value = claim.get("value", "")
        
        result = {
            "claim": claim["claim"],
            "claim_id": claim.get("id"),
            "claim_type": claim_type,
            "value": value,
            "status": "self_reported",
            "trust_score": 50,
            "evidence": [],
            "reasoning": "",
        }
        
        if claim_type == "skill_match":
            # Check tech consistency results
            inconsistency = verification_results.get("tech_consistency", {})
            consistency_report = inconsistency.get("consistency_report", {})
            
            verified = consistency_report.get("verified_skills", [])
            partial = consistency_report.get("partially_verified_skills", [])
            
            for v in verified:
                if v.get("skill") == value.lower():
                    result["status"] = "verified"
                    result["trust_score"] = 95
                    result["evidence"].append(f"Found in {v.get('found_in', 'github')}")
                    break
            
            for p in partial:
                if p.get("skill") == value.lower():
                    result["status"] = "partially_verified"
                    result["trust_score"] = 75
                    result["evidence"].append(f"Found in {p.get('found_in', 'projects')}")
                    break
            
            if result["status"] == "unverified":
                result["status"] = "self_reported"
                result["trust_score"] = 50
                result["evidence"].append("Self-reported claim; no contradictory evidence found")
        
        elif claim_type == "link_verification":
            # Check if link is accessible
            if extracted_data.get("github_username") and "github" in value.lower():
                github_info = verification_results.get("github_verification", {})
                if github_info.get("user_profile", {}).get("exists"):
                    result["status"] = "verified"
                    result["trust_score"] = 100
                    result["evidence"].append("GitHub profile verified")
                else:
                    result["status"] = "self_reported"
                    result["trust_score"] = 50
                    result["evidence"].append("GitHub link provided, but profile could not be verified")
            
            elif extracted_data.get("kaggle_username") and "kaggle" in value.lower():
                kaggle_info = verification_results.get("kaggle_verification", {})
                if kaggle_info.get("user_profile", {}).get("exists"):
                    result["status"] = "verified"
                    result["trust_score"] = 100
                    result["evidence"].append("Kaggle profile verified")
                else:
                    result["status"] = "self_reported"
                    result["trust_score"] = 50
                    result["evidence"].append("Kaggle link provided, but profile could not be verified")
        
        elif claim_type == "numeric":
            result["trust_score"] = 50
            result["evidence"].append("Numeric claim self-reported in resume")
        
        elif claim_type == "timeline":
            timeline_info = verification_results.get("timeline_validity", {})
            # Check project or work timelines
            for proj_timeline in timeline_info.get("project_timelines", []):
                if proj_timeline.get("verified"):
                    result["status"] = "verified"
                    result["trust_score"] = 90
                    break
            if result["status"] == "self_reported":
                result["trust_score"] = 50
                result["evidence"].append("Timeline claim remains self-reported unless a direct contradiction is detected")
        
        result["reasoning"] = self._generate_reasoning(result)
        return result
    
    def _generate_reasoning(self, claim_result: Dict[str, Any]) -> str:
        """Generate reasoning for claim evaluation"""
        status = claim_result.get("status", "unverified")
        score = claim_result.get("trust_score", 0)
        evidence = claim_result.get("evidence", [])
        
        if status == "verified":
            return f"Claim verified with {score}% confidence. {' '.join(evidence)}"
        elif status == "partially_verified":
            return f"Claim partially verified ({score}% confidence). {' '.join(evidence)}"
        else:
            return f"Insufficient evidence to verify claim ({score}% confidence). {' '.join(evidence) if evidence else 'No supporting evidence found.'}"
    
    def _extract_project_techs(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Extract all technologies from projects"""
        techs = []
        for project in extracted_data.get("projects", []):
            techs.extend(project.get("technologies", []))
        return techs
    
    def _extract_work_techs(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Extract all technologies from work experience"""
        techs = []
        for work in extracted_data.get("work_experience", []):
            techs.extend(work.get("technologies", []))
        return techs
