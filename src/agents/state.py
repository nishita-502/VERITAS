# AgentState for VERITAS Resume Verification System
from typing import List, Dict, Any, TypedDict

try:
    from typing import NotRequired
except ImportError:  # Python 3.10 compatibility
    from typing_extensions import NotRequired

class GraphState(TypedDict):
    """
    State carried through the verification graph
    """
    # Input
    resume_file_path: str
    resume_file_bytes: NotRequired[bytes]
    jd_text: str
    
    # Extracted Data
    extracted_resume_data: Dict[str, Any]
    extracted_jd_data: Dict[str, Any]
    sanitized_resume_text: NotRequired[str]
    pii_redactions: NotRequired[List[Dict[str, Any]]]
    
    # Claims
    detected_claims: List[Dict[str, Any]]
    
    # Verification Results
    verification_results: Dict[str, Any]
    claim_verification_results: List[Dict[str, Any]]
    
    # Scoring
    trust_score_report: Dict[str, Any]
    ats_score_report: Dict[str, Any]
    resume_completeness_score: Dict[str, Any]
    red_flags: List[Dict[str, str]]
    
    # Final Report
    executive_summary: Dict[str, str]
    final_report: Dict[str, Any]

