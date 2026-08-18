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
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');

        /* Global App Styling - Base Background (Bright Tan / Stucco from the building image) */
        .stApp {{
            background-color: #E6DBC6; /* Tan/Stucco */
            /* Adding a very subtle noise texture to mimic stucco */
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.05'/%3E%3C/svg%3E");
            font-family: 'Roboto', sans-serif;
            color: #2C2C2C; /* Deep Charcoal for general readability */
        }}

        /* Typography - Headers (Charcoal Trim Color) */
        h1, h2, h3, h4, h5, h6 {{
            color: #262626 !important; /* Charcoal black from building trim */
            font-family: 'Roboto', sans-serif !important;
            font-weight: 900 !important;
            letter-spacing: 0.5px;
        }}

        /* Input Fields & Text Areas (Light matching Stucco with charcoal border) */
        .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input {{
            background-color: #FDFBF7 !important;
            color: #262626 !important;
            border: 2px solid #262626 !important;
            border-radius: 2px;
            font-weight: bold;
        }}

        /* Button Styling - The Bright Signature Outback Red from the sign */
        .stButton>button {{
            background-color: #E41B23 !important; /* Bright Outback Red */
            color: #FFFFFF !important;
            border: none !important;
            text-transform: uppercase;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
            letter-spacing: 1px;
            border-radius: 4px;
            box-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            transition: none; /* No animations */
        }}

        /* Button hover/active (Terracotta Awning color) */
        .stButton>button:hover, .stButton>button:active {{
            background-color: #BA4A45 !important; /* Terracotta awning color */
            color: #FFFFFF !important;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.5) !important;
            transition: none;
        }}

        /* Disabled Button styling (Charcoal greyed out) */
        .stButton>button[disabled] {{
            background-color: #8C8C8C !important;
            color: #E6DBC6 !important;
            border: none !important;
            box-shadow: none !important;
            cursor: not-allowed !important;
        }}

        /* DataFrame / Tables (Light wood / neutral) */
        [data-testid="stTable"], [data-testid="stDataFrame"] {{
            background-color: rgba(253, 251, 247, 0.9) !important;
            border: 2px solid #262626 !important;
            border-radius: 2px;
            color: #262626 !important;
        }}

        /* Containers (Dark Wood Siding from building) */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {{
            background-color: #5E4633 !important; /* Medium-Dark Wood Siding Color */
            border: 3px solid #3E291B !important; /* Darker wood border */
            padding: 15px;
            border-radius: 4px;
            box-shadow: 4px 4px 8px rgba(0,0,0,0.2);
            color: #FDFBF7 !important; /* Force light text inside the dark wood containers */
        }}

        /* Override headers and markdown inside the dark wood containers to be readable */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] h1,
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] h2,
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] h3,
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] p,
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] span {{
            color: #FDFBF7 !important;
        }}

        /* Top Navigation/Header Bar Fixes */
        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}

        /* Warning/Error Banners (Terracotta/Red theme) */
        .stAlert {{
            background-color: rgba(228, 27, 35, 0.1) !important;
            border: 2px solid #E41B23 !important;
            color: #262626 !important;
            font-weight: bold;
        }}

        /* Success Banners */
        div[data-testid="stAlert"]:has(div:contains("PASSED")), div[data-testid="stAlert"]:has(div:contains("Verified")) {{
            background-color: rgba(85, 139, 47, 0.2) !important;
            border: 2px solid #558B2F !important;
            color: #262626 !important;
        }}

        /* Logo Styling */
        .mh-logo {{
            max-width: 250px;
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-bottom: 20px;
            /* Removed the heavy borders from previous theme to let the transparent SVG float cleanly */
        }}

        /* Tabs styling */
        button[data-baseweb="tab"] {{
            background-color: #FDFBF7 !important;
            color: #262626 !important;
            border: 2px solid #262626 !important;
            border-bottom: none !important;
            font-weight: bold;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: #262626 !important;
            color: #FDFBF7 !important;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )
