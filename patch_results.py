import re
with open('app.py', 'r') as f:
    content = f.read()

old_res_block = """    for task in tasks_for_station:
        task_key = f"{station}_{task}"
        res = results[task_key]

        with st.container():
            st.markdown(f"**{task}**")"""

new_res_block = """    for task_dict in tasks_for_station:
        task = task_dict['task']
        display_task = f"**{task}** (Daily)" if task_dict.get('day_of_week') else task
        task_key = f"{station}_{task}"
        res = results[task_key]

        with st.container():
            st.markdown(f"**{display_task}**")
            if task_dict.get('details'):
                with st.expander("ℹ️ Details"):
                    st.write(task_dict['details'])"""

content = content.replace(old_res_block, new_res_block)

old_verify_block = """                tasks_to_verify = [f"{station}_{task}" for task in tasks_for_station if st.session_state.verification_results[f"{station}_{task}"]["status"] != "PASS"]"""
new_verify_block = """                tasks_to_verify = [f"{station}_{task_dict['task']}" for task_dict in tasks_for_station if st.session_state.verification_results[f"{station}_{task_dict['task']}"]["status"] != "PASS"]"""
content = content.replace(old_verify_block, new_verify_block)

old_submit_block = """                for task in tasks_for_station:
                    task_key = f"{station}_{task}"
                    photo_base64 = base64.b64encode(st.session_state.task_photos[task_key]).decode('utf-8')"""
new_submit_block = """                for task_dict in tasks_for_station:
                    task = task_dict['task']
                    task_key = f"{station}_{task}"
                    photo_base64 = base64.b64encode(st.session_state.task_photos[task_key]).decode('utf-8')"""
content = content.replace(old_submit_block, new_submit_block)

old_task_keys_block = """                        task_keys = [f"{station}_{task}" for task in tasks_for_station]"""
new_task_keys_block = """                        task_keys = [f"{station}_{task_dict['task']}" for task_dict in tasks_for_station]"""
content = content.replace(old_task_keys_block, new_task_keys_block)


with open('app.py', 'w') as f:
    f.write(content)
