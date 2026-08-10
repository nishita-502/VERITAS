"""
Trust Scorer
Calculates trust scores for individual claims and overall resume
"""
from typing import Dict, List, Any

from src.core.config import PARTIAL_MATCH_THRESHOLD, VERIFIED_THRESHOLD
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class TrustScorer:
    """Calculate trust scores for claims and resume."""

    @staticmethod
    def score_claim(claim_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assign trust score to a single claim."""

        logger.debug("Scoring claim: %s", claim_result.get("claim"))

        status = (claim_result.get("status") or "self_reported").lower()
        trust_score = claim_result.get("trust_score")
        if trust_score is None:
            trust_score = {
                "verified": 95,
                "partially_verified": 75,
                "self_reported": 50,
                "unverified": 50,
                "contradicted": 0,
                "flagged": 0,
            }.get(status, 50)

        if status == "verified":
            confidence = "High"
            label = "✅ Verified External Evidence"
        elif status == "partially_verified":
            confidence = "Medium"
            label = "⚠️ Partially Verified Evidence"
        elif status in {"contradicted", "flagged"}:
            confidence = "Low"
            label = "🚩 Contradicted / Suspicious"
        else:
            confidence = "Neutral"
            label = "ℹ️ Self-Reported / Neutral"

        return {
            "claim": claim_result.get("claim"),
            "claim_id": claim_result.get("claim_id"),
            "claim_type": claim_result.get("claim_type"),
            "status": status,
            "trust_score": float(trust_score),
            "confidence": confidence,
            "label": label,
            "evidence": claim_result.get("evidence", []),
            "reasoning": claim_result.get("reasoning", ""),
        }

    @staticmethod
    def score_all_claims(claim_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score all claims and generate summary."""

        logger.info("Scoring %s claims", len(claim_results))
        scored_claims = [TrustScorer.score_claim(c) for c in claim_results]

        verified_count = sum(1 for c in scored_claims if c["status"] == "verified")
        partial_count = sum(1 for c in scored_claims if c["status"] == "partially_verified")
        self_reported_count = sum(1 for c in scored_claims if c["status"] in {"self_reported", "unverified"})
        contradicted_count = sum(1 for c in scored_claims if c["status"] in {"contradicted", "flagged"})

        total = len(scored_claims)
        overall_score = sum(c["trust_score"] for c in scored_claims) / total if total else 0

        if contradicted_count > 0:
            overall_label = "🚩 Contradiction Present"
        elif overall_score >= VERIFIED_THRESHOLD:
            overall_label = "✅ High External Confidence"
        elif overall_score >= PARTIAL_MATCH_THRESHOLD:
            overall_label = "⚠️ Mixed Confidence"
        else:
            overall_label = "ℹ️ Mostly Self-Reported"

        result = {
            "overall_trust_score": round(overall_score),
            "overall_label": overall_label,
            "summary": {
                "total_claims": total,
                "verified": verified_count,
                "partially_verified": partial_count,
                "self_reported": self_reported_count,
                "contradicted": contradicted_count,
            },
            "percentages": {
                "verified": round(verified_count / total * 100) if total > 0 else 0,
                "partially_verified": round(partial_count / total * 100) if total > 0 else 0,
                "self_reported": round(self_reported_count / total * 100) if total > 0 else 0,
                "contradicted": round(contradicted_count / total * 100) if total > 0 else 0,
            },
            "scored_claims": scored_claims,
            "reasoning": TrustScorer._generate_overall_reasoning(overall_score, scored_claims),
        }

        logger.info("Overall trust score: %.2f", overall_score)
        return result

    @staticmethod
    def _generate_overall_reasoning(score: float, scored_claims: List[Dict[str, Any]]) -> str:
        """Generate reasoning for overall trust score."""

        verified = [c for c in scored_claims if c["status"] == "verified"]
        partial = [c for c in scored_claims if c["status"] == "partially_verified"]
        neutral = [c for c in scored_claims if c["status"] in {"self_reported", "unverified"}]
        contradicted = [c for c in scored_claims if c["status"] in {"contradicted", "flagged"}]

        if contradicted:
            return f"{len(contradicted)} claim(s) directly contradict external evidence. Review these items first."

        if score >= VERIFIED_THRESHOLD:
            return f"External evidence supports most claims. {len(verified)} verified and {len(partial)} partially verified claims."

        if score >= PARTIAL_MATCH_THRESHOLD:
            return f"A mixed evidence picture: {len(verified)} verified, {len(partial)} partial, and {len(neutral)} self-reported claims."

        return f"Most claims are self-reported ({len(neutral)} of {len(scored_claims)}). This is neutral, but it warrants confirmation if the role needs hard evidence."

    @staticmethod
    def score_resume_completeness(extracted_data: Dict[str, Any]) -> Dict[str, float]:
        """Score resume completeness with partial credit."""

        logger.info("Scoring resume completeness")
        extracted_data = extracted_data or {}

        scores: Dict[str, int] = {}
        evidence: Dict[str, Any] = {}

        # Contact information: 25 points
        contact_score = 0
        if extracted_data.get("full_name"):
            contact_score += 5
        if extracted_data.get("email"):
            contact_score += 10
        if extracted_data.get("phone"):
            contact_score += 7
        if extracted_data.get("github_username") or extracted_data.get("linkedin_url") or extracted_data.get("kaggle_username"):
            contact_score += 3
        scores["contact_info"] = min(25, contact_score)

        # Education: 25 points
        education_score = 0
        if extracted_data.get("university"):
            education_score += 10
        if extracted_data.get("cgpa") is not None:
            education_score += 5
        if extracted_data.get("graduation_year"):
            education_score += 5
        if extracted_data.get("education"):
            education_score += 5
        scores["education"] = min(25, education_score)

        # Experience: 25 points
        projects = extracted_data.get("projects", []) or []
        work_experience = extracted_data.get("work_experience", []) or []
        experience_score = 0
        experience_score += min(15, len(projects) * 4)
        experience_score += min(10, len(work_experience) * 5)
        scores["experience"] = min(25, experience_score)

        # Skills: 25 points
        skills = extracted_data.get("skills", []) or []
        technologies = extracted_data.get("technologies", []) or []
        skills_score = 0
        skills_score += min(15, len(skills) * 2)
        skills_score += min(10, len(technologies) * 1)
        scores["skills"] = min(25, skills_score)

        total_score = sum(scores.values())
        max_score = 100
        percentage = (total_score / max_score) * 100 if max_score else 0

        if not extracted_data.get("full_name"):
            evidence.setdefault("missing", []).append("full_name")
        if not extracted_data.get("email"):
            evidence.setdefault("missing", []).append("email")
        if not extracted_data.get("phone"):
            evidence.setdefault("missing", []).append("phone")

        logger.info("Resume completeness score: %.1f%%", percentage)

        return {
            "scores": scores,
            "evidence": evidence,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": round(percentage),
            "missing_fields": evidence.get("missing", []),
        }
