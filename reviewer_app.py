import streamlit as st
st.set_page_config(page_title="Manager Command Center", page_icon="👁️", layout="wide")

import pandas as pd
import io
import base64
from PIL import Image
from config import supabase, fetch_station_tasks
from ui_styling import apply_custom_css
from ai_validator import validate_photo_with_ai


apply_custom_css()

try:
    with open("assets/logo.png", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.sidebar.markdown(f'<img src="data:image/png;base64,{logo_data}" class="mh-logo">', unsafe_allow_html=True)
except:
    pass

def check_password():
    def password_entered():
        manager_pass = st.secrets.get("MANAGER_PASSWORD", "manager123")
        if st.session_state["password_input"] == manager_pass:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Manager Access Code", type="password", on_change=password_entered, key="password_input")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Manager Access Code", type="password", on_change=password_entered, key="password_input")
        st.error("Access Denied. Incorrect verification code.")
        return False
    return True

if not check_password():
    st.stop()

st.title("👁️ Manager Operations Review Dashboard")
st.markdown("Remote verification portal for live shift closing logs and photographic proof.")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📋 Review Logs", "🤖 AI Verification Setup", "⚙️ Station Configuration"])

with tab1:
    def fetch_logs():
        try:
            # Increased limit so a single multi-task checkout isn't cut off
            response = supabase.table('closing_logs').select('id, timestamp, employee_name, station, photo_data, status').order('id', desc=True).limit(250).execute()
            return response.data
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            return []

    logs = fetch_logs()

    # Group logs by checkout (timestamp, employee, base station)
    checkouts = {}
    for log in logs:
        # Handle the fact that station strings might look like "Fry Station - Oil filtered"
        station_str = log['station']
        if " - " in station_str:
            base_station, task_name = station_str.split(" - ", 1)
        else:
            base_station, task_name = station_str, "General"

        checkout_key = f"{log['timestamp']}_{log['employee_name']}_{base_station}"

        if checkout_key not in checkouts:
            checkouts[checkout_key] = {
                'timestamp': log['timestamp'],
                'employee': log['employee_name'],
                'station': base_station,
                'status': log['status'], # Take the status of the first found log
                'tasks': []
            }

        checkouts[checkout_key]['tasks'].append({
            'id': log['id'],
            'task_name': task_name,
            'photo_data': log['photo_data'],
            'status': log['status']
        })

    # Allow download and clear even if there are no logs to avoid confusing the user
    # that the buttons are just gone.
    if not logs:
        st.info("No compliance logs detected in the database.")
    else:
        # Summary Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Checkouts", len(checkouts))

        # Get the latest submission timestamp
        latest_time = list(checkouts.values())[0]['timestamp'] if checkouts else "N/A"
        col2.metric("Latest Submission", latest_time)

        unique_stations = len(set(c['station'] for c in checkouts.values()))
        col3.metric("Stations Audited", unique_stations)

        st.markdown("---")
        st.subheader("📸 Visual Compliance Feed")
        st.markdown("Click any photo to expand it to full screen.")

        for key, checkout in checkouts.items():
            timestamp = checkout['timestamp']
            employee = checkout['employee']
            station = checkout['station']
            overall_status = checkout['status']
            tasks = checkout['tasks']

            with st.expander(f"{timestamp} | {employee} — {station} ({len(tasks)} tasks verified)"):

                # Create a dynamic 3-column grid
                cols = st.columns(3)

                for idx, task in enumerate(tasks):
                    col = cols[idx % 3] # Distribute evenly across the 3 columns
                    with col:
                        st.markdown(f"**{task['task_name']}**")
                        if task['photo_data']:
                            # Implement lazy loading to prevent massive DOM slow-downs
                            # Store a unique key for this image in session state
                            view_key = f"view_img_{task['id']}"

                            if st.session_state.get(view_key, False):
                                try:
                                    photo_bytes = base64.b64decode(task['photo_data'])
                                    image = Image.open(io.BytesIO(photo_bytes))
                                    st.image(image, use_container_width=True)

                                    if st.button("Hide Image", key=f"hide_btn_{task['id']}"):
                                        st.session_state[view_key] = False
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to load image data: {str(e)}")
                            else:
                                if st.button("🖼️ View Photo", key=f"show_btn_{task['id']}"):
                                    st.session_state[view_key] = True
                                    st.rerun()
                        else:
                            st.warning("No image data found.")
                        st.markdown("---")

    st.markdown("---")
    st.subheader("🛠️ Data Management")

    # Prepare data for download (excluding base64 image data).
    # We export the raw, flat, highly detailed logs here for the user's records.
    download_data = []
    for log in logs:
        download_data.append({
            "ID": log["id"],
            "Timestamp": log["timestamp"],
            "Employee": log["employee_name"],
            "Station & Task": log["station"],
            "Status": log["status"]
        })

    if download_data:
        df = pd.DataFrame(download_data)
    else:
        df = pd.DataFrame(columns=["ID", "Timestamp", "Employee", "Station & Task", "Status"])

    csv = df.to_csv(index=False).encode('utf-8')

    col_dl, col_clear = st.columns(2)

    with col_dl:
        st.download_button(
            label="📥 Download Detailed Logs (CSV)",
            data=csv,
            file_name="detailed_closing_logs.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_clear:
        if st.button("🗑️ Clear All Logs", type="secondary", use_container_width=True):
            st.session_state.confirm_clear = True

    if st.session_state.get("confirm_clear", False):
        st.warning("⚠️ **WARNING:** This will permanently delete ALL checkout logs. This action cannot be undone.")
        col_confirm, col_cancel = st.columns(2)

        with col_confirm:
            if st.button("🚨 Yes, Delete ALL Logs", type="primary", use_container_width=True):
                try:
                    # Delete all rows where id is not 0 (which is always true)
                    response = supabase.table('closing_logs').delete().neq('id', 0).execute()
                    st.success("All logs successfully deleted.")
                    st.session_state.confirm_clear = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete logs: {str(e)}")

        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()

with tab2:
    st.subheader("🤖 AI Reference Standards")
    st.markdown("Upload clean reference photos and set AI strictness levels. If a task has no reference photo, it will automatically pass verification.")

    # Fetch existing AI references
    try:
        ref_response = supabase.table('ai_references').select('*').execute()
        existing_refs = {row['task_key']: row for row in ref_response.data}
    except Exception as e:
        st.error(f"Failed to load AI references: {e}")
        existing_refs = {}

    station_tasks = fetch_station_tasks()

    # Select a station to configure
    selected_station = st.selectbox("Select Station to Configure", list(station_tasks.keys()))

    st.markdown(f"### {selected_station} Tasks")

    for task in station_tasks[selected_station]:
        task_key = f"{selected_station}_{task}"

        with st.expander(f"Task: {task}"):
            col_img, col_settings = st.columns(2)

            ref_data = existing_refs.get(task_key)
            current_strictness = ref_data['strictness'] if ref_data else 5

            with col_img:
                st.markdown("**Current Reference Image**")
                if ref_data and ref_data['photo_data']:
                    try:
                        photo_bytes = base64.b64decode(ref_data['photo_data'])
                        image = Image.open(io.BytesIO(photo_bytes))
                        st.image(image, use_container_width=True)
                    except Exception:
                        st.error("Failed to render existing image.")
                else:
                    st.info("No reference image uploaded.")

            with col_settings:
                # Uploader for new reference
                new_image = st.file_uploader(f"Upload New Reference", type=["jpg", "jpeg", "png"], key=f"up_{task_key}")

                # Strictness slider
                new_strictness = st.slider(
                    "AI Strictness Level",
                    min_value=1, max_value=10, value=current_strictness,
                    help="1 = Very loose (passes almost anything), 10 = Very strict (must look exactly like reference)",
                    key=f"slider_{task_key}"
                )

                test_image = st.file_uploader(f"Upload Test Image (Evaluates current slider value without saving)", type=["jpg", "jpeg", "png"], key=f"test_{task_key}")
                if st.button("🔬 Test AI Strictness", key=f"test_btn_{task_key}"):
                    if test_image is not None:
                        # Determine which baseline to use (the newly uploaded one, or the existing one)
                        baseline_bytes = None
                        if new_image is not None:
                            baseline_bytes = new_image.getvalue()
                        elif ref_data and ref_data['photo_data']:
                            baseline_bytes = base64.b64decode(ref_data['photo_data'])

                        if not baseline_bytes:
                            st.warning("You must upload a Reference image first before testing.")
                        else:
                            with st.spinner("Testing current strictness..."):
                                ai_res = validate_photo_with_ai(baseline_bytes, test_image.getvalue(), new_strictness)
                            if ai_res['status'] == 'PASS':
                                st.success(f"✅ PASSED at strictness {new_strictness} ({ai_res['reason']})")
                            else:
                                st.error(f"❌ FAILED at strictness {new_strictness} ({ai_res['reason']})")
                                if ai_res.get('feedback'):
                                    st.warning(f"🔍 AI Feedback: {ai_res['feedback']}")
                    else:
                        st.warning("Upload a test image first.")

                st.markdown("---")
                if st.button("Save AI Settings", type="primary", key=f"save_{task_key}"):
                    update_data = {"strictness": new_strictness}

                    if new_image is not None:
                        # Process uploaded image
                        img_bytes = new_image.getvalue()
                        update_data["photo_data"] = base64.b64encode(img_bytes).decode('utf-8')

                    try:
                        if ref_data:
                            # Update existing
                            supabase.table('ai_references').update(update_data).eq('task_key', task_key).execute()
                        else:
                            # Insert new
                            if "photo_data" not in update_data:
                                st.error("You must upload an image to create a new reference.")
                                st.stop()
                            update_data["task_key"] = task_key
                            supabase.table('ai_references').insert(update_data).execute()

                        st.success("Settings saved successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save settings: {e}")

with tab3:
    st.subheader("⚙️ Station Requirements Management")
    st.markdown("Modify, add, or remove check-out stations and their specific tasks. Changes instantly reflect on the closer application.")

    # Reload fresh station tasks
    station_tasks = fetch_station_tasks()

    # Use expanders for existing stations
    for station, tasks in station_tasks.items():
        with st.expander(f"Station: {station}"):
            st.markdown(f"**Current Tasks for {station}**")

            # Display current tasks with a delete button for each
            for i, task in enumerate(tasks):
                col_task, col_del = st.columns([4, 1])
                with col_task:
                    st.write(f"- {task}")
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_task_{station}_{i}"):
                        try:
                            supabase.table('station_tasks').delete().eq('station', station).eq('task', task).execute()
                            fetch_station_tasks.clear()
                            st.success(f"Task '{task}' removed.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting task: {e}")

            st.markdown("---")
            st.markdown("**Add New Task**")
            # Form to add a new task to this station
            with st.form(key=f"add_task_form_{station}"):
                new_task_desc = st.text_input("New Task Description", placeholder="e.g., Sanitize countertops")
                submit_new_task = st.form_submit_button("➕ Add Task")

                if submit_new_task:
                    if new_task_desc.strip():
                        try:
                            supabase.table('station_tasks').insert({
                                "station": station,
                                "task": new_task_desc.strip()
                            }).execute()
                            fetch_station_tasks.clear()
                            st.success(f"Task added to {station}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding task: {e}")
                    else:
                        st.warning("Task description cannot be empty.")

            st.markdown("---")
            # Delete Entire Station
            if st.button("🚨 Delete Entire Station", type="primary", key=f"del_station_{station}"):
                try:
                    supabase.table('station_tasks').delete().eq('station', station).execute()
                    fetch_station_tasks.clear()
                    st.success(f"Station '{station}' completely removed.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting station: {e}")

    st.markdown("---")
    st.markdown("### ➕ Create New Station")
    with st.form(key="create_station_form"):
        new_station_name = st.text_input("New Station Name", placeholder="e.g., Dining Room")
        new_station_task = st.text_input("Initial Task", placeholder="e.g., Wipe all tables")
        submit_new_station = st.form_submit_button("Create Station")

        if submit_new_station:
            if new_station_name.strip() and new_station_task.strip():
                try:
                    supabase.table('station_tasks').insert({
                        "station": new_station_name.strip(),
                        "task": new_station_task.strip()
                    }).execute()
                    fetch_station_tasks.clear()
                    st.success(f"New station '{new_station_name.strip()}' created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating station: {e}")
            else:
                st.warning("Both Station Name and Initial Task are required to create a new station.")
