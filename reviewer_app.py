import streamlit as st
import pandas as pd
import sqlite3
import io
import os
import base64
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

# 1. Page Configuration
st.set_page_config(
    page_title="Manager Command Center",
    page_icon="👁️",
    layout="wide"
)

# 2. Timezone Conversion Helper
def to_eastern_time(timestamp_val):
    """Converts a UTC or database timestamp string to Eastern Time (America/Detroit)."""
    if not timestamp_val:
        return "N/A"
    try:
        if isinstance(timestamp_val, str):
            cleaned_str = timestamp_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned_str)
        elif isinstance(timestamp_val, datetime):
            dt = timestamp_val
        else:
            return str(timestamp_val)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        eastern_dt = dt.astimezone(ZoneInfo("America/Detroit"))
        return eastern_dt.strftime("%Y-%m-%d %I:%M:%S %p")
    except Exception:
        return str(timestamp_val)

# 3. Security Access Gate
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

# 4. Header
st.title("👁️ Manager Operations Review Dashboard")
st.caption("Outback Steakhouse #2313 - Shift Verification & Compliance Feed")
st.markdown("---")

# 5. Database Connection
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATA_DIR, "compliance.db")

@st.cache_data(ttl=30)
def fetch_logs():
    if HAS_SUPABASE and "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        try:
            supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
            response = supabase.table("closing_logs").select("*").order("timestamp", desc=True).limit(50).execute()
            return response.data
        except Exception as e:
            st.warning(f"Cloud DB fetch error: {e}")

    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, timestamp, employee_name, station, photo_data, image_url, status FROM closing_logs ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            conn.close()
            data = []
            for row in rows:
                data.append({
                    "id": row[0],
                    "timestamp": row,
                    "employee_name": row,
                    "station": row,
                    "photo_data": row,
                    "image_url": row,
                    "status": row if len(row) > 6 else "APPROVED"
                })
            return data
        except Exception as e:
            st.error(f"Local DB error: {e}")
            return []
    return []

logs = fetch_logs()

if not logs:
    st.info("No compliance logs detected in the database.")
    st.stop()

# 6. Macro Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Closing Logs", len(logs))
latest_ts = to_eastern_time(logs[0].get("timestamp")) if logs else "N/A"
col2.metric("Latest Submission (ET)", latest_ts)
unique_stations = len(set(log.get("station", "Unknown") for log in logs))
col3.metric("Stations Audited", unique_stations)

st.markdown("---")

# 7. Image Helper
def display_proof_image(image_url, photo_data, caption):
    if image_url and isinstance(image_url, str) and (image_url.startswith("http://") or image_url.startswith("https://")):
        st.image(image_url, caption=caption, use_container_width=True)
        return

    if photo_data:
        if isinstance(photo_data, str) and (photo_data.startswith("http://") or photo_data.startswith("https://")):
            st.image(photo_data, caption=caption, use_container_width=True)
            return

        if isinstance(photo_data, str):
            try:
                b64_str = photo_data.split("base64,") if "base64," in photo_data else photo_data
                decoded = base64.b64decode(b64_str)
                img = Image.open(io.BytesIO(decoded))
                st.image(img, caption=caption, use_container_width=True)
                return
            except Exception:
                st.image(photo_data, caption=caption, use_container_width=True)
                return

        if isinstance(photo_data, (bytes, bytearray)):
            try:
                img = Image.open(io.BytesIO(photo_data))
                st.image(img, caption=caption, use_container_width=True)
                return
            except Exception:
                st.image(photo_data, caption=caption, use_container_width=True)
                return

    st.warning("No photographic proof attached to this log entry.")

# 8. Visual Compliance Feed
st.subheader("📸 Visual Compliance Feed")

for log in logs:
    log_id = log.get("id", "N/A")
    raw_ts = log.get("timestamp", "")
    eastern_ts = to_eastern_time(raw_ts)
    employee = log.get("employee_name", "Unknown")
    station = log.get("station", "General")
    status = log.get("status", "APPROVED")
    image_url = log.get("image_url")
    photo_data = log.get("photo_data")

    with st.expander(f"Log #{log_id}: {eastern_ts} | {employee} — {station}"):
        data_col, photo_col = st.columns(2)

        with data_col:
            st.write(f"**Timestamp (Eastern):** {eastern_ts}")
            st.write(f"**Employee:** {employee}")
            st.write(f"**Station:** {station}")
            st.write(f"**Compliance Status:** ✅ {status}")

        with photo_col:
            caption_text = f"Proof for {station} (Captured {eastern_ts})"
            display_proof_image(image_url, photo_data, caption_text)

# 9. Data Management (CSV & Clear Logs)
st.markdown("---")
st.subheader("🛠️ Data Management")

col_dl, col_clear = st.columns(2)

# CSV Export
csv_records = []
for l in logs:
    csv_records.append({
        "ID": l.get("id"),
        "Timestamp_ET": to_eastern_time(l.get("timestamp")),
        "Employee": l.get("employee_name"),
        "Station": l.get("station"),
        "Status": l.get("status", "APPROVED")
    })
df_export = pd.DataFrame(csv_records)
csv_bytes = df_export.to_csv(index=False).encode("utf-8")

col_dl.download_button(
    label="📥 Download Logs (CSV)",
    data=csv_bytes,
    file_name="closing_logs.csv",
    mime="text/csv",
    use_container_width=True
)

# Clear Logs
if col_clear.button("🗑️ Clear All Logs", type="secondary", use_container_width=True):
    st.session_state["confirm_clear"] = True

if st.session_state.get("confirm_clear", False):
    st.warning("⚠️ **WARNING:** This will permanently delete all logs. This cannot be undone.")
    col_confirm, col_cancel = st.columns(2)

    if col_confirm.button("🚨 Yes, Delete ALL Logs", type="primary", use_container_width=True):
        try:
            if HAS_SUPABASE and "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
                supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
                supabase.table("closing_logs").delete().neq("id", 0).execute()
            
            if os.path.exists(DB_PATH):
                conn = sqlite3.connect(DB_PATH)
                conn.execute("DELETE FROM closing_logs")
                conn.commit()
                conn.close()

            # Clear cache and reset confirmation
            st.cache_data.clear()
            st.session_state["confirm_clear"] = False
            st.success("All logs successfully deleted.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to delete logs: {e}")

    if col_cancel.button("Cancel", use_container_width=True):
        st.session_state["confirm_clear"] = False
        st.rerun()

