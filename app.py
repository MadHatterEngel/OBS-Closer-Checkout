import streamlit as st
st.set_page_config(
    page_title="Closing Verification Protocol",
    page_icon="🔒",
    layout="centered"
)

import base64
from datetime import datetime
from config import supabase, fetch_station_tasks
from ai_validator import validate_photo_with_ai
from ui_styling import apply_custom_css

apply_custom_css()

try:
    with open("assets/logo.png", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(f'<img src="data:image/png;base64,{logo_data}" class="mh-logo">', unsafe_allow_html=True)
except:
    pass

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
                photo_bytes = photo.getvalue()

                # Retrieve AI Reference from Supabase
                baseline_bytes = None
                strictness = 5
                try:
                    ref_response = supabase.table('ai_references').select('photo_data, strictness').eq('task_key', task_key).execute()
                    if ref_response.data and len(ref_response.data) > 0:
                        ref_record = ref_response.data[0]
                        baseline_bytes = base64.b64decode(ref_record['photo_data'])
                        strictness = ref_record['strictness']
                except Exception as e:
                    st.warning(f"Failed to check reference image: {e}")

                with st.spinner("🤖 AI Auditing Photo..."):
                    ai_res = validate_photo_with_ai(baseline_bytes, photo_bytes, strictness)

                if ai_res["status"] == "FAIL":
                    st.error(f"❌ AI Verification Failed: {ai_res['reason']} Please try again.")
                    # We do not save it, forcing them to retake
                else:
                    if baseline_bytes:
                        st.success(f"✅ AI Approved! ({ai_res['reason']})")
                    else:
                        st.success("✅ Saved! (No AI reference found for this task, auto-passed).")

                    st.session_state.task_photos[task_key] = photo_bytes
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

                photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')

                # Insert individual log for this task
                try:
                    response = supabase.table('closing_logs').insert({
                        'timestamp': current_time,
                        'employee_name': employee_name,
                        'station': f"{station} - {task}",
                        'photo_data': photo_base64,
                        'status': "APPROVED" # Since it passed AI at the camera stage
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
