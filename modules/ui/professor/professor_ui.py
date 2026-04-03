# modules/ui/professor/professor_ui.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Importaciones modulares
from modules.database.sql_db import execute_query
from modules.database.semantic_mongo_db import get_student_semantic_analysis
from modules.database.chat_mongo_db import get_chat_history
from modules.metrics.metrics_processor import process_semantic_data
from modules.metrics.report_generator import create_docx_report
from modules.utils.helpers import decode_professor_id

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  HELPER: construir DataFrame de chat por grupo
# ─────────────────────────────────────────────
def _build_chat_df(group_id: str) -> pd.DataFrame:
    """
    Recupera los registros de chat_history-v3 para un grupo y los convierte
    en un DataFrame compatible con el schema del dashboard de Martha.
    Extrae m1_score y m2_score desde metadata.
    """
    try:
        raw_chats = get_chat_history(group_id=group_id, analysis_type='chat_interaction')
        if not raw_chats:
            return pd.DataFrame()

        rows = []
        for chat in raw_chats:
            meta = chat.get('metadata', {}) or {}
            username = None
            # El username puede estar directamente en el doc o en los mensajes
            for msg in chat.get('messages', []):
                pass  # campo username no está aquí; lo buscamos en el doc raíz

            # chat_mongo_db almacena username a nivel de documento
            # pero get_chat_history no lo retorna directamente — usamos group_id
            # para inferir el usuario desde los mensajes si es posible
            full_id = meta.get('username', chat.get('username', f"{group_id}-t?"))

            import re
            match = re.search(r'[tT](\d+)', full_id)
            id_estudiante = f"t{match.group(1)}" if match else "S/N"
            id_grupo_base = re.split(r'-[tT]\d+', full_id)[0] or group_id
            parts = id_grupo_base.split('-')
            display_grupo = f"Grupo {parts[1]} ({parts[2]}-{parts[3]})" if len(parts) >= 4 else id_grupo_base

            ts = chat.get('timestamp', datetime.utcnow())

            rows.append({
                'Estudiante_ID': id_estudiante,
                'Username_Completo': full_id,
                'Grupo_ID': id_grupo_base,
                'Grupo_Display': display_grupo,
                'Fecha': ts,
                'M1_chat': float(meta.get('m1_score', 0.0)),
                'M2_chat': float(meta.get('m2_score', 0.0)),
                'Fuente': 'Chat'
            })

        return pd.DataFrame(rows).sort_values('Fecha')

    except Exception as e:
        logger.error(f"Error construyendo chat_df para {group_id}: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────
#  HELPER: calcular M1_D cross-cubeta
# ─────────────────────────────────────────────
def _calcular_m1d(df_sem: pd.DataFrame, df_chat: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada estudiante, calcula:
      M1_D = mean(M1_escritura, M1_chat) * (1 - 0.15 * std)
    Retorna DataFrame con columnas: Estudiante_ID, M1_escritura, M1_chat, M1_D, Grupo_Display.
    """
    if df_sem.empty:
        return pd.DataFrame()

    # M1 promedio de escritura por estudiante
    sem_avg = (
        df_sem.groupby(['Estudiante_ID', 'Grupo_Display', 'Grupo_ID'])['M1']
        .mean()
        .reset_index()
        .rename(columns={'M1': 'M1_escritura'})
    )

    result = sem_avg.copy()
    result['M1_chat'] = 0.0

    # Agregar M1_chat si hay datos de chat
    if not df_chat.empty and 'M1_chat' in df_chat.columns:
        chat_avg = (
            df_chat.groupby('Estudiante_ID')['M1_chat']
            .mean()
            .reset_index()
        )
        result = result.merge(chat_avg, on='Estudiante_ID', how='left', suffixes=('', '_new'))
        if 'M1_chat_new' in result.columns:
            result['M1_chat'] = result['M1_chat_new'].fillna(0.0)
            result.drop(columns=['M1_chat_new'], inplace=True)
        result['M1_chat'] = result['M1_chat'].fillna(0.0)

    # Fórmula M1_D del CLAUDE.md
    def _m1d_row(row):
        scores = [row['M1_escritura']]
        if row['M1_chat'] > 0:
            scores.append(row['M1_chat'])
        mean_val = float(np.mean(scores))
        std_val = float(np.std(scores)) if len(scores) > 1 else 0.0
        return round(mean_val * (1 - 0.15 * std_val), 4)

    result['M1_D'] = result.apply(_m1d_row, axis=1)
    return result


# ─────────────────────────────────────────────
#  PÁGINA PRINCIPAL DE MARTHA
# ─────────────────────────────────────────────
def professor_page():
    # 1. Recuperar contexto del Profesor
    prof_user = st.session_state.get('username', 'MG-EDU-UNIFE-LIM')
    full_name = st.session_state.get('full_name', 'Docente')

    try:
        info = decode_professor_id(prof_user)
    except Exception:
        info = {'institucion': 'UNIFE', 'facultad': 'Educación', 'iniciales': 'MG'}

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👩‍🏫 {full_name}")
        st.divider()
        st.markdown(f"**Institución:**\n{info['institucion']}")
        st.markdown(f"**Facultad:**\n{info['facultad']}")
        st.divider()
        st.caption(f"Cátedra: {info['iniciales']}")

    st.title("Panel de Gestión Académica")

    # --- 2. GRUPOS (SQL) ---
    user_prefix = info['iniciales']
    query = """
        SELECT DISTINCT class_id FROM users
        WHERE (id LIKE %s OR class_id LIKE %s)
        AND role = 'Estudiante'
        AND class_id != %s
    """
    grupos_db = execute_query(query, (f"{user_prefix}%", f"{user_prefix}%", prof_user))
    lista_grupos_ids = sorted(list(set([g['class_id'] for g in grupos_db if g['class_id']])))

    if not lista_grupos_ids:
        st.warning("No se encontraron grupos de tesistas bajo su cátedra.")
        return

    # --- 3. CARGA DE DATOS (MongoDB — Escritura + Chat) ---
    all_raw_sem = []
    all_chat_frames = []

    for g_id in lista_grupos_ids:
        sem_data = get_student_semantic_analysis(group_id=g_id)
        all_raw_sem.extend(sem_data)

        df_chat_g = _build_chat_df(g_id)
        if not df_chat_g.empty:
            all_chat_frames.append(df_chat_g)

    df_global_sem = process_semantic_data(all_raw_sem)
    df_global_chat = pd.concat(all_chat_frames, ignore_index=True) if all_chat_frames else pd.DataFrame()

    # M1_D cross-cubeta global
    df_m1d = _calcular_m1d(df_global_sem, df_global_chat)

    # --- 4. TABS ---
    tab_global, tab_grupo, tab_m1d, tab_alumno = st.tabs([
        "🌐 Cátedra (Global)",
        "👥 Visión por Grupo",
        "📊 Coherencia Dialógica (M1_D)",
        "🔍 Seguimiento Individual"
    ])

    # ── TAB 0: GLOBAL ──
    with tab_global:
        st.subheader("Estado General de la Cátedra")
        if not df_global_sem.empty:
            resumen = df_global_sem.groupby('Grupo_Display')['M1'].mean().reset_index()
            fig_bar = px.bar(
                resumen, x='Grupo_Display', y='M1',
                title="Promedio de Coherencia Semántica (M1) por Grupo",
                labels={'Grupo_Display': 'Grupo', 'M1': 'Coherencia M1'},
                color='M1', color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_bar, width='stretch')
        else:
            st.info("No hay datos históricos suficientes para el promedio global.")

    # ── TAB 1: GRUPO ──
    with tab_grupo:
        st.subheader("Análisis del Grupo de Tesis")
        if not df_global_sem.empty:
            opciones_display = sorted(df_global_sem['Grupo_Display'].unique())
            grupo_visual = st.selectbox("Seleccione el grupo:", opciones_display, key="sel_grupo_tab1")
            df_grupo = df_global_sem[df_global_sem['Grupo_Display'] == grupo_visual]

            if not df_grupo.empty:
                fig_evol = px.line(
                    df_grupo, x='Fecha', y='M1', color='Estudiante_ID',
                    markers=True,
                    title=f"Evolución de Coherencia Semántica: {grupo_visual}"
                )
                st.plotly_chart(fig_evol, width='stretch')
            else:
                st.warning(f"El grupo {grupo_visual} no tiene registros de análisis.")
        else:
            st.info("Cargando datos de grupos...")

    # ── TAB 2: M1_D CROSS-CUBETA ──
    with tab_m1d:
        st.subheader("📊 Coherencia Dialógica — Escritura vs. Diálogo")
        st.caption(
            "M1_D = promedio(M1_escritura, M1_chat) × (1 − 0.15 × std)  "
            "— La penalización baja si el estudiante es inconsistente entre lo que escribe y lo que dice al tutor."
        )

        if df_m1d.empty:
            st.info("No hay suficientes datos para calcular M1_D. Se necesitan análisis semánticos registrados.")
        else:
            # Selector de grupo
            grupos_m1d = sorted(df_m1d['Grupo_Display'].unique())
            grupo_m1d_sel = st.selectbox("Grupo:", grupos_m1d, key="sel_grupo_m1d")
            df_m1d_g = df_m1d[df_m1d['Grupo_Display'] == grupo_m1d_sel]

            # ── Tarjetas de resumen ──
            cols = st.columns(len(df_m1d_g))
            for i, (_, row) in enumerate(df_m1d_g.iterrows()):
                with cols[i]:
                    m1d_pct = int(row['M1_D'] * 100)
                    color = "#28a745" if row['M1_D'] >= 0.7 else ("#ffc107" if row['M1_D'] >= 0.4 else "#dc3545")
                    st.markdown(
                        f"""
                        <div style='border:1px solid {color}; border-radius:10px; padding:12px; text-align:center;'>
                            <h3 style='color:{color}; margin:0;'>{row['Estudiante_ID']}</h3>
                            <p style='font-size:2em; font-weight:bold; margin:6px 0; color:{color};'>{m1d_pct}%</p>
                            <p style='margin:2px; font-size:0.85em;'>M1_D</p>
                            <hr style='margin:6px 0;'/>
                            <p style='margin:2px; font-size:0.8em;'>✍️ Escritura: {row['M1_escritura']:.3f}</p>
                            <p style='margin:2px; font-size:0.8em;'>💬 Chat: {row['M1_chat']:.3f}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            st.divider()

            # ── Gráfico comparativo Escritura vs Chat ──
            if not df_m1d_g.empty:
                fig_compare = go.Figure()
                fig_compare.add_trace(go.Bar(
                    name='✍️ Escritura (M1)',
                    x=df_m1d_g['Estudiante_ID'],
                    y=df_m1d_g['M1_escritura'],
                    marker_color='#4e79a7'
                ))
                fig_compare.add_trace(go.Bar(
                    name='💬 Chat con Tutor (M1)',
                    x=df_m1d_g['Estudiante_ID'],
                    y=df_m1d_g['M1_chat'],
                    marker_color='#f28e2b'
                ))
                fig_compare.add_trace(go.Scatter(
                    name='📊 M1_D (Dialógica)',
                    x=df_m1d_g['Estudiante_ID'],
                    y=df_m1d_g['M1_D'],
                    mode='markers+text',
                    marker=dict(size=14, color='#e15759', symbol='diamond'),
                    text=[f"{v:.3f}" for v in df_m1d_g['M1_D']],
                    textposition='top center'
                ))
                fig_compare.update_layout(
                    title=f"Escritura vs. Diálogo — {grupo_m1d_sel}",
                    barmode='group',
                    yaxis=dict(range=[0, 1.05], title='Score (0–1)'),
                    xaxis_title='Tesista',
                    legend=dict(orientation='h', y=1.12)
                )
                st.plotly_chart(fig_compare, width='stretch')

                # Alerta automática si hay brecha grande
                for _, row in df_m1d_g.iterrows():
                    brecha = abs(row['M1_escritura'] - row['M1_chat'])
                    if brecha > 0.3 and row['M1_chat'] > 0:
                        st.warning(
                            f"⚠️ **{row['Estudiante_ID']}**: brecha Escritura–Chat = {brecha:.2f}. "
                            "El tesista podría no estar integrando lo que escribe con lo que discute con el tutor."
                        )

    # ── TAB 3: INDIVIDUAL ──
    with tab_alumno:
        st.subheader("Seguimiento Detallado por Tesista")
        if not df_global_sem.empty:
            opciones_display_a = sorted(df_global_sem['Grupo_Display'].unique())
            grupo_visual_a = st.selectbox("Grupo:", opciones_display_a, key="sel_grupo_tab3")
            df_grupo_a = df_global_sem[df_global_sem['Grupo_Display'] == grupo_visual_a]

            if not df_grupo_a.empty:
                est_id_sel = st.selectbox("Tesista:", df_grupo_a['Estudiante_ID'].unique(), key="sel_est")
                df_est = df_grupo_a[df_grupo_a['Estudiante_ID'] == est_id_sel].sort_values('Fecha')
                full_username = df_est['Username_Completo'].iloc[0]

                st.markdown(f"#### Reporte Evolutivo: `{full_username}`")

                try:
                    doc_buffer = create_docx_report(full_username, df_est)
                    st.download_button(
                        label=f"📥 Descargar DOCX: {est_id_sel}",
                        data=doc_buffer,
                        file_name=f"Reporte_{full_username}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Error al generar el documento: {e}")

                st.divider()

                if len(df_est) > 0:
                    idx = st.select_slider(
                        "Línea de tiempo de sesiones:",
                        options=range(len(df_est)),
                        format_func=lambda i: df_est.iloc[i]['Fecha'].strftime('%d/%m %H:%M')
                        if hasattr(df_est.iloc[i]['Fecha'], 'strftime') else str(df_est.iloc[i]['Fecha'])
                    )
                    sesion_actual = df_est.iloc[idx]
                    col_texto, col_metricas = st.columns([2, 1])

                    with col_texto:
                        st.markdown("**Texto analizado:**")
                        st.info(sesion_actual['Texto'])

                    with col_metricas:
                        st.metric("Coherencia M1", f"{sesion_actual['M1']:.4f}")
                        st.metric("Robustez M2", f"{sesion_actual['M2']:.4f}")
                        # M1_D del alumno si está disponible
                        if not df_m1d.empty:
                            row_m1d = df_m1d[df_m1d['Estudiante_ID'] == est_id_sel]
                            if not row_m1d.empty:
                                st.metric("Dialógica M1_D", f"{row_m1d.iloc[0]['M1_D']:.4f}")
            else:
                st.info("El grupo seleccionado no tiene registros.")
        else:
            st.info("No hay datos de estudiantes disponibles.")
