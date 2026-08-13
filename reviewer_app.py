import streamlit as st
import pandas as pd
import io
import base64
from PIL import Image
from config import supabase

st.set_page_config(page_title="Manager Command Center", page_icon="👁️", layout="wide")

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

def fetch_logs():
    try:
        response = supabase.table('closing_logs').select('id, timestamp, employee_name, station, photo_data, status').order('id', desc=True).limit(50).execute()
        return response.data
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return []

logs = fetch_logs()

if not logs:
    st.info("No compliance logs detected in the database.")
    st.stop()

# Summary Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Closing Logs", len(logs))
col2.metric("Latest Submission", logs[0]['timestamp'] if logs else "N/A")
unique_stations = len(set(log['station'] for log in logs))
col3.metric("Stations Audited", unique_stations)

st.markdown("---")
st.subheader("📸 Visual Compliance Feed")

for log in logs:
    log_id = log['id']
    timestamp = log['timestamp']
    employee = log['employee_name']
    station = log['station']
    photo_data_b64 = log['photo_data']
    status = log['status']

    with st.expander(f"Log #{log_id}: {timestamp} | {employee} — {station}"):
        data_col, photo_col = st.columns([1, 2])

        with data_col:
            st.write(f"**Timestamp:** {timestamp}")
            st.write(f"**Employee:** {employee}")
            st.write(f"**Station:** {station}")
            st.write(f"**Compliance Status:** ✅ {status}")

        with photo_col:
            if photo_data_b64:
                try:
                    photo_bytes = base64.b64decode(photo_data_b64)
                    image = Image.open(io.BytesIO(photo_bytes))
                    st.image(image, caption=f"Captured live at {timestamp}", use_column_width=True)
                except Exception as e:
                    st.error(f"Failed to load image data: {str(e)}")
            else:
                st.warning("No image data found for this entry.")
