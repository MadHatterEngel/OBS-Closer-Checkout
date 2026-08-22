import re

with open('reviewer_app.py', 'r') as f:
    content = f.read()

# In reviewer_app.py:
# old: for task_dict in station_tasks[selected_station]:
#          task = task_dict['task']
#          task_key = f"{selected_station}_{task}"
# new: for idx, task_dict in enumerate(station_tasks[selected_station]):
#          task = task_dict['task']
#          task_key = f"{selected_station}_{task}"
#          ui_key = f"{task_key}_{idx}"

old_loop = "for task_dict in station_tasks[selected_station]:\n        task = task_dict['task']\n        task_key = f\"{selected_station}_{task}\""
new_loop = "for idx, task_dict in enumerate(station_tasks[selected_station]):\n        task = task_dict['task']\n        task_key = f\"{selected_station}_{task}\"\n        ui_key = f\"{task_key}_{idx}\""
content = content.replace(old_loop, new_loop)

# Now we need to replace `key=f"..._{task_key}"` with `key=f"..._{ui_key}"`
# Wait, let's just do a blanket replace for the specific keys in that block.
# The keys are: up_, slider_, test_, test_btn_, set_btn_

content = content.replace('key=f"up_{task_key}"', 'key=f"up_{ui_key}"')
content = content.replace('key=f"slider_{task_key}"', 'key=f"slider_{ui_key}"')
content = content.replace('key=f"test_{task_key}"', 'key=f"test_{ui_key}"')
content = content.replace('key=f"test_btn_{task_key}"', 'key=f"test_btn_{ui_key}"')
content = content.replace('key=f"set_btn_{task_key}"', 'key=f"set_btn_{ui_key}"')

with open('reviewer_app.py', 'w') as f:
    f.write(content)
