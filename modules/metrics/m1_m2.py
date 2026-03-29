# modules/metrics/m1_m2.py
#
# M1 — Índice de Coherencia Transmodal
#     Similitud coseno entre el embedding del grafo escrito (Borrador/Capítulo) 
#     y el grafo de la conversación (LO QUE INTERACTÚA CON EL TUTOR VIRTUAL).
#     Usa los vectores de spaCy (es_core_news_md) ponderados por grado de
#     centralidad (PageRank), enfocándose estrictamente en la red de sustantivos (CRA).
#
# M2 — Índice de Robustez Estructural
#     Densidad del grafo + grado promedio, calculados con NetworkX sobre
#     el grafo ya construido en semantic_analysis.create_concept_graph() 
#     (ahora filtrado solo para NOUN y PROPN).
#
# Umbrales pedagógicos para el piloto UNIFE (según ProyPilot 2026):
#   M1 >= 0.80    → coherencia alta      (verde)
#   M1  0.60–0.79 → coherencia moderada  (amarillo — el asesor debe revisar)
#   M1 < 0.60     → riesgo reproductivo  (rojo — alerta inmediata)
#
#   M2 densidad esperada: 0.10 (abril) → 0.30 (junio)
#   M2 grado promedio esperado: 2.0 (abril) → 5.0 (junio)

import logging
import numpy as np
import networkx as nx

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  HELPERS INTERNOS
# ─────────────────────────────────────────────

def _graph_embedding(G: nx.Graph, nlp) -> np.ndarray | None:
    """
    Representación vectorial del grafo como promedio ponderado de los
    embeddings de sus nodos (Sustantivos), usando PageRank como peso.
    Esto da más importancia a los conceptos centrales de la tesis o del diálogo.
    """
    if not G or G.number_of_nodes() == 0:
        return None

    try:
        pagerank = nx.pagerank(G, weight='weight')
    except Exception:
        # Fallback si PageRank no converge (raro en grafos pequeños)
        pagerank = {node: 1.0 for node in G.nodes()}

    embeddings = []
    weights = []

    for node in G.nodes():
        # Obtenemos el vector de spaCy para el concepto (sustantivo)
        token = nlp(node)
        if token and token.has_vector:
            embeddings.append(token.vector)
            weights.append(pagerank.get(node, 1.0))

    if not embeddings:
        return None

    # Promedio ponderado
    emb_array = np.array(embeddings)
    w_array = np.array(weights).reshape(-1, 1)
    weighted_sum = np.sum(emb_array * w_array, axis=0)
    total_weight = np.sum(w_array)

    return weighted_sum / total_weight if total_weight > 0 else None


# ─────────────────────────────────────────────
#  M1: COHERENCIA TRANSMODAL
# ─────────────────────────────────────────────

def calculate_M1(G_Escrito: nx.Graph, G_TutorVirtual: nx.Graph, nlp) -> float | None:
    """
    Calcula M1 (Coherencia Transmodal) usando Similitud Coseno.
    Compara la red de conceptos del documento escrito contra la del chat.
    
    Args:
        G_Escrito (nx.Graph): Grafo generado a partir del borrador del estudiante.
        G_TutorVirtual (nx.Graph): Grafo generado de la interacción limpia con el bot.
        nlp: Modelo spaCy cargado.
        
    Returns:
        float: Similitud coseno [0.0 - 1.0], o None si falta información.
    """
    vec_escrito = _graph_embedding(G_Escrito, nlp)
    vec_tutor = _graph_embedding(G_TutorVirtual, nlp)

    if vec_escrito is None or vec_tutor is None:
        logger.warning("No se pudo calcular M1: uno de los grafos está vacío o sin vectores.")
        return None

    # Similitud coseno: (A · B) / (||A|| * ||B||)
    dot_product = np.dot(vec_escrito, vec_tutor)
    norm_escrito = np.linalg.norm(vec_escrito)
    norm_tutor = np.linalg.norm(vec_tutor)

    if norm_escrito == 0 or norm_tutor == 0:
        return 0.0

    sim = dot_product / (norm_escrito * norm_tutor)
    
    # Clip para evitar errores de precisión de punto flotante fuera de [-1, 1]
    return float(np.clip(sim, -1.0, 1.0))

def interpret_M1(m1_score: float) -> dict:
    """
    Interpreta el valor M1 según los umbrales del piloto UNIFE 2026.
    Retorna nivel de coherencia y color para la UI.
    """
    if m1_score is None:
        return {"level": "Sin datos", "color": "gray", "message": "Requiere interacción con el Tutor Virtual."}
    
    if m1_score >= 0.80:
        return {"level": "Alta", "color": "green", "message": "Excelente coherencia terminológica entre redacción y diálogo."}
    elif m1_score >= 0.60:
        return {"level": "Moderada", "color": "orange", "message": "Coherencia aceptable. Revisar si hay conceptos desconectados."}
    else:
        return {"level": "Baja", "color": "red", "message": "Riesgo reproductivo. El estudiante no verbaliza los conceptos que escribe."}


# ─────────────────────────────────────────────
#  M2: ROBUSTEZ ESTRUCTURAL
# ─────────────────────────────────────────────

def calculate_M2(G: nx.Graph) -> dict:
    """
    Calcula métricas de robustez estructural (M2) de un grafo de conceptos.
    Válido tanto para el grafo escrito como para el grafo del tutor virtual.
    """
    if not G or G.number_of_nodes() == 0:
        return {
            "M2_density": 0.0,
            "M2_average_degree": 0.0,
            "M2_node_count": 0,
            "M2_edge_count": 0
        }

    nodes = G.number_of_nodes()
    edges = G.number_of_edges()
    
    # Densidad: relación entre aristas reales y aristas posibles
    density = nx.density(G)
    
    # Grado promedio: promedio de conexiones por concepto (sustantivo)
    degrees = dict(G.degree())
    avg_degree = sum(degrees.values()) / nodes if nodes > 0 else 0.0

    return {
        "M2_density": round(density, 4),
        "M2_average_degree": round(avg_degree, 2),
        "M2_node_count": nodes,
        "M2_edge_count": edges
    }

def interpret_M2_evolution(m2_current: dict, m2_previous: dict) -> dict:
    """
    Compara dos estados de M2 para evaluar el progreso longitudinal del tesista.
    """
    if not m2_previous or m2_previous.get("M2_node_count", 0) == 0:
        return {"status": "baseline", "message": "Primera medición registrada."}

    delta_density = m2_current["M2_density"] - m2_previous["M2_density"]
    delta_degree = m2_current["M2_average_degree"] - m2_previous["M2_average_degree"]

    if delta_degree > 0.5:
        level = "crecimiento"
        message = "La red conceptual se está enriqueciendo. Mayor articulación de ideas."
    elif delta_degree < -0.5:
        level = "simplificación"
        message = "Pérdida de conexiones. El estudiante podría estar fragmentando el tema."
    elif delta_density > 0.05:
        level = "consolidación"
        message = "Mismos conceptos, pero más integrados entre sí."
    elif delta_density < -0.05:
        level = "dispersión"
        message = "Se añadieron conceptos nuevos pero sin relacionarlos con los anteriores."
    else:
        level = "estático"
        message = "Sin cambios significativos en la estructura del conocimiento."

    return {
        "delta_density": delta_density,
        "delta_degree": delta_degree,
        "level": level,
        "message": message
    }


# ─────────────────────────────────────────────
#  SERIALIZACIÓN  (para guardar en DocumentDB)
# ─────────────────────────────────────────────

def graph_to_dict(G: nx.Graph) -> dict:
    """
    Serializa un nx.Graph a dict almacenable en DocumentDB/JSON.
    Incluye estructura completa + métricas M2 precalculadas.
    """
    m2 = calculate_M2(G)
    return {
        "nodes": [
            {"id": n, "weight": G.nodes[n].get("weight", 1)}
            for n in G.nodes()
        ],
        "edges": [
            {"source": u, "target": v, "weight": G[u][v].get("weight", 1)}
            for u, v in G.edges()
        ],
        **m2,
    }

def dict_to_graph(d: dict) -> nx.Graph:
    """
    Reconstruye un nx.Graph desde el dict almacenado en DocumentDB.
    Útil para recalcular M1 sobre análisis históricos al cargar el Dashboard.
    """
    G = nx.Graph()
    for node in d.get("nodes", []):
        G.add_node(node["id"], weight=node.get("weight", 1))
    
    for edge in d.get("edges", []):
        G.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 1))
        
    return G