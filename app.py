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

# If station changes, we want to reset the task photos and active camera
if 'current_station' not in st.session_state:
    st.session_state.current_station = list(STATION_TASKS.keys())[0]

station = st.selectbox("Select Station", list(STATION_TASKS.keys()))

if station != st.session_state.current_station:
    st.session_state.current_station = station
    st.session_state.task_photos = {}
    st.session_state.active_camera = None
    st.rerun()

st.subheader(f"{station} Operational Requirements")

# Initialize session state for task photos
if 'task_photos' not in st.session_state:
    st.session_state.task_photos = {}

# Track which task's camera is currently open
if 'active_camera' not in st.session_state:
    st.session_state.active_camera = None

st.info("Click '📷 Verify Task' to open the camera and submit photographic proof.")

st.markdown("---")
st.subheader("Task Verification")

tasks_for_station = STATION_TASKS[station]

for task in tasks_for_station:
    task_key = f"{station}_{task}"

    col_text, col_btn = st.columns([3, 1])

    with col_text:
        st.write(f"**{task}**")

    with col_btn:
        if task_key in st.session_state.task_photos:
            st.success("✅ Verified")
            # Option to retake photo
            if st.button("Retake", key=f"retake_{task_key}"):
                del st.session_state.task_photos[task_key]
                st.session_state.active_camera = task_key
                st.rerun()
        else:
            if st.button("📷 Verify Task", key=f"verify_{task_key}"):
                st.session_state.active_camera = task_key
                st.rerun()

    # If this task is the currently active camera, show the camera input
    if st.session_state.active_camera == task_key:
        with st.container():
            st.markdown(f"**Taking photo for:** {task}")
            photo = st.camera_input("Capture Proof", key=f"camera_{task_key}")

            if photo:
                st.session_state.task_photos[task_key] = photo.getvalue()
                st.session_state.active_camera = None
                st.rerun()

            if st.button("Cancel", key=f"cancel_{task_key}"):
                st.session_state.active_camera = None
                st.rerun()
    st.markdown("---")

# Only allow submission if all tasks have a photo
all_tasks_verified = len(st.session_state.task_photos) == len(tasks_for_station)

if st.button("Submit All Verifications", type="primary", use_container_width=True, disabled=not all_tasks_verified):
    if not employee_name:
        st.error("Error: Employee Identifier required.")
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
            st.session_state.active_camera = None
            st.session_state.current_station = station
