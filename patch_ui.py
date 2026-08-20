import re

with open('app.py', 'r') as f:
    content = f.read()

# Instead of modifying the whole file again by hand, let's just do a string replacement
# for the task display block in app.py

old_block = """                        if task_key in st.session_state.task_photos:
                            st.success(f"✅ {task}")
                            if st.button("Retake", key=f"retake_btn_{task_key}"):
                                del st.session_state.task_photos[task_key]
                                st.rerun()
                        else:
                            st.error(f"❌ {task}")
                            # Give option to take it right here if they don't want sequential
                            img_data = native_camera(key=f"cam_{task_key}")"""

new_block = """                        display_task = f"**{task}** (Daily)" if task_dict.get('day_of_week') else task

                        if task_key in st.session_state.task_photos:
                            st.success(f"✅ {display_task}")
                            if task_dict.get('details'):
                                with st.expander("ℹ️ Restock List Details"):
                                    st.write(task_dict['details'])
                            if st.button("Retake", key=f"retake_btn_{task_key}"):
                                del st.session_state.task_photos[task_key]
                                st.rerun()
                        else:
                            st.error(f"❌ {display_task}")
                            if task_dict.get('details'):
                                with st.expander("ℹ️ Restock List Details"):
                                    st.write(task_dict['details'])
                            # Give option to take it right here if they don't want sequential
                            img_data = native_camera(key=f"cam_{task_key}")"""

content = content.replace(old_block, new_block)
with open('app.py', 'w') as f:
    f.write(content)
