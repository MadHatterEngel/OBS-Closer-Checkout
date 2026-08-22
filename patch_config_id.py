import re

with open('config.py', 'r') as f:
    content = f.read()

# Update fetch_station_tasks to select 'id'
# old: response = supabase.table('station_tasks').select('station, task, day_of_week, details').execute()
# new: response = supabase.table('station_tasks').select('id, station, task, day_of_week, details').execute()
content = content.replace(
    "response = supabase.table('station_tasks').select('station, task, day_of_week, details').execute()",
    "response = supabase.table('station_tasks').select('id, station, task, day_of_week, details').execute()"
)

# old: task_dict = {"task": row['task']}
# new: task_dict = {"id": row['id'], "task": row['task']}
content = content.replace(
    "task_dict = {\"task\": row['task']}",
    "task_dict = {\"id\": row['id'], \"task\": row['task']}"
)

# old: with open(os.path.join(DATA_DIR, 'default_tasks.json'), 'r') as f:
#          return json.load(f)
# new: with open(os.path.join(DATA_DIR, 'default_tasks.json'), 'r') as f:
#          data = json.load(f)
#          # Add mock IDs for local fallback
#          mock_id = 1
#          for station, tasks in data.items():
#              for task in tasks:
#                  task['id'] = mock_id
#                  mock_id += 1
#          return data
old_fallback = """            with open(os.path.join(DATA_DIR, 'default_tasks.json'), 'r') as f:
                return json.load(f)"""
new_fallback = """            with open(os.path.join(DATA_DIR, 'default_tasks.json'), 'r') as f:
                data = json.load(f)
                mock_id = 1
                for station, tasks in data.items():
                    for task in tasks:
                        task['id'] = mock_id
                        mock_id += 1
                return data"""
content = content.replace(old_fallback, new_fallback)

with open('config.py', 'w') as f:
    f.write(content)
