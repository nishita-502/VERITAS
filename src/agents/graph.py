"""
VERITAS Agent Graph - Orchestrates the entire verification workflow
"""
from langgraph.graph import END, StateGraph
from src.agents.state import GraphState
from src.agents.nodes import (
    resume_parser_node,
    structured_extraction_node,
    claim_detector_node,
    jd_extractor_node,
    verification_orchestrator_node,
    trust_scorer_node,
    completeness_scorer_node,
    ats_calculator_node,
    red_flag_detector_node,
    executive_summary_node,
    final_report_generator_node,
)
from src.core.logging_config import get_logger

logger = get_logger(__name__)


def build_workflow():
    """Build the comprehensive VERITAS verification workflow"""
    logger.info("Building VERITAS Verification Workflow")
    
    workflow = StateGraph(GraphState)

    # ========== EXTRACTION STAGE ==========
    workflow.add_node("resume_parser", resume_parser_node)
    workflow.add_node("structured_extraction", structured_extraction_node)
    workflow.add_node("claim_detector", claim_detector_node)
    
    # ========== JD PROCESSING STAGE ==========
    workflow.add_node("jd_extractor", jd_extractor_node)
    
    # ========== VERIFICATION STAGE ==========
    workflow.add_node("verification_orchestrator", verification_orchestrator_node)
    
    # ========== SCORING STAGE ==========
    workflow.add_node("trust_scorer", trust_scorer_node)
    workflow.add_node("completeness_scorer", completeness_scorer_node)
    workflow.add_node("ats_calculator", ats_calculator_node)
    workflow.add_node("red_flag_detector", red_flag_detector_node)
    
    # ========== REPORT GENERATION STAGE ==========
    workflow.add_node("executive_summary", executive_summary_node)
    workflow.add_node("final_report_generator", final_report_generator_node)

    # ========== DEFINE FLOW ==========
    # Entry point
    workflow.set_entry_point("resume_parser")
    
    # Extraction pipeline
    workflow.add_edge("resume_parser", "structured_extraction")
    workflow.add_edge("structured_extraction", "claim_detector")
    
    # Parallel: JD extraction (if JD provided)
    workflow.add_edge("claim_detector", "jd_extractor")
    
    # Verification starts after claims detected
    workflow.add_edge("claim_detector", "verification_orchestrator")
    
    # After verification, run scoring nodes in parallel
    workflow.add_edge("verification_orchestrator", "trust_scorer")
    workflow.add_edge("verification_orchestrator", "completeness_scorer")
    workflow.add_edge("verification_orchestrator", "red_flag_detector")
    
    # JD extractor completes independently
    workflow.add_edge("jd_extractor", "ats_calculator")
    
    # Wait for all scoring nodes before ATS calculator
    workflow.add_edge("trust_scorer", "ats_calculator")
    workflow.add_edge("completeness_scorer", "ats_calculator")
    workflow.add_edge("red_flag_detector", "ats_calculator")
    
    # Generate summary after all scores
    workflow.add_edge("ats_calculator", "executive_summary")
    
    # Final report generation
    workflow.add_edge("executive_summary", "final_report_generator")
    
    # End
    workflow.add_edge("final_report_generator", END)

    return workflow.compile()
