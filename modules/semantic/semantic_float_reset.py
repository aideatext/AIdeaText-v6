import streamlit as st
import uuid
import streamlit.components.v1 as components
import base64

# Lista de estilos de sombra
shadow_list = [
    "box-shadow: rgba(0, 0, 0, 0.1) 0px 4px 12px;",
    "box-shadow: rgba(0, 0, 0, 0.15) 0px 5px 15px 0px;",
    "box-shadow: rgba(0, 0, 0, 0.05) 0px 6px 24px 0px, rgba(0, 0, 0, 0.08) 0px 0px 0px 1px;",
    "box-shadow: rgba(0, 0, 0, 0.16) 0px 10px 36px 0px, rgba(0, 0, 0, 0.06) 0px 0px 0px 1px;",
]

# Lista de estilos de transición
transition_list = [
    "transition: all 0.3s ease;",
    "transition: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);",
    "transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);",

]

###################################################################################
def semantic_float_init():
    st.markdown("""
    <style>
    #semantic-float-container {
        position: fixed;
        top: 0;
        right: 0;
        width: 800px;
        height: 100vh;
        z-index: 9999;
        background-color: white;
        border-left: 1px solid #ddd;
        box-shadow: -5px 0 15px rgba(0,0,0,0.1);
        overflow: auto;
        transition: transform 0.3s ease-in-out;
        transform: translateX(100%);
    }
    #semantic-float-container.visible {
        transform: translateX(0);
    }
    #semantic-float-container img {
        max-width: 100%;
        height: auto;
    }
    </style>
    """, unsafe_allow_html=True)

    components.html("""
    <div id="semantic-float-container"></div>
    <script>
    const container = document.getElementById('semantic-float-container');
    if (!container) {
        const newContainer = document.createElement('div');
        newContainer.id = 'semantic-float-container';
        document.body.appendChild(newContainer);
    }
    </script>
    """, height=0)

def float_graph(content):
    js = f"""
    <script>
    const container = document.getElementById('semantic-float-container');
    if (container) {{
        container.innerHTML = `{content}`;
        container.classList.add('visible');
    }}
    </script>
    """
    components.html(js, height=0)

def toggle_float_visibility(visible):
    js = f"""
    <script>
    const container = document.getElementById('semantic-float-container');
    if (container) {{
        container.classList.{'add' if visible else 'remove'}('visible');
    }}
    </script>
    """
    components.html(js, height=0)

def update_float_content(new_content):
    js = f"""
    <script>
    const container = document.getElementById('semantic-float-container');
    if (container) {{
        container.innerHTML = `{new_content}`;
    }}
    </script>
    """
    components.html(js, height=0)