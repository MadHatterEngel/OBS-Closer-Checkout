import streamlit as st
import base64
from datetime import datetime
from config import supabase, fetch_station_tasks
from ai_validator import validate_photo_with_ai

st.set_page_config(
    page_title="Closing Verification Protocol",
    page_icon="🔒",
    layout="centered"
)

STATION_TASKS = fetch_station_tasks()

st.title("🔒 Shift Verification Protocol")
st.markdown("Live photographic proof & binary station checklist verification.")
st.markdown("---")

employee_name = st.text_input("Employee Identifier", placeholder="Enter your name")
station = st.selectbox("Select Station", list(STATION_TASKS.keys()))

st.subheader(f"{station} Operational Requirements")

# Initialize session state for task photos
if 'task_photos' not in st.session_state:
    st.session_state.task_photos = {}

st.info("You must capture a live photo for a task before you can check it off.")

# Single camera input for all tasks
photo = st.camera_input("Capture Proof")
if photo:
    st.success("Photo captured! You can now use it to verify a task below.")

st.markdown("---")
st.subheader("Task Verification")

tasks_for_station = STATION_TASKS[station]
checklist_status = []

for task in tasks_for_station:
    task_key = f"{station}_{task}"

    col1, col2 = st.columns([3, 1])
    with col1:
        # Checkbox is disabled until a photo is captured or already saved for this task
        can_check = photo is not None or task_key in st.session_state.task_photos
        is_done = st.checkbox(
            task,
            key=f"check_{task_key}",
            disabled=not can_check,
            help="Take a photo first to enable this checkbox." if not can_check else ""
        )
        checklist_status.append(is_done)

    with col2:
        if is_done and photo is not None and task_key not in st.session_state.task_photos:
            # Save the currently captured photo to this task in session state
            st.session_state.task_photos[task_key] = photo.getvalue()

        if task_key in st.session_state.task_photos and is_done:
            st.success("📸 Verified")
        elif not is_done and task_key in st.session_state.task_photos:
            # If user unchecks the box, clear the photo
            del st.session_state.task_photos[task_key]

st.markdown("---")

if st.button("Submit All Verifications", type="primary", use_container_width=True):
    if not employee_name:
        st.error("Error: Employee Identifier required.")
    elif not all(checklist_status):
        st.error("Error: All operational requirements must be verified. No partial completions accepted.")
    elif len(st.session_state.task_photos) < len(tasks_for_station):
        st.error("Error: Missing photos for some verified tasks.")
    else:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_success = True

        with st.spinner("Uploading verification logs..."):
            for task in tasks_for_station:
                task_key = f"{station}_{task}"
                photo_bytes = st.session_state.task_photos[task_key]

                # Optional AI Validation check
                ai_res = validate_photo_with_ai(None, photo_bytes)
                status = ai_res["status"]

                if status == "FAIL":
                    st.error(f"AI Verification Failed for '{task}': {ai_res['reason']}")
                    all_success = False
                    break

                photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')

                # Insert individual log for this task
                try:
                    response = supabase.table('closing_logs').insert({
                        'timestamp': current_time,
                        'employee_name': employee_name,
                        'station': f"{station} - {task}",
                        'photo_data': photo_base64,
                        'status': status
                    }).execute()
                except Exception as e:
                    st.error(f"Database error on task '{task}': {str(e)}")
                    all_success = False
                    break

        if all_success:
            st.success(f"All verifications accepted at {current_time}. You are authorized to log off.")
            st.balloons()
            # Clear session state for next user
            st.session_state.task_photos = {}
