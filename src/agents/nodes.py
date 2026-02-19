"""
Agent Nodes for VERITAS Resume Verification System
Each node represents a step in the verification pipeline
"""
from typing import Dict, Any
from src.core.logging_config import get_logger
from src.extraction import ResumeParser, StructuredExtractor, ClaimExtractor
from src.verification import VerificationEngine, TechConsistencyChecker, TimelineValidator
from src.scoring import TrustScorer, ATSEngine
from src.scoring.scoring_utils import generate_red_flag_report, generate_executive_summary
from src.matching import JDExtractor
from src.agents.state import GraphState

logger = get_logger(__name__)


# ============================================================================
# EXTRACTION NODES
# ============================================================================

def resume_parser_node(state: GraphState) -> Dict[str, Any]:
    """Parse and load resume PDF"""
    logger.info("STAGE: Resume Parser Node")
    
    try:
        parser = ResumeParser()
        resume_data = parser.process_resume(state["resume_file_path"])
        
        logger.info(f"Parsed resume: {resume_data['total_chunks']} chunks")
        
        return {
            "extracted_resume_data": {"raw_text": resume_data["normalized_text"]}
        }
    except Exception as e:
        logger.error(f"Resume parsing failed: {str(e)}")
        raise


def structured_extraction_node(state: GraphState) -> Dict[str, Any]:
    """Extract structured data from resume"""
    logger.info("STAGE: Structured Extraction Node")
    
    try:
        import asyncio
        extractor = StructuredExtractor()
        raw_text = state["extracted_resume_data"]["raw_text"]
        
        structured_data = asyncio.run(extractor.extract(raw_text))
        
        logger.info(f"Extracted: {len(structured_data.get('projects', []))} projects, {len(structured_data.get('skills', []))} skills")
        
        return {
            "extracted_resume_data": structured_data
        }
    except Exception as e:
        logger.error(f"Structured extraction failed: {str(e)}")
        raise


def claim_detector_node(state: GraphState) -> Dict[str, Any]:
    """Detect and organize claims from resume"""
    logger.info("STAGE: Claim Detector Node")
    
    try:
        extracted_data = state["extracted_resume_data"]
        claims = ClaimExtractor.extract_claims(extracted_data)
        
        prioritized = ClaimExtractor.prioritize_claims(claims)
        
        logger.info(f"Detected {len(prioritized)} claims (prioritized by severity)")
        
        return {
            "detected_claims": prioritized
        }
    except Exception as e:
        logger.error(f"Claim detection failed: {str(e)}")
        raise


# ============================================================================
# JD PROCESSING NODES
# ============================================================================

def jd_extractor_node(state: GraphState) -> Dict[str, Any]:
    """Extract structured data from Job Description"""
    logger.info("STAGE: JD Extractor Node")
    
    if not state.get("jd_text"):
        logger.warning("No JD provided, skipping JD extraction")
        return {"extracted_jd_data": {"job_title": "Unknown"}}
    
    try:
        import asyncio
        extractor = JDExtractor()
        jd_data = asyncio.run(extractor.extract_jd_requirements(state["jd_text"]))
        
        logger.info(f"Extracted JD: {jd_data.get('job_title')}, {len(jd_data.get('required_skills', []))} required skills")
        
        return {
            "extracted_jd_data": jd_data
        }
    except Exception as e:
        logger.error(f"JD extraction failed: {str(e)}")
        raise


# ============================================================================
# VERIFICATION NODES
# ============================================================================

def verification_orchestrator_node(state: GraphState) -> Dict[str, Any]:
    """Orchestrate all verification agents"""
    logger.info("STAGE: Verification Orchestrator Node")
    
    try:
        import asyncio
        engine = VerificationEngine()
        
        verification_results = asyncio.run(engine.verify_all_claims(
            state["extracted_resume_data"],
            state["detected_claims"]
        ))
        
        logger.info("Verification complete")
        
        return {
            "verification_results": verification_results
        }
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        raise


# ============================================================================
# SCORING NODES
# ============================================================================

def trust_scorer_node(state: GraphState) -> Dict[str, Any]:
    """Calculate trust scores for all claims"""
    logger.info("STAGE: Trust Scorer Node")
    
    try:
        claim_results = state.get("verification_results", {}).get("all_claim_results", [])
        
        trust_report = TrustScorer.score_all_claims(claim_results)
        
        logger.info(f"Trust Score: {trust_report['overall_trust_score']}/100 - {trust_report['overall_label']}")
        
        return {
            "trust_score_report": trust_report
        }
    except Exception as e:
        logger.error(f"Trust scoring failed: {str(e)}")
        raise


def completeness_scorer_node(state: GraphState) -> Dict[str, Any]:
    """Score resume completeness"""
    logger.info("STAGE: Completeness Scorer Node")
    
    try:
        completeness = TrustScorer.score_resume_completeness(state["extracted_resume_data"])
        
        logger.info(f"Resume Completeness: {completeness['percentage']}%")
        
        return {
            "resume_completeness_score": completeness
        }
    except Exception as e:
        logger.error(f"Completeness scoring failed: {str(e)}")
        raise


def ats_calculator_node(state: GraphState) -> Dict[str, Any]:
    """Calculate ATS score"""
    logger.info("STAGE: ATS Calculator Node")
    
    try:
        jd_text = state.get("jd_text", "")
        
        ats_report = ATSEngine.calculate_ats_score(
            jd_text=jd_text,
            extracted_data=state["extracted_resume_data"],
            claim_results=state.get("verification_results", {}).get("all_claim_results", []),
            verification_results=state.get("verification_results", {}),
            completeness_score=state.get("resume_completeness_score", {})
        )
        
        logger.info(f"ATS Score: {ats_report['ats_score']}/100 - {ats_report['ats_status']}")
        
        return {
            "ats_score_report": ats_report
        }
    except Exception as e:
        logger.error(f"ATS calculation failed: {str(e)}")
        raise


def red_flag_detector_node(state: GraphState) -> Dict[str, Any]:
    """Detect and compile red flags"""
    logger.info("STAGE: Red Flag Detector Node")
    
    try:
        red_flags = generate_red_flag_report(state.get("verification_results", {}))
        
        high_severity = [f for f in red_flags if f.get("severity") == "high"]
        logger.info(f"Found {len(red_flags)} red flags ({len(high_severity)} high severity)")
        
        return {
            "red_flags": red_flags
        }
    except Exception as e:
        logger.error(f"Red flag detection failed: {str(e)}")
        raise


# ============================================================================
# REPORT GENERATION NODES
# ============================================================================

def executive_summary_node(state: GraphState) -> Dict[str, Any]:
    """Generate executive summary with recommendation"""
    logger.info("STAGE: Executive Summary Node")
    
    try:
        summary = generate_executive_summary(
            ats_score=state.get("ats_score_report", {}),
            trust_score=state.get("trust_score_report", {}),
            red_flags=state.get("red_flags", [])
        )
        
        logger.info(f"Recommendation: {summary['recommendation']}")
        
        return {
            "executive_summary": summary
        }
    except Exception as e:
        logger.error(f"Executive summary generation failed: {str(e)}")
        raise


def final_report_generator_node(state: GraphState) -> Dict[str, Any]:
    """Generate comprehensive final report"""
    logger.info("STAGE: Final Report Generator Node")
    
    try:
        final_report = {
            "resume_analysis": state.get("extracted_resume_data", {}),
            "jd_analysis": state.get("extracted_jd_data", {}),
            "claims_detected": state.get("detected_claims", []),
            "verification_results": state.get("verification_results", {}),
            "trust_score": state.get("trust_score_report", {}),
            "ats_score": state.get("ats_score_report", {}),
            "resume_completeness": state.get("resume_completeness_score", {}),
            "red_flags": state.get("red_flags", []),
            "executive_summary": state.get("executive_summary", {}),
        }
        
        logger.info("Final report generated successfully")
        
        return {
            "final_report": final_report
        }
    except Exception as e:
        logger.error(f"Final report generation failed: {str(e)}")
        raise
