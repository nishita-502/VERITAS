"""
ATS Score Engine
Calculates dynamic ATS score using real formula
"""
from typing import Dict, List, Any, Tuple
from difflib import SequenceMatcher
from src.core.config import ATS_WEIGHTS
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class ATSEngine:
    """Calculate ATS score dynamically"""
    
    @staticmethod
    def extract_jd_skills(jd_text: str) -> List[str]:
        """Extract required skills from job description"""
        logger.info("Extracting skills from JD")
        
        # Common skill keywords
        skill_keywords = {
            "Python", "JavaScript", "Java", "C++", "React", "Angular", "Vue",
            "Node.js", "Django", "Flask", "Spring", "MongoDB", "PostgreSQL",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git",
            "SQL", "REST", "APIs", "Agile", "Scrum", "Machine Learning",
            "Deep Learning", "TensorFlow", "PyTorch", "Data Analysis",
            "Communication", "Problem Solving", "Leadership", "Team Work",
        }
        
        found_skills = []
        jd_lower = jd_text.lower()
        
        for skill in skill_keywords:
            if skill.lower() in jd_lower:
                found_skills.append(skill)
        
        logger.info(f"Found {len(found_skills)} JD skills")
        return list(set(found_skills))
    
    @staticmethod
    def calculate_skill_match(
        jd_skills: List[str],
        resume_skills: List[str],
        verified_tech: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate JD skill match percentage"""
        logger.info("Calculating skill match")
        
        if not jd_skills:
            logger.warning("No JD skills to match against")
            return 0.0, {"matched_skills": [], "missing_skills": [], "match_count": 0}
        
        matched_skills = []
        missing_skills = []
        
        for jd_skill in jd_skills:
            found = False
            jd_skill_lower = jd_skill.lower()
            
            # Check against resume skills
            for resume_skill in resume_skills:
                if ATSEngine._skills_match(jd_skill_lower, resume_skill.lower()):
                    matched_skills.append(jd_skill)
                    found = True
                    break
            
            # Check against verified technologies
            if not found and verified_tech:
                verified_skills = verified_tech.get("verified_skills", [])
                for v_skill in verified_skills:
                    if ATSEngine._skills_match(jd_skill_lower, v_skill.get("skill", "").lower()):
                        matched_skills.append(f"{jd_skill} (verified)")
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
        
        logger.info(f"Skill match: {match_percentage:.1f}%")
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
    def calculate_claim_verification_rate(claim_results: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """Calculate percentage of verified claims"""
        logger.info("Calculating claim verification rate")
        
        if not claim_results:
            logger.warning("No claims to verify")
            return 0.0, {"total_claims": 0, "verified_claims": 0, "percentage": 0}
        
        verified_count = sum(1 for c in claim_results if c.get("status") == "verified")
        partial_count = sum(1 for c in claim_results if c.get("status") == "partially_verified")
        
        # Weight: verified = 100%, partial = 50%
        weighted_verified = verified_count + (partial_count * 0.5)
        total = len(claim_results)
        
        percentage = (weighted_verified / total * 100) if total > 0 else 0
        
        result = {
            "total_claims": total,
            "verified_claims": verified_count,
            "partially_verified_claims": partial_count,
            "weighted_verified": round(weighted_verified),
            "percentage": round(percentage, 1),
        }
        
        logger.info(f"Claim verification rate: {percentage:.1f}%")
        return percentage, result
    
    @staticmethod
    def calculate_timeline_consistency_score(timeline_validation: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Calculate timeline consistency percentage"""
        logger.info("Calculating timeline consistency score")
        
        if not timeline_validation:
            logger.warning("No timeline validation data")
            return 0.0, {"consistent_timelines": 0, "inconsistent_timelines": 0, "percentage": 0}
        
        overall = timeline_validation.get("overall_consistency", {})
        project_timelines = timeline_validation.get("project_timelines", [])
        work_timelines = timeline_validation.get("work_timelines", [])
        
        # Count valid timelines
        consistent = sum(1 for p in project_timelines if p.get("verified", False))
        consistent += sum(1 for w in work_timelines if w.get("verified", False))
        
        total = len(project_timelines) + len(work_timelines)
        
        # Check for overlaps
        overlaps = len(overall.get("overlapping_periods", []))
        consistent -= overlaps * 5  # Penalize overlaps
        consistent = max(0, consistent)
        
        percentage = (consistent / total * 100) if total > 0 else 100  # 100% if no timelines
        
        result = {
            "consistent_timelines": consistent,
            "total_timelines": total,
            "overlapping_periods": overlaps,
            "percentage": round(percentage, 1),
        }
        
        logger.info(f"Timeline consistency: {percentage:.1f}%")
        return percentage, result
    
    @staticmethod
    def calculate_ats_score(
        jd_text: str,
        extracted_data: Dict[str, Any],
        claim_results: List[Dict[str, Any]],
        verification_results: Dict[str, Any],
        completeness_score: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Calculate ATS score using formula:
        ATS Score = (JD Match % × 0.4) + (Verified Claims % × 0.3) +
                    (Resume Completeness % × 0.2) + (Timeline Consistency % × 0.1)
        """
        logger.info("Calculating ATS score")
        
        # 1. JD Skill Match
        jd_skills = ATSEngine.extract_jd_skills(jd_text)
        verified_tech = verification_results.get("tech_consistency", {}).get("consistency_report", {})
        skill_match_pct, skill_details = ATSEngine.calculate_skill_match(
            jd_skills,
            extracted_data.get("skills", []),
            verified_tech,
        )
        
        # 2. Verified Claims Percentage
        claim_verification_pct, claim_details = ATSEngine.calculate_claim_verification_rate(claim_results)
        
        # 3. Resume Completeness Percentage
        completeness_pct = completeness_score.get("percentage", 0)
        
        # 4. Timeline Consistency Percentage
        timeline_consistency_pct, timeline_details = ATSEngine.calculate_timeline_consistency_score(
            verification_results.get("timeline_validity", {})
        )
        
        # Calculate weighted ATS score
        ats_score = (
            (skill_match_pct * ATS_WEIGHTS["jd_skill_match"]) +
            (claim_verification_pct * ATS_WEIGHTS["verified_claims"]) +
            (completeness_pct * ATS_WEIGHTS["resume_completeness"]) +
            (timeline_consistency_pct * ATS_WEIGHTS["timeline_consistency"])
        )
        
        ats_score = round(min(100, max(0, ats_score)))  # Clamp between 0-100
        
        # Determine ATS status
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
            "breakdown": {
                "jd_skill_match": {
                    "percentage": round(skill_match_pct, 1),
                    "weight": ATS_WEIGHTS["jd_skill_match"],
                    "weighted_contribution": round(skill_match_pct * ATS_WEIGHTS["jd_skill_match"], 1),
                    "details": skill_details,
                },
                "verified_claims": {
                    "percentage": round(claim_verification_pct, 1),
                    "weight": ATS_WEIGHTS["verified_claims"],
                    "weighted_contribution": round(claim_verification_pct * ATS_WEIGHTS["verified_claims"], 1),
                    "details": claim_details,
                },
                "resume_completeness": {
                    "percentage": completeness_pct,
                    "weight": ATS_WEIGHTS["resume_completeness"],
                    "weighted_contribution": round(completeness_pct * ATS_WEIGHTS["resume_completeness"], 1),
                    "details": completeness_score,
                },
                "timeline_consistency": {
                    "percentage": round(timeline_consistency_pct, 1),
                    "weight": ATS_WEIGHTS["timeline_consistency"],
                    "weighted_contribution": round(timeline_consistency_pct * ATS_WEIGHTS["timeline_consistency"], 1),
                    "details": timeline_details,
                },
            },
            "formula_used": "ATS = (JD Match % × 0.4) + (Verified Claims % × 0.3) + (Completeness % × 0.2) + (Timeline % × 0.1)",
        }
        
        logger.info(f"ATS Score calculated: {ats_score} - {ats_status}")
        return result
