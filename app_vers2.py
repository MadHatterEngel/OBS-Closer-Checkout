import streamlit as st
st.set_page_config(page_title="Outback Station Validator", page_icon="🥩", layout="centered")

import base64
from datetime import datetime
import uuid
from config import supabase, fetch_station_tasks
from ai_validator import validate_bulk_photos_with_ai
from ui_styling import apply_custom_css, apply_mobile_tweaks
from components import bulk_uploader

apply_custom_css()
apply_mobile_tweaks()

try:
    with open("assets/logo.svg", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(f'<img src="data:image/svg+xml;base64,{logo_data}" class="mh-logo">', unsafe_allow_html=True)
except Exception:
    pass


def task_key_for(station_name, task_name):
    """Generate a consistent task key for state management."""
    return f"{station_name}_{task_name}"


def fetch_reference_map(task_keys):
    """
    Fetch AI reference photos from the database.
    Optimized for mobile by using timeout and graceful fallback.
    """
    references = {}
    if not task_keys:
        return references

    try:
        ref_response = supabase.table("ai_references").select("task_key, photo_data, strictness").in_("task_key", task_keys).execute()
        if ref_response.data:
            for row in ref_response.data:
                import requests

                img_val = row.get("photo_data")
                baseline_bytes = None

                if img_val and str(img_val).strip() not in ["", "None"] and str(img_val).startswith("http"):
                    try:
                        # Mobile-friendly timeout
                        resp = requests.get(img_val, timeout=10)
                        if resp.status_code == 200:
                            baseline_bytes = resp.content
                    except Exception:
                        pass

                references[row["task_key"]] = {
                    "photo_data": baseline_bytes,
                    "strictness": row.get("strictness", 5)
                }
    except Exception as e:
        st.warning(f"⚠️ Could not load reference images: {str(e)[:50]}...")

    return references


@st.dialog("Upload Retake Photo")
def upload_retake_modal(task_key, task_name):
    """
    Modal for uploading a retake photo.
    Optimized for mobile with simple UI and instant feedback.
    """
    st.write(f"Uploading new photo for: **{task_name}**")

    retake_file = st.file_uploader(
        "Select new photo",
        type=["jpg", "jpeg", "png"],
        key=f"modal_upload_{task_key}",
        help="Choose from your device photos"
    )

    if retake_file:
        try:
            photo_bytes = retake_file.getvalue()
            st.session_state.task_photos[task_key] = photo_bytes
            st.session_state.verification_results[task_key] = {
                "status": "RETAKEN",
                "reason": "Photo updated. Waiting for re-verification."
            }
            st.success("✅ Photo saved. Click 'Close' and then 'Re-Verify Failed Tasks'.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save photo: {str(e)[:50]}...")


STATION_TASKS = fetch_station_tasks()

st.markdown("## 🥩 Closing Protocol")

col1, col2 = st.columns(2)
with col1:
    employee_name = st.text_input("Employee Identifier", placeholder="Your name")
with col2:
    if not STATION_TASKS:
        st.error("No stations configured. Please contact your manager.")
        st.stop()

    if "current_station" not in st.session_state:
        st.session_state.current_station = list(STATION_TASKS.keys())[0]
    station = st.selectbox("Station", list(STATION_TASKS.keys()))

if station != st.session_state.current_station:
    st.session_state.current_station = station
    st.session_state.task_photos = {}
    st.session_state.verification_results = None
    st.session_state.submission_complete = False
    st.session_state.submission_bytes_list = []
    st.session_state.last_uploader_val = None
    st.rerun()

st.subheader(f"{station} Duties")

# Initialize session state
if "task_photos" not in st.session_state:
    st.session_state.task_photos = {}
if "verification_results" not in st.session_state:
    st.session_state.verification_results = None
if "submission_complete" not in st.session_state:
    st.session_state.submission_complete = False
if "submission_bytes_list" not in st.session_state:
    st.session_state.submission_bytes_list = []
if "last_uploader_val" not in st.session_state:
    st.session_state.last_uploader_val = None

current_day = datetime.now().strftime("%A")
raw_tasks = STATION_TASKS[station]
filtered_tasks = []
daily_tasks = []

for t in raw_tasks:
    if isinstance(t, str):
        filtered_tasks.append({"task": t})
    elif t.get("day_of_week"):
        if t["day_of_week"] == current_day:
            daily_tasks.append(t)
    else:
        filtered_tasks.append(t)

tasks_for_station = filtered_tasks + daily_tasks

# --- MODE 1: BULK COLLECTION ---
if st.session_state.verification_results is None:

    st.markdown("### 1. Snap Photos")
    st.info("📸 Use your phone's native camera to snap photos. Upload them all at once below.")

    with st.expander("📋 View Station Checklist", expanded=False):
        for task_dict in tasks_for_station:
            # We want to format this with (Monday Deep Clean) if they have a day of week
            if task_dict.get('day_of_week'):
                display_task = f"**{task_dict['task']}** ({task_dict['day_of_week']} Deep Clean)"
            else:
                display_task = f"**{task_dict['task']}**"
            st.markdown(f"- {display_task}")
            if task_dict.get("details"):
                st.caption(f"  *Details: {task_dict['details']}*")

    st.markdown("### 2. Upload & Process")

    # Custom bulk uploader component (client-side compression for Android)
    compressed_base64_list = bulk_uploader(key="bulk_uploader_comp")

    if compressed_base64_list and compressed_base64_list != st.session_state.last_uploader_val:
        st.session_state.last_uploader_val = compressed_base64_list
        new_bytes = []
        for b64_str in compressed_base64_list:
            try:
                clean_b64 = b64_str.split(",")[1] if "," in b64_str else b64_str
                new_bytes.append(base64.b64decode(clean_b64))
            except Exception:
                st.warning("⚠️ One photo failed to process. Skipping...")
                continue

        st.session_state.submission_bytes_list.extend(new_bytes)
        st.rerun()

    if st.session_state.submission_bytes_list:
        st.success(f"✅ {len(st.session_state.submission_bytes_list)} photos ready")

        with st.expander("🔍 Review & Edit Photos", expanded=False):
            idx_to_remove = None
            cols = st.columns(5)

            for idx, b_bytes in enumerate(st.session_state.submission_bytes_list):
                with cols[idx % 5]:
                    st.image(b_bytes, use_container_width=True)
                    if st.button("❌", key=f"remove_thumb_{idx}", help="Remove", use_container_width=True):
                        idx_to_remove = idx

            if idx_to_remove is not None:
                st.session_state.submission_bytes_list.pop(idx_to_remove)
                st.rerun()

    if st.button(
        "🤖 Process & Verify Station",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.submission_bytes_list
    ):
        if not employee_name.strip():
            st.error("Employee Identifier is required.")
        else:
            with st.spinner("🤖 AI analyzing photos... This may take 15-30 seconds on mobile..."):
                try:
                    task_keys = [task_key_for(station, t["task"]) for t in tasks_for_station]
                    references = fetch_reference_map(task_keys)

                    results, mapped_photos = validate_bulk_photos_with_ai(
                        tasks_for_station,
                        station,
                        references,
                        st.session_state.submission_bytes_list
                    )

                    st.session_state.verification_results = results
                    st.session_state.task_photos = mapped_photos
                    st.rerun()

                except Exception as e:
                    st.error(f"AI verification failed: {str(e)[:100]}...")
                    st.info("Try refreshing the page and uploading again.")


# --- MODE 2: RESULTS SCREEN ---
else:
    st.header("📋 Verification Results")
    results = st.session_state.verification_results
    all_passed = True

    for idx, task_dict in enumerate(tasks_for_station):
        task = task_dict["task"]
        if task_dict.get('day_of_week'):
            display_task = f"**{task}** ({task_dict['day_of_week']} Deep Clean)"
        else:
            display_task = f"**{task}**"

        task_key = task_key_for(station, task)
        res = results.get(task_key, {"status": "FAIL", "reason": "No result found."})

        with st.container():
            st.markdown(f"{display_task}")
            if task_dict.get("details"):
                with st.expander("ℹ️ Details"):
                    st.write(task_dict["details"])

            if res["status"] == "FAIL":
                all_passed = False
                st.error(f"❌ FAILED: {res['reason']}")
                if res.get("feedback"):
                    st.warning(f"🔍 AI Feedback: {res['feedback']}")

                if st.button("📸 Upload Retake", key=f"retake_btn_{task_key}_{idx}"):
                    upload_retake_modal(task_key, task)

            elif res["status"] == "RETAKEN":
                all_passed = False
                st.info("🔄 Photo updated. Ready for re-verification.")
                if st.button("📸 Upload Different Photo", key=f"retake_btn2_{task_key}_{idx}"):
                    upload_retake_modal(task_key, task)

            else:
                st.success(f"✅ PASSED: {res['reason']}")

        st.markdown("---")

    if not all_passed:
        if st.button("Re-Verify Failed Tasks", type="primary", use_container_width=True):
            with st.spinner("🤖 Re-checking updated photos..."):
                try:
                    failed_tasks = []
                    failed_task_keys = []

                    for task_dict in tasks_for_station:
                        task_key = task_key_for(station, task_dict["task"])
                        current_result = st.session_state.verification_results.get(task_key)
                        if not current_result or current_result.get("status") != "PASS":
                            failed_tasks.append(task_dict)
                            failed_task_keys.append(task_key)

                    if failed_tasks:
                        references = fetch_reference_map([task_key_for(station, t["task"]) for t in failed_tasks])

                        failed_photos = []
                        for task_dict in failed_tasks:
                            task_key = task_key_for(station, task_dict["task"])
                            if task_key in st.session_state.task_photos:
                                failed_photos.append(st.session_state.task_photos[task_key])

                        if failed_photos:
                            results_subset, mapped_photos = validate_bulk_photos_with_ai(
                                failed_tasks,
                                station,
                                references,
                                failed_photos
                            )

                            for task_key, result in results_subset.items():
                                st.session_state.verification_results[task_key] = result

                            st.session_state.task_photos.update(mapped_photos)

                    st.rerun()

                except Exception as e:
                    st.error(f"Re-verification failed: {str(e)[:100]}...")

    if all_passed:
        if not st.session_state.get("submission_complete", False):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with st.spinner("📤 Uploading final logs..."):
                all_success = True

                for task_dict in tasks_for_station:
                    task = task_dict["task"]
                    task_key = task_key_for(station, task)
                    photo_bytes = st.session_state.task_photos.get(task_key)

                    if photo_bytes is None:
                        st.error(f"Missing photo for task: {task}")
                        all_success = False
                        break

                    try:
                        file_ext = "jpg"
                        file_name = f"{current_time.replace(' ', '_').replace(':', '-')}_{uuid.uuid4().hex[:8]}.{file_ext}"

                        supabase.storage.from_("closing-photos").upload(
                            file_name,
                            photo_bytes,
                            {"content-type": "image/jpeg"}
                        )

                        public_url = supabase.storage.from_("closing-photos").get_public_url(file_name)

                        if not public_url or not isinstance(public_url, str) or len(public_url.strip()) < 10:
                            raise Exception("Invalid storage URL returned.")

                        supabase.table("closing_logs").insert({
                            "timestamp": current_time,
                            "employee_name": employee_name.strip(),
                            "station": f"{station} - {task}",
                            "image_url": public_url,
                            "status": "APPROVED"
                        }).execute()

                    except Exception as e:
                        st.error(f"Upload error: {str(e)[:100]}...")
                        all_success = False
                        break

                if all_success:
                    st.session_state.submission_complete = True
                    st.rerun()
        else:
            st.success("🎉 All duties passed and logged successfully!")
            st.balloons()

            if st.button("Close Shift & Restart"):
                st.session_state.task_photos = {}
                st.session_state.verification_results = None
                st.session_state.submission_complete = False
                st.session_state.submission_bytes_list = []
                st.session_state.last_uploader_val = None
                st.rerun()
