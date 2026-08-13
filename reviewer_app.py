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

# Allow download and clear even if there are no logs to avoid confusing the user
# that the buttons are just gone.
if not logs:
    st.info("No compliance logs detected in the database.")
else:
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

st.markdown("---")
st.subheader("🛠️ Data Management")

# Prepare data for download (excluding base64 image data)
download_data = []
for log in logs:
    download_data.append({
        "ID": log["id"],
        "Timestamp": log["timestamp"],
        "Employee": log["employee_name"],
        "Station": log["station"],
        "Status": log["status"]
    })

if download_data:
    df = pd.DataFrame(download_data)
else:
    df = pd.DataFrame(columns=["ID", "Timestamp", "Employee", "Station", "Status"])

csv = df.to_csv(index=False).encode('utf-8')

col_dl, col_clear = st.columns(2)

with col_dl:
    st.download_button(
        label="📥 Download Logs (CSV)",
        data=csv,
        file_name="closing_logs.csv",
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
