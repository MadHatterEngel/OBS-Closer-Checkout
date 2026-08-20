import re

with open('app.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if "tasks_for_station = STATION_TASKS[station]" in line:
        new_lines.append("    from datetime import datetime\n")
        new_lines.append("    current_day = datetime.now().strftime('%A')\n")
        new_lines.append("    raw_tasks = STATION_TASKS[station]\n")
        new_lines.append("    filtered_tasks = []\n")
        new_lines.append("    daily_tasks = []\n")
        new_lines.append("    for t in raw_tasks:\n")
        new_lines.append("        if isinstance(t, str):\n")
        new_lines.append("            filtered_tasks.append({'task': t})\n")
        new_lines.append("        elif t.get('day_of_week'):\n")
        new_lines.append("            if t['day_of_week'] == current_day:\n")
        new_lines.append("                daily_tasks.append(t)\n")
        new_lines.append("        else:\n")
        new_lines.append("            filtered_tasks.append(t)\n")
        new_lines.append("    tasks_for_station = filtered_tasks + daily_tasks\n")
    elif "for task in tasks_for_station:" in line:
        new_lines.append(line.replace("for task in tasks_for_station:", "for task_dict in tasks_for_station:"))
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(indent + "    task = task_dict['task']\n")
    elif "for idx, task in enumerate(tasks_for_station):" in line:
        new_lines.append(line.replace("for idx, task in enumerate(tasks_for_station):", "for idx, task_dict in enumerate(tasks_for_station):"))
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(indent + "    task = task_dict['task']\n")
    else:
        new_lines.append(line)

# Let's write it out
with open('app.py', 'w') as f:
    f.writelines(new_lines)
