"""
Trust Scorer
Calculates trust scores for individual claims and overall resume
"""
from typing import Dict, List, Any
from src.core.config import VERIFIED_THRESHOLD, PARTIAL_MATCH_THRESHOLD
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class TrustScorer:
    """Calculate trust scores for claims and resume"""
    
    SCORE_WEIGHTS = {
        "verified": 100,
        "partially_verified": 70,
        "unverified": 30,
        "flagged": 0,
    }
    
    @staticmethod
    def score_claim(claim_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assign trust score to a single claim"""
        logger.debug(f"Scoring claim: {claim_result.get('claim')}")
        
        status = claim_result.get("status", "unverified")
        trust_score = claim_result.get("trust_score", 0)
        
        # Determine confidence level
        if trust_score >= VERIFIED_THRESHOLD:
            confidence = "High"
            label = "✅ Verified"
        elif trust_score >= PARTIAL_MATCH_THRESHOLD:
            confidence = "Medium"
            label = "⚠️ Partially Verified"
        elif trust_score >= 40:
            confidence = "Low"
            label = "❓ Unverified"
        else:
            confidence = "Very Low"
            label = "🚩 Flagged"
        
        return {
            "claim": claim_result.get("claim"),
            "claim_id": claim_result.get("claim_id"),
            "claim_type": claim_result.get("claim_type"),
            "status": status,
            "trust_score": trust_score,
            "confidence": confidence,
            "label": label,
            "evidence": claim_result.get("evidence", []),
            "reasoning": claim_result.get("reasoning", ""),
        }
    
    @staticmethod
    def score_all_claims(claim_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score all claims and generate summary"""
        logger.info(f"Scoring {len(claim_results)} claims")
        
        scored_claims = [TrustScorer.score_claim(c) for c in claim_results]
        
        # Calculate statistics
        verified_count = sum(1 for c in scored_claims if c["status"] == "verified")
        partial_count = sum(1 for c in scored_claims if c["status"] == "partially_verified")
        unverified_count = sum(1 for c in scored_claims if c["status"] == "unverified")
        flagged_count = sum(1 for c in scored_claims if c.get("trust_score", 0) < 40)
        
        total = len(scored_claims)
        
        # Calculate overall trust score (weighted average)
        if total > 0:
            overall_score = sum(c["trust_score"] for c in scored_claims) / total
        else:
            overall_score = 0
        
        # Determine overall label
        if overall_score >= VERIFIED_THRESHOLD:
            overall_label = "✅ Highly Trustworthy"
        elif overall_score >= PARTIAL_MATCH_THRESHOLD:
            overall_label = "⚠️ Partially Trustworthy"
        elif overall_score >= 50:
            overall_label = "❓ Moderately Trustworthy"
        else:
            overall_label = "🚩 Low Trustworthiness"
        
        result = {
            "overall_trust_score": round(overall_score),
            "overall_label": overall_label,
            "summary": {
                "total_claims": total,
                "verified": verified_count,
                "partially_verified": partial_count,
                "unverified": unverified_count,
                "flagged": flagged_count,
            },
            "percentages": {
                "verified": round(verified_count / total * 100) if total > 0 else 0,
                "partially_verified": round(partial_count / total * 100) if total > 0 else 0,
                "unverified": round(unverified_count / total * 100) if total > 0 else 0,
                "flagged": round(flagged_count / total * 100) if total > 0 else 0,
            },
            "scored_claims": scored_claims,
            "reasoning": TrustScorer._generate_overall_reasoning(overall_score, scored_claims),
        }
        
        logger.info(f"Overall trust score: {overall_score:.2f}")
        return result
    
    @staticmethod
    def _generate_overall_reasoning(score: float, scored_claims: List[Dict[str, Any]]) -> str:
        """Generate reasoning for overall trust score"""
        
        if score >= VERIFIED_THRESHOLD:
            return "Candidate claims are well-supported by external verification sources. High confidence in resume authenticity."
        
        elif score >= PARTIAL_MATCH_THRESHOLD:
            flagged = [c for c in scored_claims if c["status"] in ["unverified", "flagged"]]
            if flagged:
                return f"Most claims verified, but {len(flagged)} claims lack supporting evidence. Recommend human review of flagged items."
            return "Generally trustworthy with some unverified claims. External verification sources partially confirm resume content."
        
        elif score >= 50:
            flagged = [c for c in scored_claims if c["status"] in ["unverified", "flagged"]]
            return f"Multiple claims ({len(flagged)}) lack verification. Significant inconsistencies detected. Recommend detailed interview validation."
        
        else:
            return "Low overall trustworthiness. Many claims unverified or contradicted by external sources. Recommend rejecting or detailed verification interview."
    
    @staticmethod
    def score_resume_completeness(extracted_data: Dict[str, Any]) -> Dict[str, float]:
        """Score resume completeness"""
        logger.info("Scoring resume completeness")
        
        scores = {}
        
        # Contact information (20 points possible)
        contact_score = 0
        if extracted_data.get("email"):
            contact_score += 10
        if extracted_data.get("phone"):
            contact_score += 10
        scores["contact_info"] = contact_score
        
        # Education (15 points possible)
        education_score = 0
        if extracted_data.get("university"):
            education_score += 10
        if extracted_data.get("cgpa"):
            education_score += 5
        scores["education"] = education_score
        
        # Experience (25 points possible)
        experience_score = 0
        num_projects = len(extracted_data.get("projects", []))
        num_work = len(extracted_data.get("work_experience", []))
        
        if num_projects > 0:
            experience_score += min(15, num_projects * 3)  # Up to 15 points for projects
        if num_work > 0:
            experience_score += min(10, num_work * 2)  # Up to 10 points for work
        scores["experience"] = experience_score
        
        # Skills (20 points possible)
        skills_score = 0
        num_skills = len(extracted_data.get("skills", []))
        if num_skills > 0:
            skills_score += min(20, num_skills * 2)
        scores["skills"] = skills_score
        
        # Links (20 points possible)
        links_score = 0
        if extracted_data.get("github_username"):
            links_score += 10
        if extracted_data.get("kaggle_username"):
            links_score += 5
        if extracted_data.get("linkedin_url"):
            links_score += 5
        scores["links"] = links_score
        
        total_score = sum(scores.values())
        max_score = 100
        
        percentage = (total_score / max_score) * 100
        
        logger.info(f"Resume completeness score: {percentage:.1f}%")
        
        return {
            "scores": scores,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": round(percentage),
        }
