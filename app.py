import streamlit as st
import base64
from datetime import datetime
from config import supabase, STATION_TASKS
from ai_validator import validate_photo_with_ai

st.set_page_config(
    page_title="Closing Verification Protocol",
    page_icon="🔒",
    layout="centered"
)

st.title("🔒 Shift Verification Protocol")
st.markdown("Live photographic proof & binary station checklist verification.")
st.markdown("---")

employee_name = st.text_input("Employee Identifier", placeholder="Enter your name")
station = st.selectbox("Select Station", list(STATION_TASKS.keys()))

st.subheader(f"{station} Operational Requirements")

# Dynamic binary checklist
checklist_status = []
for task in STATION_TASKS[station]:
    is_done = st.checkbox(task)
    checklist_status.append(is_done)

st.markdown("---")
st.subheader("Photographic Verification")
st.info("Live capture required. Point camera at the primary verification choke point (e.g. clean floor drain or scraped grill).")

photo = st.camera_input("Capture Proof")

if st.button("Submit Verification", type="primary", use_container_width=True):
    if not employee_name:
        st.error("Error: Employee Identifier required.")
    elif not all(checklist_status):
        st.error("Error: All operational requirements must be verified. No partial completions accepted.")
    elif photo is None:
        st.error("Error: Live photographic proof required to authorize departure.")
    else:
        photo_bytes = photo.getvalue()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Optional AI Validation check
        ai_res = validate_photo_with_ai(None, photo_bytes)

        if ai_res["status"] == "FAIL":
            st.error(f"AI Verification Failed: {ai_res['reason']}")
        else:
            photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')

            try:
                response = supabase.table('closing_logs').insert({
                    'timestamp': current_time,
                    'employee_name': employee_name,
                    'station': station,
                    'photo_data': photo_base64,
                    'status': ai_res["status"]
                }).execute()
                st.success(f"Verification accepted at {current_time}. You are authorized to log off.")
                st.balloons()
            except Exception as e:
                st.error(f"Database error: {str(e)}")
