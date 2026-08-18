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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

        /* Global App Styling - Clean, flat modern off-white */
        .stApp {{
            background-color: #FAFAF8;
            font-family: 'Inter', sans-serif;
            color: #1E1E1E;
        }}

        /* Typography - Sleek Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: #1E1E1E !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
            text-shadow: none !important;
        }}

        /* Input Fields & Text Areas - Flat and minimalistic */
        .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input {{
            background-color: #FFFFFF !important;
            color: #1E1E1E !important;
            border: 1px solid #D1D1D1 !important;
            border-radius: 6px;
            font-weight: 400;
            padding: 10px;
            box-shadow: none !important;
        }}

        /* Focus state for inputs */
        .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus {{
            border-color: #E41B23 !important;
            box-shadow: 0 0 0 2px rgba(228, 27, 35, 0.2) !important;
        }}

        /* Button Styling - Flat Modern Red */
        .stButton>button {{
            background-color: #E41B23 !important;
            color: #FFFFFF !important;
            border: none !important;
            text-transform: uppercase;
            font-weight: 800 !important;
            font-size: 1rem !important;
            letter-spacing: 0.5px;
            border-radius: 6px;
            box-shadow: none !important;
            transition: background-color 0.2s ease-in-out;
            padding: 10px 20px;
        }}

        /* Button hover/active (Smooth transition, no shadows) */
        .stButton>button:hover, .stButton>button:active {{
            background-color: #C0141D !important;
            color: #FFFFFF !important;
            box-shadow: none !important;
        }}

        /* Disabled Button styling (Flat Grey) */
        .stButton>button[disabled] {{
            background-color: #E0E0E0 !important;
            color: #A0A0A0 !important;
            border: none !important;
            box-shadow: none !important;
            cursor: not-allowed !important;
        }}

        /* DataFrame / Tables (Clean borders) */
        [data-testid="stTable"], [data-testid="stDataFrame"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #EAEAEA !important;
            border-radius: 8px;
            color: #1E1E1E !important;
        }}

        /* Containers (Sleek Flat Dark Grey/Brown) */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {{
            background-color: #2D2A28 !important; /* Very dark, sleek, neutral brown-grey */
            border: none !important;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05); /* Very subtle modern shadow */
            color: #FFFFFF !important;
        }}

        /* Text overrides inside dark containers */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] h1,
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] h2,
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] h3,
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] p,
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] span,
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] strong {{
            color: #FFFFFF !important;
        }}

        /* Top Navigation/Header Bar Fixes */
        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}

        /* Warning/Error Banners (Modern flat styles) */
        .stAlert {{
            background-color: rgba(228, 27, 35, 0.05) !important;
            border: 1px solid rgba(228, 27, 35, 0.2) !important;
            border-radius: 8px !important;
            color: #1E1E1E !important;
        }}

        /* Success Banners */
        div[data-testid="stAlert"]:has(div:contains("PASSED")), div[data-testid="stAlert"]:has(div:contains("Verified")), div[data-testid="stAlert"]:has(div:contains("successfully")) {{
            background-color: rgba(67, 160, 71, 0.05) !important;
            border: 1px solid rgba(67, 160, 71, 0.2) !important;
            color: #1E1E1E !important;
        }}

        /* Logo Styling */
        .mh-logo {{
            max-width: 200px;
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-bottom: 30px;
        }}

        /* Tabs styling */
        button[data-baseweb="tab"] {{
            background-color: transparent !important;
            color: #6C6C6C !important;
            border: none !important;
            border-bottom: 2px solid transparent !important;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            padding-bottom: 10px;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: #E41B23 !important;
            border-bottom: 2px solid #E41B23 !important;
            background-color: transparent !important;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )
