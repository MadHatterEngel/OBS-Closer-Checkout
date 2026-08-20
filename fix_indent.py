with open('app.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("    from datetime import datetime"):
        new_lines.append(line[4:])
    elif line.startswith("    current_day = datetime.now()"):
        new_lines.append(line[4:])
    elif line.startswith("    raw_tasks = STATION_TASKS[station]"):
        new_lines.append(line[4:])
    elif line.startswith("    filtered_tasks = []"):
        new_lines.append(line[4:])
    elif line.startswith("    daily_tasks = []"):
        new_lines.append(line[4:])
    elif line.startswith("    for t in raw_tasks:"):
        new_lines.append(line[4:])
    elif line.startswith("        if isinstance(t, str):"):
        new_lines.append(line[4:])
    elif line.startswith("            filtered_tasks.append({'task': t})"):
        new_lines.append(line[4:])
    elif line.startswith("        elif t.get('day_of_week'):"):
        new_lines.append(line[4:])
    elif line.startswith("            if t['day_of_week'] == current_day:"):
        new_lines.append(line[4:])
    elif line.startswith("                daily_tasks.append(t)"):
        new_lines.append(line[4:])
    elif line.startswith("        else:"):
        new_lines.append(line[4:])
    elif line.startswith("            filtered_tasks.append(t)"):
        new_lines.append(line[4:])
    elif line.startswith("    tasks_for_station = filtered_tasks + daily_tasks"):
        new_lines.append(line[4:])
    else:
        new_lines.append(line)

with open('app.py', 'w') as f:
    f.writelines(new_lines)
