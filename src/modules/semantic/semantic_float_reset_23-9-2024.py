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

def semantic_float_init():
    components.html("""
    <style>
    .semantic-float {
        position: fixed;
        z-index: 9999;
        background-color: white;
        border-radius: 8px;
        padding: 16px;
        overflow: auto;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    </style>
    """, height=0)

def float_graph(content, width="40%", height="60%", position="center-right", shadow=0, transition=0):
    position_css = {
        "top-left": "top: 20px; left: 20px;",
        "top-right": "top: 20px; right: 20px;",
        "bottom-left": "bottom: 20px; left: 20px;",
        "bottom-right": "bottom: 20px; right: 20px;",
        "center-right": "top: 50%; right: 20px; transform: translateY(-50%);"
    }

    css = f"""
    position: fixed;
    width: {width};
    height: {height};
    {position_css.get(position, position_css['center-right'])}
    {shadow_list[shadow % len(shadow_list)]}
    {transition_list[transition % len(transition_list)]}
    z-index: 9999;
    display: block !important;
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 10px;
    overflow: auto;
    """

    box_id = f"semantic-float-{str(uuid.uuid4())[:8]}"
    components.html(f"""
    <div id="{box_id}" class="semantic-float" style="{css}">
        {content}
    </div>
    <script>
    (function() {{
        const box = document.getElementById('{box_id}');
        if (box) {{
            box.style.display = 'block';
            console.log('Float graph created with ID: {box_id}');
        }} else {{
            console.error('Float graph element not found');
        }}
    }})();
    </script>
    """, height=0)
    return box_id

def float_box(content, css=""):
    box_id = f"semantic-float-{str(uuid.uuid4())[:8]}"
    components.html(f"""
    <div id="{box_id}" class="semantic-float" style="{css}">
        {content}
    </div>
    <script>
    (function() {{
        const box = document.getElementById('{box_id}');
        if (box) {{
            console.log('Float box created with ID: {box_id}');
        }} else {{
            console.error('Float box element not found');
        }}
    }})();
    </script>
    """, height=0)
    return box_id

def toggle_float_visibility(box_id, visible):
    display = "block" if visible else "none"
    components.html(f"""
    <script>
    (function() {{
        const element = document.getElementById('{box_id}');
        if (element) {{
            element.style.display = '{display}';
            console.log('Float visibility toggled: {display}');
        }} else {{
            console.error('Float element not found for toggling visibility');
        }}
    }})();
    </script>
    """, height=0)

def update_float_content(box_id, new_content):
    components.html(f"""
    <script>
    (function() {{
        const element = document.getElementById('{box_id}');
        if (element) {{
            element.innerHTML = `{new_content}`;
            console.log('Float content updated');
        }} else {{
            console.error('Float element not found for updating content');
        }}
    }})();
    </script>
    """, height=0)