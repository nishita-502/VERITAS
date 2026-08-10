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
        st.markdown(f"<div class='metric-card'><h3>{summary.get('self_reported', 0)}</h3><p>Self-Reported Claims</p></div>", unsafe_allow_html=True)
    
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
            "Self-Reported": percentages.get("self_reported", 0),
            "Contradicted": percentages.get("contradicted", 0),
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
        elif status in {"self_reported", "unverified"}:
            badge = "ℹ️ SELF-REPORTED"
            bg_color = "#e7f1ff"
        else:
            badge = "🚩 CONTRADICTED"
            bg_color = "#f8d7da"
        
        st.markdown(f"""
        <div style='background-color: {bg_color}; padding: 15px; border-radius: 5px; margin-bottom: 10px;'>
            <strong>{badge}</strong> | <strong>{claim.get('claim_type', 'Unknown').upper()}</strong> | Score: {score}/100<br>
            <em>{claim.get('claim', 'N/A')}</em><br>
            <small>{claim.get('reasoning', 'No reasoning provided')}</small>
        </div>
        """, unsafe_allow_html=True)


def render_ats_match_tab(final_report):
    """Render ATS Match & JD Comparison Tab with TRANSPARENT scoring"""
    
    st.subheader("🎯 ATS Score & JD Matching")
    
    ats_report = final_report.get("ats_score", {})
    
    if not ats_report:
        st.warning("No JD provided. ATS score not calculated.")
        st.info("Upload a Job Description to see ATS matching analysis.")
        return
    
    # ========== MAIN ATS SCORE ==========
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        score = ats_report.get('ats_score', 0)
        st.markdown(f"<h1 style='text-align: center; color: #007BFF;'>{score}/100</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'><strong>ATS Score</strong></p>", unsafe_allow_html=True)
    
    with col2:
        status = ats_report.get("ats_status", "Unknown")
        st.info(f"**Status:** {status}")
        
        note = ats_report.get("note", "")
        if note:
            st.caption(f"ℹ️ {note}")
    
    with col3:
        if score >= 80:
            rec = "🟢 Strong"
        elif score >= 60:
            rec = "🟡 Review"
        else:
            rec = "🔴 Caution"
        
        st.markdown(f"<h4 style='text-align: center;'>{rec}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'><strong>Recommendation</strong></p>", unsafe_allow_html=True)
    
    # ========== ATS CRITERIA PANEL (VERY IMPORTANT) ==========
    st.write("---")
    st.subheader("📋 ATS Scoring Criteria & Weights")
    
    st.markdown("""
    This panel shows EXACTLY how the ATS score is calculated:
    """)
    
    # Create a visual criteria panel
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### Base Alignment: 100% of base score")
        st.info("""
        **JD Requirement Alignment** (70% of base score)
        - Uses structured JD requirements when available
        - Falls back to text skill extraction only when needed
        
        **Resume Completeness** (30% of base score)
        - Evaluates contact info, education, experience, and skills
        - Partial credit is awarded for each section present
        
        **Project Depth**
        - Informational only
        - Helps explain resume strength, but does not directly score
        """)
    
    with col_right:
        st.markdown("### External Evidence: Positive Boost")
        st.info("""
        **GitHub Verification**
        - Profile existence, targeted project search, and language footprint
        
        **Kaggle Verification**
        - Profile existence and activity signals
        
        **Competitive Programming**
        - Verified profile evidence from DSA platforms

        External evidence increases the score; lack of evidence does not reduce it.
        """)
    
    # ========== DETAILED BREAKDOWN ==========
    st.write("---")
    st.subheader("📊 Detailed Score Breakdown")
    
    breakdown = ats_report.get("breakdown", {})
    
    # Resume Strength Section
    if "base_alignment" in breakdown:
        with st.expander("💪 Base Alignment Section", expanded=True):
            rs = breakdown["base_alignment"]
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Base Alignment Contribution", f"{rs.get('contribution', 0):.1f} points")
            
            with col2:
                st.metric("Base Alignment Weight", "100% of base score")
            
            st.write("---")
            
            # JD Skill Match
            jd_match = rs.get("jd_requirement_alignment", {})
            st.write("#### 🔧 JD Requirement Alignment (70% of base)")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Match %", f"{jd_match.get('percentage', 0)}%")
            with col_b:
                st.metric("Weight", "70%")
            with col_c:
                st.metric("Contribution", f"{jd_match.get('weighted_contribution', 0):.1f}")
            
            details = jd_match.get("details", {})
            if details:
                st.write(f"**Matched Skills:** {details.get('match_count', 0)}/{details.get('total_jd_skills', 0)}")
                if details.get('matched_skills'):
                    st.write(f"✅ Found: {', '.join(details.get('matched_skills', [])[:5])}")
                if details.get('missing_skills'):
                    st.write(f"❌ Missing: {', '.join(details.get('missing_skills', [])[:5])}")
            
            st.write("\n")
            
            # Resume Completeness
            completeness = rs.get("resume_completeness", {})
            st.write("#### 📝 Resume Completeness (30% of base)")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Completeness %", f"{completeness.get('percentage', 0)}%")
            with col_b:
                st.metric("Weight", "30%")
            with col_c:
                st.metric("Contribution", f"{completeness.get('weighted_contribution', 0):.1f}")
            
            comp_details = completeness.get("details", {})
            st.caption(f"Score: {comp_details.get('percentage', 0)}/100")
            
            st.write("\n")
            
            # Project Depth
            project_depth = rs.get("project_depth", {})
            st.write("#### 🚀 Project Depth (informational)")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Depth %", f"{project_depth.get('percentage', 0)}%")
            with col_b:
                st.metric("Weight", "0%")
            with col_c:
                st.metric("Contribution", f"{project_depth.get('weighted_contribution', 0):.1f}")
            
            proj_details = project_depth.get("details", {})
            if proj_details:
                st.write(f"**Total Projects:** {proj_details.get('total_projects', 0)}")
    
    # External Verification Section
    if "external_verification" in breakdown:
        with st.expander("🔗 External Evidence Section", expanded=True):
            ev = breakdown["external_verification"]
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Boost Points", f"{ev.get('boost_points', 0):.1f}")
            
            with col2:
                st.metric("Evidence Strength", f"{ev.get('evidence_strength', 0)}%")
            
            st.write("---")
            
            st.write("#### Profile & Platform Verification")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Boost Multiplier", f"{ev.get('boost_multiplier', 0):.2f}")
            with col_b:
                st.metric("Weight", "0%")
            with col_c:
                st.metric("Contribution", f"{ev.get('boost_points', 0):.1f}")
            
            details = ev.get("details", {})
            if details:
                st.write(f"**GitHub Verification Score:** {details.get('github_verification', 0)} points")
                st.write(f"**Kaggle Verification Score:** {details.get('kaggle_verification', 0)} points")
                st.write(f"**Competitive Programming Score:** {details.get('competitive_programming', 0)} points")
                st.write(f"**Evidence Strength:** {details.get('evidence_strength', 0)}/100")
    
    # ========== SKILL VERIFICATION BREAKDOWN ==========
    st.write("---")
    st.subheader("💬 Individual Skill Verification Status")
    
    st.markdown("""
    For HR transparency: Each skill shows verification status with evidence
    """)
    
    # Get skill details from breakdown
    jd_match_details = breakdown.get("base_alignment", {}).get("jd_requirement_alignment", {}).get("details", {})
    matched_skills = jd_match_details.get("matched_skills", [])
    missing_skills = jd_match_details.get("missing_skills", [])
    
    if matched_skills:
        st.markdown("#### ✅ Verified Skills")
        for skill in matched_skills[:10]:
            st.write(f"🟢 **{skill}**")
    
    if missing_skills:
        st.markdown("#### ❌ Missing Skills (not found in resume)")
        for skill in missing_skills[:5]:
            st.write(f"🔴 **{skill}** - _Candidate does not have this skill_")
    
    # ========== COMPETITIVE PROGRAMMING VERIFICATION ==========
    st.write("---")
    st.subheader("🏆 Competitive Programming Verification (DSA)")
    
    verification_results = final_report.get("verification_results", {})
    dsa_verification = verification_results.get("competitive_programming", {})
    
    if dsa_verification:
        st.markdown("""
        Verification of candidates' competitive programming profiles helps validate 
        Data Structures & Algorithms expertise.
        """)
        
        platforms_verified = dsa_verification.get("platforms_verified", {})
        
        if platforms_verified:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("DSA Score", f"{dsa_verification.get('dsa_score', 0):.0f}/100")
            
            with col2:
                st.metric("Verified Platforms", f"{dsa_verification.get('verified_count', 0)}")
            
            with col3:
                st.metric("Total Platforms", f"{dsa_verification.get('total_platforms', 0)}")
            
            st.write("\n")
            
            # LeetCode
            if "leetcode" in platforms_verified:
                lc = platforms_verified["leetcode"]
                if lc.get("verified"):
                    st.markdown("#### ✅ LeetCode Verified")
                    col_lc1, col_lc2, col_lc3 = st.columns(3)
                    with col_lc1:
                        st.metric("Problems Solved", lc.get("problems_solved", 0))
                    with col_lc2:
                        st.metric("Total Problems", lc.get("total_problems", 0))
                    with col_lc3:
                        st.metric("Ranking", lc.get("ranking", "N/A"))
                else:
                    st.markdown("#### ❌ LeetCode Not Verified")
                    st.write("_No LeetCode profile found or not publicly visible_")
            
            # Codeforces
            if "codeforces" in platforms_verified:
                cf = platforms_verified["codeforces"]
                if cf.get("verified"):
                    st.markdown("#### ✅ Codeforces Verified")
                    col_cf1, col_cf2, col_cf3 = st.columns(3)
                    with col_cf1:
                        st.metric("Rating", cf.get("rating", 0))
                    with col_cf2:
                        st.metric("Max Rating", cf.get("max_rating", 0))
                    with col_cf3:
                        st.metric("Contributions", cf.get("contributions", 0))
                else:
                    st.markdown("#### ❌ Codeforces Not Verified")
                    st.write("_No Codeforces profile found_")
            
            # CodeChef
            if "codechef" in platforms_verified:
                cc = platforms_verified["codechef"]
                if cc.get("verified"):
                    st.markdown("#### ✅ CodeChef Verified")
                    col_cc1, col_cc2 = st.columns(2)
                    with col_cc1:
                        st.metric("Rating", cc.get("rating", 0))
                    with col_cc2:
                        st.metric("Problems Solved", cc.get("problems_solved", 0))
                else:
                    st.markdown("#### ❌ CodeChef Not Verified")
                    st.write("_No CodeChef profile found_")
            
            # HackerRank
            if "hackerrank" in platforms_verified:
                hr = platforms_verified["hackerrank"]
                if hr.get("verified"):
                    st.markdown("#### ✅ HackerRank Verified")
                    col_hr1, col_hr2 = st.columns(2)
                    with col_hr1:
                        st.metric("Badges Earned", hr.get("badge_count", 0))
                    with col_hr2:
                        st.metric("Problems Solved", hr.get("problem_solving_count", 0))
                else:
                    st.markdown("#### ❌ HackerRank Not Verified")
                    st.write("_No HackerRank profile found_")
        else:
            st.info("ℹ️ No competitive programming profiles found in resume")
    
    # ========== FORMULA DISPLAY ==========
    st.write("---")
    st.write("#### 📐 Scoring Formula Used")
    formula = ats_report.get("formula", "Not available")
    st.code(formula, language="text")
    
    st.info("""
    **Key Principle:** External verification strengthens the score, not destroys it.
    Absence of GitHub proof ≠ proof of dishonesty.
    """)

    if "base_alignment" in breakdown:
        skill_data = breakdown["base_alignment"]["jd_requirement_alignment"]["details"]
        
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


def render_github_tech_verification_tab(final_report):
    """Render GitHub & Tech Consistency Verification Tab"""
    
    st.subheader("🔗 GitHub & Technology Verification")
    
    verification_results = final_report.get("verification_results", {})
    github_verification = verification_results.get("github_verification")
    tech_consistency = verification_results.get("tech_consistency")
    
    if not github_verification:
        st.info("ℹ️ No GitHub username provided in resume")
        return
    
    # GitHub Profile Status
    col1, col2, col3 = st.columns(3)
    
    username = github_verification.get("username", "Unknown")
    
    with col1:
        if github_verification.get("user_profile", {}).get("exists"):
            st.success(f"✅ GitHub: @{username}")
        else:
            st.error(f"❌ GitHub: @{username} not found")
    
    with col2:
        public_repos = github_verification.get("user_profile", {}).get("public_repos", 0)
        st.metric("Public Repos", public_repos)
    
    with col3:
        followers = github_verification.get("user_profile", {}).get("followers", 0)
        st.metric("Followers", followers)
    
    # Tech Consistency
    st.write("---")
    st.subheader("⚙️ Technology Consistency Analysis")
    
    if tech_consistency:
        consistency_report = tech_consistency.get("consistency_report", {})
        consistency_score = consistency_report.get("consistency_score", 0) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Consistency Score", f"{consistency_score:.0f}%")
        
        with col2:
            verified_count = len(consistency_report.get("verified_skills", []))
            st.metric("Verified Skills", verified_count)
        
        with col3:
            partial_count = len(consistency_report.get("partially_verified_skills", []))
            st.metric("Partially Verified", partial_count)
        
        st.write("\n")
        
        # Verified Skills with Ecosystem Matching
        st.write("#### ✅ Verified Skills (Found in GitHub)")
        verified_skills = consistency_report.get("verified_skills", [])
        if verified_skills:
            for skill_info in verified_skills:
                skill = skill_info.get("skill", "")
                found_in = skill_info.get("found_in", "")
                match_type = skill_info.get("match_type", "direct")
                matched_with = skill_info.get("matched_with", "")
                
                if match_type == "semantic" and matched_with:
                    st.write(f"🟢 **{skill}** → Found as **{matched_with}** (semantic tech group)")
                else:
                    st.write(f"🟢 **{skill}** ✓ Verified")
        else:
            st.caption("No verified skills found")
        
        st.write("\n")
        
        # Partially Verified
        st.write("#### 🟡 Partially Verified Skills (Found in Projects/Work)")
        partial_skills = consistency_report.get("partially_verified_skills", [])
        if partial_skills:
            for skill_info in partial_skills:
                skill = skill_info.get("skill", "")
                found_in = skill_info.get("found_in", "")
                st.write(f"🟡 **{skill}** - Found in {found_in}")
        else:
            st.caption("No partially verified skills")
        
        st.write("\n")
        
        # Unverified Skills
        st.write("#### 🔴 Self-Reported Skills (Not externally confirmed)")
        unverified_skills = consistency_report.get("unverified_skills", [])
        if unverified_skills:
            st.write("These skills are currently self-reported and not externally confirmed:")
            for skill in unverified_skills[:10]:
                st.write(f"🔴 **{skill}**")
            if len(unverified_skills) > 10:
                st.write(f"... and {len(unverified_skills) - 10} more")
        else:
            st.success("✅ All claimed skills have external support!")
        
        st.write("\n")
        
        # Key Messages
        st.write("---")
        st.write("#### 📊 What This Means")
        
        if consistency_score >= 80:
            st.success("""
            🟢 **Strong Tech Stack Consistency**
            - Candidate's claimed skills strongly match GitHub portfolio
            - High confidence in technical expertise
            """)
        elif consistency_score >= 60:
            st.warning("""
            🟡 **Moderate Tech Stack Consistency**
            - Most claimed skills verified, but some gaps
            - Recommend verifying unmatched skills in interview
            """)
        else:
            st.error("""
            🔴 **Low Tech Stack Consistency**
            - Limited overlap between claims and external verification
            - Recommend detailed technical interview
            """)


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
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Resume Analysis",
            "🔗 GitHub & Tech Verification",
            "🔍 Verification Dashboard",
            "🎯 ATS Match & JD",
            "⚠️ Red Flags"
        ])
        
        with tab1:
            render_resume_analysis_tab(final_report)
        
        with tab2:
            render_github_tech_verification_tab(final_report)
        
        with tab3:
            render_verification_dashboard_tab(final_report)
        
        with tab4:
            render_ats_match_tab(final_report)
        
        with tab5:
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
