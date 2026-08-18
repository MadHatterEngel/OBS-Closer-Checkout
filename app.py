import streamlit as st
st.set_page_config(
    page_title="Outback Station Validator",
    page_icon="🥩",
    layout="centered"
)

import base64
from datetime import datetime
import concurrent.futures
from config import supabase, fetch_station_tasks
from ai_validator import validate_photo_with_ai
from ui_styling import apply_custom_css
from components import native_camera

apply_custom_css()

try:
    with open("assets/logo.svg", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(f'<img src="data:image/svg+xml;base64,{logo_data}" class="mh-logo">', unsafe_allow_html=True)
except:
    pass

STATION_TASKS = fetch_station_tasks()

st.title("🥩 Outback Closing Protocol")
st.markdown("Batch photo capture and AI verification system.")
st.markdown("---")

employee_name = st.text_input("Employee Identifier", placeholder="Enter your name")

if 'current_station' not in st.session_state:
    st.session_state.current_station = list(STATION_TASKS.keys())[0]

station = st.selectbox("Select Station", list(STATION_TASKS.keys()))

if station != st.session_state.current_station:
    st.session_state.current_station = station
    st.session_state.task_photos = {}
    st.session_state.verification_results = None
    st.rerun()

st.subheader(f"{station} Duties")

# Track staged photos BEFORE verification
if 'task_photos' not in st.session_state:
    st.session_state.task_photos = {}

# Track batch verification results
if 'verification_results' not in st.session_state:
    st.session_state.verification_results = None

st.info("Capture a photo for each duty. Once all photos are staged, click 'Verify & Submit All'.")

tasks_for_station = STATION_TASKS[station]
all_photos_captured = True

# Mode 1: Photo Collection
if st.session_state.verification_results is None:
    for task in tasks_for_station:
        task_key = f"{station}_{task}"

        with st.container():
            st.markdown(f"**{task}**")

            if task_key in st.session_state.task_photos:
                st.success("📸 Photo Staged")
                # Show small preview
                st.image(st.session_state.task_photos[task_key], width=150)
                if st.button("Retake Photo", key=f"retake_{task_key}"):
                    del st.session_state.task_photos[task_key]
                    st.rerun()
            else:
                all_photos_captured = False
                st.write("Native Camera / Upload:")
                # Use our custom native component
                img_data = native_camera(key=f"cam_{task_key}")

                # Custom component returns base64 string: "data:image/jpeg;base64,..."
                if img_data:
                    if img_data != st.session_state.get(f"raw_cam_{task_key}"):
                        st.session_state[f"raw_cam_{task_key}"] = img_data
                        # Strip the metadata header
                        base64_str = img_data.split(',')[1]
                        photo_bytes = base64.b64decode(base64_str)
                        st.session_state.task_photos[task_key] = photo_bytes
                        st.rerun()

        st.markdown("---")

    can_submit = len(st.session_state.task_photos) == len(tasks_for_station)
    if st.button("Verify & Submit All", type="primary", use_container_width=True, disabled=not can_submit):
        if not employee_name:
            st.error("Employee Identifier is required.")
        else:
            with st.spinner("🤖 AI Auditing all photos simultaneously..."):
                results = {}
                task_keys = [f"{station}_{task}" for task in tasks_for_station]

                # 1. Batch fetch all references for this station in one DB call
                references = {}
                try:
                    ref_response = supabase.table('ai_references').select('task_key, photo_data, strictness').in_('task_key', task_keys).execute()
                    if ref_response.data:
                        for row in ref_response.data:
                            references[row['task_key']] = {
                                'photo_data': base64.b64decode(row['photo_data']),
                                'strictness': row['strictness']
                            }
                except Exception as e:
                    print(f"Failed to fetch references: {e}")

                # Helper for threading
                def verify_single(t_key, p_bytes, b_bytes, strict):
                    res = validate_photo_with_ai(b_bytes, p_bytes, strict)
                    return t_key, res

                # 2. Process all AI validations in parallel
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_to_task = {}
                    for tk in task_keys:
                        # Extract data safely on the main thread
                        p_bytes = st.session_state.task_photos[tk]
                        b_bytes = references.get(tk, {}).get('photo_data')
                        strict = references.get(tk, {}).get('strictness', 5)
                        future = executor.submit(verify_single, tk, p_bytes, b_bytes, strict)
                        future_to_task[future] = tk

                    for future in concurrent.futures.as_completed(future_to_task):
                        tk, res = future.result()
                        results[tk] = res

                st.session_state.verification_results = results
                st.rerun()

# Mode 2: Verification Results & Retake
else:
    st.header("📋 Verification Results")
    results = st.session_state.verification_results

    all_passed = True

    for task in tasks_for_station:
        task_key = f"{station}_{task}"
        res = results[task_key]

        with st.container():
            st.markdown(f"**{task}**")
            st.image(st.session_state.task_photos[task_key], width=200)

            if res["status"] == "FAIL":
                all_passed = False
                st.error(f"❌ FAILED: {res['reason']}")
                if res.get('feedback'):
                    st.warning(f"🔍 AI Feedback: {res['feedback']}")

                st.write("Please fix the issue and upload a new photo:")

                # Custom Native Component for retake
                img_data = native_camera(key=f"retake_cam_{task_key}")
                if img_data:
                    base64_str = img_data.split(',')[1]
                    photo_bytes = base64.b64decode(base64_str)
                    if photo_bytes != st.session_state.task_photos.get(task_key):
                        st.session_state.task_photos[task_key] = photo_bytes
                        # Update the results status to 'RETAKEN' so they know it needs to be verified again
                        st.session_state.verification_results[task_key] = {"status": "RETAKEN", "reason": "Photo updated. Waiting for re-verification."}
                        st.rerun()
            elif res["status"] == "RETAKEN":
                all_passed = False
                st.info("🔄 Photo updated. Ready for re-verification.")
                st.write("Native Camera / Upload:")
                img_data = native_camera(key=f"retake_cam2_{task_key}")
                if img_data:
                    base64_str = img_data.split(',')[1]
                    photo_bytes = base64.b64decode(base64_str)
                    if photo_bytes != st.session_state.task_photos.get(task_key):
                        st.session_state.task_photos[task_key] = photo_bytes
                        st.session_state.verification_results[task_key] = {"status": "RETAKEN", "reason": "Photo updated. Waiting for re-verification."}
                        st.rerun()
            else:
                st.success(f"✅ PASSED: {res['reason']}")

        st.markdown("---")

    if not all_passed:
        if st.button("Re-Verify Pending Duties", type="primary", use_container_width=True):
            with st.spinner("🤖 Re-evaluating updated photos simultaneously..."):
                tasks_to_verify = [f"{station}_{task}" for task in tasks_for_station if st.session_state.verification_results[f"{station}_{task}"]["status"] != "PASS"]

                if tasks_to_verify:
                    references = {}
                    try:
                        ref_response = supabase.table('ai_references').select('task_key, photo_data, strictness').in_('task_key', tasks_to_verify).execute()
                        if ref_response.data:
                            for row in ref_response.data:
                                references[row['task_key']] = {
                                    'photo_data': base64.b64decode(row['photo_data']),
                                    'strictness': row['strictness']
                                }
                    except Exception as e:
                        print(f"Failed to fetch references: {e}")

                    def verify_single(t_key, p_bytes, b_bytes, strict):
                        res = validate_photo_with_ai(b_bytes, p_bytes, strict)
                        return t_key, res

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future_to_task = {}
                        for tk in tasks_to_verify:
                            p_bytes = st.session_state.task_photos[tk]
                            b_bytes = references.get(tk, {}).get('photo_data')
                            strict = references.get(tk, {}).get('strictness', 5)
                            future = executor.submit(verify_single, tk, p_bytes, b_bytes, strict)
                            future_to_task[future] = tk

                        for future in concurrent.futures.as_completed(future_to_task):
                            tk, res = future.result()
                            st.session_state.verification_results[tk] = res

                st.rerun()

    if all_passed:
        if not st.session_state.get('submission_complete', False):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with st.spinner("Submitting final logs..."):
                all_success = True
                for task in tasks_for_station:
                    task_key = f"{station}_{task}"
                    photo_base64 = base64.b64encode(st.session_state.task_photos[task_key]).decode('utf-8')

                    try:
                        supabase.table('closing_logs').insert({
                            'timestamp': current_time,
                            'employee_name': employee_name,
                            'station': f"{station} - {task}",
                            'photo_data': photo_base64,
                            'status': "APPROVED"
                        }).execute()
                    except Exception as e:
                        st.error(f"Database error: {e}")
                        all_success = False
                        break

                if all_success:
                    st.session_state.submission_complete = True
                    st.rerun()
        else:
            st.success("🎉 All duties passed and logged successfully. Great job!")
            st.balloons()
            if st.button("Close Shift & Restart"):
                st.session_state.task_photos = {}
                st.session_state.verification_results = None
                st.session_state.submission_complete = False
                st.rerun()
    else:
        st.warning("Some duties failed verification. Please retake the failed photos above.")
