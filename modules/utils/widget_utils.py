# modules/utils/widget_utils.py
import streamlit as st

def generate_unique_key(module_name, element_type="input", username=None, suffix=None):
    username = username or st.session_state.username
    base_key = f"{module_name}_{element_type}_{username}"
    
    # Si pasamos un sufijo (como un ID de la DB o un índice), lo añadimos
    if suffix:
        return f"{base_key}_{suffix}"
    return base_key