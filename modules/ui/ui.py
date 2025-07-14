# modules/ui/ui.py
import streamlit as st
from PIL import Image
import base64
from streamlit_player import st_player
import logging
from datetime import datetime
from dateutil.parser import parse

#########################################################
# Configuración de estilo CSS para el carrusel
st.markdown("""
<style>
    .carousel-container {
        position: relative;
        max-width: 800px;
        margin: 0 auto;
    }
    .carousel-image {
        width: 100%;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        display: none;
    }
    .carousel-image.active {
        display: block;
        animation: fadeIn 0.5s;
    }
    @keyframes fadeIn {
        from {opacity: 0.4;}
        to {opacity: 1;}
    }
    .carousel-caption {
        text-align: center;
        margin-top: 10px;
        font-size: 1.1em;
        color: #333;
    }
    .carousel-nav {
        display: flex;
        justify-content: center;
        margin-top: 15px;
    }
    .carousel-dot {
        height: 12px;
        width: 12px;
        margin: 0 5px;
        background-color: #bbb;
        border-radius: 50%;
        display: inline-block;
        cursor: pointer;
    }
    .carousel-dot.active {
        background-color: #717171;
    }
</style>
""", unsafe_allow_html=True)

# Datos del carrusel (imágenes y descripciones)
eventos = [
    {
        "imagen": "assets/img/socialmedia/WebSummit_ShowCase_2025.png",
        "titulo": "WebSummitRio 2025, Brasil, april, 27-30",
        "descripcion": "AIdeaText showcase"
    },
    
    {
        "imagen": "assets/img/socialmedia/image_pycon_2024.png",
        "titulo": "PyCon 2024, Colombia, june, 7-9",
        "descripcion": "AIdeaText showcase"
    }
]

def initialize_carousel_state():
    """Inicializa todas las variables de estado necesarias para el carrusel"""
    if not hasattr(st.session_state, 'current_event'):
        st.session_state.current_event = 0
    if not hasattr(st.session_state, 'carousel_initialized'):
        st.session_state.carousel_initialized = True

#####################
def show_carousel():
    """Muestra el carrusel de imágenes con inicialización segura del estado"""
    try:
        # Inicialización segura del estado
        initialize_carousel_state()
        
        # Verificación adicional
        if not hasattr(st.session_state, 'current_event'):
            st.session_state.current_event = 0
            st.rerun()
            
        current_idx = st.session_state.current_event
        
        with st.container():
            #st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>Eventos Relevantes</h2>", 
            #           unsafe_allow_html=True)
            
            # Controles de navegación
            col1, col2, col3 = st.columns([1, 6, 1])
            
            with col1:
                if st.button("◀", key="carousel_prev"):
                    st.session_state.current_event = (current_idx - 1) % len(eventos)
                    st.rerun()
            
            with col2:
                event = eventos[current_idx]
                img = Image.open(event["imagen"]) if isinstance(event["imagen"], str) else event["imagen"]
                st.image(
                    img,
                    use_container_width=True,  # <-- Cambio realizado aquí
                    caption=f"{event['titulo']} - {event['descripcion']}"
                )
            
            with col3:
                if st.button("▶", key="carousel_next"):
                    st.session_state.current_event = (current_idx + 1) % len(eventos)
                    st.rerun()
            
            # Indicadores de posición
            st.markdown("<div class='carousel-nav'>", unsafe_allow_html=True)
            cols = st.columns(len(eventos))
            for i, col in enumerate(cols):
                with col:
                    if st.button("•", key=f"carousel_dot_{i}"):
                        st.session_state.current_event = i
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error al mostrar el carrusel: {str(e)}")
        logger.error(f"Error en show_carousel: {str(e)}")

#########################################################


# Configura el logger PRIMERO, antes de cualquier uso
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importaciones locales
from session_state import initialize_session_state, logout
from translations import get_translations, get_landing_translations
from ..auth.auth import authenticate_user, authenticate_student, authenticate_admin
from ..database.sql_db import store_application_request

# Intento de importación con logger YA DEFINIDO
try:
    from .user_page import user_page
except ImportError as e:
    logger.error(f"No se pudo importar user_page: {str(e)}. Asegúrate de que el archivo existe.")
    
    # Función de respaldo
    def user_page(lang_code, t):
        st.error("La página de usuario no está disponible. Por favor, contacta al administrador.")

from ..admin.admin_ui import admin_page

#############################################################
def main():
    logger.info(f"Entrando en main() - Página actual: {st.session_state.page}")

    if 'nlp_models' not in st.session_state:
        logger.error("Los modelos NLP no están inicializados.")
        st.error("Los modelos NLP no están inicializados. Por favor, reinicie la aplicación.")
        return

    lang_code = st.session_state.get('lang_code', 'es')
    t = get_translations(lang_code)

    logger.info(f"Página actual antes de la lógica de enrutamiento: {st.session_state.page}")

    if st.session_state.get('logged_out', False):
        st.session_state.logged_out = False
        st.session_state.page = 'login'
        st.rerun()

    if not st.session_state.get('logged_in', False):
        logger.info("Usuario no ha iniciado sesión. Mostrando página de login/registro")
        login_register_page(lang_code, t)
    elif st.session_state.page == 'user':
        if st.session_state.role == 'Administrador':
            logger.info("Redirigiendo a la página de administrador")
            st.session_state.page = 'Admin'
            st.rerun()
        else:
            logger.info("Renderizando página de usuario")
            user_page(lang_code, t)
    elif st.session_state.page == "Admin":
        logger.info("Renderizando página de administrador")
        admin_page()
    else:
        logger.error(f"Página no reconocida: {st.session_state.page}")
        st.error(t.get('unrecognized_page', 'Página no reconocida'))
        # Redirigir a la página de usuario en caso de error
        st.session_state.page = 'user'
        st.rerun()

    logger.info(f"Saliendo de main() - Estado final de la sesión: {st.session_state}")

#############################################################
#############################################################    
def login_register_page(lang_code, t):
    # Obtener traducciones específicas para landing page
    landing_t = get_landing_translations(lang_code)
    
    # Language selection dropdown at the top
    languages = {'Español': 'es', 'English': 'en', 'Français': 'fr', 'Português': 'pt'}
    
    # Estilo personalizado para mejorar el espaciado y alineación
    st.markdown("""
    <style>
        div.row-widget.stHorizontalBlock {
            align-items: center;
        }
    </style>
    """, unsafe_allow_html=True)

#################################### LOGOS ################################################################################################    
    # Crear contenedor para logos y selector de idioma usando columnas de Streamlit
    col1, col2, col3, col4, col5 = st.columns([0.25, 0.25, 0.50, 1, 1])
    
    with col1:
        # Logo de AIdeaText
        st.image("https://huggingface.co/spaces/AIdeaText/v5Prod/resolve/main/assets/img/AIdeaText_Logo_vectores.png", width=100)
        
    with col2:
        # Logo de ALPHA
        st.image("https://huggingface.co/spaces/AIdeaText/v5Prod/resolve/main/assets/img/ALPHA_Startup%20Badges.png", width=100)
    
    with col3:
        # Logo de NVIDIA
        st.image("https://huggingface.co/spaces/AIdeaText/v5Prod/resolve/main/assets/img/socialmedia/nvidia/nvidia-inception-program-badge-rgb-for-screen.png", width=300)
   
    with col5:
        # Selector de idioma
        selected_lang = st.selectbox(
            landing_t['select_language'],
            list(languages.keys()),
            index=list(languages.values()).index(lang_code),
            key=f"landing_language_selector_{lang_code}"
        )
        new_lang_code = languages[selected_lang]
        if lang_code != new_lang_code:
            st.session_state.lang_code = new_lang_code
            st.rerun()
    
    # Main content with columns
    left_column, right_column = st.columns([1, 3])
    
    with left_column:
        tab1, tab2 = st.tabs([landing_t['login'], landing_t['register']])
        
        with tab1:
            login_form(lang_code, landing_t)
        
        with tab2:
            register_form(lang_code, landing_t)
    
    with right_column:
        display_videos_and_info(lang_code, landing_t)

#############################################################
#############################################################
def login_form(lang_code, landing_t):
    with st.form("login_form"):
        username = st.text_input(landing_t['email'])
        password = st.text_input(landing_t['password'], type="password")
        submit_button = st.form_submit_button(landing_t['login_button'])

    if submit_button:
        success, role = authenticate_user(username, password)
        if success:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role
            if role == 'Administrador':
                st.session_state.page = 'Admin'
            else:
                st.session_state.page = 'user'
            logger.info(f"Usuario autenticado: {username}, Rol: {role}")
            st.rerun()
        else:
            st.error(landing_t['invalid_credentials'])


#############################################################
#############################################################
def register_form(lang_code, landing_t):
    name = st.text_input(landing_t['name'])
    lastname = st.text_input(landing_t['lastname'])
    institution = st.text_input(landing_t['institution'])
    current_role = st.selectbox(landing_t['current_role'],
                              [landing_t['professor'], landing_t['student'], landing_t['administrative']])
    
    # Definimos el rol por defecto como estudiante
    desired_role = landing_t['student']
    
    email = st.text_input(landing_t['institutional_email'])
    reason = st.text_area(landing_t['interest_reason'])
    
    if st.button(landing_t['submit_application']):
        logger.info(f"Intentando enviar solicitud para {email}")
        logger.debug(f"Datos del formulario: name={name}, lastname={lastname}, email={email}, institution={institution}, current_role={current_role}, desired_role={desired_role}, reason={reason}")
        
        if not name or not lastname or not email or not institution or not reason:
            logger.warning("Envío de formulario incompleto")
            st.error(landing_t['complete_all_fields'])
        elif not is_institutional_email(email):
            logger.warning(f"Email no institucional utilizado: {email}")
            st.error(landing_t['use_institutional_email'])
        else:
            logger.info(f"Intentando almacenar solicitud para {email}")
            success = store_application_request(name, lastname, email, institution, current_role, desired_role, reason)
            if success:
                st.success(landing_t['application_sent'])
                logger.info(f"Solicitud almacenada exitosamente para {email}")
            else:
                st.error(landing_t['application_error'])
                logger.error(f"Error al almacenar solicitud para {email}")


#############################################################
#############################################################
def is_institutional_email(email):
        forbidden_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
        return not any(domain in email.lower() for domain in forbidden_domains)

#############################################################
#############################################################
def display_videos_and_info(lang_code, landing_t):
    # Crear tabs para cada sección
    tab_gallery, tab_use_case, tab_videos, tab_events, tab_news = st.tabs([
        landing_t['event_photos'],
        landing_t['use_cases'], 
        landing_t['presentation_videos'], 
        landing_t['academic_presentations'],
        landing_t['version_control']
    ])

    # Tab de Casos de uso
    with tab_use_case:
        use_case_videos = {
            "Español - Semantic Analysis": "https://https://youtu.be/_4WMufl6MTA"
        }
        
        selected_title = st.selectbox(landing_t['select_use_case'], list(use_case_videos.keys()))
        if selected_title in use_case_videos:
            try:
                st_player(use_case_videos[selected_title])
            except Exception as e:
                st.error(f"Error al cargar el video: {str(e)}")

    # Tab de Videos
    with tab_videos:
        videos = {
            "Reel AIdeaText": "https://youtu.be/hXnwUvN1Q9Q",
            "Presentación en SENDA, UNAM. Ciudad de México, México" : "https://www.youtube.com/watch?v=XFLvjST2cE0",        
            "Presentación en PyCon 2024. Colombia, Medellín": "https://www.youtube.com/watch?v=Jn545-IKx5Q",
            "Presentación en Fundación Ser Maaestro. Lima, Perú": "https://www.youtube.com/watch?v=imc4TI1q164",
            "Presentación en Explora del IFE, TEC de Monterrey, Nuevo León, México": "https://www.youtube.com/watch?v=Fqi4Di_Rj_s",
            "Entrevista con el Dr. Guillermo Ruíz. Lima, Perú": "https://www.youtube.com/watch?v=_ch8cRja3oc",
            "Demo de la versión de escritorio.": "https://www.youtube.com/watch?v=nP6eXbog-ZY"
        }

        selected_title = st.selectbox(landing_t['select_presentation'], list(videos.keys()))
        if selected_title in videos:
            try:
                st_player(videos[selected_title])
            except Exception as e:
                st.error(f"Error al cargar el video: {str(e)}")
                
    # Tab de Eventos
    with tab_events:
        st.markdown("""
        ## 2025
    
        **El Agente Cognitivo Vinculante como Innovación en el Aprendizaje Adaptativo: el caso de AIdeaText**  
        IFE CONFERENCE 2025. Organizado por el Instituto para el Futuro de la Educación del TEC de Monterrey. 
        Nuevo León, México. Del 28 al 30 enero 2025
    
        ## 2024
        [1]
        AIdeaText, AIdeaText, recurso digital que emplea la técnica de Análisis de Resonancia Central para perfeccionar textos académicos**  
        V Temporada SENDA - Organizado por el Seminario de Entornos y Narrativas Digitales en la Academia del 
        Instituto de Investigaciones Antropológicas (IIA) de la Universidad Autonóma de México (UNAM). 22 noviembre 2024
    
        [2]
        Aproximación al Agente Cognitivo Vinculante (ACV) desde la Teoría del Actor Red (TAR)**  
        Congreso HeETI 2024: Horizontes Expandidos de la Educación, la Tecnología y la Innovación  
        Universidad el Claustro de Sor Juana. Del 25 al 27 septiembre 2024
        
        [3]
        AIdeaText, visualización de mapas semánticos**
        PyCon 2024, Organizado por el grupo de desarrolladores independientes de Python. 
        Universidad EAFIT, Medellín, Colombia. Del 7 al 9 de junio de 2024. 
        
        ## 2023
        **Aproximación al Agente Cognitivo Vinculante (ACV) desde la Teoría del Actor Red (TAR)**  
        [1]
        XVII Congreso Nacional de Investigación Educativa - VII Encuentro de Estudiantes de Posgrado Educación.
        Consejo Mexicano de Investigación Educativa (COMIE)  
        Villahermosa, Tabasco, México. 
        Del 4 al 8 de diciembre 2023
        
        [2]
        XXXI Encuentro Internacional de Educación a Distancia  
        Universidad de Guadalajara. Jalisco, México. 
        Del 27 al 30 noviembre 2023
        
        [3]
        IV Temporada SENDA - Seminario de Entornos y Narrativas Digitales en la Academia  
        Instituto de Investigaciones Antropológicas (IIA), UNAM. 
        22 noviembre 2023
        
        [4]
        1er Congreso Internacional de Educación Digital  
        Instituto Politécnico Nacional, sede Zacatecas. México. 
        Del 23 al 24 de noviembre de 2023
    
        [5]
        La cuestión de la centralidad del maestro frente a las tecnologías digitales generativas**  
        Innova Fórum: Ecosistemas de Aprendizaje  
        Universidad de Guadalajara. Jalisco, México. 
        Del 16 al 18 de mayo 2023
        """)

##########################################################################################
    
    # Tab de Galería
    with tab_gallery:
        show_carousel()

#############################################################
#############################################################    
    # Tab de Novedades - Usar contenido traducido
    with tab_news:
        st.markdown(f"### {landing_t['latest_version_title']}")
        for update in landing_t['version_updates']:
            st.markdown(f"- {update}")
            
#############################################################
#############################################################
# Definición de __all__ para especificar qué se exporta
__all__ = ['main', 'login_register_page', 'initialize_session_state']

# Bloque de ejecución condicional
if __name__ == "__main__":
    main()


#############################################################
#############################################################

footer_placeholder = st.empty()

footer_placeholder.markdown("""
<style>
#footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #f0f2f6;
    color: #4f4f4f;
    text-align: center;
    padding: 10px;
    font-size: 12px;
    border-top: 1px solid #e6e6e6;
    z-index: 100;
}

.main > div {
    padding-bottom: 60px;
}
</style>

<div id="footer">
    © 2025 NVIDIA, the NVIDIA logo, and AIdeaText, ALPHA are trademarks and/or registered trademarks of NVIDIA Corporation in the U.S. and other countries.
</div>
""", unsafe_allow_html=True)