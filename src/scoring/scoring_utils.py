"""Scoring utilities"""
from typing import List, Dict, Any


def generate_red_flag_report(verification_results: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate comprehensive red flag report."""

    red_flags = []

    tech_consistency = verification_results.get("tech_consistency", {})
    if tech_consistency:
        red_flags.extend(tech_consistency.get("red_flags", []))

    direct_flags = verification_results.get("red_flags", [])
    if direct_flags:
        red_flags.extend(direct_flags)

    deduped = []
    seen = set()
    for flag in red_flags:
        key = (flag.get("type"), flag.get("description"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(flag)

    return deduped


def generate_executive_summary(
    ats_score: Dict[str, Any],
    trust_score: Dict[str, Any],
    red_flags: List[Dict[str, str]],
) -> Dict[str, str]:
    """Generate executive summary for hiring decision"""
    
    ats = ats_score.get("ats_score", 0)
    trust = trust_score.get("overall_trust_score", 0)
    high_severity_flags = len([f for f in red_flags if f.get("severity") == "high"])
    
    # Decision logic
    if ats >= 80 and trust >= 85 and high_severity_flags == 0:
        recommendation = "🟢 STRONG RECOMMEND - Proceed to interview"
        reasoning = "Excellent ATS match, high trust score, and no major red flags."
    
    elif ats >= 60 and trust >= 70 and high_severity_flags <= 1:
        recommendation = "🟡 MODERATE RECOMMEND - Review before interview"
        reasoning = "Good ATS match with minor concerns. Recommend additional verification during interview."
    
    elif ats >= 40 or trust >= 50:
        recommendation = "🟠 WEAK RECOMMEND - Conduct detailed verification"
        reasoning = "Moderate fit with several verification concerns. Additional scrutiny recommended."
    
    else:
        recommendation = "🔴 NOT RECOMMENDED - Consider rejection"
        reasoning = "Poor ATS match and/or low trust score. Multiple red flags detected."
    
    return {
        "recommendation": recommendation,
        "reasoning": reasoning,
        "ats_score": ats,
        "trust_score": trust,
        "red_flags_count": len(red_flags),
        "high_severity_flags": high_severity_flags,
    }
