import streamlit as st
station_tasks = {}
selected_station = st.selectbox("Select Station", list(station_tasks.keys()))
st.write(selected_station)
try:
    for idx, task_dict in enumerate(station_tasks[selected_station]):
        st.write(task_dict)
except Exception as e:
    st.write("Error:", type(e).__name__, str(e))
