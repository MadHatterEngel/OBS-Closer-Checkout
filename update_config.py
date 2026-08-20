import re

with open('config.py', 'r') as f:
    content = f.read()

# Make sure json is imported
if 'import json' not in content:
    content = "import json\n" + content

# Replace fetch_station_tasks function
new_fetch_func = '''@st.cache_data
def fetch_station_tasks():
    """
    Fetches station tasks dynamically from the Supabase station_tasks table.
    Returns a dictionary mapping station names to a list of task dictionaries.
    """
    try:
        response = supabase.table('station_tasks').select('station, task, day_of_week, details').execute()
        tasks_data = response.data

        # Group tasks by station
        station_tasks = {}
        for row in tasks_data:
            station = row['station']
            if station not in station_tasks:
                station_tasks[station] = []

            task_dict = {"task": row['task']}
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
                return json.load(f)
        except Exception as e2:
            print(f"Error loading defaults: {e2}")
            return {}
'''

content = re.sub(r'@st\.cache_data\ndef fetch_station_tasks\(\):.*?(?=\n\n|\Z)', new_fetch_func, content, flags=re.DOTALL)

with open('config.py', 'w') as f:
    f.write(content)
