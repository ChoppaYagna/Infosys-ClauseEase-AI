import streamlit as st
import time
from db import save_document, update_glossary_from_ai_output
from utils import get_word_count, is_likely_legal

# --- NEW: Import the readability analyzer ---
from readability import analyze_readability

def process_document_logic(tenant_db, tenant_user_id, source_type):
    """Handles the core processing steps (Single-Level) with st.status() container."""
    
    # --- LAZY LOAD HEAVY MODULES ---
    import models
    # from readability import analyze_readability # <-- Already imported above
    
    status = None
    current_step = "Initialization"
    try:
        with st.status("Processing document...", expanded=True) as status_context:
            status = status_context

            # Step 1: Extract Text (Already done in upload_view)
            current_step = "Validating Text"
            st.write(f"{current_step}...")
            if st.session_state.current_text is None:
                raise ValueError("No text found to process.")
            time.sleep(0.2)

            # --- Step 2: RAG Building (Now uses cached models) ---
            current_step = "Building RAG Model"
            st.write(f"{current_step}...")
            try:
                st.session_state.rag_chain = models.create_rag_chain(st.session_state.current_text)
                if isinstance(st.session_state.rag_chain, str) and st.session_state.rag_chain.startswith("Error:"):
                    raise ValueError(st.session_state.rag_chain)
                st.session_state.model_ready = hasattr(st.session_state.rag_chain, 'query')
                if not st.session_state.model_ready:
                    raise ValueError("RAG chain creation returned an unknown object type (missing .query method).")
            except Exception as e:
                raise ValueError(f"Failed during RAG Building step: {e}") from e
            time.sleep(0.5)

            # --- Step 3: Single-Level Simplification (Now uses cached models) ---
            chosen_level = st.session_state.simplification_level
            
            current_step = f"Simplifying Text ({chosen_level})"
            st.write(f"{current_step} using {st.session_state.simplification_model}...")
            try:
                s_text = models.simplify_text(
                    st.session_state.current_text, 
                    model_choice=st.session_state.simplification_model, 
                    level=chosen_level
                )
                st.session_state.simplified_text = s_text
                if "Error:" in str(s_text):
                    raise ValueError(f"Simplification failed: {s_text}")
            except Exception as e:
                st.session_state.simplified_text = None
                raise ValueError(f"Failed during Simplification step: {e}") from e
            
            time.sleep(0.5)

            # --- Step 4: Readability Analysis (NOW ANALYZES BOTH) ---
            current_step = "Analyzing Readability"
            st.write(f"{current_step}...")
            try:
                # --- START FIX ---
                # 1. Analyze Original Text
                st.session_state.doc_analytics = analyze_readability(st.session_state.current_text)
                
                # 2. Analyze Simplified Text
                st.session_state.simplified_doc_analytics = analyze_readability(st.session_state.simplified_text)
                
                # 3. Run original legal check
                st.session_state.is_likely_legal = is_likely_legal(st.session_state.current_text)
                # --- END FIX ---
            except Exception as analysis_e:
                st.warning(f"Readability/Legal analysis failed: {analysis_e}")
                st.session_state.doc_analytics = None
                st.session_state.simplified_doc_analytics = None # <-- NEW
                st.session_state.is_likely_legal = None
            time.sleep(0.2)

            # --- Step 4.5: AI Issue & Risk Analysis ---
            current_step = "AI Issue & Risk Analysis"
            st.write(f"{current_step}...")
            try:
                st.session_state.ai_issues = models.get_ai_analysis(
                    st.session_state.current_text,
                    analysis_type="issues",
                    model="mistralai/mistral-7b-instruct:free" 
                )
                st.session_state.ai_risks = models.get_ai_analysis(
                    st.session_state.current_text,
                    analysis_type="risks",
                    model="mistralai/mistral-7b-instruct:free"
                )
            except Exception as ai_e:
                st.warning(f"AI analysis failed: {ai_e}")
                st.session_state.ai_issues = []
                st.session_state.ai_risks = []
            time.sleep(0.1)
            
            # --- Prepare Analytics Data for Saving ---
            is_legal_flag = 1 if st.session_state.is_likely_legal is True else (0 if st.session_state.is_likely_legal is False else -1)
            wc_orig = get_word_count(st.session_state.current_text)
            wc_simple = get_word_count(st.session_state.simplified_text)

            # --- Step 5: Saving Document ---
            current_step = "Saving Document"
            st.write(f"{current_step} to database...")
            
            doc_id = save_document(
                tenant_db, tenant_user_id, st.session_state.uploaded_file_name,
                st.session_state.current_title, st.session_state.current_text,
                st.session_state.simplified_text,    
                chosen_level,                    
                is_legal_flag,                   
                wc_orig,                         
                wc_simple                        
            )
            st.session_state.current_document_id = int(doc_id)
            time.sleep(0.3)

            # --- Step 6: Auto-Glossary Update ---
            current_step = "Updating Glossary"
            st.write(f"{current_step}...")
            try:
                if st.session_state.simplified_text:
                    update_glossary_from_ai_output(
                        tenant_db,
                        st.session_state.current_text,
                        st.session_state.simplified_text
                    )
                time.sleep(0.1)
            except Exception as glossary_update_e:
                st.warning(f"Automatic glossary update failed: {glossary_update_e}")
            
            status.update(label="Processing Complete!", state="complete", expanded=False)
        time.sleep(1)
        return True

    except Exception as e:
        error_message = f"Processing Failed at step '{current_step}': {e}"
        if status:
             status.update(label=error_message, state="error", expanded=True)
        else:
             st.error(error_message)

        st.session_state.model_ready = False
        st.session_state.simplified_text = None
        st.session_state.doc_analytics = None
        st.session_state.simplified_doc_analytics = None # <-- NEW
        st.session_state.rag_chain = None
        return False