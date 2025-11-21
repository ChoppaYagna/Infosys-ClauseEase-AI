import streamlit as st

def inject_css():
    """Injects all custom CSS into the Streamlit app."""
    theme_css = ""
    if st.session_state.theme == "dark":
        theme_css = """
        /* --- Dark Theme Overrides --- */
        :root {
            --primary-color: #4CAF50; --primary-color-dark: #388E3C; --text-color: #E0E0E0;
            --background-color: #101010; 
            --secondary-background-color: #1C1C1C; 
            --card-background-color: #262626;
            --border-color: #383838; --info-bg-color: #2E7D32; --warn-bg-color: #D32F2F;
            --non-legal-color: #FFCDD2; color-scheme: dark;
            
            /* --- NEW: Dark mode complexity colors --- */
            --word-simple-color: #C8E6C9;
            --word-simple-bg: #2E7D32;
            --word-medium-color: #FFECB3;
            --word-medium-bg: #E65100;
            --word-complex-color: #FFCDD2;
            --word-complex-bg: #C62828;
        }
        
        /* --- NEW: Complexity word styling (Dark) --- */
        .word-simple { color: var(--word-simple-color); background-color: var(--word-simple-bg); padding: 1px 3px; border-radius: 3px; }
        .word-medium { color: var(--word-medium-color); background-color: var(--word-medium-bg); padding: 1px 3px; border-radius: 3px; }
        .word-complex { color: var(--word-complex-color); background-color: var(--word-complex-bg); padding: 1px 3px; border-radius: 3px; }
        
        [data-testid="stAppViewContainer"] { background: var(--background-color); }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, var(--secondary-background-color), var(--background-color)); border-right: 1px solid var(--border-color); }
        .card { background-color: var(--card-background-color) !important; border: 1px solid var(--border-color) !important; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important; }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stSidebarNavToggler"] { color: var(--primary-color) !important; }
        [data-testid="stSidebarNavToggler"]:hover { color: var(--primary-color-dark) !important; }
        .stTextInput input, .stTextArea textarea { background-color: #333333 !important; color: var(--text-color) !important; border: 1.3px solid var(--border-color) !important; }
        .form-label, .small-muted, [data-testid="stCaption"] { color: var(--text-color) !important; }
        .doc-viewer { background-color: #1A1A1A !important; border: 1px solid var(--border-color) !important; }
        .doc-viewer[style*="background-color: #F8FBFB"] { background-color: #121A1A !important; }
        .doc-type-legal { background-color: var(--info-bg-color) !important; color: #FFF !important; }
        .doc-type-non-legal { background-color: var(--warn-bg-color) !important; color: #FFF !important; }
        .doc-type-unknown { background-color: var(--secondary-background-color) !important; color: var(--text-color) !important; }
        .stButton button { background-color: var(--primary-color) !important; color: white !important; }
        .stButton button:hover { background-color: var(--primary-color-dark) !important; }
        .stButton button[kind="secondary"] { background-color: var(--secondary-background-color) !important; color: var(--text-color) !important; border: 1px solid var(--border-color) !important; }
        .stButton button[kind="secondary"]:hover { background-color: #383838 !important; }
        .google-auth-button {
            background-color: var(--secondary-background-color) !important; 
            color: var(--text-color) !important; 
            border: 1px solid var(--border-color) !important;
            padding: 12px !important; border-radius: 8px !important;
            font-size: 14px !important; font-weight: 600 !important;
            text-decoration: none !important; width: 100%;
            text-align: center; box-sizing: border-box; 
            display: flex !important; align-items: center !important;
            justify-content: center !important; gap: 0.75rem !important;
        }
        .google-auth-button:hover {
            background-color: #383838 !important;
            color: var(--text-color) !important; 
            text-decoration: none !important;
        }
        .or-divider { color: var(--text-color) !important; }
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: var(--text-color) !important; }
        div[data-testid="stChatMessage"] { background-color: var(--card-background-color) !important; border: 1px solid var(--border-color) !important; }
        div[data-testid="stChatMessage"] p { color: var(--text-color) !important; }
        [data-testid="stPlotlyChart"] { background-color: transparent !important; }
        .history-item-container { border-bottom: 1px solid var(--border-color) !important; }
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3 { color: var(--primary-color) !important; }
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] li { color: var(--text-color) !important; }
        [data-testid="stTabs"] button { color: var(--text-color) !important; }
        [data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--primary-color) !important;
            border-bottom-color: var(--primary-color) !important;
        }
        .metric-value {
            color: var(--primary-color) !important;
        }
        .tooltip {
            background-color: rgba(212, 175, 55, 0.7);
            color: #000;
        }
        """

    static_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    :root { /* Light theme variables */
        --primary-color: #00796B; --primary-color-dark: #004D40; --non-legal-color: #D32F2F;
        --info-bg-color: #E0F2F1; --warn-bg-color: #FFEBEE; --text-color: #2E3D3D;
        --background-color: #F7F9F9; --secondary-background-color: #F4F7F6; --card-background-color: white;
        --border-color: #E0E7E7; color-scheme: light;

        /* --- NEW: Light mode complexity colors --- */
        --word-simple-color: #1B5E20;
        --word-simple-bg: #E8F5E9;
        --word-medium-color: #E65100;
        --word-medium-bg: #FFF3E0;
        --word-complex-color: #C62828;
        --word-complex-bg: #FFEBEE;
    }
    
    /* --- NEW: Complexity word styling (Light) --- */
    .word-simple { color: var(--word-simple-color); background-color: var(--word-simple-bg); padding: 1px 3px; border-radius: 3px; }
    .word-medium { color: var(--word-medium-color); background-color: var(--word-medium-bg); padding: 1px 3px; border-radius: 3px; }
    .word-complex { color: var(--word-complex-color); background-color: var(--word-complex-bg); padding: 1px 3px; border-radius: 3px; }

    [data-testid="stAppViewContainer"] { background: linear-gradient(135deg, var(--background-color) 0%, var(--secondary-background-color) 100%); }
    [data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; border-bottom: none !important; height: 0 !important; overflow: hidden; position: fixed !important; }
    [data-testid="stSidebarNavToggler"] { visibility: visible !important; position: fixed !important; top: 0.8rem !important; left: 1rem !important; z-index: 1000 !important; color: var(--primary-color) !important; background-color: transparent !important; border: none !important; font-size: 1.5rem !important; }
    [data-testid="stSidebarNavToggler"]::before { content: "☰"; font-size: 24px; }
    [data-testid="stSidebarNavToggler"]:hover { color: var(--primary-color-dark) !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stDeployButton { visibility: hidden !important; display: none !important; }
    .main > div { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    [data-testid="stHorizontalBlock"] { gap: 0.8rem !important; }
    .st-emotion-cache-ocqkz7, .st-emotion-cache-1tzf6as { padding: 0 !important; margin: 0 !important; }
    .row-widget.stButton { margin-top: 5px; }
    div[data-testid="stHorizontalBlock"]:has(div.image-container) { 
        align-items: stretch !important; 
    }
    div.image-container { display: flex !important; flex-direction: column !important; justify-content: center !important; height: 100% !important; background-color: transparent !important; padding: 1rem 0; animation: fadeIn 0.8s ease-out forwards; text-align: center; }
    .image-container img { background-color: transparent !important; padding: 0; max-width: 100%; height: auto; }
    .image-container h2, .image-container p { text-align: center !important; }
    .small-muted, [data-testid="stCaption"] { color: var(--text-color) !important; opacity: 1 !important; }
    iframe[src^="data:application/pdf"] { height: 70vh; min-height: 600px; width: 100%; border: none; }
    .card { background-color: var(--card-background-color) !important; border-radius: 12px; padding: 18px; border: 1px solid var(--border-color); box-shadow: 0 4px 12px rgba(38, 50, 56, 0.04); margin-bottom: 1rem; animation: fadeIn 0.5s ease-out; }
    .form-label { font-size: 14px; font-weight: 600; color: var(--text-color); margin-bottom: 8px; display: block; }
    .stTextInput input, .stTextArea textarea { width: 100%; padding: 16px 12px; border: 1.3px solid #B2DFDB; border-radius: 8px; font-size: 14px; margin-bottom: 16px; background-color: #ffffff; color: var(--text-color);}
    .stButton button { background-color: var(--primary-color) !important; color: white !important; border: none !important; padding: 12px !important; border-radius: 8px !important; font-size: 14px !important; font-weight: 600 !important; cursor: pointer !important; width: 100%; }
    .stButton button:hover { background-color: var(--primary-color-dark) !important; }
    .stButton button[kind="secondary"] { background-color: #ECEFF1 !important; color: #37474F !important; border: 1px solid #CFD8DC !important; }
    .stButton button[kind="secondary"]:hover { background-color: #CFD8DC !important; color: #263238 !important; }
    
    .google-auth-button {
        background-color: #ECEFF1 !important; 
        color: #37474F !important; 
        border: 1px solid #CFD8DC !important;
        padding: 12px !important; border-radius: 8px !important;
        font-size: 14px !important; font-weight: 600 !important;
        text-decoration: none !important; width: 100%;
        text-align: center; box-sizing: border-box; 
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.75rem !important;
    }
    .google-auth-button:hover {
        background-color: #CFD8DC !important;
        color: #263238 !important; 
        text-decoration: none !important;
    }
    .google-auth-button svg {
        width: 18px;
        height: 18px;
    }
    .or-divider { text-align: center; margin: 20px 0; color: #546E7A; font-size: 13px; font-weight: 500; position: relative; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(244,247,246,0.98)); border-right: 1px solid rgba(0, 77, 64, 0.06); padding-top: 4rem; }
    .doc-viewer { border-radius: 10px; border: 1px solid var(--border-color); background-color: #ffffff; height: 65vh; padding: 12px; overflow: auto; color: var(--text-color); }
    .stTextArea textarea:disabled {
        color: var(--text-color) !important;
        -webkit-text-fill-color: var(--text-color) !important; 
        opacity: 0.9 !important; 
        background-color: var(--secondary-background-color) !important;
    }
    .tooltip {
        position: relative;
        display: inline;
        background-color: rgba(255, 229, 100, 0.7);
        padding: 0 2px;
        border-radius: 3px;
        cursor: help;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 220px;
        background-color: #333;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 8px 10px;
        position: absolute;
        z-index: 10;
        bottom: 130%;
        left: 50%;
        margin-left: -110px;
        opacity: 0;
        transition: opacity 0.3s, visibility 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        font-size: 0.9em;
        font-weight: normal;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    [data-testid="stProgressBar"] > div { background-color: var(--primary-color); }
    .doc-type-label { display: inline-block; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px; text-align: center; width: 100%; margin-top: 5px; }
    .doc-type-legal { background-color: var(--info-bg-color); color: var(--primary-color-dark); }
    .doc-type-non-legal { background-color: var(--warn-bg-color); color: var(--non-legal-color); }
    .doc-type-unknown { background-color: #ECEFF1; color: #546E7A; }
    .history-item-container { border-bottom: 1px solid #f0f2f6; padding-bottom: 10px; margin-bottom: 10px; }
    .history-item-container:last-child { border-bottom: none; margin-bottom: 0; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    div[data-testid="stRadio"] > label > div[data-testid="stWidgetLabel"] {}
    div[data-testid="stRadio"] > div { padding-top: 0; }
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 { color: var(--primary-color-dark) !important; }
    div[data-testid="stStatusContainer"] { background-color: var(--card-background-color); border: 1px solid var(--border-color); border-radius: 0.5rem; padding: 1rem; }
    .metric-container {
        width: 100%;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-color);
        opacity: 0.8;
        margin-bottom: 0;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 600;
        color: var(--primary-color-dark);
        line-height: 1.2;
    }
    [data-testid="stTabs"] button {
        color: var(--text-color) !important;
        opacity: 0.7;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--primary-color) !important;
        border-bottom-color: var(--primary-color) !important;
        opacity: 1;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-weight: 600 !important; 
        color: var(--text-color) !important;
    }
    .st-emotion-cache-1r4qj8v p {
        font-weight: 600 !important;
        color: var(--text-color) !important;
    }
    """ 

    # --- *** START CSS FIX *** ---
    fixed_dynamic_and_closing_css = f"""
    {theme_css}
    
{'.st-emotion-cache-1r4qj8v p { font-weight: 600 !important; color: var(--text-color) !important; }' if st.session_state.theme == "dark" else ''}
    </style>
    """
    # --- *** END CSS FIX *** ---

    final_css = static_css + fixed_dynamic_and_closing_css 
    st.markdown(final_css, unsafe_allow_html=True)