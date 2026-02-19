"""
VERITAS CLI - Command Line Interface for Resume Verification
"""
import sys
from pathlib import Path
from src.agents.graph import build_workflow
from src.core.logging_config import get_logger

logger = get_logger(__name__)


def run_veritas_cli():
    """Run VERITAS verification system via CLI"""
    
    print("\n" + "="*60)
    print("🕵️‍♂️  VERITAS - THE SMART RECRUITER AGENT")
    print("Enterprise-Grade Resume Verification System")
    print("="*60)
    print("\nType 'exit' or 'quit' to stop the session.\n")
    
    logger.info("Starting VERITAS CLI")
    
    while True:
        try:
            # Get resume file path
            resume_path = input("📄 Enter resume file path (PDF): ").strip()
            
            if resume_path.lower() in ["exit", "quit"]:
                print("\nGoodbye! Ending session.")
                break
            
            if not resume_path:
                print("❌ Please provide a file path.\n")
                continue
            
            if not Path(resume_path).exists():
                print(f"❌ File not found: {resume_path}\n")
                continue
            
            # Get JD (optional)
            jd_input = input("📋 Enter job description text (or press Enter to skip): ").strip()
            
            # Build and run workflow
            print("\n🔍 Starting verification process...\n")
            
            app = build_workflow()
            
            inputs = {
                "resume_file_path": resume_path,
                "jd_text": jd_input,
                "extracted_resume_data": {},
                "extracted_jd_data": {},
                "detected_claims": [],
                "verification_results": {},
                "claim_verification_results": [],
                "trust_score_report": {},
                "ats_score_report": {},
                "resume_completeness_score": {},
                "red_flags": [],
                "executive_summary": {},
                "final_report": {},
            }
            
            # Stream results
            stage_count = 0
            final_results = {}
            
            for output in app.stream(inputs):
                for stage_name, stage_data in output.items():
                    stage_count += 1
                    status = "✅" if stage_data else "⏳"
                    print(f"{status} Stage {stage_count}: {stage_name.upper().replace('_', ' ')}")
                    final_results = stage_data
            
            # Display Results
            if final_results.get("final_report"):
                report = final_results["final_report"]
                
                print("\n" + "="*60)
                print("📊 VERIFICATION COMPLETE")
                print("="*60)
                
                # Executive Summary
                if report.get("executive_summary"):
                    summary = report["executive_summary"]
                    print(f"\n{summary.get('recommendation')}")
                    print(f"Reasoning: {summary.get('reasoning')}")
                
                # Trust Score
                if report.get("trust_score"):
                    ts = report["trust_score"]
                    print(f"\n✅ TRUST SCORE: {ts.get('overall_trust_score')}/100")
                    print(f"Status: {ts.get('overall_label')}")
                    print(f"Summary: {ts.get('summary')}")
                
                # ATS Score (if JD provided)
                if report.get("ats_score"):
                    ats = report["ats_score"]
                    print(f"\n🎯 ATS SCORE: {ats.get('ats_score')}/100 - {ats.get('ats_status')}")
                    
                    breakdown = ats.get("breakdown", {})
                    if breakdown:
                        print("\n📈 ATS BREAKDOWN:")
                        for metric, data in breakdown.items():
                            print(f"  • {metric.replace('_', ' ').title()}: {data.get('percentage')}%")
                
                # Resume Completeness
                if report.get("resume_completeness"):
                    completeness = report["resume_completeness"]
                    print(f"\n📝 RESUME COMPLETENESS: {completeness.get('percentage')}%")
                
                # Red Flags
                if report.get("red_flags"):
                    red_flags = report["red_flags"]
                    if red_flags:
                        print(f"\n⚠️  RED FLAGS ({len(red_flags)}):")
                        for flag in red_flags[:5]:  # Show top 5
                            severity = f"[{flag.get('severity').upper()}]"
                            print(f"  • {severity} {flag.get('description')}")
                
                print("\n" + "="*60 + "\n")
            
            # Ask for another verification
            again = input("Run another verification? (y/n): ").strip().lower()
            if again != "y":
                print("\nGoodbye! Thank you for using VERITAS.")
                break
                
        except KeyboardInterrupt:
            print("\n\nSession interrupted by user. Closing...")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            print(f"\n❌ Error occurred: {str(e)}")
            print("Please try again or type 'exit' to quit.\n")


if __name__ == "__main__":
    try:
        run_veritas_cli()
    except KeyboardInterrupt:
        print("\n\nSession terminated.")
        sys.exit(0)
