import json
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

@st.cache_data
def fetch_station_tasks():
    """
    Fetches station tasks dynamically from the Supabase station_tasks table.
    Returns a dictionary mapping station names to a list of task dictionaries.
    """
    try:
        try:
            response = supabase.table('station_tasks').select('id, station, task, day_of_week, details').execute()
        except Exception as sel_e:
            if 'PGRST204' in str(sel_e) or 'could not find' in str(sel_e).lower():
                response = supabase.table('station_tasks').select('id, station, task').execute()
            else:
                raise sel_e

        tasks_data = response.data

        # Group tasks by station
        station_tasks = {}
        for row in tasks_data:
            station = row['station']
            if station not in station_tasks:
                station_tasks[station] = []

            task_dict = {"id": row['id'], "task": row['task']}
            if row.get('day_of_week'):
                task_dict["day_of_week"] = row['day_of_week']
            if row.get('details'):
                task_dict["details"] = row['details']

            station_tasks[station].append(task_dict)

        # Fallback to defaults if table is empty or missing
        if not station_tasks:
            raise ValueError("No tasks found in database")

        return station_tasks

    except Exception as e:
        print(f"Warning: Failed to fetch tasks from Supabase ({e}). Using fallback defaults.")
        try:
            with open(os.path.join(DATA_DIR, 'default_tasks.json'), 'r') as f:
                data = json.load(f)
                mock_id = 1
                for station, tasks in data.items():
                    for task in tasks:
                        task['id'] = mock_id
                        mock_id += 1
                return data
        except Exception as e2:
            print(f"Error loading defaults: {e2}")
            return {}
