import streamlit as st
from db import get_user_and_doc_counts, get_all_documents
import pandas as pd
import altair as alt

def show_page(tenant_db, tenant_user_id):
    """
    Renders the main Dashboard page with stats and welcome message.
    """
    st.title(f"Welcome back, {st.session_state.get('user_name', 'User')}!")
    st.markdown("Here's a summary of your account. Use the workspace menu on the left to get started.")
    
    st.markdown("---")

    # --- 1. Top-Level Stats ---
    try:
        total_users, total_docs = get_user_and_doc_counts(tenant_db)
        
        # Get user-specific doc count
        all_docs_df = get_all_documents(tenant_db)
        user_docs_count = all_docs_df[all_docs_df['user_id'] == tenant_user_id].shape[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="metric-container">
                    <p class="metric-label">Your Processed Documents</p>
                    <p class="metric-value">{user_docs_count}</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="metric-container">
                    <p class="metric-label">Total Documents (All Users)</p>
                    <p class="metric-value">{total_docs}</p>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="metric-container">
                    <p class="metric-label">Total Users in Workspace</p>
                    <p class="metric-value">{total_users}</p>
                </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Failed to load dashboard metrics: {e}")
        
    st.markdown("---")

    # --- 2. Recent Documents Chart ---
    try:
        if user_docs_count > 0:
            st.subheader("Recent Activity")
            # Get last 5 documents
            user_docs_df = all_docs_df[all_docs_df['user_id'] == tenant_user_id].sort_values(by='uploaded_at', ascending=False).head(5)
            
            # Ensure 'uploaded_at' is datetime
            user_docs_df['uploaded_at'] = pd.to_datetime(user_docs_df['uploaded_at'])
            user_docs_df['Date'] = user_docs_df['uploaded_at'].dt.strftime('%Y-%m-%d')
            
            # Simple bar chart of original vs simplified word counts
            chart_data = user_docs_df[['document_title', 'original_word_count', 'simplified_word_count', 'Date']]
            chart_data = chart_data.melt('document_title', var_name='Version', value_name='Word Count')
            
            # Replace names for clarity
            chart_data['Version'] = chart_data['Version'].replace({
                'original_word_count': 'Original',
                'simplified_word_count': 'Simplified'
            })
            
            chart = alt.Chart(chart_data).mark_bar().encode(
                x=alt.X('document_title', title='Document Title', sort=None),
                y=alt.Y('Word Count', title='Word Count'),
                color=alt.Color('Version',
                                scale=alt.Scale(domain=['Original', 'Simplified'],
                                                range=['#D32F2F', '#00796B'])), # Red, Green
                tooltip=['document_title', 'Version', 'Word Count']
            ).properties(
                title='Word Count Comparison (Last 5 Docs)'
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("You haven't processed any documents yet. Go to 'Upload & Process' to get started.")

    except Exception as e:
        st.error(f"Failed to render chart: {e}")