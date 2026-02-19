"""
Claim Detection and Organization Module
Identifies verifiable claims in resume
"""
from typing import List, Dict, Any
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class ClaimExtractor:
    """Extract and organize claims from structured resume data"""
    
    CLAIM_TYPES = {
        "skill_match": "Technical skill proficiency",
        "numeric": "Numeric achievement (problems solved, etc)",
        "timeline": "Time-based claim (worked during period X)",
        "depth": "Depth of knowledge/expertise",
        "link_verification": "External link validation",
    }
    
    @staticmethod
    def extract_claims(extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all verifiable claims from resume data"""
        logger.info("Starting claim extraction")
        claims = []
        
        # Skill claims
        if extracted_data.get("skills"):
            for skill in extracted_data["skills"]:
                claims.append({
                    "id": f"skill_{len(claims)}",
                    "claim": f"Proficient in {skill}",
                    "claim_type": "skill_match",
                    "value": skill,
                    "source": "resume_skills",
                    "severity": "high",  # Skills are critical to verify
                })
        
        # Technology claims from projects
        if extracted_data.get("projects"):
            for project in extracted_data["projects"]:
                # Skip if project is not a dict
                if not isinstance(project, dict):
                    continue
                    
                if project.get("technologies"):
                    techs = ", ".join(project["technologies"])
                    claims.append({
                        "id": f"tech_{len(claims)}",
                        "claim": f"Used {techs} in {project.get('name', 'unnamed project')}",
                        "claim_type": "skill_match",
                        "value": techs,
                        "source": f"project_{project.get('name', 'unknown')}",
                        "severity": "high",
                    })
                
                # Timeline claims from projects
                if project.get("timeline"):
                    claims.append({
                        "id": f"timeline_{len(claims)}",
                        "claim": f"Completed {project.get('name', 'project')} during {project['timeline']}",
                        "claim_type": "timeline",
                        "value": project["timeline"],
                        "source": f"project_{project.get('name', 'unknown')}",
                        "severity": "medium",
                    })
                
                # Depth claims from projects
                if project.get("description"):
                    claims.append({
                        "id": f"depth_{len(claims)}",
                        "claim": f"Built {project.get('name', 'project')} with deep understanding",
                        "claim_type": "depth",
                        "value": project.get("description", ""),
                        "source": f"project_{project.get('name', 'unknown')}",
                        "severity": "medium",
                    })
        
        # Work experience timeline claims
        if extracted_data.get("work_experience"):
            for exp in extracted_data["work_experience"]:
                # Skip if exp is not a dict
                if not isinstance(exp, dict):
                    continue
                    
                timeline = f"{exp.get('start_year', '?')}-{exp.get('end_year', '?')}"
                claims.append({
                    "id": f"work_timeline_{len(claims)}",
                    "claim": f"Worked at {exp.get('company', 'unknown')} from {timeline}",
                    "claim_type": "timeline",
                    "value": timeline,
                    "source": "work_experience",
                    "severity": "high",
                })
                
                # Technology claims from work experience
                if exp.get("technologies"):
                    techs = ", ".join(exp["technologies"])
                    claims.append({
                        "id": f"work_tech_{len(claims)}",
                        "claim": f"Used {techs} at {exp.get('company', 'unknown')}",
                        "claim_type": "skill_match",
                        "value": techs,
                        "source": f"work_{exp.get('company', 'unknown')}",
                        "severity": "high",
                    })
        
        # Numeric claims (from structured extraction)
        if extracted_data.get("claims"):
            for claim in extracted_data["claims"]:
                # Skip if claim is not a dict
                if not isinstance(claim, dict):
                    continue
                    
                if claim.get("type") == "numeric":
                    claims.append({
                        "id": f"numeric_{len(claims)}",
                        "claim": claim.get("claim", ""),
                        "claim_type": "numeric",
                        "value": claim.get("value", ""),
                        "source": "resume_text",
                        "severity": "medium",
                    })
        
        # Link verification claims
        for link_type in ["github_username", "kaggle_username", "linkedin_url"]:
            if extracted_data.get(link_type):
                link_value = extracted_data[link_type]
                claims.append({
                    "id": f"link_{len(claims)}",
                    "claim": f"Has active {link_type.replace('_', ' ')}: {link_value}",
                    "claim_type": "link_verification",
                    "value": link_value,
                    "source": "resume_links",
                    "severity": "high",
                })
        
        # CGPA claims
        if extracted_data.get("cgpa"):
            claims.append({
                "id": f"cgpa_{len(claims)}",
                "claim": f"CGPA: {extracted_data['cgpa']}/10",
                "claim_type": "numeric",
                "value": str(extracted_data["cgpa"]),
                "source": "education",
                "severity": "low",
            })
        
        logger.info(f"Extracted {len(claims)} claims")
        return claims
    
    @staticmethod
    def group_claims_by_type(claims: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group claims by claim type"""
        grouped = {claim_type: [] for claim_type in ClaimExtractor.CLAIM_TYPES.keys()}
        
        for claim in claims:
            claim_type = claim.get("claim_type", "unknown")
            if claim_type in grouped:
                grouped[claim_type].append(claim)
        
        logger.info(f"Grouped {len(claims)} into {sum(1 for v in grouped.values() if v)} category types")
        return grouped
    
    @staticmethod
    def prioritize_claims(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize claims by severity for verification"""
        severity_order = {"high": 0, "medium": 1, "low": 2}
        sorted_claims = sorted(
            claims,
            key=lambda x: severity_order.get(x.get("severity", "low"), 3)
        )
        
        logger.info(f"Prioritized {len(sorted_claims)} claims")
        return sorted_claims
