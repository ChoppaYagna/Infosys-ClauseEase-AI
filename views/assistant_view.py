import streamlit as st
import pandas as pd
import altair as alt
from db import get_glossary_terms
# --- FIX: Added missing imports ---
from readability import highlight_legal_terms, analyze_readability, color_code_complexity

def show_page(tenant_db, tenant_user_id):
    """
    Renders the "Legal Assistant" comparison and analysis page.
    """
    col_preview, col_simplify, col_analysis = st.columns([2, 2, 1], gap="medium")
    glossary_terms = {}
    
    try:
        glossary_terms = get_glossary_terms(tenant_db)
        # glossary_loaded = bool(glossary_terms) # This check is no longer needed
    except Exception as e:
        st.error(f"Glossary load error: {e}")

    # --- Original Text Column (FIXED to use Glossary Highlights) ---
    with col_preview:
        st.subheader("Extracted Document Text") # Icon removed
        current_text = st.session_state.get("current_text")
        if current_text:
            try:
                # --- THIS IS THE FIX ---
                # Call the correct function for glossary tooltips
                highlighted_html = highlight_legal_terms(current_text, glossary_terms) 
                st.markdown(f'<div class="doc-viewer">{highlighted_html}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error generating highlights: {e}")
                # Fallback to plain text
                st.markdown(f'<div class="doc-viewer" style="white-space: pre-wrap;">{current_text}</div>', unsafe_allow_html=True) 
        else:
            st.markdown('<div class="doc-viewer">No document processed or loaded.</div>', unsafe_allow_html=True)
    # --- END FIX ---


    # --- Simplified Text Column (FIXED to ALWAYS show Glossary Highlights) ---
    with col_simplify:
        model_name = st.session_state.get("simplification_model", "N/A")
        st.subheader(f"Simplified Version ({model_name})") # Icon removed
        
        level = st.session_state.get("simplification_level", "N/A")
        st.caption(f"Simplification Level Chosen: **{level}**")
        
        simplified_text = st.session_state.get("simplified_text")

        if simplified_text:
            if "Error:" in str(simplified_text):
                st.error(f"Simplification failed: {simplified_text}")
            else:
                # --- THIS IS THE FIX ---
                # Always try to highlight. The function is safe even if glossary_terms is empty.
                try:
                    highlighted_simplified = highlight_legal_terms(simplified_text, glossary_terms)
                    st.markdown(f'<div class="doc-viewer" style="background-color: #F8FBFB;">{highlighted_simplified}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Highlight error (simplified): {e}")
                    # Fallback to plain text
                    st.markdown(f'<div class="doc-viewer" style="background-color: #F8FBFB; white-space: pre-wrap;">{simplified_text}</div>', unsafe_allow_html=True) 
                # --- END FIX ---
        else:
            st.markdown('<div class="doc-viewer" style="background-color: #F8FBFB;">No simplified text available.</div>', unsafe_allow_html=True)

    # --- Analysis Column ---
    with col_analysis:
        st.subheader("Document Type") # Icon removed
        is_legal = st.session_state.get("is_likely_legal")
        
        # Cleaned up logic for displaying document type
        if is_legal is True: 
            st.markdown('<span class="doc-type-legal">Likely Legal Document</span>', unsafe_allow_html=True)
        elif is_legal is False: 
            st.markdown('<span class="doc-type-non-legal">Likely Non-Legal Document</span>', unsafe_allow_html=True)
        elif st.session_state.current_text:
             st.info("Analysis Pending/Failed")
        else: 
            st.info("No document analyzed.")


        st.subheader("Readability Score") # Icon removed
        analytics = st.session_state.get("doc_analytics")
        if analytics and isinstance(analytics, dict):
            ease = analytics.get("flesch_ease", 0)
            ease_pct = int(max(0, min(100, ease)))
            st.progress(ease_pct / 100)
            
            lvl = "Very Difficult"
            if ease >= 80: lvl = "Very Easy"
            elif ease >= 60: lvl = "Easy"
            elif ease >= 30: lvl = "Difficult"
            
            st.markdown(f"**Score: {ease:.1f}** ({lvl})")
            st.caption("Flesch-Kincaid Ease")
        else:
            st.progress(0)
            st.markdown('<span style="color: #546E7A;">Not calculated</span>', unsafe_allow_html=True)

        st.subheader("Issues Detected") # Icon removed
        current_text = st.session_state.get("current_text")
        
        if current_text:
            if is_legal is True:
                issues = st.session_state.get("ai_issues", [])
                
                # Fallback simple check
                if not issues:
                    issues = []
                    text_lower = current_text.lower()
                    if "governing law" not in text_lower: issues.append("Governing Law clause potentially missing.")
                    if "liability" not in text_lower: issues.append("Liability clause potentially missing.")
                    if "termination" not in text_lower: issues.append("Termination clause potentially missing.")
                
                if issues:
                    for it in issues:
                        st.warning(f"- {it}")
                else:
                    st.success("No obvious major issues detected.")
            elif is_legal is False:
                st.info("No legal issues detected (document appears to be non-legal).")
            else:
                st.info("Analysis pending or document is too short.")
        else:
            st.markdown('<span style="color: #546E7A;">No document</span>', unsafe_allow_html=True)

    # --- Bottom Analytics Section ---
    st.markdown("---")
    col_analytics_detail, col_graph = st.columns([1, 2], gap="medium")
    
    with col_analytics_detail:
        st.subheader("Detailed Analytics") # Icon removed
        analytics = st.session_state.get("doc_analytics")
        if analytics and isinstance(analytics, dict):
            try:
                fk = analytics.get("flesch_kincaid", 0.0)
                fog = analytics.get("gunning_fog", 0.0)
                rt = analytics.get("read_time_minutes", 0)
                
                if fk > 0 or fog > 0 or rt > 0:
                   st.metric("FK Grade Level", f"{fk:.1f}")
                   st.metric("Gunning Fog", f"{fog:.1f}")
                   st.metric("Est. Read Time", f"{rt} min")
                else:
                    st.info("Analytics calculated but values are zero.")
            except Exception as e:
                st.error(f"Display error in detailed analytics: {e}.")
        elif st.session_state.current_text:
            st.warning("Analytics not calculated.")
        else:
            st.info("No document to analyze.")
    
    with col_graph:
        st.subheader("Estimated Clause Risk") # Icon removed
        
        ai_risks = st.session_state.get("ai_risks", [])
        
        if ai_risks:
            chart_data = pd.DataFrame([{"Risk": r} for r in ai_risks])
            st.dataframe(chart_data, use_container_width=True)
        else:
            # Fallback placeholder chart
            analytics = st.session_state.get("doc_analytics")
            if analytics and isinstance(analytics, dict):
                ease = analytics.get("flesch_ease", 50)
                factor = max(0.5, (100 - ease) / 40)
                issues_found = [max(1, round(c * factor)) for c in [10, 7, 5, 2]]
            else:
                issues_found = [1, 1, 1, 1]
            
            chart_data = pd.DataFrame({
                "Clause Type": ["Liability", "Payment", "Confidentiality", "Termination"],
                "Risk Score": issues_found
            })
            
            bins = [0, 5, 9, float('inf')]
            labels = ['Low', 'Medium', 'High']
            chart_data['Risk Level'] = pd.cut(chart_data['Risk Score'], bins=bins, labels=labels, right=False)
            domain_ = ['Low', 'Medium', 'High']
            range_ = ['#00796B', '#FFC107', '#D32F2F']
            
            try:
                chart = alt.Chart(chart_data).mark_bar().encode(
                    x=alt.X('Clause Type', sort=None, title=None, axis=alt.Axis(labels=True, ticks=False, domain=False, labelAngle=0)),
                    y=alt.Y('Risk Score', title='Estimated Risk Score'),
                    color=alt.Color('Risk Level',
                                    scale=alt.Scale(domain=domain_, range=range_),
                                    legend=alt.Legend(title="Risk Level")
                                    ),
                    tooltip=['Clause Type', 'Risk Score', 'Risk Level']
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
                st.caption("Note: Risk estimated from complexity.")
            except Exception as e:
                st.error(f"Failed to render chart: {e}")
                st.bar_chart(chart_data.set_index("Clause Type"))
        # --- END FIX ---