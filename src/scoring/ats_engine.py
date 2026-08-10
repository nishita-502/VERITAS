"""
ATS Score Engine
Calculates dynamic ATS score using JD alignment, completeness, and evidence boosts
"""
from typing import Dict, List, Any, Tuple, Optional
from difflib import SequenceMatcher

from src.core.config import ATS_WEIGHTS
from src.core.logging_config import get_logger

logger = get_logger(__name__)

EXTERNAL_BOOST_MAX = 15.0


class ATSEngine:
    """Calculate ATS score dynamically."""

    @staticmethod
    def extract_jd_skills(jd_text: str, jd_data: Optional[Dict[str, Any]] = None) -> List[str]:
        """Extract required skills from job description or extracted JD data."""

        logger.info("Extracting skills from JD")

        jd_data = jd_data or {}
        extracted_skills = []

        for key in ("required_skills", "preferred_skills", "technologies_mentioned"):
            values = jd_data.get(key) or []
            for value in values:
                if isinstance(value, str) and value.strip():
                    extracted_skills.append(value.strip())

        if extracted_skills:
            deduped = list(dict.fromkeys(extracted_skills))
            logger.info("Using %s JD skills from structured JD data", len(deduped))
            return deduped

        skill_keywords = {
            "Python", "JavaScript", "Java", "C++", "React", "Angular", "Vue",
            "Node.js", "Django", "Flask", "Spring", "MongoDB", "PostgreSQL",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git",
            "SQL", "REST", "APIs", "Agile", "Scrum", "Machine Learning",
            "Deep Learning", "TensorFlow", "PyTorch", "Data Analysis",
            "Communication", "Problem Solving", "Leadership", "Team Work",
        }

        found_skills = []
        jd_lower = (jd_text or "").lower()

        for skill in skill_keywords:
            if skill.lower() in jd_lower:
                found_skills.append(skill)

        logger.info("Found %s JD skills from text fallback", len(found_skills))
        return list(dict.fromkeys(found_skills))
    
    @staticmethod
    def calculate_skill_match(
        jd_skills: List[str],
        resume_skills: List[str],
        verified_tech: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate JD skill match percentage."""

        logger.info("Calculating skill match")

        if not jd_skills:
            logger.warning("No JD skills to match against - using neutral alignment score")
            return 50.0, {
                "matched_skills": [],
                "missing_skills": [],
                "match_count": 0,
                "note": "JD skill extraction unavailable - neutral score applied",
            }

        matched_skills = []
        missing_skills = []
        verified_skills = verified_tech.get("verified_skills", []) if verified_tech else []
        partially_verified_skills = verified_tech.get("partially_verified_skills", []) if verified_tech else []

        for jd_skill in jd_skills:
            found = False
            jd_skill_lower = jd_skill.lower()

            for resume_skill in resume_skills:
                if ATSEngine._skills_match(jd_skill_lower, resume_skill.lower()):
                    matched_skills.append(jd_skill)
                    found = True
                    break

            if not found:
                for v_skill in verified_skills:
                    if ATSEngine._skills_match(jd_skill_lower, str(v_skill.get("skill", "")).lower()):
                        matched_skills.append(f"{jd_skill} (verified)")
                        found = True
                        break

            if not found:
                for v_skill in partially_verified_skills:
                    if ATSEngine._skills_match(jd_skill_lower, str(v_skill.get("skill", "")).lower()):
                        matched_skills.append(f"{jd_skill} (semantic)")
                        found = True
                        break

            if not found:
                missing_skills.append(jd_skill)

        match_percentage = (len(matched_skills) / len(jd_skills) * 100) if jd_skills else 0

        result = {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "match_count": len(matched_skills),
            "total_jd_skills": len(jd_skills),
            "match_percentage": round(match_percentage, 1),
        }

        logger.info("Skill match: %.1f%%", match_percentage)
        return match_percentage, result
    
    @staticmethod
    def _skills_match(jd_skill: str, resume_skill: str) -> bool:
        """Check if two skills match (flexible matching)"""
        
        if jd_skill == resume_skill:
            return True
        
        # Substring matching
        if jd_skill in resume_skill or resume_skill in jd_skill:
            return True
        
        # Fuzzy matching
        similarity = SequenceMatcher(None, jd_skill, resume_skill).ratio()
        if similarity > 0.8:
            return True
        
        return False
    
    @staticmethod
    def classify_verifiable_claims(claim_results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Classify claims into evidence-backed and self-reported buckets."""

        logger.info("Classifying claims for evidence handling")

        evidence_backed_claims = []
        self_reported_claims = []

        for claim in claim_results:
            status = (claim.get("status") or "self_reported").lower()
            if status in {"verified", "partially_verified"}:
                evidence_backed_claims.append(claim)
            else:
                self_reported_claims.append(claim)

        logger.info(
            "Classified %s evidence-backed and %s self-reported claims",
            len(evidence_backed_claims),
            len(self_reported_claims),
        )
        return evidence_backed_claims, self_reported_claims
    
    @staticmethod
    def calculate_claim_verification_rate(claim_results: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """Calculate evidence-backed claim rate without penalizing self-reported claims."""

        logger.info("Calculating claim verification rate")

        if not claim_results:
            logger.warning("No claims to verify")
            return 0.0, {"total_claims": 0, "evidence_backed_claims": 0, "self_reported_claims": 0, "percentage": 0}

        evidence_backed_claims, self_reported_claims = ATSEngine.classify_verifiable_claims(claim_results)

        if not evidence_backed_claims:
            return 0.0, {
                "total_claims": len(claim_results),
                "evidence_backed_claims": 0,
                "self_reported_claims": len(self_reported_claims),
                "verified_claims": 0,
                "percentage": 0,
                "note": "No external evidence found; self-reported claims remain neutral",
            }

        verified_count = sum(1 for c in evidence_backed_claims if c.get("status") == "verified")
        partial_count = sum(1 for c in evidence_backed_claims if c.get("status") == "partially_verified")

        weighted_verified = verified_count + (partial_count * 0.75)
        total_evidence_backed = len(evidence_backed_claims)
        percentage = (weighted_verified / total_evidence_backed * 100) if total_evidence_backed > 0 else 0

        result = {
            "total_claims": len(claim_results),
            "evidence_backed_claims": total_evidence_backed,
            "self_reported_claims": len(self_reported_claims),
            "verified_claims": verified_count,
            "partially_verified_claims": partial_count,
            "neutral_claims": len(self_reported_claims),
            "weighted_verified": round(weighted_verified),
            "percentage": round(percentage, 1),
        }

        logger.info("Claim verification rate: %.1f%% (from %s evidence-backed claims)", percentage, total_evidence_backed)
        return percentage, result
    
    @staticmethod
    def calculate_timeline_consistency_score(timeline_validation: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Calculate timeline consistency percentage."""

        logger.info("Calculating timeline consistency score")

        if not timeline_validation:
            logger.warning("No timeline validation data")
            return 100.0, {"consistent_timelines": 0, "inconsistent_timelines": 0, "percentage": 100}

        overall = timeline_validation.get("overall_consistency", {})
        project_timelines = timeline_validation.get("project_timelines", [])
        work_timelines = timeline_validation.get("work_timelines", [])

        consistent = sum(1 for p in project_timelines if p.get("verified", False))
        consistent += sum(1 for w in work_timelines if w.get("verified", False))

        total = len(project_timelines) + len(work_timelines)
        overlaps = len(overall.get("overlapping_periods", []))

        percentage = 100.0 if total == 0 else max(0.0, ((consistent - overlaps) / total) * 100)

        result = {
            "consistent_timelines": consistent,
            "total_timelines": total,
            "overlapping_periods": overlaps,
            "percentage": round(percentage, 1),
        }

        logger.info("Timeline consistency: %.1f%%", percentage)
        return percentage, result
    
    @staticmethod
    def calculate_project_depth(extracted_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Calculate project depth score as a supporting signal only."""

        logger.info("Calculating project depth score")

        projects = extracted_data.get("projects", []) or []

        if not projects:
            return 0.0, {"total_projects": 0, "average_depth": 0}

        total_depth = 0
        project_details = []

        for project in projects:
            if not isinstance(project, dict):
                continue

            depth_score = 0
            description = project.get("description", "") or ""
            if len(description) > 120:
                depth_score += 40
            elif len(description) > 60:
                depth_score += 25
            elif len(description) > 20:
                depth_score += 10

            techs = project.get("technologies", []) or []
            if len(techs) >= 4:
                depth_score += 30
            elif len(techs) >= 2:
                depth_score += 18
            elif len(techs) > 0:
                depth_score += 8

            impact = project.get("impact", "") or ""
            if impact and len(impact) > 30:
                depth_score += 15
            elif impact:
                depth_score += 8

            timeline = project.get("timeline", "") or ""
            if timeline and len(timeline) > 5:
                depth_score += 15
            elif timeline:
                depth_score += 7

            project_details.append({"name": project.get("name", "Unknown"), "depth_score": depth_score})
            total_depth += depth_score

        average_depth = min(100, (total_depth / (len(projects) * 100) * 100) if projects else 0)

        logger.info("Project depth score: %.1f%%", average_depth)

        return average_depth, {
            "total_projects": len(projects),
            "average_depth": round(average_depth, 1),
            "project_details": project_details,
        }
    
    @staticmethod
    def calculate_external_verification_boost(verification_results: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Calculate external verification strength and the resulting positive boost."""

        logger.info("Calculating external verification boost")

        github_result = verification_results.get("github_verification") or {}
        kaggle_result = verification_results.get("kaggle_verification") or {}
        competitive_result = verification_results.get("competitive_programming") or {}

        evidence_strength = 0.0
        details = {
            "github_verification": 0.0,
            "kaggle_verification": 0.0,
            "competitive_programming": 0.0,
            "matched_projects": 0,
            "verified_skills": 0,
        }

        if github_result.get("user_profile", {}).get("exists"):
            details["github_verification"] += 35
            project_match_rate = (github_result.get("projects_verified") or {}).get("match_rate", 0.0)
            details["matched_projects"] = len((github_result.get("projects_verified") or {}).get("matched_projects", []))
            details["github_verification"] += min(35, project_match_rate * 35)

            tech_verification = github_result.get("tech_verification") or {}
            verified_skills = len(tech_verification.get("verified_skills", []))
            partial_skills = len(tech_verification.get("partially_verified_skills", []))
            details["verified_skills"] = verified_skills + partial_skills
            details["github_verification"] += min(30, verified_skills * 6 + partial_skills * 3)

        if kaggle_result.get("user_profile", {}).get("exists"):
            competitions = kaggle_result.get("competitions", {}).get("total_count", len(kaggle_result.get("competitions", [])))
            details["kaggle_verification"] = min(20, 8 + competitions * 1.5)

        if competitive_result.get("verified"):
            details["competitive_programming"] = min(15, float(competitive_result.get("dsa_score", competitive_result.get("score", 0))))

        evidence_strength = min(100.0, sum(details.values()))
        boost_multiplier = min(0.15, evidence_strength / 100.0 * 0.15)
        boost_points = boost_multiplier

        logger.info("External evidence strength: %.1f%%", evidence_strength)

        return evidence_strength, {
            "github_verification": round(details["github_verification"], 1),
            "kaggle_verification": round(details["kaggle_verification"], 1),
            "competitive_programming": round(details["competitive_programming"], 1),
            "evidence_strength": round(evidence_strength, 1),
            "boost_multiplier": round(boost_multiplier, 4),
            "boost_points": round(boost_points, 4),
        }
    
    @staticmethod
    def calculate_ats_score(
        jd_text: str,
        extracted_data: Dict[str, Any],
        claim_results: List[Dict[str, Any]],
        verification_results: Dict[str, Any],
        completeness_score: Dict[str, float],
        jd_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calculate ATS score with a neutral base and a bounded external boost."""

        logger.info("Calculating ATS score with neutral-base formula")

        extracted_data = extracted_data or {}
        claim_results = claim_results or []
        verification_results = verification_results or {}
        completeness_score = completeness_score or {"percentage": 0}
        jd_data = jd_data or {}

        jd_skills = ATSEngine.extract_jd_skills(jd_text, jd_data)
        verified_tech = (verification_results.get("tech_consistency") or {}).get("consistency_report", {})
        skill_match_pct, skill_details = ATSEngine.calculate_skill_match(
            jd_skills,
            extracted_data.get("skills", []),
            verified_tech,
        )

        completeness_pct = completeness_score.get("percentage", 0)
        project_depth_pct, project_depth_details = ATSEngine.calculate_project_depth(extracted_data)
        external_strength_pct, external_details = ATSEngine.calculate_external_verification_boost(verification_results)

        base_alignment_score = (
            (skill_match_pct * ATS_WEIGHTS["jd_requirement_alignment"]) +
            (completeness_pct * ATS_WEIGHTS["resume_completeness"])
        )

        boost_multiplier = external_details.get("boost_multiplier", 0.0)
        boost_points = base_alignment_score * boost_multiplier
        ats_score = min(100.0, base_alignment_score + boost_points)
        ats_score = round(max(0.0, ats_score))

        if ats_score >= 80:
            ats_status = "🟢 Strong Match"
        elif ats_score >= 60:
            ats_status = "🟡 Moderate Match"
        elif ats_score >= 40:
            ats_status = "🟠 Weak Match"
        else:
            ats_status = "🔴 Poor Match"

        result = {
            "ats_score": ats_score,
            "ats_status": ats_status,
            "formula": "ATS = Base JD Alignment (70%) + Resume Completeness (30%) with a bounded external evidence boost",
            "breakdown": {
                "base_alignment": {
                    "weight": 1.0,
                    "contribution": round(base_alignment_score, 1),
                    "jd_requirement_alignment": {
                        "percentage": round(skill_match_pct, 1),
                        "weight": ATS_WEIGHTS["jd_requirement_alignment"],
                        "weighted_contribution": round(skill_match_pct * ATS_WEIGHTS["jd_requirement_alignment"], 1),
                        "details": skill_details,
                    },
                    "resume_completeness": {
                        "percentage": completeness_pct,
                        "weight": ATS_WEIGHTS["resume_completeness"],
                        "weighted_contribution": round(completeness_pct * ATS_WEIGHTS["resume_completeness"], 1),
                        "details": completeness_score,
                    },
                    "project_depth": {
                        "percentage": round(project_depth_pct, 1),
                        "weight": 0.0,
                        "weighted_contribution": 0.0,
                        "details": project_depth_details,
                        "informational": True,
                    },
                },
                "external_verification": {
                    "weight": 0.0,
                    "evidence_strength": round(external_strength_pct, 1),
                    "boost_multiplier": round(boost_multiplier, 4),
                    "boost_points": round(boost_points, 1),
                    "details": external_details,
                },
            },
            "note": "External evidence increases the score when available; absence of evidence is neutral.",
        }

        logger.info("ATS Score calculated: %s - %s", ats_score, ats_status)
        return result
