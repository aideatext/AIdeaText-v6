import streamlit as st
import uuid
import streamlit.components.v1 as components
import streamlit.components.v1 as stc

########################## PRUEBA 1  #########################
            # COMBINADO CON SEMANCTIC_INTERFACE_68OK APARECEN DOS BOX FLOTANTES
# Lista de estilos de sombra (puedes ajustar según tus preferencias)

'''
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
    st.markdown("""
    <style>
    .semantic-float {
        position: fixed;
        z-index: 9999;
        background-color: white;
        border: 1px solid #ddd;
        padding: 10px;
        overflow: auto;
    }
    </style>
    """, unsafe_allow_html=True)

####################################################
def float_graph(content, width="40%", height="60%", position="bottom-right", shadow=0, transition=0):
    position_css = {
        "top-left": "top: 20px; left: 20px;",
        "top-right": "top: 20px; right: 20px;",
        "bottom-left": "bottom: 20px; left: 20px;",
        "bottom-right": "bottom: 20px; right: 20px;",
    }
    css = f"""
    width: {width};
    height: {height};
    position: fixed;
    z-index: 9999;
    background-color: white;
    border: 1px solid #ddd;
    padding: 10px;
    overflow: auto;
    {position_css.get(position, position_css['bottom-right'])}
    {shadow_list[shadow % len(shadow_list)]}
    {transition_list[transition % len(transition_list)]}
    """
    return float_box(content, css=css)

#########################################################
def float_box(content, css=""):
    box_id = f"semantic-float-{str(uuid.uuid4())[:8]}"
    st.markdown(f"""
    <div id="{box_id}" style="{css}">
        {content}
    </div>
    """, unsafe_allow_html=True)
    return box_id

#########################################################

def toggle_float_visibility(box_id, visible):
    """
    Cambia la visibilidad de un contenedor flotante.

    :param box_id: ID del contenedor flotante
    :param visible: True para mostrar, False para ocultar
    """
    display = "block" if visible else "none"
    st.markdown(f"""
    <script>
        var element = window.parent.document.getElementById('{box_id}');
        if (element) {{
            element.style.display = '{display}';
        }}
    </script>
    """, unsafe_allow_html=True)

###########################################################
def update_float_content(box_id, new_content):
    """
    Actualiza el contenido de un contenedor flotante.

    :param box_id: ID del contenedor flotante
    :param new_content: Nuevo contenido HTML o Markdown
    """
    st.markdown(f"""
    <script>
        var element = window.parent.document.getElementById('{box_id}');
        if (element) {{
            element.querySelector('.semantic-float-content').innerHTML = `{new_content}`;
        }}
    </script>
    """, unsafe_allow_html=True)

# Puedes agregar más funciones específicas para la interfaz semántica según sea necesario
'''

################################################# version backup #########################
            # COMBINADO CON SEMANCTIC_INTERFACE_68OK APARECEN SOLO UN CUADRO A LA DERECJHA Y AL CENTRO
 # Lista de estilos de sombra (puedes ajustar según tus preferencias)
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
    """Inicializa los estilos necesarios para los elementos flotantes en la interfaz semántica."""
    st.markdown("""
    <style>
    .semantic-float {
        position: fixed;
        z-index: 1000;
    }
    .semantic-float-content {
        background-color: white;
        border-radius: 8px;
        padding: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

def float_graph(content, width="40%", height="60%", position="bottom-right", shadow=0, transition=0):
    """
    Crea un contenedor flotante para el gráfico de visualización semántica.

    :param content: Contenido HTML o Markdown para el gráfico
    :param width: Ancho del contenedor
    :param height: Altura del contenedor
    :param position: Posición del contenedor ('top-left', 'top-right', 'bottom-left', 'bottom-right')
    :param shadow: Índice del estilo de sombra a utilizar
    :param transition: Índice del estilo de transición a utilizar
    """
    position_css = {
        "top-left": "top: 20px; left: 20px;",
        "top-right": "top: 20px; right: 20px;",
        "bottom-left": "bottom: 20px; left: 20px;",
        "bottom-right": "bottom: 20px; right: 20px;",
    }

    css = f"""
    width: {width};
    height: {height};
    {position_css.get(position, position_css['bottom-right'])}
    {shadow_list[shadow % len(shadow_list)]}
    {transition_list[transition % len(transition_list)]}
    """

    return float_box(content, css=css)

def float_box(content, css=""):
    """
    Crea un contenedor flotante genérico.

    :param content: Contenido HTML o Markdown para el contenedor
    :param css: Estilos CSS adicionales
    """
    box_id = f"semantic-float-{str(uuid.uuid4())[:8]}"
    st.markdown(f"""
    <div id="{box_id}" class="semantic-float">
        <div class="semantic-float-content" style="{css}">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)
    return box_id

def toggle_float_visibility(box_id, visible):
    """
    Cambia la visibilidad de un contenedor flotante.

    :param box_id: ID del contenedor flotante
    :param visible: True para mostrar, False para ocultar
    """
    display = "block" if visible else "none"
    st.markdown(f"""
    <script>
        var element = window.parent.document.getElementById('{box_id}');
        if (element) {{
            element.style.display = '{display}';
        }}
    </script>
    """, unsafe_allow_html=True)

def update_float_content(box_id, new_content):
    """
    Actualiza el contenido de un contenedor flotante.

    :param box_id: ID del contenedor flotante
    :param new_content: Nuevo contenido HTML o Markdown
    """
    st.markdown(f"""
    <script>
        var element = window.parent.document.getElementById('{box_id}');
        if (element) {{
            element.querySelector('.semantic-float-content').innerHTML = `{new_content}`;
        }}
    </script>
    """, unsafe_allow_html=True)

# Puedes agregar más funciones específicas para la interfaz semántica según sea necesario
#################FIN BLOQUE DEL BACK UP#################################################





















'''
############ TEST  #########################################
def semantic_float_init():
    st.markdown("""
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
    """, unsafe_allow_html=True)

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
    html_content = f"""
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
    """

    components.html(html_content, height=600, scrolling=True)
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










############BackUp #########################################
























# Lista de estilos de sombra y transición (sin cambios)
shadow_list = [
    "box-shadow: rgba(0, 0, 0, 0.1) 0px 4px 12px;",
    "box-shadow: rgba(0, 0, 0, 0.15) 0px 5px 15px 0px;",
    "box-shadow: rgba(0, 0, 0, 0.05) 0px 6px 24px 0px, rgba(0, 0, 0, 0.08) 0px 0px 0px 1px;",
    "box-shadow: rgba(0, 0, 0, 0.16) 0px 10px 36px 0px, rgba(0, 0, 0, 0.06) 0px 0px 0px 1px;",
]

transition_list = [
    "transition: all 0.3s ease;",
    "transition: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);",
    "transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);",
]

def semantic_float_init():
    st.markdown("""
    <style>
    .semantic-float {
        position: fixed;
        z-index: 1000;
        display: none;
    }
    .semantic-float-content {
        background-color: white;
        border-radius: 8px;
        padding: 16px;
        overflow: auto;
    }
    </style>
    """, unsafe_allow_html=True)

def float_graph(content, width="40%", height="60%", position="bottom-right", shadow=0, transition=0):
    position_css = {
        "top-left": "top: 20px; left: 20px;",
        "top-right": "top: 20px; right: 20px;",
        "bottom-left": "bottom: 20px; left: 20px;",
        "bottom-right": "bottom: 20px; right: 20px;",
        "center-right": "top: 50%; right: 20px; transform: translateY(-50%);"
    }

    css = f"""
    width: {width};
    height: {height};
    {position_css.get(position, position_css['bottom-right'])}
    {shadow_list[shadow % len(shadow_list)]}
    {transition_list[transition % len(transition_list)]}
    """

    return float_box(content, css=css)

def float_box(content, css=""):
    box_id = f"semantic-float-{str(uuid.uuid4())[:8]}"
    components.html(f"""
    <div id="{box_id}" class="semantic-float" style="{css}">
        <div class="semantic-float-content">
            {content}
        </div>
    </div>
    <script>
    (function() {{
        const box = document.getElementById('{box_id}');
        if (box) {{
            box.style.display = 'block';
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
            element.querySelector('.semantic-float-content').innerHTML = `{new_content}`;
        }}
    }})();
    </script>
    """, height=0)
'''