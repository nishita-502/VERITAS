"""
VERITAS Streamlit Dashboard
Enterprise UI for Resume Verification
"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from src.agents.graph import build_workflow
from src.extraction import ResumeParser
from src.core.logging_config import get_logger

logger = get_logger(__name__)


def setup_page():
    """Configure Streamlit page"""
    st.set_page_config(
        page_title="VERITAS Resume Verification",
        page_icon="🕵️‍♂️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007BFF;
    }
    .trust-high {
        color: #28a745;
        font-weight: bold;
        font-size: 18px;
    }
    .trust-medium {
        color: #ffc107;
        font-weight: bold;
        font-size: 18px;
    }
    .trust-low {
        color: #dc3545;
        font-weight: bold;
        font-size: 18px;
    }
    .ats-score {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        padding: 20px;
    }
    .verified-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 10px 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .unverified-badge {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px 15px;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
    .partial-badge {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px 15px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    </style>
    """, unsafe_allow_html=True)


def render_resume_analysis_tab(final_report):
    """Render Resume Analysis Tab"""
    
    if not final_report or not final_report.get("resume_analysis"):
        st.warning("No resume analysis data available")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Extracted Resume Data")
        
        resume_data = final_report.get("resume_analysis", {})
        
        # Contact Information
        with st.expander("👤 Contact Information", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Name:** {resume_data.get('full_name', 'N/A')}")
                st.write(f"**Email:** {resume_data.get('email', 'N/A')}")
            with col_b:
                st.write(f"**Phone:** {resume_data.get('phone', 'N/A')}")
                st.write(f"**GitHub:** {resume_data.get('github_username', 'N/A')}")
        
        # Education
        with st.expander("🎓 Education", expanded=True):
            st.write(f"**University:** {resume_data.get('university', 'N/A')}")
            st.write(f"**CGPA:** {resume_data.get('cgpa', 'N/A')}")
            st.write(f"**Graduation Year:** {resume_data.get('graduation_year', 'N/A')}")
        
        # Skills
        if resume_data.get("skills"):
            with st.expander("🛠️ Skills", expanded=True):
                skills = resume_data.get("skills", [])
                cols = st.columns(3)
                for idx, skill in enumerate(skills):
                    with cols[idx % 3]:
                        st.write(f"• {skill}")
        
        # Projects
        if resume_data.get("projects"):
            with st.expander(f"📦 Projects ({len(resume_data.get('projects', []))})", expanded=True):
                for project in resume_data.get("projects", []):
                    st.write(f"**{project.get('name', 'Unknown Project')}**")
                    st.write(f"Description: {project.get('description', 'N/A')}")
                    st.write(f"Technologies: {', '.join(project.get('technologies', []))}")
                    st.write(f"Timeline: {project.get('timeline', 'N/A')}")
                    st.divider()
        
        # Work Experience
        if resume_data.get("work_experience"):
            with st.expander(f"💼 Work Experience ({len(resume_data.get('work_experience', []))})", expanded=True):
                for work in resume_data.get("work_experience", []):
                    st.write(f"**{work.get('company', 'Unknown')}** - {work.get('position', 'Position')}")
                    st.write(f"Period: {work.get('start_year', '?')}-{work.get('end_year', '?')}")
                    st.write(f"Description: {work.get('description', 'N/A')}")
                    st.divider()
    
    with col2:
        st.subheader("📊 Resume Completeness")
        completeness = final_report.get("resume_completeness", {})
        pct = completeness.get("percentage", 0)
        
        st.markdown(f"<div class='metric-card'><h2>{pct}%</h2><p>Overall Completeness</p></div>", unsafe_allow_html=True)
        
        if "scores" in completeness:
            scores_data = completeness["scores"]
            for category, score in scores_data.items():
                st.write(f"**{category.title()}:** {score} points")


def render_verification_dashboard_tab(final_report):
    """Render Verification Dashboard Tab"""
    
    st.subheader("🔍 Claim Verification Status")
    
    trust_report = final_report.get("trust_score", {})
    
    # Overall Trust Score
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = trust_report.get("overall_trust_score", 0)
        label = trust_report.get("overall_label", "Unknown")
        
        if score >= 85:
            css_class = "trust-high"
        elif score >= 70:
            css_class = "trust-medium"
        else:
            css_class = "trust-low"
        
        st.markdown(f"<div class='metric-card'><div class='{css_class}'>{score}/100</div><p>{label}</p></div>", unsafe_allow_html=True)
    
    with col2:
        summary = trust_report.get("summary", {})
        st.markdown(f"<div class='metric-card'><h3>{summary.get('verified', 0)}</h3><p>Verified Claims</p></div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"<div class='metric-card'><h3>{len(final_report.get('red_flags', []))}</h3><p>Red Flags</p></div>", unsafe_allow_html=True)
    
    # Claim Breakdown
    st.write("---")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("#### Claim Verification Breakdown")
        summary = trust_report.get("summary", {})
        percentages = trust_report.get("percentages", {})
        
        verification_data = {
            "Verified": percentages.get("verified", 0),
            "Partially Verified": percentages.get("partially_verified", 0),
            "Unverified": percentages.get("unverified", 0),
            "Flagged": percentages.get("flagged", 0),
        }
        
        df = pd.DataFrame(list(verification_data.items()), columns=["Status", "Percentage"])
        st.bar_chart(df.set_index("Status"))
    
    with col_b:
        st.write("#### Claims by Type")
        
        claims = final_report.get("claims_detected", [])
        claim_types = {}
        
        for claim in claims:
            claim_type = claim.get("claim_type", "unknown")
            claim_types[claim_type] = claim_types.get(claim_type, 0) + 1
        
        if claim_types:
            df_types = pd.DataFrame(list(claim_types.items()), columns=["Type", "Count"])
            st.bar_chart(df_types.set_index("Type"))
    
    # Detailed Claims
    st.write("---")
    st.write("#### Detailed Claim Verification")
    
    scored_claims = trust_report.get("scored_claims", [])
    
    for claim in scored_claims[:10]:  # Show top 10
        status = claim.get("status", "unverified")
        score = claim.get("trust_score", 0)
        
        if status == "verified":
            badge = "✅ VERIFIED"
            bg_color = "#d4edda"
        elif status == "partially_verified":
            badge = "⚠️ PARTIAL"
            bg_color = "#fff3cd"
        else:
            badge = "❌ UNVERIFIED"
            bg_color = "#f8d7da"
        
        st.markdown(f"""
        <div style='background-color: {bg_color}; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
            <strong>{badge}</strong> | <strong>{claim.get('claim_type', 'Unknown').upper()}</strong> | Score: {score}/100<br>
            <em>{claim.get('claim', 'N/A')}</em><br>
            <small>{claim.get('reasoning', 'No reasoning provided')}</small>
        </div>
        """, unsafe_allow_html=True)


def render_ats_match_tab(final_report):
    """Render ATS Match & JD Comparison Tab"""
    
    st.subheader("🎯 ATS Score & JD Matching")
    
    ats_report = final_report.get("ats_score", {})
    
    if not ats_report:
        st.warning("No JD provided. ATS score not calculated.")
        st.info("Upload a Job Description to see ATS matching analysis.")
        return
    
    # Main ATS Score
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.metric("ATS Score", f"{ats_report.get('ats_score', 0)}/100")
    
    with col2:
        status = ats_report.get("ats_status", "Unknown")
        st.info(f"**Status:** {status}")
    
    with col3:
        st.metric("Recommendation", "Review" if ats_report.get('ats_score', 0) < 60 else "Proceed")
    
    # ATS Breakdown
    st.write("---")
    st.subheader("📊 ATS Score Breakdown")
    
    breakdown = ats_report.get("breakdown", {})
    
    col_a, col_b, col_c, col_d = st.columns(4)
    
    metrics = [
        ("jd_skill_match", "JD Skill Match", col_a),
        ("verified_claims", "Verified Claims", col_b),
        ("resume_completeness", "Completeness", col_c),
        ("timeline_consistency", "Timeline", col_d),
    ]
    
    for key, label, col in metrics:
        if key in breakdown:
            data = breakdown[key]
            with col:
                pct = data.get("percentage", 0)
                weight = data.get("weight", 0)
                contribution = data.get("weighted_contribution", 0)
                
                st.metric(label, f"{pct}%")
                st.caption(f"Weight: {weight * 100:.0f}%")
                st.caption(f"Contribution: {contribution:.1f}")
    
    # Detailed Breakdown
    st.write("---")
    st.write("#### Skill Match Details")
    
    if "jd_skill_match" in breakdown:
        skill_data = breakdown["jd_skill_match"]["details"]
        
        col_x, col_y = st.columns(2)
        
        with col_x:
            st.write(f"**Matched Skills: {skill_data.get('match_count', 0)}/{skill_data.get('total_jd_skills', 0)}**")
            matched = skill_data.get("matched_skills", [])
            for skill in matched:
                st.write(f"✅ {skill}")
        
        with col_y:
            st.write(f"**Missing Skills:**")
            missing = skill_data.get("missing_skills", [])
            if missing:
                for skill in missing:
                    st.write(f"❌ {skill}")
            else:
                st.write("None - All skills present!")


def render_red_flags_analysis(final_report):
    """Render Red Flags Analysis Section"""
    
    st.subheader("⚠️ Red Flags & Concerns")
    
    red_flags = final_report.get("red_flags", [])
    
    if not red_flags:
        st.success("✅ No red flags detected!")
        return
    
    # Severity Distribution
    severity_counts = {}
    for flag in red_flags:
        severity = flag.get("severity", "unknown")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        for severity, count in severity_counts.items():
            if severity == "high":
                st.error(f"🔴 High Severity: {count}")
            elif severity == "medium":
                st.warning(f"🟡 Medium Severity: {count}")
            else:
                st.info(f"🔵 Low Severity: {count}")
    
    with col2:
        total = len(red_flags)
        st.metric("Total Red Flags", total)
    
    # Detailed Flags
    st.write("---")
    for idx, flag in enumerate(red_flags, 1):
        severity = flag.get("severity", "unknown").upper()
        description = flag.get("description", "No description")
        
        if severity == "HIGH":
            emoji = "🔴"
        elif severity == "MEDIUM":
            emoji = "🟡"
        else:
            emoji = "🔵"
        
        with st.expander(f"{emoji} [{severity}] Flag {idx}"):
            st.write(description)
            flag_type = flag.get("type", "unknown")
            st.caption(f"Type: {flag_type}")


def run_dashboard():
    """Run the Streamlit Dashboard"""
    
    setup_page()
    
    # Header
    st.title("🕵️‍♂️ VERITAS")
    st.markdown("**Enterprise-Grade Resume Verification System**")
    st.divider()
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Upload & Configure")
        
        uploaded_resume = st.file_uploader("Upload Resume (PDF)", type="pdf", key="resume_uploader")
        
        jd_input_method = st.radio("Job Description", ["Paste Text", "Skip"])
        jd_text = ""
        
        if jd_input_method == "Paste Text":
            jd_text = st.text_area("Paste JD here:", height=200)
        
        if uploaded_resume and st.button("🚀 Run Verification", use_container_width=True):
            
            # Save resume temp
            from src.core.config import DATA_DIR
            resume_path = DATA_DIR / uploaded_resume.name
            with open(resume_path, "wb") as f:
                f.write(uploaded_resume.getbuffer())
            
            with st.spinner("🔍 Running comprehensive verification..."):
                try:
                    app = build_workflow()
                    
                    inputs = {
                        "resume_file_path": str(resume_path),
                        "jd_text": jd_text,
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
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    total_steps = 11
                    current_step = 0
                    final_results = {}
                    
                    for output in app.stream(inputs):
                        for stage_name, stage_data in output.items():
                            current_step += 1
                            
                            # Calculate progress safely (clamp between 0.0 and 1.0)
                            progress = current_step / total_steps if total_steps > 0 else 0.0
                            progress = max(0.0, min(progress, 1.0))
                            
                            # Validate progress value
                            if not (0.0 <= progress <= 1.0):
                                logger.warning(f"Progress value out of range: {progress}, clamping to 1.0")
                                progress = 1.0
                            
                            progress_bar.progress(progress)
                            status_text.text(f"Processing: {stage_name.replace('_', ' ').title()}")
                            if stage_data:
                                final_results = stage_data
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    if final_results and "final_report" in final_results:
                        report = final_results.get("final_report")
                        if report:
                            st.session_state.final_report = report
                            st.success("✅ Verification complete!")
                            st.balloons()
                        else:
                            st.error("❌ Final report not generated properly")
                    else:
                        st.error("❌ Verification workflow did not complete properly")
                
                except Exception as e:
                    st.error(f"❌ Error during verification: {str(e)}")
                    logger.error(f"Verification error: {str(e)}")
    
    # Main Content - Tabs
    if "final_report" in st.session_state:
        final_report = st.session_state.final_report
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Resume Analysis",
            "🔍 Verification Dashboard",
            "🎯 ATS Match & JD",
            "⚠️ Red Flags"
        ])
        
        with tab1:
            render_resume_analysis_tab(final_report)
        
        with tab2:
            render_verification_dashboard_tab(final_report)
        
        with tab3:
            render_ats_match_tab(final_report)
        
        with tab4:
            render_red_flags_analysis(final_report)
        
        # Executive Summary
        st.divider()
        st.subheader("📌 Executive Summary & Recommendation")
        
        summary = final_report.get("executive_summary", {})
        if summary:
            st.write(f"### {summary.get('recommendation', 'Review Required')}")
            st.write(f"**Reasoning:** {summary.get('reasoning', 'N/A')}")
            
            col_summary1, col_summary2, col_summary3 = st.columns(3)
            with col_summary1:
                st.metric("Trust Score", f"{summary.get('ats_score', 0)}/100")
            with col_summary2:
                st.metric("ATS Score", f"{summary.get('trust_score', 0)}/100")
            with col_summary3:
                st.metric("High Severity Flags", summary.get('high_severity_flags', 0))
    else:
        st.info("👈 Upload a resume and JD (optional) to start verification.")


if __name__ == "__main__":
    run_dashboard()
