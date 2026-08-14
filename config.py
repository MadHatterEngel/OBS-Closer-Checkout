import os
import streamlit as st
from supabase import create_client, Client

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_PATH = os.path.join(DATA_DIR, "compliance.db") # No longer needed

@st.cache_resource
def init_connection():
    # Try multiple ways to retrieve the Supabase secrets
    url = None
    key = None

    if "supabase" in st.secrets:
        url = st.secrets["supabase"].get("URL")
        key = st.secrets["supabase"].get("KEY")

    if not url:
        url = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL"))
    if not key:
        key = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY"))

    if not url or not key:
        raise ValueError("Supabase URL or KEY not found in Streamlit secrets or environment variables.")

    return create_client(url, key)

# Initialize Supabase client
supabase: Client = init_connection()

@st.cache_data(ttl=600)
def fetch_station_tasks():
    """
    Fetches station tasks dynamically from the Supabase station_tasks table.
    Returns a dictionary mapping station names to a list of tasks.
    """
    try:
        response = supabase.table('station_tasks').select('station, task').execute()
        tasks_data = response.data

        # Group tasks by station
        station_tasks = {}
        for row in tasks_data:
            station = row['station']
            task = row['task']
            if station not in station_tasks:
                station_tasks[station] = []
            station_tasks[station].append(task)

        # Fallback to defaults if table is empty or missing
        if not station_tasks:
            raise ValueError("No tasks found in database")

        return station_tasks

    except Exception as e:
        print(f"Warning: Failed to fetch tasks from Supabase ({e}). Using fallback defaults.")
        return {
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
