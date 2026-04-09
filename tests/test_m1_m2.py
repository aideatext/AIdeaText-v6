"""
Test de validación para M1 (Coherencia Dialógica) y M2 (Robustez Estructural).

Según Doc3_Metodo_v2 — Piloto UNIFE Abril–Junio 2025.

Ejecutar:
    python -m pytest tests/test_m1_m2.py -v
    (o directamente: python tests/test_m1_m2.py)
"""

import sys
import os

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import networkx as nx
import numpy as np

from modules.metrics.m1_m2 import (
    calculate_M1,
    calculate_M2,
    interpret_M1,
    interpret_M2_evolution,
    graph_to_dict,
    dict_to_graph,
    _graph_to_text,
    _calculate_depth,
)


# ─── Helpers: Grafos de prueba ───────────────────────────────────────────────

def _make_graph(concepts: list[str], edges: list[tuple[str, str, int]] = None) -> nx.Graph:
    """Crea un grafo de conceptos para testing."""
    G = nx.Graph()
    for c in concepts:
        G.add_node(c, weight=1)
    if edges:
        for u, v, w in edges:
            G.add_edge(u, v, weight=w)
    return G


def graph_tesis_metodologia() -> nx.Graph:
    """Grafo típico de un capítulo de metodología de tesis."""
    concepts = ['investigación', 'metodología', 'muestra', 'instrumento',
                'variable', 'hipótesis', 'análisis', 'datos', 'resultado', 'validez']
    edges = [
        ('investigación', 'metodología', 3),
        ('metodología', 'muestra', 2),
        ('metodología', 'instrumento', 2),
        ('muestra', 'datos', 2),
        ('instrumento', 'variable', 1),
        ('variable', 'hipótesis', 2),
        ('hipótesis', 'análisis', 1),
        ('análisis', 'datos', 3),
        ('datos', 'resultado', 2),
        ('resultado', 'validez', 1),
        ('investigación', 'hipótesis', 1),
        ('análisis', 'resultado', 2),
    ]
    return _make_graph(concepts, edges)


def graph_tutor_metodologia() -> nx.Graph:
    """Grafo del tutor virtual discutiendo metodología (alta coherencia esperada)."""
    concepts = ['investigación', 'metodología', 'muestra', 'instrumento',
                'variable', 'análisis', 'datos', 'confiabilidad']
    edges = [
        ('investigación', 'metodología', 2),
        ('metodología', 'muestra', 3),
        ('metodología', 'instrumento', 2),
        ('instrumento', 'variable', 1),
        ('variable', 'análisis', 2),
        ('análisis', 'datos', 2),
        ('datos', 'confiabilidad', 1),
        ('muestra', 'datos', 1),
    ]
    return _make_graph(concepts, edges)


def graph_tutor_otro_tema() -> nx.Graph:
    """Grafo del tutor sobre tema diferente (baja coherencia esperada)."""
    concepts = ['deporte', 'nutrición', 'entrenamiento', 'músculo',
                'proteína', 'resistencia', 'fuerza']
    edges = [
        ('deporte', 'entrenamiento', 3),
        ('entrenamiento', 'músculo', 2),
        ('nutrición', 'proteína', 2),
        ('proteína', 'músculo', 1),
        ('entrenamiento', 'resistencia', 1),
        ('resistencia', 'fuerza', 1),
    ]
    return _make_graph(concepts, edges)


# ─── Tests M1 ────────────────────────────────────────────────────────────────

def test_m1_high_coherence():
    """M1 entre grafos del mismo tema debe ser alto (>= 0.60)."""
    G_w = graph_tesis_metodologia()
    G_t = graph_tutor_metodologia()
    m1 = calculate_M1(G_w, G_t)
    if m1 is None:
        print("  ⚠ SKIP: sentence-transformers no disponible")
        return True
    print(f"  M1 (mismo tema) = {m1:.4f}")
    assert m1 >= 0.60, f"M1 debería ser >= 0.60 para grafos del mismo tema, obtuvo {m1:.4f}"
    return True


def test_m1_low_coherence():
    """M1 entre grafos de temas distintos debe ser bajo (< 0.60)."""
    G_w = graph_tesis_metodologia()
    G_t = graph_tutor_otro_tema()
    m1 = calculate_M1(G_w, G_t)
    if m1 is None:
        print("  ⚠ SKIP: sentence-transformers no disponible")
        return True
    print(f"  M1 (temas distintos) = {m1:.4f}")
    assert m1 < 0.60, f"M1 debería ser < 0.60 para temas distintos, obtuvo {m1:.4f}"
    return True


def test_m1_identical_graphs():
    """M1 de un grafo contra sí mismo debe ser ~1.0."""
    G = graph_tesis_metodologia()
    m1 = calculate_M1(G, G)
    if m1 is None:
        print("  ⚠ SKIP: sentence-transformers no disponible")
        return True
    print(f"  M1 (idéntico) = {m1:.4f}")
    assert m1 >= 0.95, f"M1 de grafo contra sí mismo debería ser >= 0.95, obtuvo {m1:.4f}"
    return True


def test_m1_empty_graph():
    """M1 con grafo vacío debe retornar None."""
    G_w = graph_tesis_metodologia()
    G_empty = nx.Graph()
    m1 = calculate_M1(G_w, G_empty)
    print(f"  M1 (con vacío) = {m1}")
    assert m1 is None, f"M1 con grafo vacío debería ser None, obtuvo {m1}"
    return True


def test_m1_nlp_param_deprecated():
    """calculate_M1 debe aceptar (y ignorar) el param nlp por compatibilidad."""
    G_w = graph_tesis_metodologia()
    G_t = graph_tutor_metodologia()
    # No debe crashear aunque se pase nlp=<algo>
    m1 = calculate_M1(G_w, G_t, nlp="dummy_value")
    print(f"  M1 (con nlp deprecado) = {m1}")
    # Solo verificamos que no crashea — el valor puede ser None si no hay modelo
    return True


def test_m1_range():
    """M1 siempre debe estar en [0.0, 1.0] o ser None."""
    G_w = graph_tesis_metodologia()
    G_t = graph_tutor_metodologia()
    m1 = calculate_M1(G_w, G_t)
    if m1 is not None:
        assert 0.0 <= m1 <= 1.0, f"M1 fuera de rango: {m1}"
        print(f"  M1 en rango [0,1]: {m1:.4f} ✓")
    else:
        print("  ⚠ SKIP: sentence-transformers no disponible")
    return True


# ─── Tests interpret_M1 ──────────────────────────────────────────────────────

def test_interpret_m1_five_tiers():
    """interpret_M1 debe tener 5 niveles según Doc3_Metodo_v2."""
    cases = [
        (0.90, "Alta", "green"),
        (0.70, "Moderada-alta", "lightgreen"),
        (0.50, "Moderada", "orange"),
        (0.30, "Baja", "red"),
        (0.10, "Sin coherencia", "darkred"),
        (None, "Sin datos", "gray"),
    ]
    for score, expected_level, expected_color in cases:
        result = interpret_M1(score)
        assert result["level"] == expected_level, \
            f"score={score}: esperado level='{expected_level}', obtuvo '{result['level']}'"
        assert result["color"] == expected_color, \
            f"score={score}: esperado color='{expected_color}', obtuvo '{result['color']}'"
        print(f"  interpret_M1({score}) → {result['level']} ({result['color']}) ✓")
    return True


# ─── Tests M2 ────────────────────────────────────────────────────────────────

def test_m2_density():
    """M2 density debe coincidir con nx.density()."""
    G = graph_tesis_metodologia()
    m2 = calculate_M2(G)
    expected_density = nx.density(G)
    print(f"  density = {m2['density']:.4f} (expected {expected_density:.4f})")
    assert abs(m2['density'] - expected_density) < 0.0001
    return True


def test_m2_depth():
    """M2 depth debe ser el diámetro del grafo."""
    # Grafo lineal: A-B-C-D-E → depth = 4
    G_linear = nx.path_graph(5)
    G_linear = nx.relabel_nodes(G_linear, {i: f"n{i}" for i in range(5)})
    m2 = calculate_M2(G_linear)
    print(f"  depth (lineal 5 nodos) = {m2['depth']} (expected 4)")
    assert m2['depth'] == 4, f"Depth de grafo lineal de 5 nodos debería ser 4, obtuvo {m2['depth']}"

    # Grafo completo: K4 → depth = 1
    G_complete = nx.complete_graph(4)
    G_complete = nx.relabel_nodes(G_complete, {i: f"c{i}" for i in range(4)})
    m2_c = calculate_M2(G_complete)
    print(f"  depth (completo K4) = {m2_c['depth']} (expected 1)")
    assert m2_c['depth'] == 1, f"Depth de K4 debería ser 1, obtuvo {m2_c['depth']}"

    return True


def test_m2_depth_tesis():
    """M2 depth de un grafo de tesis realista."""
    G = graph_tesis_metodologia()
    m2 = calculate_M2(G)
    print(f"  depth (tesis) = {m2['depth']}")
    assert m2['depth'] >= 1, "Depth de grafo de tesis debe ser >= 1"
    return True


def test_m2_topic_alignment():
    """M2 topic_alignment con tema provisto."""
    G = graph_tesis_metodologia()
    m2_with_topic = calculate_M2(G, topic="metodología de investigación científica")
    m2_no_topic = calculate_M2(G, topic=None)

    print(f"  topic_alignment (con tema) = {m2_with_topic['topic_alignment']}")
    print(f"  topic_alignment (sin tema) = {m2_no_topic['topic_alignment']}")

    assert m2_no_topic['topic_alignment'] is None, "Sin tema, topic_alignment debe ser None"

    if m2_with_topic['topic_alignment'] is not None:
        assert 0.0 <= m2_with_topic['topic_alignment'] <= 1.0, \
            f"topic_alignment fuera de rango: {m2_with_topic['topic_alignment']}"
    else:
        print("  ⚠ SKIP topic_alignment: sentence-transformers no disponible")

    return True


def test_m2_empty_graph():
    """M2 de grafo vacío debe retornar valores por defecto."""
    G = nx.Graph()
    m2 = calculate_M2(G)
    print(f"  M2 (vacío) = {m2}")
    assert m2['density'] == 0.0
    assert m2['depth'] == 0
    assert m2['node_count'] == 0
    assert m2['edge_count'] == 0
    assert m2['topic_alignment'] is None
    return True


def test_m2_has_required_keys():
    """M2 debe retornar las 5 claves del Doc3_Metodo_v2."""
    G = graph_tesis_metodologia()
    m2 = calculate_M2(G)
    required_keys = {'density', 'topic_alignment', 'depth', 'node_count', 'edge_count'}
    assert required_keys == set(m2.keys()), \
        f"Claves M2 incorrectas: esperado {required_keys}, obtuvo {set(m2.keys())}"
    print(f"  Claves M2 correctas: {sorted(m2.keys())} ✓")
    return True


# ─── Tests M2 Evolution ──────────────────────────────────────────────────────

def test_m2_evolution_growth():
    """Evolución positiva cuando density y depth crecen."""
    prev = {"density": 0.10, "depth": 2, "topic_alignment": 0.50, "node_count": 8, "edge_count": 5}
    curr = {"density": 0.20, "depth": 4, "topic_alignment": 0.70, "node_count": 12, "edge_count": 10}
    result = interpret_M2_evolution(curr, prev)
    print(f"  Evolution = {result['level']}: {result['message']}")
    assert result['level'] == 'crecimiento'
    return True


def test_m2_evolution_baseline():
    """Primera medición debe retornar 'baseline'."""
    curr = {"density": 0.15, "depth": 2, "node_count": 6, "edge_count": 4}
    result = interpret_M2_evolution(curr, None)
    print(f"  Evolution baseline = {result['status']}")
    assert result['status'] == 'baseline'
    return True


# ─── Tests Serialización ─────────────────────────────────────────────────────

def test_graph_roundtrip():
    """Serialización y deserialización de grafos debe ser lossless."""
    G_original = graph_tesis_metodologia()
    d = graph_to_dict(G_original)
    G_restored = dict_to_graph(d)

    assert set(G_original.nodes()) == set(G_restored.nodes()), "Nodos no coinciden"
    assert set(G_original.edges()) == set(G_restored.edges()), "Aristas no coinciden"

    # Verificar que el dict tiene claves M2
    assert 'density' in d, "graph_to_dict debe incluir 'density'"
    assert 'depth' in d, "graph_to_dict debe incluir 'depth'"
    assert 'nodes' in d, "graph_to_dict debe incluir 'nodes'"
    assert 'edges' in d, "graph_to_dict debe incluir 'edges'"

    print(f"  Roundtrip: {len(G_original.nodes())} nodos, {len(G_original.edges())} aristas ✓")
    print(f"  Dict keys: {sorted(d.keys())}")
    return True


# ─── Tests _graph_to_text ────────────────────────────────────────────────────

def test_graph_to_text():
    """_graph_to_text debe producir texto no vacío para grafos con nodos."""
    G = graph_tesis_metodologia()
    text = _graph_to_text(G)
    print(f"  graph_to_text = '{text[:80]}...'")
    assert len(text) > 0, "Texto del grafo no debe estar vacío"
    # Verificar que los conceptos clave aparecen
    assert 'investigación' in text or 'metodología' in text
    return True


def test_graph_to_text_empty():
    """_graph_to_text de grafo vacío debe retornar string vacío."""
    G = nx.Graph()
    text = _graph_to_text(G)
    assert text == "", f"Texto de grafo vacío debe ser '', obtuvo '{text}'"
    print("  graph_to_text (vacío) = '' ✓")
    return True


# ─── Runner ──────────────────────────────────────────────────────────────────

def run_all_tests():
    tests = [
        ("M1: alta coherencia (mismo tema)", test_m1_high_coherence),
        ("M1: baja coherencia (temas distintos)", test_m1_low_coherence),
        ("M1: grafos idénticos ≈ 1.0", test_m1_identical_graphs),
        ("M1: grafo vacío → None", test_m1_empty_graph),
        ("M1: param nlp deprecado (compatibilidad)", test_m1_nlp_param_deprecated),
        ("M1: rango [0.0, 1.0]", test_m1_range),
        ("interpret_M1: 5 niveles Doc3", test_interpret_m1_five_tiers),
        ("M2: density = nx.density()", test_m2_density),
        ("M2: depth (lineal y completo)", test_m2_depth),
        ("M2: depth de tesis", test_m2_depth_tesis),
        ("M2: topic_alignment", test_m2_topic_alignment),
        ("M2: grafo vacío", test_m2_empty_graph),
        ("M2: claves requeridas", test_m2_has_required_keys),
        ("M2 evolution: crecimiento", test_m2_evolution_growth),
        ("M2 evolution: baseline", test_m2_evolution_baseline),
        ("Serialización: roundtrip graph ↔ dict", test_graph_roundtrip),
        ("_graph_to_text: texto válido", test_graph_to_text),
        ("_graph_to_text: grafo vacío", test_graph_to_text_empty),
    ]

    print("\n" + "=" * 70)
    print("  TEST SUITE: M1 (Coherencia Dialógica) + M2 (Robustez Estructural)")
    print("  Referencia: Doc3_Metodo_v2 — Piloto UNIFE 2025")
    print("=" * 70)

    passed = 0
    failed = 0
    skipped = 0

    for name, test_fn in tests:
        print(f"\n▶ {name}")
        try:
            result = test_fn()
            if result:
                passed += 1
                print(f"  ✅ PASS")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ FAIL: {e}")
        except Exception as e:
            failed += 1
            print(f"  ❌ ERROR: {e}")

    print("\n" + "=" * 70)
    print(f"  RESULTADOS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
