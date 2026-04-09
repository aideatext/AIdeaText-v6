# modules/metrics/m1_m2.py
#
# Implementación según Doc3_Metodo_v2 — Piloto UNIFE Abril–Junio 2025
#
# M1 — Coherencia Dialógica (por sesión)
#     Similitud coseno entre el vector semántico del grafo de escritura
#     y el vector semántico del grafo del tutor virtual.
#     Modelo: paraphrase-multilingual-mpnet-base-v2 (768 dimensiones).
#     Se calcula cada vez que el estudiante usa un Tab y ha tenido
#     al menos una sesión con el tutor virtual.
#
# M2 — Robustez Estructural (trayectoria longitudinal)
#     Tres métricas estructurales del grafo en cada punto de medición:
#     - Densidad (density): aristas / (nodos × (nodos-1))
#     - Alineación temática (topic_alignment): cos(grafo, vector_tema)
#     - Profundidad argumentativa (depth): cadena más larga del grafo
#
# Umbrales M1 (Doc3_Metodo_v2, tabla de interpretación):
#   0.80 – 1.00  → Coherencia alta
#   0.60 – 0.79  → Coherencia moderada-alta
#   0.40 – 0.59  → Coherencia moderada
#   0.20 – 0.39  → Coherencia baja
#   0.00 – 0.19  → Sin coherencia

import logging
import numpy as np
import networkx as nx

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  CARGA DEL MODELO SENTENCE-TRANSFORMERS
# ─────────────────────────────────────────────

_model = None
_model_load_attempted = False


def _get_model():
    """
    Carga lazy (singleton) del modelo paraphrase-multilingual-mpnet-base-v2.
    Retorna None si sentence-transformers no está instalado.
    """
    global _model, _model_load_attempted
    if _model is not None:
        return _model
    if _model_load_attempted:
        return None
    _model_load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        logger.info("Modelo sentence-transformers cargado: paraphrase-multilingual-mpnet-base-v2 (768 dims)")
        return _model
    except ImportError:
        logger.warning(
            "sentence-transformers no instalado. "
            "M1 y topic_alignment no estarán disponibles. "
            "Instale con: pip install sentence-transformers"
        )
        return None
    except Exception as e:
        logger.error(f"Error cargando modelo sentence-transformers: {e}")
        return None


# ─────────────────────────────────────────────
#  HELPERS INTERNOS
# ─────────────────────────────────────────────

def _graph_to_text(G: nx.Graph) -> str:
    """
    Convierte un grafo de conceptos en representación textual para el modelo
    de embeddings. Los nodos se ordenan por PageRank (centralidad) y se
    complementan con las relaciones más fuertes del grafo.

    Esto produce un texto que captura tanto los conceptos clave como
    sus conexiones semánticas.
    """
    if not G or G.number_of_nodes() == 0:
        return ""

    # PageRank para ponderar importancia de los conceptos
    try:
        pagerank = nx.pagerank(G, weight='weight')
    except Exception:
        pagerank = {n: 1.0 for n in G.nodes()}

    # Nodos ordenados por importancia (PageRank descendente)
    sorted_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
    concepts_text = " ".join(node for node, _ in sorted_nodes)

    # Relaciones más fuertes como pares de conceptos
    sorted_edges = sorted(
        G.edges(data=True),
        key=lambda x: x[2].get('weight', 1),
        reverse=True
    )[:20]  # Top 20 relaciones
    edges_text = " ".join(f"{u} {v}" for u, v, _ in sorted_edges)

    return f"{concepts_text} {edges_text}".strip()


def _encode_text(text: str) -> np.ndarray | None:
    """Codifica texto a vector de 768 dimensiones usando sentence-transformers."""
    model = _get_model()
    if model is None or not text:
        return None
    try:
        return model.encode(text, convert_to_numpy=True)
    except Exception as e:
        logger.error(f"Error codificando texto: {e}")
        return None


def _graph_embedding(G: nx.Graph) -> np.ndarray | None:
    """
    Genera el vector semántico (768 dims) para un grafo de conceptos.

    Pipeline: grafo → texto (nodos + relaciones) → embedding
    Modelo: paraphrase-multilingual-mpnet-base-v2
    """
    text = _graph_to_text(G)
    if not text:
        return None
    return _encode_text(text)


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Similitud coseno entre dos vectores. Retorna valor en [0.0, 1.0]."""
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    sim = dot_product / (norm_a * norm_b)
    return float(np.clip(sim, 0.0, 1.0))


# ─────────────────────────────────────────────
#  M1: COHERENCIA DIALÓGICA (por sesión)
# ─────────────────────────────────────────────

def calculate_M1(G_writing: nx.Graph, G_tutor: nx.Graph, nlp=None) -> float | None:
    """
    Calcula M1 (Coherencia Dialógica) para una sesión.

    M1 = cos(V_W, V_T) = (V_W · V_T) / (|V_W| × |V_T|)

    Compara el grafo del texto escrito del estudiante (Tab 1, 2 o 3)
    contra el grafo de la conversación con el tutor virtual en esa sesión.

    Args:
        G_writing:  Grafo generado del texto escrito del estudiante.
        G_tutor:    Grafo generado de la interacción con el tutor virtual.
        nlp:        DEPRECADO — se mantiene por compatibilidad. Se ignora.
                    El embedding ahora usa sentence-transformers.

    Returns:
        float: Similitud coseno [0.0 - 1.0], o None si falta información.
    """
    if nlp is not None:
        logger.debug("calculate_M1: param 'nlp' es deprecado y se ignora. "
                      "Se usa sentence-transformers.")

    vec_w = _graph_embedding(G_writing)
    vec_t = _graph_embedding(G_tutor)

    if vec_w is None or vec_t is None:
        logger.warning("M1: No se pudo calcular — grafo vacío o modelo no disponible.")
        return None

    return _cosine_similarity(vec_w, vec_t)


def interpret_M1(m1_score: float) -> dict:
    """
    Interpreta M1 según los 5 niveles del Doc3_Metodo_v2.

    0.80–1.00: Alta — el texto integra muy bien el andamiaje del tutor.
    0.60–0.79: Moderada-alta — buena integración, mayoría de conceptos presentes.
    0.40–0.59: Moderada — integración parcial.
    0.20–0.39: Baja — brecha notable entre escritura y diálogo.
    0.00–0.19: Sin coherencia — el texto no refleja lo trabajado con el tutor.
    """
    if m1_score is None:
        return {
            "level": "Sin datos",
            "color": "gray",
            "message": "Requiere interacción con el Tutor Virtual."
        }

    if m1_score >= 0.80:
        return {
            "level": "Alta",
            "color": "green",
            "message": "El texto integra muy bien el andamiaje del tutor. "
                       "Alta fidelidad conceptual."
        }
    elif m1_score >= 0.60:
        return {
            "level": "Moderada-alta",
            "color": "lightgreen",
            "message": "Buena integración. La mayoría de conceptos del tutor "
                       "aparecen en la escritura."
        }
    elif m1_score >= 0.40:
        return {
            "level": "Moderada",
            "color": "orange",
            "message": "Integración parcial. Algunos conceptos del tutor "
                       "no llegan al texto."
        }
    elif m1_score >= 0.20:
        return {
            "level": "Baja",
            "color": "red",
            "message": "Brecha notable entre lo conversado con el tutor "
                       "y lo escrito."
        }
    else:
        return {
            "level": "Sin coherencia",
            "color": "darkred",
            "message": "El texto no refleja lo trabajado con el tutor."
        }


# ─────────────────────────────────────────────
#  M2: ROBUSTEZ ESTRUCTURAL (por punto de medición)
# ─────────────────────────────────────────────

def calculate_M2(G: nx.Graph, topic: str = None) -> dict:
    """
    Calcula las tres métricas de Robustez Estructural (M2)
    para un punto de medición específico.

    Las tres métricas son complementarias:
    - density: qué tan articulado es el argumento.
    - topic_alignment: qué tan centrado está en el tema asignado.
    - depth: cuántos niveles jerárquicos tiene el razonamiento.

    Args:
        G:     Grafo de conceptos del texto escrito.
        topic: Tema central asignado (para topic_alignment). Opcional.

    Returns:
        dict con density, topic_alignment, depth, node_count, edge_count.
    """
    if not G or G.number_of_nodes() == 0:
        return {
            "density": 0.0,
            "topic_alignment": None,
            "depth": 0,
            "node_count": 0,
            "edge_count": 0
        }

    nodes = G.number_of_nodes()
    edges = G.number_of_edges()

    # 1. Densidad: aristas / (nodos × (nodos-1))
    #    Rango: 0.0 – 1.0
    #    Densidad creciente = argumento progresivamente más articulado.
    density = nx.density(G)

    # 2. Alineación temática: cos(vector_grafo, vector_tema)
    #    Rango: 0.0 – 1.0
    #    Mide qué tan centrado está el texto en el tema asignado.
    topic_alignment = _calculate_topic_alignment(G, topic)

    # 3. Profundidad argumentativa: cadena más larga del grafo
    #    Ejemplo: A→B→C→D = profundidad 3
    #    Diferencia texto descriptivo (depth=1) de analítico (depth≥3).
    depth = _calculate_depth(G)

    return {
        "density": round(density, 4),
        "topic_alignment": round(topic_alignment, 4) if topic_alignment is not None else None,
        "depth": depth,
        "node_count": nodes,
        "edge_count": edges
    }


def _calculate_topic_alignment(G: nx.Graph, topic: str = None) -> float | None:
    """
    Alineación temática: cos(grafo, vector_tema).

    Mide semánticamente qué tan centrado está el texto en el tema central
    asignado por la profesora asesora.

    Retorna None si no se proporcionó tema o si el modelo no está disponible.
    """
    if topic is None or not topic.strip():
        return None

    graph_text = _graph_to_text(G)
    if not graph_text:
        return None

    vec_graph = _encode_text(graph_text)
    vec_topic = _encode_text(topic)

    if vec_graph is None or vec_topic is None:
        return None

    return _cosine_similarity(vec_graph, vec_topic)


def _calculate_depth(G: nx.Graph) -> int:
    """
    Profundidad argumentativa: nivel máximo de la cadena argumentativa
    más larga del grafo.

    Para un grafo de co-ocurrencia (no dirigido), usamos el diámetro
    de la componente conexa más grande (longest shortest path).

    Ejemplo: A-B-C-D = profundidad 3 (tres niveles de conexión).
    Profundidad 1 = solo afirmaciones.
    Profundidad 3+ = argumentos apoyados por sub-argumentos.
    """
    if G.number_of_nodes() <= 1:
        return 0
    if G.number_of_edges() == 0:
        return 0

    try:
        if nx.is_connected(G):
            return nx.diameter(G)
        else:
            # Usar la componente conexa más grande
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            if subgraph.number_of_nodes() <= 1:
                return 0
            return nx.diameter(subgraph)
    except Exception as e:
        logger.error(f"Error calculando profundidad argumentativa: {e}")
        return 0


def interpret_M2_evolution(current: dict, previous: dict) -> dict:
    """
    Compara dos puntos de medición M2 para evaluar progreso longitudinal
    del tesista a lo largo del semestre.

    Evalúa delta en las tres métricas: density, topic_alignment, depth.
    """
    if not previous or previous.get("node_count", 0) == 0:
        return {"status": "baseline", "message": "Primera medición registrada."}

    delta_density = current.get("density", 0) - previous.get("density", 0)
    delta_depth = current.get("depth", 0) - previous.get("depth", 0)

    signals = []

    # Densidad
    if delta_density > 0.03:
        signals.append("densidad creciente")
    elif delta_density < -0.03:
        signals.append("densidad decreciente")

    # Profundidad
    if delta_depth > 0:
        signals.append("profundidad creciente")
    elif delta_depth < 0:
        signals.append("profundidad decreciente")

    # Alineación temática (si disponible en ambos puntos)
    delta_topic = None
    curr_ta = current.get("topic_alignment")
    prev_ta = previous.get("topic_alignment")
    if curr_ta is not None and prev_ta is not None:
        delta_topic = curr_ta - prev_ta
        if delta_topic > 0.05:
            signals.append("mejor enfoque temático")
        elif delta_topic < -0.05:
            signals.append("menor enfoque temático")

    # Clasificación general
    positive = sum(1 for s in signals if "creciente" in s or "mejor" in s)
    negative = sum(1 for s in signals if "decreciente" in s or "menor" in s)

    if positive > negative:
        level = "crecimiento"
        message = "Robustez estructural en crecimiento: " + ", ".join(signals) + "."
    elif negative > positive:
        level = "regresión"
        message = "Posible regresión estructural: " + ", ".join(signals) + "."
    else:
        level = "estable"
        message = "Sin cambios significativos en la estructura del conocimiento."

    return {
        "level": level,
        "delta_density": round(delta_density, 4),
        "delta_depth": delta_depth,
        "delta_topic_alignment": round(delta_topic, 4) if delta_topic is not None else None,
        "signals": signals,
        "message": message
    }


# ─────────────────────────────────────────────
#  SERIALIZACIÓN (para guardar en DocumentDB)
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
    Útil para recalcular M1 sobre análisis históricos.
    """
    G = nx.Graph()
    for node in d.get("nodes", []):
        G.add_node(node["id"], weight=node.get("weight", 1))
    for edge in d.get("edges", []):
        G.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 1))
    return G
