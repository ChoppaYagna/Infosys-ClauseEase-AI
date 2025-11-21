import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import os
from db import (
    get_all_accounts_from_master, 
    get_table_from_master, 
    get_table, 
    tenant_db_path,
    get_all_documents
)

# --------------------------
# ADMIN-ONLY HELPER FUNCTION
# (Moved from app.py)
# --------------------------
@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_all_documents_from_all_tenants():
    """
    Admin-only function.
    Fetches all documents from all tenant databases.
    """
    try:
        all_accounts_df = get_table_from_master("accounts")
        if 'is_admin' not in all_accounts_df.columns:
            st.error("Admin Dashboard Error: `is_admin` column missing from master `accounts` table.")
            return pd.DataFrame()
            
        tenant_list = all_accounts_df[all_accounts_df['is_admin'] == 0]['email'].tolist()
        
        if not tenant_list:
            return pd.DataFrame() 

        all_dfs = []
        for email in tenant_list:
            db_path = tenant_db_path(email)
            if os.path.exists(db_path):
                try:
                    tenant_docs_df = get_all_documents(db_path) 
                    tenant_docs_df['tenant_email'] = email
                    all_dfs.append(tenant_docs_df)
                except Exception as e:
                    print(f"Failed to read documents for tenant {email}: {e}")
        
        if not all_dfs:
            return pd.DataFrame() 

        master_doc_df = pd.concat(all_dfs, ignore_index=True)
        return master_doc_df
    
    except Exception as e:
        print(f"CRITICAL Error in get_all_documents_from_all_tenants: {e}")
        return pd.DataFrame()

# --------------------------
# MAIN ADMIN PAGE FUNCTION
# (Moved from app.py)
# --------------------------
def show_page(admin_selection_display):
    """
    Renders the entire Admin Panel based on the sidebar selection.
    """
    
    user_name = st.session_state.get("user_name", st.session_state.get("user_email", "User"))
    st.header(f"Welcome, {user_name.split(' ')[0]} (Admin)")
    st.divider()

    # --- Admin: User Management ---
    if admin_selection_display == "User Management":
        st.header("All System Accounts (from Master DB)")
        try:
            users_list = get_all_accounts_from_master()
            if not users_list:
                st.info("No accounts found in master database.")
            else:
                users_df = pd.DataFrame(users_list)
                display_cols = ['id', 'email', 'created_at', 'is_admin']
                existing_cols = [col for col in display_cols if col in users_df.columns]
                st.dataframe(users_df[existing_cols], use_container_width=True, height=360)
        except Exception as e: 
            st.write(f"Error loading users: {e}")

    # --- Admin: Tenant DB Inspector ---
    elif admin_selection_display == "Tenant DB Inspector":
        st.header("Tenant Database Inspector")
        st.warning("""
        **SECURITY & PERFORMANCE WARNING:**
        You are now viewing raw, private tenant data. This is a severe privacy violation
        and should **NEVER** exist in a production application.
        """)
        
        try:
            all_accounts_df = get_table_from_master("accounts")
            if 'is_admin' not in all_accounts_df.columns:
                st.error("Master 'accounts' table missing 'is_admin' column.")
                st.stop()
                
            tenant_list = all_accounts_df[all_accounts_df['is_admin'] == 0]['email'].tolist()
            
            if not tenant_list:
                st.warning("No tenant accounts found.")
            else:
                selected_tenant_email = st.selectbox("Select Tenant to Inspect", options=tenant_list, index=None, placeholder="Select a tenant...")
                
                if selected_tenant_email:
                    st.subheader(f"Raw Data for: {selected_tenant_email}")
                    tenant_db = tenant_db_path(selected_tenant_email)
                    
                    if not os.path.exists(tenant_db):
                        st.error(f"Tenant database not found for {selected_tenant_email}.")
                    else:
                        table_to_view = st.selectbox("Select Table to View", ["documents", "users", "glossary", "chat_history"])
                        
                        if table_to_view:
                            try:
                                raw_table_df = get_table(tenant_db, table_to_view)
                                st.info(f"Displaying raw table: {table_to_view}")
                                st.dataframe(raw_table_df, use_container_width=True)
                            except Exception as e:
                                st.error(f"Failed to read table '{table_to_view}' for tenant. Error: {e}")

        except Exception as e:
            st.error(f"Failed to load tenant inspector: {e}")

    # --- Admin: Reports (NOW INTERACTIVE) ---
    elif admin_selection_display == "Reports":
        st.header("Global Admin Reports")
        
        global_docs_df = None
        with st.spinner("Loading data from all tenants..."):
            global_docs_df = get_all_documents_from_all_tenants() 

        if global_docs_df is None or global_docs_df.empty:
            st.warning("No document data found across any tenants. Process a document to see stats.")
            st.stop()

        # --- *** NEW: INTERACTIVE FILTER *** ---
        st.subheader("Report Filter")
        tenant_list = global_docs_df['tenant_email'].unique().tolist()
        filter_options = ["All Users (Aggregated)"] + sorted(tenant_list)
        
        selected_filter = st.selectbox(
            "Select a user to view their specific data", 
            options=filter_options
        )
        st.divider()

        if selected_filter == "All Users (Aggregated)":
            data_to_display = global_docs_df.copy()
            st.info("Displaying aggregated data for all tenants.")
        else:
            data_to_display = global_docs_df[global_docs_df['tenant_email'] == selected_filter].copy()
            st.info(f"Displaying data for: {selected_filter}")
        # --- *** END NEW FILTER *** ---


        # --- 1. Top-Line Metrics (Now uses filtered data) ---
        st.subheader("System-Wide Statistics")
        total_docs = len(data_to_display)
        total_users = len(data_to_display['tenant_email'].unique())
        
        data_to_display['is_legal'] = pd.to_numeric(data_to_display['is_legal'], errors='coerce').fillna(-1)
        legal_docs_count = int(data_to_display[data_to_display['is_legal'] == 1].shape[0])

        col1, col2, col3 = st.columns(3)
        if selected_filter == "All Users (Aggregated)":
            col1.metric("Total Tenants (with docs)", total_users)
        else:
           col1.metric("Selected Tenant", selected_filter.split('@')[0], label_visibility="visible")
        col2.metric("Total Documents Processed", total_docs)
        col3.metric("Legal Docs Identified", legal_docs_count)
        
        st.divider()

        # --- 2. Graphs (Now uses filtered data) ---
        col_graph1, col_graph2 = st.columns(2)

        with col_graph1:
            st.subheader("Legal vs. Non-Legal Documents")
            try:
                # Calculate counts from the filtered data
                legal_count = int(data_to_display[data_to_display['is_legal'] == 1].shape[0])
                non_legal_count = int(data_to_display[data_to_display['is_legal'] == 0].shape[0])
                unknown_count = int(data_to_display[data_to_display['is_legal'] == -1].shape[0])
                
                pie_data = pd.DataFrame({
                    'type': ['Legal', 'Non-Legal', 'Unknown'],
                    'count': [legal_count, non_legal_count, unknown_count]
                })
                pie_data = pie_data[pie_data['count'] > 0] # Filter out zero-count slices

                if pie_data.empty:
                    st.info("No document type data to display.")
                else:
                    pie_chart = alt.Chart(pie_data).mark_arc(outerRadius=120).encode(
                        theta=alt.Theta("count:Q", stack=True),
                        color=alt.Color("type:N", legend=alt.Legend(title="Document Type")),
                        tooltip=['type', 'count']
                    ).properties(
                        title='Document Type Breakdown'
                    )
                    st.altair_chart(pie_chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to build pie chart: {e}")

        with col_graph2:
            st.subheader("Document Processing Activity")
            try:
                data_to_display['uploaded_at'] = pd.to_datetime(data_to_display['uploaded_at'], errors='coerce')
                activity_df = data_to_display.dropna(subset=['uploaded_at'])
                if not activity_df.empty:
                    activity_df = activity_df.set_index('uploaded_at').resample('D').size().reset_index(name='count')
                    
                    line_chart = alt.Chart(activity_df).mark_line(point=True).encode(
                        x=alt.X('uploaded_at:T', axis=alt.Axis(title='Date')),
                        y=alt.Y('count:Q', axis=alt.Axis(title='Documents Processed')),
                        tooltip=['uploaded_at:T', 'count:Q']
                    ).properties(
                        title='Documents Processed Per Day'
                    ).interactive()
                    st.altair_chart(line_chart, use_container_width=True)
                else:
                    st.info("No document activity to display.")
            except Exception as e:
                st.error(f"Failed to build activity chart: {e}")

        st.divider()

        # --- 3. More Graphs (Now uses filtered data) ---
        col_graph3, col_graph4 = st.columns(2)

        with col_graph3:
            st.subheader("Simplification Level Usage")
            try:
                level_data = data_to_display['simplification_level'].value_counts().reset_index()
                level_data.columns = ['Level', 'Count']
                
                if level_data.empty:
                    st.info("No simplification data to display.")
                else:
                    fig = px.pie(level_data, 
                                 names='Level', 
                                 values='Count', 
                                 title='Simplification Level Usage',
                                 hole=0.3)
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Failed to build Plotly pie chart: {e}")

        with col_graph4:
            st.subheader("Simplification Effectiveness")
            try:
                wc_df = data_to_display[
                    (data_to_display['original_word_count'] > 10) &
                    (data_to_display['simplified_word_count'] > 10)
                ].copy()
                
                if wc_df.empty:
                    st.info("No word count data available for this analysis.")
                else:
                    wc_df['reduction_pct'] = 100 * (
                        (wc_df['original_word_count'] - wc_df['simplified_word_count']) / wc_df['original_word_count']
                    )
                    
                    avg_reduction = wc_df['reduction_pct'].mean()
                    st.metric("Avg. Simplification (Word Count Reduction)", f"{avg_reduction:.1f}%")

                    hist_chart = alt.Chart(wc_df).mark_bar().encode(
                        x=alt.X('reduction_pct:Q', bin=alt.Bin(maxbins=20), title='Reduction %'),
                        y=alt.Y('count()', title='Number of Documents'),
                        tooltip=[alt.Tooltip('reduction_pct:Q', bin=alt.Bin(maxbins=20), title='Reduction %'), 'count()']
                    ).properties(
                        title='Histogram of Simplification Effectiveness'
                    ).interactive()
                    st.altair_chart(hist_chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to build effectiveness analysis: {e}")
        
        # --- 4. Tenant Activity (ONLY shows for "All Users") ---
        if selected_filter == "All Users (Aggregated)":
            st.divider()
            st.subheader("Tenant Activity")
            try:
                # Use the original global_docs_df for this chart
                user_activity_df = global_docs_df.groupby('tenant_email').size().reset_index(name='document_count')
                user_activity_df = user_activity_df.sort_values(by='document_count', ascending=False).head(15) # Top 15
                
                bar_chart_users = alt.Chart(user_activity_df).mark_bar().encode(
                    x=alt.X('document_count:Q', title='Documents Processed'),
                    y=alt.Y('tenant_email:N', title='Tenant Email', sort='-x'),
                    tooltip=['tenant_email', 'document_count']
                ).properties(
                    title='Top Tenants by Document Count'
                )
                st.altair_chart(bar_chart_users, use_container_width=True)
                
                with st.expander("View Raw Tenant Activity Data"):
                    st.dataframe(user_activity_df)
                    
            except Exception as e:
                st.error(f"Failed to build user activity chart: {e}")