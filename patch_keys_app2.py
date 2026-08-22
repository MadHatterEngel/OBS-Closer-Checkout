import re
with open('app.py', 'r') as f:
    content = f.read()

# Let's change the Streamlit UI widget keys in app.py to include idx.
# 1. retake_btn_{task_key} -> retake_btn_{task_key}_{idx}
# 2. cam_{task_key} -> cam_{task_key}_{idx}
# Mode 1 already has `for idx, task_dict in enumerate(tasks_for_station):`
# So we can just replace:
content = content.replace('key=f"retake_btn_{task_key}"', 'key=f"retake_btn_{task_key}_{idx}"')
content = content.replace('key=f"cam_{task_key}"', 'key=f"cam_{task_key}_{idx}"')

# In Mode 2, there's `retake_cam_{task_key}` and `retake_cam2_{task_key}`.
# Mode 2 loop currently is: `for task_dict in tasks_for_station:`
# We need to change it to enumerate.
old_mode2_loop = "for task_dict in tasks_for_station:\n        task = task_dict['task']\n        display_task = f\"**{task}** (Daily)\" if task_dict.get('day_of_week') else task\n        task_key = f\"{station}_{task}\""
new_mode2_loop = "for idx, task_dict in enumerate(tasks_for_station):\n        task = task_dict['task']\n        display_task = f\"**{task}** (Daily)\" if task_dict.get('day_of_week') else task\n        task_key = f\"{station}_{task}\""
content = content.replace(old_mode2_loop, new_mode2_loop)

content = content.replace('key=f"retake_cam_{task_key}"', 'key=f"retake_cam_{task_key}_{idx}"')
content = content.replace('key=f"retake_cam2_{task_key}"', 'key=f"retake_cam2_{task_key}_{idx}"')

with open('app.py', 'w') as f:
    f.write(content)
