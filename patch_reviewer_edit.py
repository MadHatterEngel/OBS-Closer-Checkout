with open('reviewer_app.py', 'r') as f:
    content = f.read()

# Add edit state tracking near the top of tab3/tab4 where station_tasks are managed.
# We'll just do it globally if it doesn't exist.
if "if 'edit_task_id' not in st.session_state:" not in content:
    content = content.replace("st.markdown(\"Modify, add, or remove check-out stations and their specific tasks. Changes instantly reflect on the closer application.\")",
        "if 'edit_task_id' not in st.session_state:\n        st.session_state.edit_task_id = None\n\n    st.markdown(\"Modify, add, or remove check-out stations and their specific tasks. Changes instantly reflect on the closer application.\")")

# The block to replace:
old_block = """            for i, task_dict in enumerate(tasks):
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
                            supabase.table('station_tasks').delete().eq('id', task_dict['id']).execute()
                            fetch_station_tasks.clear()
                            st.success(f"Task '{task}' removed.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting task: {e}")"""

new_block = """            for i, task_dict in enumerate(tasks):
                task = task_dict['task']
                task_id = task_dict['id']

                if st.session_state.edit_task_id == task_id:
                    with st.container():
                        edit_desc = st.text_input("Edit Task Description", value=task, key=f"edit_desc_{task_id}")
                        current_day = task_dict.get('day_of_week', "None")
                        day_options = ["None", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        edit_day = st.selectbox("Assign to specific Day (Optional)", day_options, index=day_options.index(current_day) if current_day in day_options else 0, key=f"edit_day_{task_id}")
                        edit_details = st.text_area("Task Details / Restock Chart (Optional)", value=task_dict.get('details', ''), key=f"edit_det_{task_id}")

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("💾 Save Changes", type="primary", key=f"save_edit_{task_id}"):
                                try:
                                    update_data = {"task": edit_desc.strip()}
                                    update_data["day_of_week"] = edit_day if edit_day != "None" else None
                                    update_data["details"] = edit_details.strip() if edit_details.strip() else None

                                    supabase.table('station_tasks').update(update_data).eq('id', task_id).execute()
                                    fetch_station_tasks.clear()
                                    st.session_state.edit_task_id = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating task: {e}")
                        with col_cancel:
                            if st.button("❌ Cancel", key=f"cancel_edit_{task_id}"):
                                st.session_state.edit_task_id = None
                                st.rerun()
                else:
                    col_task, col_edit, col_del = st.columns([3, 1, 1])
                    with col_task:
                        st.write(f"- **{task}**")
                        if task_dict.get('day_of_week'):
                            st.caption(f"📅 Daily: {task_dict['day_of_week']}")
                        if task_dict.get('details'):
                            st.caption(f"ℹ️ Details: {task_dict['details'][:50]}...")
                    with col_edit:
                        if st.button("✏️ Edit", key=f"edit_task_{station}_{i}"):
                            st.session_state.edit_task_id = task_id
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ Delete", key=f"del_task_{station}_{i}"):
                            try:
                                supabase.table('station_tasks').delete().eq('id', task_id).execute()
                                fetch_station_tasks.clear()
                                st.success(f"Task '{task}' removed.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting task: {e}")"""

content = content.replace(old_block, new_block)

with open('reviewer_app.py', 'w') as f:
    f.write(content)
