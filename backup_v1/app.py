import streamlit as st
st.set_page_config(page_title="Outback Station Validator", page_icon="🥩", layout="centered")

import base64
from datetime import datetime
import concurrent.futures
from config import supabase, fetch_station_tasks
from ai_validator import validate_photo_with_ai
from ui_styling import apply_custom_css, apply_mobile_tweaks
from components import native_camera

apply_custom_css()
apply_mobile_tweaks()

try:
    with open("assets/logo.svg", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(f'<img src="data:image/svg+xml;base64,{logo_data}" class="mh-logo">', unsafe_allow_html=True)
except:
    pass

STATION_TASKS = fetch_station_tasks()

st.markdown("## 🥩 Closing Protocol")

col1, col2 = st.columns(2)
with col1:
    employee_name = st.text_input("Employee Identifier", placeholder="Your name")
with col2:
    if 'current_station' not in st.session_state:
        st.session_state.current_station = list(STATION_TASKS.keys())[0]
    station = st.selectbox("Station", list(STATION_TASKS.keys()))

if station != st.session_state.current_station:
    st.session_state.current_station = station
    st.session_state.task_photos = {}
    st.session_state.verification_results = None
    st.session_state.sequential_mode = False
    st.session_state.capture_queue = []
    st.rerun()

st.subheader(f"{station} Duties")

if 'task_photos' not in st.session_state: st.session_state.task_photos = {}
if 'verification_results' not in st.session_state: st.session_state.verification_results = None
if 'submission_complete' not in st.session_state: st.session_state.submission_complete = False
if 'sequential_mode' not in st.session_state: st.session_state.sequential_mode = False
if 'capture_queue' not in st.session_state: st.session_state.capture_queue = []

tasks_for_station = STATION_TASKS[station]

# --- MODE 1: COLLECTION ---
if st.session_state.verification_results is None:

    missing_tasks = []
    for task in tasks_for_station:
        task_key = f"{station}_{task}"
        if task_key not in st.session_state.task_photos:
            missing_tasks.append((task_key, task))

    # SEQUENTIAL CAMERA VIEW
    if st.session_state.sequential_mode and len(st.session_state.capture_queue) > 0:
        current_task_key, current_task_name = st.session_state.capture_queue[0]
        st.info(f"📸 **Capturing:** {current_task_name}")

        img_data = native_camera(key=f"seq_cam_{current_task_key}")
        if img_data:
            if img_data != st.session_state.get(f"raw_cam_{current_task_key}"):
                st.session_state[f"raw_cam_{current_task_key}"] = img_data
                base64_str = img_data.split(',')[1]
                st.session_state.task_photos[current_task_key] = base64.b64decode(base64_str)
                st.session_state.capture_queue.pop(0)
                st.rerun()

        st.write("")
        if st.button("Cancel & Return to List"):
            st.session_state.sequential_mode = False
            st.session_state.capture_queue = []
            st.rerun()

    # STANDARD LIST VIEW
    else:
        # Check if queue finished organically and trigger auto-verify
        if st.session_state.sequential_mode and len(st.session_state.capture_queue) == 0:
            st.session_state.sequential_mode = False
            auto_submit = True
        else:
            auto_submit = False

        if not auto_submit:
            # Display current staged status compactly
            cols = st.columns(2)
            for idx, task in enumerate(tasks_for_station):
                task_key = f"{station}_{task}"
                with cols[idx % 2]:
                    with st.container():
                        if task_key in st.session_state.task_photos:
                            st.success(f"✅ {task}")
                            if st.button("Retake", key=f"retake_btn_{task_key}"):
                                del st.session_state.task_photos[task_key]
                                st.rerun()
                        else:
                            st.error(f"❌ {task}")
                            # Give option to take it right here if they don't want sequential
                            img_data = native_camera(key=f"cam_{task_key}")
                            if img_data:
                                if img_data != st.session_state.get(f"raw_cam_{task_key}"):
                                    st.session_state[f"raw_cam_{task_key}"] = img_data
                                    base64_str = img_data.split(',')[1]
                                    st.session_state.task_photos[task_key] = base64.b64decode(base64_str)
                                    st.rerun()
                if (idx + 1) % 2 == 0:
                    st.write("")

        can_submit = len(missing_tasks) == 0
        btn_label = "Verify & Submit All" if can_submit else f"Capture {len(missing_tasks)} Remaining & Submit"

        if auto_submit or st.button(btn_label, type="primary", use_container_width=True):
            if not employee_name:
                st.error("Employee Identifier is required.")
                st.session_state.sequential_mode = False
            else:
                if not can_submit:
                    # Enter Sequential Capture Mode
                    st.session_state.sequential_mode = True
                    st.session_state.capture_queue = missing_tasks
                    st.rerun()
                else:
                    # Threaded Batch AI Verification
                    with st.spinner("🤖 AI Auditing all photos simultaneously..."):
                        results = {}
                        task_keys = [f"{station}_{task}" for task in tasks_for_station]
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

                        def verify_single(t_key, p_bytes, b_bytes, strict):
                            res = validate_photo_with_ai(b_bytes, p_bytes, strict)
                            return t_key, res

                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future_to_task = {}
                            for tk in task_keys:
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

# --- MODE 2: RESULTS & RETAKE ---
else:
    st.header("📋 Verification Results")
    results = st.session_state.verification_results
    all_passed = True

    for task in tasks_for_station:
        task_key = f"{station}_{task}"
        res = results[task_key]

        with st.container():
            st.markdown(f"**{task}**")

            if res["status"] == "FAIL":
                all_passed = False
                st.error(f"❌ FAILED: {res['reason']}")
                if res.get('feedback'):
                    st.warning(f"🔍 AI Feedback: {res['feedback']}")

                img_data = native_camera(key=f"retake_cam_{task_key}")
                if img_data:
                    if img_data != st.session_state.get(f"raw_cam_{task_key}"):
                        st.session_state[f"raw_cam_{task_key}"] = img_data
                        base64_str = img_data.split(',')[1]
                        st.session_state.task_photos[task_key] = base64.b64decode(base64_str)
                        st.session_state.verification_results[task_key] = {"status": "RETAKEN", "reason": "Photo updated. Waiting for re-verification."}
                        st.rerun()

            elif res["status"] == "RETAKEN":
                all_passed = False
                st.info("🔄 Photo updated. Ready for re-verification.")
                img_data = native_camera(key=f"retake_cam2_{task_key}")
                if img_data:
                    if img_data != st.session_state.get(f"raw_cam2_{task_key}"):
                        st.session_state[f"raw_cam2_{task_key}"] = img_data
                        base64_str = img_data.split(',')[1]
                        st.session_state.task_photos[task_key] = base64.b64decode(base64_str)
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
