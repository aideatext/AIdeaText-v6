import streamlit as st

def initialize_session_state():
    if 'initialized' not in st.session_state:
        st.session_state.clear()
        st.session_state.initialized = True
        st.session_state.logged_in = False
        st.session_state.page = 'login'
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.lang_code = 'es'

        # Inicializar la estructura para el chat morfosintáctico
        # st.session_state.morphosyntax_chat_history = []
        # st.session_state.morphosyntax_chat_input = ""

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session_state()
    st.session_state.logged_out = True  # Añadimos esta bandera

# Exportar las funciones
__all__ = ['initialize_session_state', 'logout']