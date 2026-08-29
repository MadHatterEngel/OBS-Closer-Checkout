import os
import streamlit.components.v1 as components

_component_func = components.declare_component(
    "native_camera",
    path=os.path.join(os.path.dirname(__file__), "native_camera")
)

def native_camera(key=None):
    return _component_func(key=key)

_bulk_uploader_func = components.declare_component(
    "bulk_uploader",
    path=os.path.join(os.path.dirname(__file__), "bulk_uploader")
)

def bulk_uploader(key=None):
    return _bulk_uploader_func(key=key)
