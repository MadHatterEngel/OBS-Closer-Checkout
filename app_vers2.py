import streamlit as st
st.set_page_config(page_title="Outback Station Validator", page_icon="🥩", layout="centered")

import base64
from datetime import datetime
import uuid
import concurrent.futures
from config import supabase, fetch_station_tasks
from ai_validator import validate_photo_with_ai
from ui_styling import apply_custom_css, apply_mobile_tweaks
from components import native_camera, bulk_uploader

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

# --- MODE 1: BULK COLLECTION ---
if st.session_state.verification_results is None:

    st.markdown("### 1. Snap Photos")
    st.info("Use your phone's native camera app to walk around and quickly snap photos of all completed tasks for this station. Then upload them all at once below.")

    # Show the list of tasks so they know what to photograph
    with st.expander("📋 View Station Checklist", expanded=False):
        for task_dict in tasks_for_station:
            display_task = f"**{task_dict['task']}** (Daily)" if task_dict.get('day_of_week') else task_dict['task']
            st.markdown(f"- {display_task}")
            if task_dict.get('details'):
                st.caption(f"  *Restock: {task_dict['details']}*")

    st.markdown("### 2. Upload & Process")

    # Initialize session state for batch uploads if not present
    if "submission_bytes_list" not in st.session_state:
        st.session_state.submission_bytes_list = []

    if "last_uploader_val" not in st.session_state:
        st.session_state.last_uploader_val = None

    # Custom bulk uploader component that compresses client-side to bypass Android memory limits
    compressed_base64_list = bulk_uploader(key="bulk_uploader_comp")

    if compressed_base64_list and compressed_base64_list != st.session_state.last_uploader_val:
        st.session_state.last_uploader_val = compressed_base64_list
        new_bytes = []
        for b64_str in compressed_base64_list:
            # The JS component returns standard data:image/jpeg;base64,... strings
            clean_b64 = b64_str.split(',')[1] if ',' in b64_str else b64_str
            new_bytes.append(base64.b64decode(clean_b64))

        # Append new uploads to session state and clear component state to prevent re-adding on reruns
        st.session_state.submission_bytes_list.extend(new_bytes)
        st.rerun()

    if st.session_state.submission_bytes_list:
        st.success(f"{len(st.session_state.submission_bytes_list)} photos processed & ready.")

        # Inject CSS to force side-by-side columns on mobile by targeting the gallery container specifically.
        # This overrides Streamlit's default media queries that stack columns.
        # Generate HTML for a flexbox grid of thumbnails
        import base64
        html_images = ""
        for idx, b_bytes in enumerate(st.session_state.submission_bytes_list):
            b64_encoded = base64.b64encode(b_bytes).decode("utf-8")
            html_images += f'''
            <div style="flex: 1 1 calc(20% - 10px); min-width: 60px; max-width: 20%; box-sizing: border-box; text-align: center;">
                <img src="data:image/jpeg;base64,{b64_encoded}" style="width: 100%; border-radius: 4px; object-fit: cover; aspect-ratio: 1/1;" />
            </div>
            '''

        grid_html = f'''
        <div style="display: flex; flex-wrap: wrap; gap: 10px; width: 100%; margin-bottom: 10px;">
            {html_images}
        </div>
        '''
        st.markdown(grid_html, unsafe_allow_html=True)

        st.write("Select a photo to remove it:")

        # We must keep track of indices to delete to avoid modifying list during iteration
        idx_to_remove = None

        # We still need Streamlit buttons for interaction, we render them below the HTML grid as a row of small buttons
        cols = st.columns(len(st.session_state.submission_bytes_list))
        for idx in range(len(st.session_state.submission_bytes_list)):
            with cols[idx]:
                if st.button(f"❌ {idx+1}", key=f"remove_thumb_{idx}", help="Remove this photo"):
                    idx_to_remove = idx

        if idx_to_remove is not None:
            st.session_state.submission_bytes_list.pop(idx_to_remove)
            st.rerun()

    if st.button("🤖 Process & Verify Station", type="primary", use_container_width=True, disabled=not st.session_state.submission_bytes_list):
        if not employee_name:
            st.error("Employee Identifier is required.")
        else:
            with st.spinner("🤖 AI is matching and verifying your photos. This may take a moment..."):
                from ai_validator import validate_bulk_photos_with_ai

                # Fetch references for this station
                task_keys = [f"{station}_{t['task']}" for t in tasks_for_station]
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

                # We need to map tasks to photos and grade them
                results, mapped_photos = validate_bulk_photos_with_ai(tasks_for_station, station, references, st.session_state.submission_bytes_list)

                st.session_state.verification_results = results
                st.session_state.task_photos = mapped_photos
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

                retake_file = st.file_uploader("Upload Retake", type=["jpg", "jpeg", "png"], key=f"retake_cam_{task_key}_{idx}")
                if retake_file:
                    st.session_state.task_photos[task_key] = retake_file.getvalue()
                    st.session_state.verification_results[task_key] = {"status": "RETAKEN", "reason": "Photo updated. Waiting for re-verification."}
                    st.rerun()

            elif res["status"] == "RETAKEN":
                all_passed = False
                st.info("🔄 Photo updated. Ready for re-verification.")
                retake_file = st.file_uploader("Upload Retake", type=["jpg", "jpeg", "png"], key=f"retake_cam2_{task_key}_{idx}")
                if retake_file:
                    st.session_state.task_photos[task_key] = retake_file.getvalue()
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
                            'photo_data': None, # Deprecated the base64 column
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
