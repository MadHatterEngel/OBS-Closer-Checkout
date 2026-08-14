import streamlit as st
import base64

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def apply_custom_css():
    try:
        bg_ext = "png"
        logo_ext = "png"
        bg_base64 = get_base64_of_bin_file("assets/background.png")
        logo_base64 = get_base64_of_bin_file("assets/logo.png")
    except Exception as e:
        bg_base64 = ""
        logo_base64 = ""
        print(f"Warning: Missing asset files - {e}")

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

        /* Global App Styling - Base Background */
        .stApp {{
            background-image: linear-gradient(rgba(5, 2, 11, 0.85), rgba(19, 8, 37, 0.9)), url("data:image/{bg_ext};base64,{bg_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            font-family: 'Share Tech Mono', monospace;
            color: #E8E2F2;
        }}

        /* Quantum Mad Hatter specific neon static glows */
        h1, h2, h3, h4, h5, h6 {{
            color: #FF00FF !important;
            text-shadow: 0 0 5px #FF00FF, 0 0 10px #FF00FF, 0 0 20px #8A2BE2;
            font-family: 'Share Tech Mono', monospace !important;
        }}

        /* Input Fields & Text Areas */
        .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input {{
            background-color: rgba(19, 8, 37, 0.7) !important;
            color: #00FFFF !important;
            border: 1px solid #FF00FF !important;
            box-shadow: 0 0 5px #FF00FF inset;
            border-radius: 5px;
        }}

        /* Button Styling - Static Neon Borders */
        .stButton>button {{
            background-color: rgba(5, 2, 11, 0.9) !important;
            color: #00FFFF !important;
            border: 2px solid #00FFFF !important;
            box-shadow: 0 0 10px #00FFFF;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: bold;
            border-radius: 8px;
            transition: none; /* No animations as strictly requested */
        }}

        /* Button hover/active (static color change only, no animation) */
        .stButton>button:hover, .stButton>button:active {{
            background-color: #00FFFF !important;
            color: #05020B !important;
            border-color: #FF00FF !important;
            box-shadow: 0 0 15px #FF00FF !important;
            transition: none;
        }}

        /* DataFrame / Tables */
        [data-testid="stTable"], [data-testid="stDataFrame"] {{
            background-color: rgba(19, 8, 37, 0.8) !important;
            border: 1px solid #FF00FF !important;
            border-radius: 8px;
        }}

        /* Containers */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {{
            background-color: rgba(5, 2, 11, 0.6) !important;
            border: 1px solid #8A2BE2 !important;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 0 8px #8A2BE2;
        }}

        /* Top Navigation/Header Bar Fixes */
        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}

        /* Add Logo at top left conceptually using css if stApp is selected, but best placed in sidebar/header via python.
           We'll provide a class to wrap logos safely */
        .mh-logo {{
            border-radius: 50%;
            box-shadow: 0 0 20px #FF00FF, 0 0 40px #00FFFF;
            border: 3px solid #8A2BE2;
            max-width: 150px;
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-bottom: 20px;
        }}

        /* Tabs styling */
        button[data-baseweb="tab"] {{
            background-color: rgba(5, 2, 11, 0.9) !important;
            color: #00FFFF !important;
            border: 1px solid #8A2BE2 !important;
            border-bottom: none !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: #FF00FF !important;
            color: #05020B !important;
            border-color: #FF00FF !important;
            box-shadow: 0 0 10px #FF00FF inset;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )
