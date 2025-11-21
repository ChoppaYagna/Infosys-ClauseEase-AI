import streamlit as st
from db import add_glossary_term, get_glossary_terms, delete_glossary_term

def show_page(tenant_db, tenant_user_id):
    """
    Renders the "Glossary" management page.
    """
    st.header("Glossary Management")
    st.caption("Manage terms for your specific account. These will be highlighted in documents.")
    
    # --- Form to Add New Term ---
    st.subheader("Add/Update Glossary Term")
    with st.form("add_term_form"):
        new_term = st.text_input("Term")
        new_definition = st.text_area("Definition (Simplified Explanation)")
        submitted_add = st.form_submit_button("Save Term")
        
        if submitted_add:
            if new_term and new_definition:
                try:
                    ok, msg = add_glossary_term(tenant_db, new_term.strip(), new_definition.strip())
                    if ok:
                        st.success(msg)
                        st.rerun()  # Rerun to update the list below
                    else:
                        st.error(msg)
                except Exception as e:
                    st.error(f"Failed to add term: {e}")
            else:
                st.warning("Please enter both term and definition.")

    # --- List of Existing Terms ---
    st.subheader("Existing Terms")
    try:
        current_terms_dict = get_glossary_terms(tenant_db)
        if not current_terms_dict:
            st.info("Your glossary is currently empty.")
        else:
            sorted_terms = sorted(current_terms_dict.items())
            
            for term, definition in sorted_terms:
                col1_gloss, col2_gloss = st.columns([3, 1])
                with col1_gloss:
                    st.markdown(f"**{term.capitalize()}**") # Capitalize for display
                    st.caption(definition)
                
                with col2_gloss:
                    # Use the original (lowercase) term for the key and delete logic
                    if st.button("Delete", key=f"del_{term}", type="secondary", width='stretch'):
                        try:
                            ok, msg = delete_glossary_term(tenant_db, term)
                            if ok:
                                st.success(msg)
                                st.rerun() # Rerun to update the list
                            else:
                                st.error(msg)
                        except Exception as e:
                            st.error(f"Failed to delete term: {e}")
                
                st.markdown("---")
                
    except Exception as e:
        st.error(f"Error loading glossary terms: {e}")