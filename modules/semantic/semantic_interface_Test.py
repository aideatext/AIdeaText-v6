import streamlit as st
from streamlit_float import *

# Limpiar el caché al inicio
st.cache_data.clear()
st.cache_resource.clear()


# initialize float feature/capability
float_init()

col1, col2 = st.columns(2)

# Fix/float the whole column
col1.write("This entire column is fixed/floating")
col1.float()

with col2:
    container = st.container()
    # Fix/float a single container inside
    container.write("This text is in a container that is fixed")
    container.float()