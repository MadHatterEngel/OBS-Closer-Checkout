import streamlit.components.v1 as components
import os

_component_func = components.declare_component(
    "native_camera",
    path=os.path.join(os.path.dirname(__file__), "native_camera")
)

def native_camera(key=None):
    return _component_func(key=key, default=None)
