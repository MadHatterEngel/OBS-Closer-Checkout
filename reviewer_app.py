import streamlit as st
import pandas as pd
import sqlite3
import io
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image

# Optional Supabase import
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
            # Clean ISO string if needed
            cleaned_str = timestamp_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned_str)
        elif isinstance(timestamp_val, datetime):
            dt = timestamp_val
        else:
            return str(timestamp_val)

        # If naive (no timezone attached), assume UTC from DB
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        # Convert to Eastern Time (handles EST/EDT daylight saving automatically)
        eastern_dt = dt.astimezone(ZoneInfo("America/Detroit"))
        return eastern_dt.strftime("%Y-%m-%d %I:%M:%S %p")
    except Exception:
        return str(timestamp_val)

# 3. Security Access Gate
def check_password():
    """Protects the dashboard with a password from Streamlit secrets."""
    def password_entered():
        manager_pass = st.secrets.get("MANAGER_PASSWORD", "manager123")
        if st.session_state["password_input"] == manager_pass:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Enter Manager Access Code",
            type="password",
            on_change=password_entered,
            key="password_input"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Enter Manager Access Code",
            type="password",
            on_change=password_entered,
            key="password_input"
        )
        st.error("Access Denied. Incorrect verification code.")
        return False
    return True

if not check_password():
    st.stop()

# 4. Header
st.title("👁️ Manager Operations Review Dashboard")
st.caption("Outback Steakhouse #2313 - Shift Verification & Compliance Feed")
st.markdown("---")

# 5. Database Connection (Supabase Cloud or SQLite Fallback)
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATA_DIR, "compliance.db")

@st.cache_data(ttl=30)
def fetch_logs():
    # If Supabase credentials are configured in secrets
    if HAS_SUPABASE and "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        try:
            supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
            response = supabase.table("closing_logs").select("*").order("timestamp", desc=True).limit(50).execute()
            return response.data
        except Exception as e:
            st.warning(f"Cloud DB fetch failed, falling back to local database: {e}")

    # Fallback to local SQLite database
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, timestamp, employee_name, station, photo_data, image_url, status "
                "FROM closing_logs ORDER BY id DESC LIMIT 50"
            )
            rows = cursor.fetchall()
            conn.close()
            
            data = []
            for row in rows:
                data.append({
                    "id": row[0],
                    "timestamp": row,
                    "employee_name": row[2],
                    "station": row[3],
                    "photo_data": row[4],
                    "image_url": row[5],
                    "status": row[6] if len(row) > 6 else "APPROVED"
                })
            return data
        except Exception as e:
            st.error(f"Local DB read error: {e}")
            return []
    return []

logs = fetch_logs()

if not logs:
    st.info("No compliance logs detected in the database.")
    st.stop()

# 6. Macro-Level Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Recent Submissions", len(logs))
latest_ts = to_eastern_time(logs[0].get("timestamp")) if logs else "N/A"
col2.metric("Latest Submission (ET)", latest_ts)
unique_stations = len(set(log.get("station", "Unknown") for log in logs))
col3.metric("Stations Audited", unique_stations)

st.markdown("---")

# 7. Visual Compliance Feed
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
        data_col, photo_col = st.columns("")

        with data_col:
            st.write(f"**Timestamp (Eastern):** {eastern_ts}")
            st.write(f"**Employee:** {employee}")
            st.write(f"**Station:** {station}")
            st.write(f"**Compliance Status:** ✅ {status}")

        with photo_col:
            # 1. Cloud URL rendering (Supabase storage)
            if image_url:
                try:
                    st.image(image_url, caption=f"Proof for {station} (Captured {eastern_ts})", use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to render image URL: {e}")
            # 2. Local byte rendering (SQLite BLOB)
            elif photo_data:
                try:
                    img = Image.open(io.BytesIO(photo_data))
                    st.image(img, caption=f"Proof for {station} (Captured {eastern_ts})", use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to render image bytes: {e}")
            else:
                st.warning("No photographic proof attached to this log entry.")
