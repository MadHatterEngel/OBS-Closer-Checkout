with open('app.py', 'r') as f:
    content = f.read()

# 1. Replace initialization of tasks_for_station
old_init = "tasks_for_station = STATION_TASKS[station]"
new_init = """from datetime import datetime
current_day = datetime.now().strftime('%A')
raw_tasks = STATION_TASKS[station]
filtered_tasks = []
daily_tasks = []
for t in raw_tasks:
    if isinstance(t, str):
        filtered_tasks.append({'task': t})
    elif t.get('day_of_week'):
        if t['day_of_week'] == current_day:
            daily_tasks.append(t)
    else:
        filtered_tasks.append(t)
tasks_for_station = filtered_tasks + daily_tasks"""
content = content.replace(old_init, new_init)

# 2. Update the missing_tasks loop
old_missing = """    missing_tasks = []
    for task in tasks_for_station:
        task_key = f"{station}_{task}"
        if task_key not in st.session_state.task_photos:
            missing_tasks.append((task_key, task))"""
new_missing = """    missing_tasks = []
    for task_dict in tasks_for_station:
        task = task_dict['task']
        task_key = f"{station}_{task}"
        if task_key not in st.session_state.task_photos:
            missing_tasks.append((task_key, task))"""
content = content.replace(old_missing, new_missing)

# 3. Update task list UI rendering
old_ui = """                        if task_key in st.session_state.task_photos:
                            st.success(f"✅ {task}")
                            if st.button("Retake", key=f"retake_btn_{task_key}"):
                                del st.session_state.task_photos[task_key]
                                st.rerun()
                        else:
                            st.error(f"❌ {task}")
                            # Give option to take it right here if they don't want sequential
                            img_data = native_camera(key=f"cam_{task_key}")"""
new_ui = """                        display_task = f"**{task}** (Daily)" if task_dict.get('day_of_week') else task
                        if task_key in st.session_state.task_photos:
                            st.success(f"✅ {display_task}")
                            if task_dict.get('details'):
                                with st.expander("ℹ️ Restock Details"):
                                    st.write(task_dict['details'])
                            if st.button("Retake", key=f"retake_btn_{task_key}"):
                                del st.session_state.task_photos[task_key]
                                st.rerun()
                        else:
                            st.error(f"❌ {display_task}")
                            if task_dict.get('details'):
                                with st.expander("ℹ️ Restock Details"):
                                    st.write(task_dict['details'])
                            # Give option to take it right here if they don't want sequential
                            img_data = native_camera(key=f"cam_{task_key}")"""
content = content.replace(old_ui, new_ui)

# 4. Update enumerate(tasks_for_station)
content = content.replace("for idx, task in enumerate(tasks_for_station):", "for idx, task_dict in enumerate(tasks_for_station):\n                task = task_dict['task']")

# 5. Update tasks_keys map in submission
content = content.replace("task_keys = [f\"{station}_{task}\" for task in tasks_for_station]", "task_keys = [f\"{station}_{t['task']}\" for t in tasks_for_station]")

# 6. Update results display loop
old_results = """    for task in tasks_for_station:
        task_key = f"{station}_{task}"
        res = results[task_key]

        with st.container():
            st.markdown(f"**{task}**")"""
new_results = """    for task_dict in tasks_for_station:
        task = task_dict['task']
        display_task = f"**{task}** (Daily)" if task_dict.get('day_of_week') else task
        task_key = f"{station}_{task}"
        res = results[task_key]

        with st.container():
            st.markdown(f"**{display_task}**")
            if task_dict.get('details'):
                with st.expander("ℹ️ Restock Details"):
                    st.write(task_dict['details'])"""
content = content.replace(old_results, new_results)

# 7. Update re-verify button tasks_to_verify list
content = content.replace("tasks_to_verify = [f\"{station}_{task}\" for task in tasks_for_station if st.session_state.verification_results[f\"{station}_{task}\"][\"status\"] != \"PASS\"]", "tasks_to_verify = [f\"{station}_{t['task']}\" for t in tasks_for_station if st.session_state.verification_results[f\"{station}_{t['task']}\"][\"status\"] != \"PASS\"]")

# 8. Update submission loop
old_submit = """                for task in tasks_for_station:
                    task_key = f"{station}_{task}"
                    photo_base64 = base64.b64encode(st.session_state.task_photos[task_key]).decode('utf-8')"""
new_submit = """                for task_dict in tasks_for_station:
                    task = task_dict['task']
                    task_key = f"{station}_{task}"
                    photo_base64 = base64.b64encode(st.session_state.task_photos[task_key]).decode('utf-8')"""
content = content.replace(old_submit, new_submit)

with open('app.py', 'w') as f:
    f.write(content)
