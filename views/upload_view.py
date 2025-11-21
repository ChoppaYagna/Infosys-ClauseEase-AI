import streamlit as st
import os
import base64
from PIL import Image
from db import get_all_documents, get_glossary_terms
from preprocess import extract_text_from_upload
# Note: You'll need to pass 'process_document_logic' into this function
# since it's defined in app.py

def show_page(tenant_db, tenant_user_id, process_document_logic_func):
    """
    Renders the "Upload & Process" page.
    """
    st.subheader("Upload & Process Document")
    col_left, col_right = st.columns([2, 1], gap="medium")
    
    with col_left:
        tab1, tab2 = st.tabs(["Upload a File", "Paste Text"])
        
        with tab1:
            uploaded_file = st.file_uploader(
                "Drag and drop file here", 
                type=['pdf', 'docx', 'txt', 'odt', 'png', 'jpg', 'jpeg'], 
                key="uploader_main", 
                label_visibility="collapsed", 
                on_change=lambda: st.session_state.update({
                    "uploaded_pdf_base64": None, "current_text": None, 
                    "simplified_text": None, "doc_analytics": None, "is_likely_legal": None
                })
            )
            
            level_selection_file = st.radio(
                "Select Simplification Level",
                options=["Basic", "Intermediate", "Advanced"],
                index=1, horizontal=True, key="level_radio_file"
            )
            
            opt_col1, opt_col2 = st.columns([1, 3])
            with opt_col1: 
                use_ocr = st.checkbox("Enable OCR", key="ocr_checkbox", help="Use for scanned PDFs & images")
            with opt_col2: 
                title_input = st.text_input("Title (optional)", placeholder="Display title...", key="title_input_file")

            if uploaded_file:
                # --- PREVIEW LOGIC ---
                file_name, file_extension = os.path.splitext(uploaded_file.name)
                file_extension = file_extension.lower()
                
                if file_extension == ".pdf":
                    try:
                        file_bytes = uploaded_file.getvalue()
                        uploaded_file.seek(0)
                        if 'uploaded_file_bytes_cache' not in st.session_state or st.session_state.uploaded_file_bytes_cache != file_bytes:
                            st.session_state.uploaded_file_bytes_cache = file_bytes
                            st.session_state.uploaded_pdf_base64 = base64.b64encode(file_bytes).decode('utf-8')
                            st.session_state.uploaded_file_name = uploaded_file.name
                        if st.session_state.uploaded_pdf_base64:
                            st.markdown("**PDF Preview**")
                            pdf_display = f'<iframe src="data:application/pdf;base64,{st.session_state.uploaded_pdf_base64}" width="100%" height="600px" type="application/pdf"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error creating PDF preview: {e}")
                
                elif file_extension in [".png", ".jpg", ".jpeg"]:
                    try:
                        image = Image.open(uploaded_file)
                        st.markdown("**Image Preview**")
                        st.image(image, caption=uploaded_file.name, use_column_width=True)
                    except Exception as e:
                        st.error(f"Error creating image preview: {e}")
                # ... (add your preview logic for .txt, .docx, .odt here if you have it) ...
            
            st.markdown("---")

            if uploaded_file:
                if st.button("Process File", width='stretch', type="primary", key="process_file_btn"):
                    st.session_state.simplification_level = level_selection_file
                    
                    st.session_state.update({k: None for k in ["current_text", "simplified_text", "doc_analytics", "current_document_id", "rag_chain", "is_likely_legal"]})
                    st.session_state.update({"model_ready": False, "chat_history": []})
                    st.session_state.uploaded_file_name = uploaded_file.name
                    st.session_state.current_title = title_input or uploaded_file.name
                    
                    try:
                        # --- FIX: ADDED ST.SPINNER ---
                        with st.spinner("Extracting text from document... Please wait."):
                            current_glossary_keys = list(get_glossary_terms(tenant_db).keys())
                            st.session_state.current_text = extract_text_from_upload(
                                uploaded_file=uploaded_file, 
                                use_ocr=use_ocr, 
                                glossary_words=current_glossary_keys
                            )
                        # --- END FIX ---
                            
                        if not st.session_state.current_text:
                            st.error("Text extraction failed or yielded no text.")
                        else:
                            # Use the function passed in from app.py
                            success = process_document_logic_func(tenant_db, tenant_user_id, source_type="file")
                            if success:
                                st.session_state.active_workspace_tab = "Legal Assistant"
                                st.rerun()
                    except Exception as e:
                        st.error(f"Failed to initiate processing: {e}")
            else:
                st.info("Upload a document to begin.")

        with tab2:
            pasted_text = st.text_area("Paste your text here...", height=200, key="pasted_text_input", max_chars=100000)
            
            level_selection_paste = st.radio(
                "Select Simplification Level",
                options=["Basic", "Intermediate", "Advanced"],
                index=1, horizontal=True, key="level_radio_paste"
            )
            
            paste_title_input = st.text_input("Title (optional)", placeholder="Display title...", key="title_input_paste")
            
            if st.button("Process Pasted Text", width='stretch', type="secondary", key="process_paste_btn"):
                if pasted_text and pasted_text.strip():
                    st.session_state.simplification_level = level_selection_paste
                    
                    st.session_state.update({k: None for k in ["current_text", "simplified_text", "doc_analytics", "current_document_id", "rag_chain", "is_likely_legal", "uploaded_pdf_base64"]})
                    st.session_state.update({"model_ready": False, "chat_history": []})

                    st.session_state.current_text = pasted_text.strip()
                    st.session_state.uploaded_file_name = "Pasted Text"
                    st.session_state.current_title = paste_title_input or "Pasted Document"
                    
                    # Use the function passed in from app.py
                    success = process_document_logic_func(tenant_db, tenant_user_id, source_type="paste")
                    if success:
                        st.session_state.active_workspace_tab = "Legal Assistant"
                        st.rerun()
                else:
                    st.warning("Please paste some text before processing.")

    with col_right:
        st.markdown("**Your Document History**")
        
        search_query = st.text_input(
            "Search history...", 
            placeholder="Search by title...", 
            label_visibility="collapsed", 
            key="history_search"
        )
        st.markdown("---")

        try:
            all_docs_df = get_all_documents(tenant_db)
            user_docs_df = all_docs_df[all_docs_df['user_id'] == tenant_user_id]

            if search_query:
                user_docs_df = user_docs_df[
                    user_docs_df['document_title'].str.contains(search_query, case=False, na=False)
                ]

            if not user_docs_df.empty:
                user_docs_df = user_docs_df.sort_values(by='uploaded_at', ascending=False)
                user_docs_list = user_docs_df.to_dict('records')
                
                for doc in user_docs_list:
                    with st.container():
                        st.markdown('<div class="history-item-container">', unsafe_allow_html=True)
                        title = doc.get('document_title', 'Untitled')
                        date_str = doc.get('uploaded_at', '')
                        if isinstance(date_str, str) and '.' in date_str: 
                            date_str = date_str.split('.')[0]
                        
                        col1_hist, col2_hist = st.columns([3, 1])
                        with col1_hist: 
                            st.markdown(f"**{title}**")
                        with col2_hist: 
                            st.caption(f"{date_str.split(' ')[0] if date_str else ''}")
                        st.markdown('</div>', unsafe_allow_html=True)
            
            else:
                if search_query:
                    st.info("No documents found matching your search.")
                else:
                    st.info("No documents processed yet.")

        except Exception as e: 
            st.error(f"History load error: {e}")