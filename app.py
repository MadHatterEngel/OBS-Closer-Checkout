import streamlit as st
st.set_page_config(page_title="Outback Station Validator", page_icon="🥩", layout="centered")

import base64
from datetime import datetime
import uuid
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
    if not STATION_TASKS:
        st.error("No stations configured. Please contact your manager.")
        st.stop()

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

current_day = datetime.now().strftime('%A')
raw_tasks = STATION_TASKS[station]
filtered_tasks = []
daily_tasks = []
for t in raw_tasks:
    if isinstance(t, str):
        filtered_tasks.append({'task': t})
    elif t.get('day_of_week'):
        if t['day_of_week'] == current_day:
            daily_tasks.append(t)
    else:
        filtered_tasks.append(t)
tasks_for_station = filtered_tasks + daily_tasks

# --- MODE 1: COLLECTION ---
if st.session_state.verification_results is None:

    missing_tasks = []
    for task_dict in tasks_for_station:
        task = task_dict['task']
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
            for idx, task_dict in enumerate(tasks_for_station):
                task = task_dict['task']
                task_key = f"{station}_{task}"
                with cols[idx % 2]:
                    with st.container():
                        display_task = f"**{task}** (Daily)" if task_dict.get('day_of_week') else task
                        if task_key in st.session_state.task_photos:
                            st.success(f"✅ {display_task}")
                            if task_dict.get('details'):
                                with st.expander("ℹ️ Restock Details"):
                                    st.write(task_dict['details'])
                            if st.button("Retake", key=f"retake_btn_{task_key}_{idx}"):
                                del st.session_state.task_photos[task_key]
                                st.rerun()
                        else:
                            st.error(f"❌ {display_task}")
                            if task_dict.get('details'):
                                with st.expander("ℹ️ Restock Details"):
                                    st.write(task_dict['details'])
                            # Give option to take it right here if they don't want sequential
                            img_data = native_camera(key=f"cam_{task_key}_{idx}")
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
                        task_keys = [f"{station}_{t['task']}" for t in tasks_for_station]
                        references = {}
                        try:
                            ref_response = supabase.table('ai_references').select('task_key, photo_data, strictness').in_('task_key', task_keys).execute()
                            if ref_response.data:
                                for row in ref_response.data:
                                    import requests
                                    img_val = row['photo_data']
                                    baseline_bytes = None
                                    if img_val and str(img_val).strip() not in ['', 'None'] and img_val.startswith('http'):
                                        try:
                                            resp = requests.get(img_val)
                                            if resp.status_code == 200:
                                                baseline_bytes = resp.content
                                        except Exception:
                                            pass

                                    references[row['task_key']] = {
                                        'photo_data': baseline_bytes,
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

    for idx, task_dict in enumerate(tasks_for_station):
        task = task_dict['task']
        display_task = f"**{task}** (Daily)" if task_dict.get('day_of_week') else task
        task_key = f"{station}_{task}"
        res = results[task_key]

        with st.container():
            st.markdown(f"**{display_task}**")
            if task_dict.get('details'):
                with st.expander("ℹ️ Restock Details"):
                    st.write(task_dict['details'])

            if res["status"] == "FAIL":
                all_passed = False
                st.error(f"❌ FAILED: {res['reason']}")
                if res.get('feedback'):
                    st.warning(f"🔍 AI Feedback: {res['feedback']}")

                img_data = native_camera(key=f"retake_cam_{task_key}_{idx}")
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
                img_data = native_camera(key=f"retake_cam2_{task_key}_{idx}")
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
                tasks_to_verify = [f"{station}_{t['task']}" for t in tasks_for_station if st.session_state.verification_results[f"{station}_{t['task']}"]["status"] != "PASS"]
                if tasks_to_verify:
                    references = {}
                    try:
                        ref_response = supabase.table('ai_references').select('task_key, photo_data, strictness').in_('task_key', tasks_to_verify).execute()
                        if ref_response.data:
                            for row in ref_response.data:
                                import requests
                                img_val = row['photo_data']
                                baseline_bytes = None
                                if img_val and str(img_val).strip() not in ['', 'None'] and img_val.startswith('http'):
                                    try:
                                        resp = requests.get(img_val)
                                        if resp.status_code == 200:
                                            baseline_bytes = resp.content
                                    except Exception:
                                        pass

                                references[row['task_key']] = {
                                    'photo_data': baseline_bytes,
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
                for task_dict in tasks_for_station:
                    task = task_dict['task']
                    task_key = f"{station}_{task}"
                    photo_bytes = st.session_state.task_photos[task_key]
                    try:
                        # 1. Upload to Storage Bucket
                        file_ext = "jpg"
                        file_name = f"{current_time.replace(' ', '_').replace(':', '-')}_{uuid.uuid4().hex[:8]}.{file_ext}"

                        supabase.storage.from_('closing-photos').upload(
                            file_name,
                            photo_bytes,
                            {"content-type": "image/jpeg"}
                        )

                        # 2. Get Public URL
                        public_url = supabase.storage.from_('closing-photos').get_public_url(file_name)

                        # 3. Save to Database
                        supabase.table('closing_logs').insert({
                            'timestamp': current_time,
                            'employee_name': employee_name,
                            'station': f"{station} - {task}",
                            'image_url': public_url,
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
