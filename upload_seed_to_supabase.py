import os
import json
import toml
from supabase import create_client, Client

# Try to get credentials from secrets or env
try:
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets['supabase']['URL']
    key = secrets['supabase']['KEY']
except FileNotFoundError:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Please set SUPABASE_URL and SUPABASE_KEY in your environment variables.")
    exit(1)

supabase: Client = create_client(url, key)

with open('default_tasks.json', 'r') as f:
    tasks_data = json.load(f)

for station, tasks in tasks_data.items():
    print(f"Uploading tasks for {station}...")
    for t in tasks:
        insert_data = {
            "station": station,
            "task": t.get("task")
        }
        if t.get("day_of_week"):
            insert_data["day_of_week"] = t.get("day_of_week")
        if t.get("details"):
            insert_data["details"] = t.get("details")

        supabase.table("station_tasks").insert(insert_data).execute()

print("✅ Successfully seeded Supabase database with all new task lists!")
