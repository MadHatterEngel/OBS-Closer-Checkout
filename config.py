import os
import streamlit as st
from supabase import create_client, Client

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_PATH = os.path.join(DATA_DIR, "compliance.db") # No longer needed

STATION_TASKS = {
    "Fry Station": [
        "Oil filtered and vats scrubbed",
        "Backsplash degreased (zero carbon buildup)",
        "Floor drains cleared of debris"
    ],
    "Grill Station": [
        "Grates scraped and bricked to silver",
        "Drip pans emptied and sanitized",
        "Under-grill sweeps completed"
    ],
    "Prep / Walk-in": [
        "All open containers wrapped, dated, and labeled",
        "Floors swept and mopped",
        "Trash receptacles emptied and relined"
    ],
    "Line / Pass": [
        "Pass counter sanitized & heat lamps wiped down",
        "Refrigerated line drawers cleaned and restocked",
        "Cutting boards scrubbed and flipped"
    ]
}

@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["URL"]
    key = st.secrets["supabase"]["KEY"]
    return create_client(url, key)

# Initialize Supabase client
supabase: Client = init_connection()
