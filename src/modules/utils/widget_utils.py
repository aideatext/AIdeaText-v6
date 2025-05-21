# modules/utils/widget_utils.py
import streamlit as st

def generate_unique_key(module_name, element_type="input", username=None):
    # Si el nombre de usuario no se pasa explícitamente, lo toma de session_state
    username = username or st.session_state.username
    return f"{module_name}_{element_type}_{username}"