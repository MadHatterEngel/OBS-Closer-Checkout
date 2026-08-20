with open('reviewer_app.py', 'r') as f:
    content = f.read()

# Replace viewing and deleting existing tasks
old_view = """            for i, task in enumerate(tasks):
                col_task, col_del = st.columns([4, 1])
                with col_task:
                    st.write(f"- {task}")
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_task_{station}_{i}"):
                        try:
                            supabase.table('station_tasks').delete().eq('station', station).eq('task', task).execute()"""
new_view = """            for i, task_dict in enumerate(tasks):
                task = task_dict['task']
                col_task, col_del = st.columns([4, 1])
                with col_task:
                    st.write(f"- **{task}**")
                    if task_dict.get('day_of_week'):
                        st.caption(f"📅 Daily: {task_dict['day_of_week']}")
                    if task_dict.get('details'):
                        st.caption(f"ℹ️ Details: {task_dict['details'][:50]}...")
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_task_{station}_{i}"):
                        try:
                            supabase.table('station_tasks').delete().eq('station', station).eq('task', task).execute()"""
content = content.replace(old_view, new_view)

# Replace adding new task form
old_add = """            with st.form(key=f"add_task_form_{station}"):
                new_task_desc = st.text_input("New Task Description", placeholder="e.g., Sanitize countertops")
                submit_new_task = st.form_submit_button("➕ Add Task")

                if submit_new_task:
                    if new_task_desc.strip():
                        try:
                            supabase.table('station_tasks').insert({
                                "station": station,
                                "task": new_task_desc.strip()
                            }).execute()"""
new_add = """            with st.form(key=f"add_task_form_{station}"):
                new_task_desc = st.text_input("New Task Description", placeholder="e.g., Sanitize countertops")
                new_day = st.selectbox("Assign to specific Day (Optional)", ["None", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], key=f"day_{station}")
                new_details = st.text_area("Task Details / Restock Chart (Optional)", placeholder="List items here...")
                submit_new_task = st.form_submit_button("➕ Add Task")

                if submit_new_task:
                    if new_task_desc.strip():
                        try:
                            insert_data = {
                                "station": station,
                                "task": new_task_desc.strip()
                            }
                            if new_day != "None":
                                insert_data["day_of_week"] = new_day
                            if new_details.strip():
                                insert_data["details"] = new_details.strip()

                            supabase.table('station_tasks').insert(insert_data).execute()"""
content = content.replace(old_add, new_add)

# There is also one line around 225: for task in station_tasks[selected_station]:
old_line = "for task in station_tasks[selected_station]:"
new_line = "for task_dict in station_tasks[selected_station]:\n        task = task_dict['task']"
content = content.replace(old_line, new_line)

with open('reviewer_app.py', 'w') as f:
    f.write(content)
