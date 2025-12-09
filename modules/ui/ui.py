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
        "titulo": "WebSummitRio 2025, Rio, Brazil, April 27-30",
        "descripcion": "AIdeaText showcase"
    },
    
    {
        "imagen": "assets/img/socialmedia/image_pycon_2024.png",
        "titulo": "PyCon 2024, Medellin, Colombia, June 7-9",
        "descripcion": "AIdeaText showcase"
    },

    {
        "imagen": "assets/img/socialmedia/_MG_2845.JPG",
        "titulo": "MakerFaire 2024, Mexico City, Mexico, October 12-13",
        "descripcion": "AIdeaText showcase"
    }    
]

#####################
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
                    use_container_width=True,
                    caption=f"{event['titulo']} - {event['descripcion']}"
                )
            
            with col3:
                if st.button("▶", key="carousel_next"):
                    st.session_state.current_event = (current_idx + 1) % len(eventos)
                    st.rerun()
            
            # Indicadores de posición (solo visuales, no botones)
            st.markdown("<div class='carousel-nav'>", unsafe_allow_html=True)
            for i in range(len(eventos)):
                active_class = "carousel-dot active" if i == current_idx else "carousel-dot"
                st.markdown(f"<span class='{active_class}'></span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
                        
    except Exception as e:
        st.error(f"Error al mostrar el carrusel: {str(e)}")
        logger.error(f"Error en show_carousel: {str(e)}")

#########################################################
# Configura el logger PRIMERO, antes de cualquier uso
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#########################################################
# Importaciones locales
from session_state import initialize_session_state, logout
from translations import get_translations, get_landing_translations
from ..auth.auth import authenticate_user, authenticate_student, authenticate_admin
from ..database.sql_db import store_application_request
from ..admin.admin_ui import admin_page

#########################################################
# Intento de importación con logger YA DEFINIDO
try:
    from .user_page import user_page
except ImportError as e:
    logger.error(f"No se pudo importar user_page: {str(e)}. Asegúrate de que el archivo existe.")
    
    # Función de respaldo
    def user_page(lang_code, t):
        st.error("La página de usuario no está disponible. Por favor, contacta al administrador.")

#############################################################
def main():
    logger.info(f"Entrando en main() - Página actual: {st.session_state.page}")

    if 'nlp_models' not in st.session_state:
        logger.error("Los modelos NLP no están inicializados.")
        st.error("Los modelos NLP no están inicializados. Por favor, reinicie la aplicación.")
        return

    # [1] CONFIGURAR INGLÉS COMO IDIOMA POR DEFECTO
    if 'lang_code' not in st.session_state:
        st.session_state.lang_code = 'en'  # Inglés por defecto
    
    lang_code = st.session_state.get('lang_code', 'en')
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
    languages = {
        'English': 'en', 
        'Español': 'es', 
        'Français': 'fr', 
        'Português': 'pt'
    }
    
    # Estilo personalizado para mejorar el espaciado y alineación
    st.markdown("""
    <style>
        div.row-widget.stHorizontalBlock {
            align-items: center;
        }
        /* Resaltar el tab de registro */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1E3A8A;
            color: white !important;
            border-radius: 5px 5px 0 0;
        }
        /* Estilo para contenedor de inicio */
        .start-container {
            background: linear-gradient(135deg, #1E3A8A 0%, #3730A3 100%);
            color: white;
            padding: 15px;
            border-radius: 10px 10px 0 0;
            text-align: center;
            margin-bottom: 10px;
        }
        .language-inline {
            display: inline-block;
            margin-left: 10px;
            vertical-align: middle;
        }
        
        /* CENTRAR EL LOGO - NUEVO ESTILO */
        .logo-center-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 20px 0 30px 0;
            width: 100%;
        }
        .logo-center-container img {
            display: block;
            margin: 0 auto;
        }
        /* Centrar el contenedor de imagen de Streamlit */
        [data-testid="stImage"] {
            text-align: center;
            margin: 0 auto;
        }
        /* Forzar centrado del logo */
        div.stImage {
            text-align: center;
        }
        div.stImage > img {
            margin: 0 auto;
            display: block;
        }
        
    </style>
    """, unsafe_allow_html=True)
####################################################################################################################################    

    # Pie de página legal (debe ir al final de la función)
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
        © 2025 NVIDIA, the NVIDIA logo are trademarks and/or registered trademarks of NVIDIA Corporation in the U.S. and other countries.
    </div>
    """, unsafe_allow_html=True)

#################################### LOGOS ################################################################################################ 
    # ============================================
    # [1] LOGO AIdeaText CENTRADO - UNA SOLA FILA
    # ============================================
    # Opción 1: Usar columnas para centrar
    st.markdown("""
    <div style="text-align: center; margin: 20px 0 30px 0;">
        <img src="https://huggingface.co/spaces/AIdeaText/v5Prod/resolve/main/assets/img/AIdeaText_Logo_vectores.png" 
             width="200" style="display: block; margin: 0 auto;">
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
#######################################################################
    
    # Main content with columns
    left_column, right_column = st.columns([1, 3])
    
    with left_column:
        
        # ============================================
        # [2] CONTENEDOR "COMIENZA" CON SELECTOR DE IDIOMA
        # ============================================
        st.markdown("""
        <div class="start-container">
            <h3 style='margin: 0;'>
                🚀 Start in 
                <span class="language-inline">
        """, unsafe_allow_html=True)
        
        # Selector de idioma inline
        selected_lang = st.selectbox(
            "",
            list(languages.keys()),
            index=list(languages.keys()).index('English'),  # Inglés seleccionado por defecto
            label_visibility="collapsed",
            key="landing_language_selector"
        )
        
        st.markdown("""
                </span>
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        new_lang_code = languages[selected_lang]
        if lang_code != new_lang_code:
            st.session_state.lang_code = new_lang_code
            st.rerun()
        
        # Crear tabs - REGISTRO siempre primero
        tab_titles = [f"📝 {landing_t['register']}", f"🔐 {landing_t['login']}"]
        tabs = st.tabs(tab_titles)
        
        # TAB 1: FORMULARIO DE REGISTRO (Siempre visible por defecto)
        with tabs[0]:
            register_form(lang_code, landing_t)
        
        # TAB 2: FORMULARIO DE LOGIN
        with tabs[1]:
            login_form(lang_code, landing_t)
    
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

def register_form(lang_code, landing_t):
    """Formulario de registro simplificado - SOLO 3 CAMPOS"""
    
    # Verificar si acabamos de registrar exitosamente
    if 'just_registered' in st.session_state and st.session_state.just_registered:
        st.success("✅ Registration successful! Your request has been sent.")
        st.info("Please check your email for further instructions.")
        
        # Botón para limpiar y empezar de nuevo
        if st.button("Register another user"):
            del st.session_state.just_registered
            st.rerun()
        return
    
    # Solo 3 campos requeridos
    name = st.text_input("Full name *", key="reg_name")
    email = st.text_input("Institutional email *", key="reg_email") 
    institution = st.text_input("Educational institution *", key="reg_institution")
    
    # Botón simplificado
    if st.button(landing_t['submit_application'], type="primary"):
        logger.info(f"Trying to send request for {email}")
        
        # Validaciones básicas
        if not name or not email or not institution:
            st.error("Please complete all required fields (*)")
            return
        
        if not is_institutional_email(email):
            st.error("Please use an institutional email (not gmail, hotmail, etc.)")
            return
        
        # Enviar solicitud
        success = store_application_request(
            name=name,
            lastname="",
            email=email,
            institution=institution,
            current_role="Student",
            desired_role="Student",  
            reason="New registration"
        )
        
        if success:
            # Marcar que acabamos de registrar
            st.session_state.just_registered = True
            logger.info(f"Request successfully stored for {email}")
            
            # Mostrar mensaje y recargar
            st.success("✅ Your request has been sent! You will receive an email with instructions.")
            st.balloons()
            
            # Recargar después de 2 segundos
            import time
            time.sleep(2)
            st.rerun()
        else:
            st.error("❌ There was an error sending your request. Please try again.")
            logger.error(f"Error storing request for {email}")


#############################################################
#############################################################
def is_institutional_email(email):
        forbidden_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
        return not any(domain in email.lower() for domain in forbidden_domains)

#############################################################
#############################################################

def display_videos_and_info(lang_code, landing_t):
    # ============================================
    # NUEVO ORDEN DE TABS CON 6 OPCIONES
    # ============================================
    tab_about, tab_programs, tab_competitions, tab_use_case, tab_presentations, tab_gallery = st.tabs([
        "👥 About Us",
        "🏆 Current Programs", 
        "💰 Competitions",
        "🎯 Use Cases",
        "🎬 Pitches & Presentations",
        "📸 Events & Recognition"
    ])

    # ============================================
    # ESTILOS GLOBALES PARA CONSISTENCIA
    # ============================================
    st.markdown("""
    <style>
        /* Estilos para títulos consistentes */
        .tab-title {
            font-size: 1.8em;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #1E3A8A;
        }
        .section-title {
            font-size: 1.4em;
            font-weight: 600;
            color: #374151;
            margin: 25px 0 15px 0;
        }
        .subsection-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #4B5563;
            margin: 20px 0 10px 0;
        }
        .content-text {
            font-size: 1em;
            line-height: 1.6;
            color: #6B7280;
        }
        .highlight-box {
            background-color: #F3F4F6;
            border-left: 4px solid #1E3A8A;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 5px 5px 0;
        }
        .quote-box {
            background-color: #F0F9FF;
            border-left: 4px solid #0EA5E9;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
            font-style: italic;
            font-size: 1.1em;
            color: #0369A1;
        }
        .principle-box {
            background-color: #FEF3C7;
            border-left: 4px solid #F59E0B;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
            font-weight: 600;
        }
        .mission-vision-container {
            display: flex;
            gap: 20px;
            margin: 25px 0;
        }
        .mission-box, .vision-box {
            flex: 1;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .mission-box {
            background-color: #F0FDF4;
            border-top: 4px solid #10B981;
        }
        .vision-box {
            background-color: #F5F3FF;
            border-top: 4px solid #8B5CF6;
        }
        .logo-grid {
            display: flex;
            align-items: center;
            margin: 15px 0;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

    # ============================================
    # TAB 1: 👥 ABOUT US - SIMPLIFICADO CON DESPLEGABLES
    # ============================================
    with tab_about:
        # NO repetir "About Us" - el tab ya lo dice
        
        about_texts = {
            'en': """
            <div class="content-text">
            
            <div class="principle-box">
            AIdeaText has this fundamental principle:<br>
            <strong>"The real transformation happens when we stop grading what students produce and start assessing how they think."</strong>
            </div>
            
            <details class="about-details">
                <summary class="about-summary">
                    <strong>Our Mission & Vision</strong>
                </summary>
                <div class="about-content">
                <p><strong>🎯 Mission:</strong> To transform how the world measures and develops critical thinking.</p>
                <p><strong>🌍 Vision:</strong> To be the global standard for cognitive development assessment.</p>
                <p>We bridge the gap between educational training and business needs by implementing 
                cognitive development measurement systems based on advanced natural language processing.</p>
                </div>
            </details>
            
            <details class="about-details">
                <summary class="about-summary">
                    <strong>Who We Are</strong>
                </summary>
                <div class="about-content">
                <p>AIdeaText is a digital technology company for human cognitive development based in Mexico. 
                Our solution has its core business in <strong>Semantic Reasoning Graphs (SRGs)</strong>, a technological 
                configuration that makes the critical thinking process visible, connecting educational 
                training with business needs by implementing a cognitive development measurement system 
                based on advanced natural language processing.</p>
                </div>
            </details>
            
            <details class="about-details">
                <summary class="about-summary">
                    <strong>Validation & Stage</strong>
                </summary>
                <div class="about-content">
                <p>We have been validated by the <strong>NVIDIA Inception</strong> program for emerging companies and are in 
                an advanced development stage with:</p>
                • <a href="https://youtu.be/_4WMufl6MTA" target="_blank">Functional MVP Demo</a><br>
                • <a href="https://youtu.be/Nt7IEas_P54" target="_blank">Scalable business model</a> in Latin America
                </div>
            </details>
            
            <details class="about-details">
                <summary class="about-summary">
                    <strong>Key Differentiators</strong>
                </summary>
                <div class="about-content">
                • <strong>First cognitive development measurement system</strong> based on NLP<br>
                • <strong>Semantic Reasoning Graphs</strong> make thinking visible<br>
                • <strong>Validated by NVIDIA</strong> Inception Program<br>
                • <strong>Scalable model</strong> for Latin American education market<br>
                • <strong>Proven technology</strong> with functional MVP<br>
                • <strong>Connects education</strong> with business needs
                </div>
            </details>
            
            </div>
            """
        }
        
        # Agregar estilos para los desplegables de About Us
        st.markdown("""
        <style>
        .about-details {
            margin-bottom: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 5px;
        }
        
        .about-summary {
            padding: 12px 15px;
            background-color: #f8f9fa;
            cursor: pointer;
            font-weight: 500;
            border-radius: 6px;
            transition: background-color 0.3s;
        }
        
        .about-summary:hover {
            background-color: #e9ecef;
        }
        
        .about-content {
            padding: 15px;
            background-color: white;
            border-top: 1px solid #e0e0e0;
            border-radius: 0 0 8px 8px;
        }
        
        .about-content p {
            margin-bottom: 10px;
        }
        
        .principle-box {
            background-color: #FEF3C7;
            border-left: 4px solid #F59E0B;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
            font-weight: 600;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
        
        about_content = about_texts.get(lang_code, about_texts['en'])
        st.markdown(about_content, unsafe_allow_html=True)
        
    # ============================================
    # TAB 2: 🏆 CURRENT PROGRAMS
    # ============================================
    with tab_programs:
        # NO repetir "Current Programs" - el tab ya lo dice
        
        st.markdown('<div class="section-title">NVIDIA Inception Program</div>', unsafe_allow_html=True)
        
        # Fila 1: NVIDIA Inception
        col_nvidia_logo, col_nvidia_text = st.columns([1, 3])
        with col_nvidia_logo:
            st.image("https://huggingface.co/spaces/AIdeaText/v5Prod/resolve/main/assets/img/socialmedia/nvidia/nvidia-inception-program-badge-rgb-for-screen.png", 
                    width=300)
        with col_nvidia_text:
            st.markdown("""
            <div class="content-text">
            <strong>Exclusive program for AI and Deep Tech startups</strong>
            
            <p>Inception is a free program that guides AI startups through the NVIDIA platform and ecosystem. 
            From prototype to production, Inception meets you where you are, with member benefits to help 
            you discover new AI opportunities, build with world-class technologies, and grow your business.
            More info: [https://www.nvidia.com/en-us/startups/]</p>
            
            <em>Status: Active Member</em>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
                
        st.markdown('<div class="section-title">incMTY Accelerator</div>', unsafe_allow_html=True)
        
        # Fila 2: incMTY
        col_inc_logo, col_inc_text = st.columns([1, 3])
        with col_inc_logo:
            st.image("https://huggingface.co/spaces/AIdeaText/v5Dev/resolve/main/assets/img/Logo_incMTY.png", 
                    width=250)
        with col_inc_text:
            st.markdown("""
            <div class="content-text">
            <strong>Deep Tech acceleration program</strong>
            
            <p>PotencIA MX Accelerator will boost 30 organizations through a virtual acceleration program.
            After two high-impact bootcamps in Monterrey and Mexico City, the selected startups and SMEs will begin 
            a six-month acceleration program. During this time, they will develop solutions with Open Source LLMs like Llama de Meta 
            and receive mentorship, specialized services, and strategy and growth workshops. The program will culminate in Demo Day 2026, 
            where the most outstanding organizations will be recognized: one startup will receive a business development trip with ecosystem partners, 
            and one SME will be offered soft landing support in new markets.</p>
            
            <em>Status: Current member</em>
            </div>
            """, unsafe_allow_html=True)
        
    # ============================================
    # TAB 3: 💰 COMPETITIONS
    # ============================================
    with tab_competitions:
        # NO repetir "Competitions" - el tab ya lo dice
        
        competitions_text = {
            'en': """
            <div class="content-text">
            <div class="highlight-box">
            Competing for <strong>$950K USD</strong> in prizes across multiple prestigious competitions.
            </div>
            
            <details class="competition-details">
                <summary class="competition-summary">
                    <strong>NVIDIA Inception Demo Pitch – GTC 2026</strong> - March 16–19 in San Jose, California
                </summary>
                <div class="competition-content">
                <p>This is a unique opportunity for startups leveraging NVIDIA technologies in innovative ways to showcase their work. 
                By completing the form below, you'll be considered to present a live, 5-minute demo or pitch at GTC, 
                highlighting your startup's progress and how NVIDIA technology is accelerating your success.</p>
                <p>More info: https://www.nvidia.com/gtc/?ncid=GTC-NV7HIY70L</p>
                </div>
            </details>
            
            <details class="competition-details">
                <summary class="competition-summary">
                    <strong>Kaggle/Google Tunix Hackathon</strong> - Explainable AI Models
                </summary>
                <div class="competition-content">
                <p>Most open-source or open-weight language models can give you an answer. But they typically don't 'show their work' 
                - the steps they went through to arrive at that conclusion in a consistent manner. Here, you'll use Tunix, 
                Google's new JAX-native library for LLM post-training, to train a model to show its work by laying out a 
                reasoning trace before landing on an answer.</p>
                <p>More info: https://kaggle.com/competitions/google-tunix-hackathon</p>
                </div>
            </details>
            
            <details class="competition-details">
                <summary class="competition-summary">
                    <strong>Tools Competition – Dataset Track</strong> - Datasets for Education Innovation
                </summary>
                <div class="competition-content">
                <p>The 2026 Tools Competition launches at a time of rapid change, rising urgency, 
                and widespread demand for understanding and direction amidst evolving technology. 
                Learners of all ages face new demands driven by AI, 
                shifting labor markets, and persistent inequities. From early learning to workforce development, 
                they need tools that are more effective, inclusive, and future-ready.</p>
                <p>More info: https://tools-competition.org/26-overview/</p>
                </div>
            </details>            
            </div>
            """
        }
        
        # Si necesitas agregar estilos CSS para los detalles
        st.markdown("""
        <style>
        .competition-details {
            margin-bottom: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 5px;
        }
        
        .competition-summary {
            padding: 12px 15px;
            background-color: #f8f9fa;
            cursor: pointer;
            font-weight: 500;
            border-radius: 6px;
            transition: background-color 0.3s;
        }
        
        .competition-summary:hover {
            background-color: #e9ecef;
        }
        
        .competition-content {
            padding: 15px;
            background-color: white;
            border-top: 1px solid #e0e0e0;
            border-radius: 0 0 8px 8px;
        }
        
        .competition-content p {
            margin-bottom: 8px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        content = competitions_text.get(lang_code, competitions_text['en'])
        st.markdown(content, unsafe_allow_html=True)
        
        #st.markdown("---")
        #if st.button("🎯 Apply as Beta Tester", use_container_width=True):
        #    st.info("Beta tester program launching Q1 2025")

    # ============================================
    # TAB 4: 🎯 USE CASES
    # ============================================
    with tab_use_case:
        # NO repetir "Use Cases" - el tab ya lo dice
        
        st.markdown("""
        <div class="content-text">
        Select a demonstration to see practical applications of our technology:
        </div>
        """, unsafe_allow_html=True)
        
        use_case_videos = {
            "📊 Semantic Analysis Example in portuguese ": "https://youtu.be/_4WMufl6MTA",
            "💻 First Demo - Standalone version ": "https://www.youtube.com/watch?v=nP6eXbog-ZY"
        }
        
        selected_title = st.selectbox(
            "Select demonstration:",
            list(use_case_videos.keys())
        )
        
        if selected_title in use_case_videos:
            try:
                st_player(
                    use_case_videos[selected_title],
                    height=400,
                    playing=False,
                    controls=True,
                    light=True
                )
            except Exception as e:
                st.error(f"Error loading video: {str(e)}")
        
        # Información adicional sobre casos de uso
        st.markdown("""
        <div class="content-text">
        <div class="section-title">Applications</div>
        
        <strong>For Students:</strong>
        • Visualize thinking processes
        • Receive immediate feedback
        • Improve academic writing
        • Track cognitive progress
        
        <strong>For Educators:</strong>
        • Assess deep understanding
        • Identify individual needs
        • Personalize teaching
        • Save grading time
        
        <strong>For Institutions:</strong>
        • Measure cognitive development
        • Improve academic outcomes
        • Validated educational innovation
        • Data for research
        </div>
        """, unsafe_allow_html=True)

    # ============================================
    # TAB 5: 🎬 PITCHES & PRESENTATIONS
    # ============================================
    with tab_presentations:
        # NO repetir "Pitches & Presentations" - el tab ya lo dice
        
        st.markdown("""
        <div class="content-text">
        Watch our key pitches, demonstrations, and conference presentations:
        </div>
        """, unsafe_allow_html=True)
        
        videos = {
            "🎬 Pitch - PotencIA MX": "https://youtu.be/Nt7IEas_P54",
            "🏆 Conference - SENDA UNAM": "https://www.youtube.com/watch?v=XFLvjST2cE0",        
            "🐍 Conference - PyCon 2024": "https://www.youtube.com/watch?v=Jn545-IKx5Q",
            "👨‍🏫 Conference - Ser Maestro Foundation": "https://www.youtube.com/watch?v=imc4TI1q164",
            "🚀 Pitch - Explora - IFE - TEC de Monterrey": "https://www.youtube.com/watch?v=Fqi4Di_Rj_s",
            "🎙️ Interview with Dr. Guillermo Ruíz": "https://www.youtube.com/watch?v=_ch8cRja3oc"
        }

        selected_title = st.selectbox(
            "Select video:",
            list(videos.keys())
        )
        
        if selected_title in videos:
            try:
                st_player(
                    videos[selected_title],
                    height=400,
                    playing=False,
                    controls=True,
                    light=True
                )
            except Exception as e:
                st.error(f"Error loading video: {str(e)}")
        
        # Próximos eventos
        st.markdown("""
        <div class="content-text">
        <div class="section-title">Upcoming Events</div>
        
        <strong>Confirmed next events for 2026</strong>
        • <strong>Stay in touch</strong><br>
        
        <em>Confirmed participation in showcases and panels.</em>
        </div>
        """, unsafe_allow_html=True)

    # ============================================
    # TAB 6: 📸 EVENTS & RECOGNITION
    # ============================================
    with tab_gallery:
        # NO repetir "Events & Recognition" - el tab ya lo dice
        
        st.markdown("""
        <div class="content-text">
        Gallery of our participation in events and recognition received:
        </div>
        """, unsafe_allow_html=True)
        
        show_carousel()
        
#############################################################
#############################################################
# Definición de __all__ para especificar qué se exporta
__all__ = ['main', 'login_register_page', 'initialize_session_state']

# Bloque de ejecución condicional
if __name__ == "__main__":
    main()