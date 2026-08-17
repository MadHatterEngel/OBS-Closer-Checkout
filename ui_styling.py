import streamlit as st
import base64

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def apply_custom_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Rye&family=Roboto:wght@400;700&display=swap');

        /* Global App Styling - Base Background */
        .stApp {{
            background-color: #2E1B15; /* Deep dark warm brown */
            background-image: url("https://www.transparenttextures.com/patterns/wood-pattern.png"); /* Subtle wood texture */
            font-family: 'Roboto', sans-serif;
            color: #F4E8D1; /* Creamy off-white/beige for text */
        }}

        /* Typography - Rustic Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: #C0392B !important; /* Earthy Red */
            text-shadow: 1px 1px 2px #000000;
            font-family: 'Rye', cursive !important;
            letter-spacing: 1px;
        }}

        /* Input Fields & Text Areas */
        .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input {{
            background-color: #4A2E24 !important;
            color: #F4E8D1 !important;
            border: 1px solid #8B4513 !important;
            border-radius: 4px;
        }}

        /* Button Styling - Rustic & Warm */
        .stButton>button {{
            background-color: #8B4513 !important; /* Saddle Brown */
            color: #F4E8D1 !important;
            border: 2px solid #5C2E16 !important;
            text-transform: uppercase;
            font-family: 'Rye', cursive;
            font-size: 1.1rem !important;
            letter-spacing: 1px;
            border-radius: 4px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
            transition: none; /* No animations */
        }}

        /* Button hover/active (static color change only, no animation) */
        .stButton>button:hover, .stButton>button:active {{
            background-color: #C0392B !important; /* Switch to earthy red on hover */
            color: #FFFFFF !important;
            border-color: #8B0000 !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.8) !important;
            transition: none;
        }}

        /* DataFrame / Tables */
        [data-testid="stTable"], [data-testid="stDataFrame"] {{
            background-color: rgba(74, 46, 36, 0.9) !important;
            border: 2px solid #8B4513 !important;
            border-radius: 4px;
        }}

        /* Containers */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {{
            background-color: rgba(46, 27, 21, 0.8) !important;
            border: 2px solid #5C2E16 !important;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 4px 4px 10px rgba(0,0,0,0.6);
        }}

        /* Top Navigation/Header Bar Fixes */
        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}

        /* Warning/Error Banners */
        .stAlert {{
            background-color: rgba(192, 57, 43, 0.2) !important;
            border: 1px solid #C0392B !important;
            color: #F4E8D1 !important;
        }}

        /* Logo Styling */
        .mh-logo {{
            border-radius: 8px;
            border: 4px solid #8B4513;
            max-width: 150px;
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-bottom: 20px;
            box-shadow: 3px 3px 8px rgba(0,0,0,0.7);
        }}

        /* Tabs styling */
        button[data-baseweb="tab"] {{
            background-color: #4A2E24 !important;
            color: #F4E8D1 !important;
            border: 1px solid #8B4513 !important;
            border-bottom: none !important;
            font-family: 'Rye', cursive;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: #8B4513 !important;
            color: #FFFFFF !important;
            border-color: #5C2E16 !important;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )
