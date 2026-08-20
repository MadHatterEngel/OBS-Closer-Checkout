import re
with open('app.py', 'r') as f:
    content = f.read()

# Replace tasks_for_station = STATION_TASKS[station] with day filtering logic
new_tasks_logic = '''import datetime
current_day = datetime.datetime.now().strftime('%A')
raw_tasks_for_station = STATION_TASKS[station]

filtered_tasks = []
daily_tasks = []
for t in raw_tasks_for_station:
    if t.get("day_of_week"):
        if t["day_of_week"] == current_day:
            daily_tasks.append(t)
    else:
        filtered_tasks.append(t)

# Daily tasks at the bottom
tasks_for_station = filtered_tasks + daily_tasks
'''

content = content.replace("tasks_for_station = STATION_TASKS[station]", new_tasks_logic)

# Replace all occurrences where `task` string is expected with `task['task']`
# Wait, `task` is used as a loop variable. Let's look for how it's unpacked:
# `for task in tasks_for_station:` -> we can just do `for task_dict in tasks_for_station:` and then `task = task_dict['task']`

# We need a robust replacement script or just rewrite the blocks.
