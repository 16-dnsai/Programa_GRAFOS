"""
    python app.py

ARQUITECTURA (secciones de este archivo):

    1. Utilidades y tipos            7. Visualización (Matplotlib / PyVis)
    2. Construcción y validación     8. Visión por computador (OpenCV)
    3. Generadores y casos de prueba 9. Sesión, tema y componentes de interfaz
    4. Algoritmos de Euler          10. Páginas: creador (A), análisis (B), imagen (C), ajustes
    5. Algoritmos de Hamilton       11. Aplicación principal (ventana) y main()
    6. Análisis estructural
"""
from __future__ import annotations

import base64
import io
import itertools
import json
import math
import os
import queue
import re
import tempfile
import threading
import tkinter as tk
import webbrowser
from dataclasses import dataclass, field
from tkinter import filedialog, ttk
from tkinter import font as tkfont
from typing import Callable, Hashable, Iterable

import customtkinter as ctk
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from PIL import Image, ImageOps

try:  # OpenCV es necesario sólo para el módulo C
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None
try:  # PyVis es opcional
    from pyvis.network import Network
except ImportError:  # pragma: no cover
    Network = None


Node = Hashable

# Paleta: tinta azul para nodos, ámbar para recorridos resaltados (único acento).
C_NODE, C_EDGE, C_HILITE, C_START, C_PANEL = "#1e3a5f", "#94a3b8", "#e76f00", "#2f855a", "#f6f7f9"
MAX_IMG_DIM = 1100
LAYOUTS = ["Resorte (spring)", "Circular", "Shell", "Kamada-Kawai", "Aleatorio"]


# ============================================================================
# 1. UTILIDADES Y TIPOS
# ============================================================================
class GraphInputError(ValueError):
    """Error de validación de datos de entrada del usuario."""


@dataclass
class PathResult:
    """Resultado de buscar un camino o ciclo (Euler o Hamilton)."""

    exists: bool | None  # None = inconcluso (límite de pasos agotado)
    sequence: list[Node] = field(default_factory=list)
    reason: str = ""
    verified: bool | None = None
    verification: str = ""
    steps: int = 0


def label_for(i: int) -> str:
    """Etiqueta estilo hoja de cálculo: 0→A, 25→Z, 26→AA..."""
    s, i = "", i + 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def sort_nodes(nodes: Iterable[Node]) -> list[Node]:
    """Ordena vértices de forma natural (A..Z, AA.. / 1..9, 10..)."""
    return sorted(nodes, key=lambda x: (len(str(x)), str(x)))


def edge_key(G: nx.Graph, u: Node, v: Node) -> Hashable:
    """Identificador de arista: (u,v) si es dirigido, {u,v} si no."""
    return (u, v) if G.is_directed() else frozenset((u, v))


def is_weighted(G: nx.Graph) -> bool:
    """True si alguna arista tiene atributo 'weight'."""
    return any("weight" in d for _, _, d in G.edges(data=True))


def signature(G: nx.Graph) -> tuple:
    """Firma hashable del grafo (para memorizar análisis costosos)."""
    ek = sorted((str(u), str(v)) if G.is_directed() else tuple(sorted((str(u), str(v)))) for u, v in G.edges)
    return (G.is_directed(), tuple(sorted(map(str, G.nodes))), tuple(ek))


def yn(v: bool | None) -> str:
    """Formatea un booleano tri-estado."""
    return "✅ Sí" if v is True else "❌ No" if v is False else "⚠️ Inconcluso"


def fmt_seq(seq: Iterable[Node]) -> str:
    """Secuencia de vértices con flechas: A → B → C."""
    return " → ".join(map(str, seq))


def n_components(G: nx.Graph) -> int:
    """Número de componentes (débiles si es dirigido)."""
    return nx.number_weakly_connected_components(G) if G.is_directed() else nx.number_connected_components(G)


def is_connected(G: nx.Graph) -> bool:
    """Conexidad (débil si es dirigido). El grafo vacío no es conexo."""
    if G.number_of_nodes() == 0:
        return False
    return nx.is_weakly_connected(G) if G.is_directed() else nx.is_connected(G)


# ============================================================================
# 2. CONSTRUCCIÓN Y VALIDACIÓN
# ============================================================================
def _clean(v: object) -> str:
    """Convierte None/NaN a cadena vacía y recorta espacios."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def build_graph(
    nodes: Iterable[object],
    edges: Iterable[tuple[object, object, float | None]],
    directed: bool,
    weighted: bool = False,
    extra_errors: list[str] | None = None,
) -> nx.Graph:
    """Construye un grafo simple validando vértices, aristas y pesos.

    Detecta: entradas vacías, vértices duplicados o inexistentes, lazos y aristas duplicadas.
    Lanza ``GraphInputError`` con todos los problemas encontrados.
    """
    errors = list(extra_errors or [])
    G: nx.Graph = nx.DiGraph() if directed else nx.Graph()
    for raw in nodes:
        n = _clean(raw)
        if not n:
            continue
        if n in G:
            errors.append(f"Vértice duplicado: «{n}».")
        G.add_node(n)
    if G.number_of_nodes() == 0:
        errors.append("Entrada vacía: no se indicó ningún vértice.")
    for u_raw, v_raw, w in edges:
        u, v = _clean(u_raw), _clean(v_raw)
        if not u and not v:
            continue
        if not u or not v:
            errors.append(f"Arista incompleta: «{u}»–«{v}».")
            continue
        missing = [x for x in (u, v) if x not in G]
        if missing:
            errors.append(f"Arista {u}–{v}: vértice inexistente «{'», «'.join(missing)}».")
            continue
        if u == v:
            errors.append(f"Lazo no permitido en «{u}».")
            continue
        if G.has_edge(u, v):
            errors.append(f"Arista duplicada: {u}–{v}.")
            continue
        wf = None if w is None or (isinstance(w, float) and math.isnan(w)) else float(w)
        if weighted:
            G.add_edge(u, v, weight=1.0 if wf is None else wf)
        else:
            G.add_edge(u, v)
    if errors:
        raise GraphInputError("\n".join(errors))
    return G


_EDGE_SEP = re.compile(r"\s*(?:->|→|–|—|-)\s*")


def parse_graph_text(vertices: str, edges: str, directed: bool, weighted: bool) -> nx.Graph:
    """Interpreta texto: vértices 'A, B, C' y aristas 'A-B, B-C:5'."""
    nodes = [t for t in re.split(r"[,;\n]+", vertices or "") if t.strip()]
    parsed: list[tuple[str, str, float | None]] = []
    errs: list[str] = []
    for tok in re.split(r"[,;\n]+", edges or ""):
        tok = tok.strip()
        if not tok:
            continue
        w: float | None = None
        if ":" in tok:
            tok, wtxt = tok.rsplit(":", 1)
            try:
                w = float(wtxt)
            except ValueError:
                errs.append(f"Peso inválido en «{tok}:{wtxt}».")
                continue
        parts = _EDGE_SEP.split(tok.strip())
        if len(parts) != 2 or not all(parts):
            errs.append(f"Arista mal formada: «{tok}» (use A-B o A-B:3).")
            continue
        parsed.append((parts[0], parts[1], w))
    return build_graph(nodes, parsed, directed, weighted, errs)


# ============================================================================
# 3. GENERADORES Y CASOS DE PRUEBA
# ============================================================================
KINDS = {
    "er": "Aleatorio Erdős–Rényi G(n, p)",
    "ba": "Aleatorio Barabási–Albert",
    "complete": "Completo Kₙ",
    "cycle": "Ciclo Cₙ",
    "bip": "Bipartito aleatorio",
}


def _orient(G: nx.Graph, rng: np.random.Generator) -> nx.DiGraph:
    D = nx.DiGraph()
    D.add_nodes_from(G.nodes)
    for u, v in G.edges:
        D.add_edge(*((u, v) if rng.random() < 0.5 else (v, u)))
    return D


def generate_graph(
    kind: str, n: int, p: float, m: int, n2: int, directed: bool,
    weighted: bool, wrange: tuple[int, int], seed: int,
) -> nx.Graph:
    """Genera un grafo según el tipo, relabelado A, B, C... y con pesos opcionales."""
    rng = np.random.default_rng(seed)
    cls = nx.DiGraph if directed else nx.Graph
    if kind == "er":
        G = nx.gnp_random_graph(n, p, seed=seed, directed=directed)
    elif kind == "ba":
        if not 1 <= m < n:
            raise GraphInputError("En Barabási–Albert se requiere 1 ≤ m < n.")
        G = nx.barabasi_albert_graph(n, m, seed=seed)
        G = _orient(G, rng) if directed else G
    elif kind == "complete":
        G = nx.complete_graph(n, create_using=cls)
    elif kind == "cycle":
        G = nx.cycle_graph(n, create_using=cls)
    elif kind == "bip":
        G = nx.bipartite.random_graph(n, n2, p, seed=seed, directed=directed)
    else:
        raise GraphInputError(f"Tipo de grafo desconocido: {kind}")
    G = nx.relabel_nodes(G, {v: label_for(i) for i, v in enumerate(sorted(G.nodes))})
    if weighted:
        for u, v in G.edges:
            G[u][v]["weight"] = int(rng.integers(wrange[0], wrange[1] + 1))
    return G


_V8 = "A,B,C,D,E,F,G,H"
_C8 = "A-B,B-C,C-D,D-E,E-F,F-G,G-H,H-A"


@dataclass
class Preset:
    """Caso de prueba: grafo, descripción y resultado esperado (EC, ECi, HC, HCi)."""

    name: str
    build: Callable[[], nx.Graph]
    desc: str
    expected: tuple[bool, bool, bool, bool]  # camino Euler, ciclo Euler, camino Hamilton, ciclo Hamilton


def _p(v: str, e: str, directed: bool = False) -> Callable[[], nx.Graph]:
    return lambda: parse_graph_text(v, e, directed, False)


PRESETS: list[Preset] = [
    Preset("Ejemplo mínimo (sección 6.3)", _p("A,B,C,D,E", "A-B,B-C,C-D,D-A,A-E,B-E"),
           "5 vértices; grados A=3, B=3, C=D=E=2. Euler: A→E→B→A→D→C→B. Hamilton: A→E→B→C→D→A.", (True, False, True, True)),
    Preset("Todos los grados pares (ciclo de Euler)", _p(_V8, _C8 + ",A-C,C-E,E-A"),
           "C₈ más el triángulo A-C-E: todos los grados son pares.", (True, True, True, True)),
    Preset("Exactamente dos vértices impares", _p(_V8, _C8 + ",A-E"),
           "C₈ más la cuerda A-E: sólo A y E tienen grado impar (camino de Euler, sin ciclo).", (True, False, True, True)),
    Preset("Más de dos vértices impares", _p(_V8, _C8 + ",A-E,B-F"),
           "C₈ más cuerdas A-E y B-F: cuatro vértices impares.", (False, False, True, True)),
    Preset("Camino de Hamilton sin ciclo", _p(_V8, "A-B,B-C,C-D,D-E,E-F,F-G,G-H,C-E"),
           "Camino A…H con cuerda C-E; A y H tienen grado 1, así que no hay ciclo.", (False, False, True, False)),
    Preset("Grafo estrella K₁,₇", _p(_V8, ",".join(f"A-{c}" for c in "BCDEFGH")),
           "Centro A con 7 hojas: no hay camino de Hamilton.", (False, False, False, False)),
    Preset("Grafo desconectado", _p(_V8, "A-B,B-C,C-D,D-A,E-F,F-G,G-H,H-E"),
           "Dos cuadrados separados: grados pares pero sin conexidad.", (False, False, False, False)),
    Preset("Grafo de Petersen", lambda: nx.relabel_nodes(nx.petersen_graph(), {i: label_for(i) for i in range(10)}),
           "10 vértices, 3-regular: tiene camino de Hamilton pero no ciclo.", (False, False, True, False)),
    Preset("Dirigido con circuito de Euler", _p(_V8, _C8 + ",A-C,C-E,E-A", True),
           "Ciclo dirigido de 8 vértices más el triángulo A→C→E→A: in = out en todos.", (True, True, True, True)),
    Preset("Dirigido: camino sin ciclo", _p(_V8, "A-B,B-C,C-D,D-E,E-F,F-G,G-H", True),
           "Camino dirigido A→…→H: Euler y Hamilton existen como camino, no como ciclo.", (True, False, True, False)),
]


# ============================================================================
# 4. ALGORITMOS DE EULER
# ============================================================================
def hierholzer(G: nx.Graph, start: Node) -> list[Node]:
    """Algoritmo de Hierholzer (iterativo) para grafos dirigidos y no dirigidos."""
    directed = G.is_directed()
    nbrs = G.successors if directed else G.neighbors
    adj = {u: sort_nodes(nbrs(u))[::-1] for u in G}  # pop() toma el menor
    stack, circuit = [start], []
    while stack:
        v = stack[-1]
        if adj[v]:
            w = adj[v].pop()
            if not directed:
                adj[w].remove(v)
            stack.append(w)
        else:
            circuit.append(stack.pop())
    return circuit[::-1]


def verify_euler(G: nx.Graph, walk: list[Node], closed: bool) -> tuple[bool, str]:
    """Comprueba que el recorrido usa cada arista exactamente una vez (y cierra, si es ciclo)."""
    m = G.number_of_edges()
    if len(walk) != m + 1:
        return False, f"El recorrido usa {len(walk) - 1} aristas y el grafo tiene {m}."
    if any(not G.has_edge(u, v) for u, v in zip(walk, walk[1:])):
        return False, "El recorrido contiene una arista inexistente."
    used = [edge_key(G, u, v) for u, v in zip(walk, walk[1:])]
    if len(set(used)) != m:
        return False, "El recorrido repite alguna arista."
    if closed and walk[0] != walk[-1]:
        return False, "El ciclo no regresa al vértice inicial."
    msg = f"Cada una de las {m} aristas se usa exactamente una vez"
    return True, msg + (f" y el recorrido regresa a {walk[0]}." if closed else ".")


def _euler_result(G: nx.Graph, start: Node, closed: bool) -> PathResult:
    walk = hierholzer(G, start)
    ok, msg = verify_euler(G, walk, closed)
    return PathResult(True, walk, "", ok, msg)


def euler_analysis(G: nx.Graph) -> tuple[PathResult, PathResult]:
    """Devuelve (camino, ciclo) de Euler, con la justificación cuando no existen."""
    if G.number_of_edges() == 0:
        r = PathResult(False, [], "El grafo no tiene aristas que recorrer.")
        return r, r
    if not is_connected(G):
        k = n_components(G)
        r = PathResult(False, [], f"El grafo está desconectado ({k} componentes): ningún recorrido puede alcanzar todas las aristas.")
        return r, r
    nodes = sort_nodes(G.nodes)
    if G.is_directed():
        diff = {v: G.out_degree(v) - G.in_degree(v) for v in nodes}
        starts = [v for v, d in diff.items() if d == 1]
        ends = [v for v, d in diff.items() if d == -1]
        bad = [v for v, d in diff.items() if abs(d) > 1]
        unb = [v for v, d in diff.items() if d != 0]
        txt = ", ".join(f"{v} (sal={G.out_degree(v)}, ent={G.in_degree(v)})" for v in unb)
        cyc_ok = not unb
        path_ok = cyc_ok or (len(starts) == 1 and len(ends) == 1 and not bad)
        cyc_why = f"Vértices con grado de entrada ≠ salida: {txt}. Un ciclo exige igualdad en todos."
        path_why = f"Se requiere a lo sumo un vértice con sal−ent=1 y uno con ent−sal=1; hay desbalance en: {txt}."
        start_path = starts[0] if starts else nodes[0]
    else:
        odd = [v for v in nodes if G.degree(v) % 2]
        cyc_ok, path_ok = not odd, len(odd) in (0, 2)
        lst = ", ".join(map(str, odd))
        cyc_why = f"Hay {len(odd)} vértice(s) de grado impar ({lst}); un ciclo exige que todos sean pares."
        path_why = f"Hay {len(odd)} vértices de grado impar ({lst}); un camino admite 0 o exactamente 2."
        start_path = odd[0] if odd else nodes[0]
    path = _euler_result(G, start_path, closed=cyc_ok) if path_ok else PathResult(False, [], path_why)
    cyc = _euler_result(G, nodes[0], closed=True) if cyc_ok else PathResult(False, [], cyc_why)
    return path, cyc


# ============================================================================
# 5. ALGORITMOS DE HAMILTON
# ============================================================================
class _StepLimit(Exception):
    """Se agotó el presupuesto de pasos del backtracking."""


def verify_hamilton(G: nx.Graph, seq: list[Node], closed: bool) -> tuple[bool, str]:
    """Comprueba que cada vértice se visita exactamente una vez (y que cierra, si es ciclo)."""
    core = seq[:-1] if closed else seq
    n = G.number_of_nodes()
    if closed and seq[0] != seq[-1]:
        return False, "El ciclo no regresa al vértice inicial."
    if len(core) != n or set(core) != set(G.nodes):
        return False, "El recorrido no visita cada vértice exactamente una vez."
    if any(not G.has_edge(u, v) for u, v in zip(seq, seq[1:])):
        return False, "El recorrido usa una arista inexistente."
    return True, f"Cada uno de los {n} vértices se visita exactamente una vez" + (
        f" y se regresa a {seq[0]} mediante una arista existente." if closed else ".")


def _hamilton_precheck(G: nx.Graph, closed: bool) -> str | None:
    """Condiciones necesarias baratas; devuelve el motivo si ya se descarta la existencia."""
    n, kind = G.number_of_nodes(), ("un ciclo" if closed else "un camino")
    if n == 0:
        return "El grafo no tiene vértices."
    if G.is_directed():
        if closed and n < 2:
            return "Un ciclo dirigido necesita al menos 2 vértices."
        if closed and not nx.is_strongly_connected(G):
            return "El grafo dirigido no es fuertemente conexo: no existe ciclo que pase por todos los vértices."
        if not is_connected(G):
            return f"El grafo está desconectado ({n_components(G)} componentes)."
        return None
    if not is_connected(G):
        return f"El grafo está desconectado ({n_components(G)} componentes)."
    if closed and n < 3:
        return "Un ciclo en un grafo simple necesita al menos 3 vértices."
    if closed:
        low = [v for v in sort_nodes(G) if G.degree(v) < 2]
        if low:
            return f"El vértice {low[0]} tiene grado {G.degree(low[0])} < 2: no puede pertenecer a un ciclo."
    else:
        leaves = [v for v in sort_nodes(G) if G.degree(v) == 1]
        if len(leaves) > 2:
            return f"Hay {len(leaves)} vértices de grado 1 ({', '.join(map(str, leaves))}) y un camino sólo tiene 2 extremos."
    limit = 1 if closed else 2
    for v in sort_nodes(G):
        H = G.copy()
        H.remove_node(v)
        c = nx.number_connected_components(H) if H.number_of_nodes() else 0
        if c > limit:
            return (f"Al quitar el vértice {v} el grafo queda en {c} componentes; {kind} de Hamilton "
                    f"admite como máximo {limit} (condición necesaria violada).")
    return None


def hamilton_search(G: nx.Graph, closed: bool, max_steps: int = 1_000_000) -> PathResult:
    """Busca camino (closed=False) o ciclo (closed=True) de Hamilton por retroceso (backtracking)."""
    why = _hamilton_precheck(G, closed)
    if why:
        return PathResult(False, [], why)
    directed = G.is_directed()
    nbrs = G.successors if directed else G.neighbors
    nodes = sort_nodes(G.nodes)
    n = len(nodes)
    key = lambda x: (G.degree(x), len(str(x)), str(x))  # noqa: E731
    adj = {u: sorted(nbrs(u), key=key) for u in nodes}
    path: list[Node] = []
    seen: set[Node] = set()
    steps = 0

    def dfs(u: Node) -> bool:
        nonlocal steps
        steps += 1
        if steps > max_steps:
            raise _StepLimit
        if len(path) == n:
            return (not closed) or G.has_edge(u, path[0])
        for w in adj[u]:
            if w not in seen:
                seen.add(w)
                path.append(w)
                if dfs(w):
                    return True
                path.pop()
                seen.discard(w)
        return False

    starts = [nodes[0]] if closed else sorted(nodes, key=key)
    try:
        for s in starts:
            path[:] = [s]
            seen.clear()
            seen.add(s)
            if dfs(s):
                seq = list(path) + ([path[0]] if closed else [])
                ok, msg = verify_hamilton(G, seq, closed)
                return PathResult(True, seq, "", ok, msg, steps)
    except _StepLimit:
        return PathResult(None, [], f"Se alcanzó el límite de {max_steps:,} pasos sin hallar solución ni descartarla. "
                                    "Aumente el límite en la barra lateral.", steps=steps)
    kind = "ciclo" if closed else "camino"
    return PathResult(False, [], f"Búsqueda completa por retroceso sin solución ({steps:,} estados explorados): "
                                 f"ningún {kind} visita todos los vértices exactamente una vez.", steps=steps)


# ============================================================================
# 6. ANÁLISIS ESTRUCTURAL
# ============================================================================
def describe_type(G: nx.Graph) -> list[str]:
    """Etiquetas descriptivas del tipo exacto de grafo."""
    n, m, d = G.number_of_nodes(), G.number_of_edges(), G.is_directed()
    if n == 0:
        return ["Vacío"]
    tags = ["Dirigido" if d else "No dirigido", "Ponderado" if is_weighted(G) else "No ponderado"]
    tags.append("Simple" if nx.number_of_selfloops(G) == 0 else "Con lazos")
    if d:
        tags.append("Fuertemente conexo" if nx.is_strongly_connected(G) else
                    "Débilmente conexo" if nx.is_weakly_connected(G) else f"Desconexo ({n_components(G)} comp.)")
        tags.append("Acíclico (DAG)" if nx.is_directed_acyclic_graph(G) else "Con ciclos")
    else:
        tags.append("Conexo" if nx.is_connected(G) else f"Desconexo ({n_components(G)} comp.)")
        if nx.is_tree(G):
            tags.append("Árbol")
        elif nx.is_forest(G):
            tags.append("Bosque")
    if n >= 2 and m == (n * (n - 1) if d else n * (n - 1) // 2):
        tags.append(f"Completo (K{n})")
    if n >= 3 and is_connected(G) and all(G.degree(v) == (2 if not d else 2) for v in G) and m == n:
        tags.append(f"Ciclo (C{n})")
    degs = {G.degree(v) for v in G}
    if len(degs) == 1 and m > 0:
        tags.append(f"Regular (grado {degs.pop()})")
    try:
        if nx.is_bipartite(G):
            tags.append("Bipartito")
    except Exception:
        pass
    return tags


def degree_table(G: nx.Graph) -> pd.DataFrame:
    """Tabla de grados por vértice (con entrada/salida si es dirigido)."""
    cent = nx.degree_centrality(G)
    rows = []
    for v in sort_nodes(G):
        row: dict[str, object] = {"Vértice": v}
        if G.is_directed():
            row.update({"Entrada": G.in_degree(v), "Salida": G.out_degree(v)})
        row["Grado"] = G.degree(v)
        if G.is_directed():
            row["Balance (sal−ent)"] = G.out_degree(v) - G.in_degree(v)
        row["Paridad"] = "impar" if G.degree(v) % 2 else "par"
        row["Centralidad"] = round(cent[v], 3)
        rows.append(row)
    return pd.DataFrame(rows)


def adjacency_df(G: nx.Graph) -> pd.DataFrame:
    """Matriz de adyacencia (con pesos si el grafo es ponderado)."""
    nodes = sort_nodes(G.nodes)
    w = "weight" if is_weighted(G) else None
    A = nx.to_numpy_array(G, nodelist=nodes, weight=w)
    return pd.DataFrame(A if w else A.astype(int), index=nodes, columns=nodes)


def incidence_df(G: nx.Graph) -> pd.DataFrame:
    """Matriz de incidencia vértice×arista (−1 origen / +1 destino si es dirigido)."""
    nodes = sort_nodes(G.nodes)
    edges = list(G.edges)
    idx = {v: i for i, v in enumerate(nodes)}
    M = np.zeros((len(nodes), len(edges)), dtype=int)
    for j, (u, v) in enumerate(edges):
        if G.is_directed():
            M[idx[u], j], M[idx[v], j] = -1, 1
        else:
            M[idx[u], j] = M[idx[v], j] = 1
    sep = "→" if G.is_directed() else "–"
    return pd.DataFrame(M, index=nodes, columns=[f"{u}{sep}{v}" for u, v in edges])


def cycle_info(G: nx.Graph) -> dict[str, object]:
    """Detecta ciclos y devuelve un ejemplo y datos complementarios."""
    out: dict[str, object] = {"has_cycle": False, "example": None, "detail": "", "basis": []}
    try:
        cyc = nx.find_cycle(G)
        out.update(has_cycle=True, example=[e[0] for e in cyc] + [cyc[0][0]])
    except nx.NetworkXNoCycle:
        pass
    if G.is_directed():
        k = len(list(itertools.islice(nx.simple_cycles(G), 200)))
        out["detail"] = ("Es un DAG (grafo dirigido acíclico)." if k == 0 else
                         f"Ciclos simples encontrados: {'200 o más' if k >= 200 else k}.")
    else:
        mu = G.number_of_edges() - G.number_of_nodes() + nx.number_connected_components(G)
        out["detail"] = f"Número ciclomático μ = m − n + c = {mu}: hay {mu} ciclo(s) independiente(s)."
        out["basis"] = nx.cycle_basis(G)
    return out


def is_planar(G: nx.Graph) -> bool | None:
    """Planaridad (se ignora la dirección). None si no se pudo evaluar."""
    try:
        return bool(nx.check_planarity(G.to_undirected())[0])
    except Exception:
        return None


def get_analysis(G: nx.Graph, budget: int) -> tuple[PathResult, PathResult, PathResult, PathResult]:
    """(camino Euler, ciclo Euler, camino Hamilton, ciclo Hamilton), memorizado por firma del grafo."""
    memo = SS.memo
    key = (signature(G), budget)
    if key not in memo:
        if len(memo) > 40:
            memo.clear()
        ep, ec = euler_analysis(G)
        memo[key] = (ep, ec, hamilton_search(G, False, budget), hamilton_search(G, True, budget))
    return memo[key]


# ============================================================================
# 7. VISUALIZACIÓN
# ============================================================================
def compute_layout(G: nx.Graph, layout: str, seed: int) -> dict[Node, np.ndarray]:
    """Posiciones de los vértices según la disposición elegida."""
    if layout == "Circular":
        return nx.circular_layout(G)
    if layout == "Shell":
        return nx.shell_layout(G)
    if layout == "Aleatorio":
        return nx.random_layout(G, seed=seed)
    if layout == "Kamada-Kawai":
        try:
            return nx.kamada_kawai_layout(G)
        except Exception:
            pass
    return nx.spring_layout(G, seed=seed, k=1.4 / math.sqrt(max(G.number_of_nodes(), 1)))


def _walk_order(G: nx.Graph, walk: list[Node] | None) -> dict[Hashable, list[int]]:
    order: dict[Hashable, list[int]] = {}
    for k, (u, v) in enumerate(zip(walk or [], (walk or [])[1:]), 1):
        order.setdefault(edge_key(G, u, v), []).append(k)
    return order


def draw_graph_mpl(G: nx.Graph, layout: str = LAYOUTS[0], seed: int = 7,
                   walk: list[Node] | None = None, show_weights: bool = True) -> plt.Figure:
    """Dibuja el grafo con Matplotlib: flechas, pesos y recorrido resaltado con su orden."""
    fig, ax = plt.subplots(figsize=(8, 5.6), dpi=110)
    fig.patch.set_facecolor(C_PANEL)
    ax.set_facecolor(C_PANEL)
    ax.axis("off")
    n, directed = G.number_of_nodes(), G.is_directed()
    pos = compute_layout(G, layout, seed)
    size = 1000 if n <= 12 else 650 if n <= 25 else 380
    order = _walk_order(G, walk)

    def draw_edges(edgelist: list[tuple[Node, Node]], color: str, width: float) -> None:
        if not edgelist:
            return
        if not directed:
            nx.draw_networkx_edges(G, pos, ax=ax, edgelist=edgelist, edge_color=color, width=width)
            return
        both = [e for e in edgelist if G.has_edge(e[1], e[0])]
        single = [e for e in edgelist if not G.has_edge(e[1], e[0])]
        for lst, rad in ((single, 0.0), (both, 0.22)):
            if lst:
                nx.draw_networkx_edges(G, pos, ax=ax, edgelist=lst, edge_color=color, width=width, arrows=True,
                                       arrowstyle="-|>", arrowsize=22, node_size=size,
                                       connectionstyle=f"arc3,rad={rad}")

    base = [e for e in G.edges if edge_key(G, *e) not in order]
    hi = [e for e in G.edges if edge_key(G, *e) in order]
    draw_edges(base, C_EDGE, 1.8)
    draw_edges(hi, C_HILITE, 3.6)
    colors = [C_START if (walk and v == walk[0]) else C_NODE for v in G.nodes]
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=size, node_color=colors, edgecolors="#0f172a", linewidths=1.4)
    nx.draw_networkx_labels(G, pos, ax=ax, font_color="white", font_weight="bold", font_size=11 if n <= 25 else 8)
    labels: dict[tuple[Node, Node], str] = {}
    for u, v, d in G.edges(data=True):
        parts = []
        if order.get(edge_key(G, u, v)):
            parts.append("#" + ",".join(map(str, order[edge_key(G, u, v)])))
        if show_weights and "weight" in d:
            parts.append(f"{d['weight']:g}")
        if parts:
            labels[(u, v)] = " · ".join(parts)
    if labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, ax=ax, font_size=8, rotate=False,
                                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))
    fig.tight_layout()
    return fig


def pyvis_html(G: nx.Graph, walk: list[Node] | None = None) -> str:
    """HTML interactivo (PyVis) con aristas resaltadas para el recorrido."""
    if Network is None:
        raise RuntimeError("PyVis no está instalado.")
    net = Network(height="580px", width="100%", directed=G.is_directed(), bgcolor=C_PANEL,
                  font_color="#0f172a", cdn_resources="in_line")
    for v in G.nodes:
        net.add_node(str(v), label=str(v), title=f"Grado: {G.degree(v)}",
                     color=C_START if (walk and v == walk[0]) else C_NODE, font={"color": "#ffffff"})
    order = _walk_order(G, walk)
    for u, v, d in G.edges(data=True):
        k = order.get(edge_key(G, u, v))
        opts: dict[str, object] = {"color": C_HILITE if k else C_EDGE, "width": 4 if k else 2}
        parts = ([f"#{','.join(map(str, k))}"] if k else []) + ([f"{d['weight']:g}"] if "weight" in d else [])
        if parts:
            opts["label"] = " · ".join(parts)
        net.add_edge(str(u), str(v), **opts)
    net.set_options('{"physics":{"stabilization":{"iterations":150}},"edges":{"font":{"size":12,"align":"middle"}}}')
    return net.generate_html()


# ============================================================================
# 8. VISIÓN POR COMPUTADOR (OpenCV)
# ============================================================================
@dataclass
class DetectParams:
    """Parámetros ajustables de la detección geométrica."""

    min_radius: int
    max_radius: int
    sensitivity: int
    coverage: float
    adaptive: bool
    directed: bool


def load_image(data: bytes) -> np.ndarray:
    """Decodifica bytes a RGB (corrige orientación EXIF) y limita el tamaño."""
    if not data:
        raise ValueError("El archivo está vacío.")
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    except Exception as exc:
        raise ValueError("No se pudo leer la imagen: el archivo está dañado o no es PNG/JPG.") from exc
    arr = np.array(img)
    if arr.ndim != 3 or min(arr.shape[:2]) < 60:
        raise ValueError("La imagen es demasiado pequeña (mínimo 60 px por lado).")
    scale = MAX_IMG_DIM / max(arr.shape[:2])
    if scale < 1:
        arr = cv2.resize(arr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return arr


def preprocess(rgb: np.ndarray, adaptive: bool) -> tuple[np.ndarray, np.ndarray]:
    """Escala de grises + desenfoque + binarización. Devuelve (gris suavizado, binaria con tinta=255)."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    if adaptive:
        binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 35, 12)
    else:
        _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if binary.mean() > 127:  # fondo oscuro: la tinta es la clase minoritaria
        binary = cv2.bitwise_not(binary)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return blur, binary


def detect_nodes(blur: np.ndarray, binary: np.ndarray, p: DetectParams) -> list[tuple[float, float, float]]:
    """Detecta nodos: círculos huecos (Hough) y discos rellenos (contornos circulares)."""
    found: list[tuple[float, float, float]] = []
    circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, dp=1.2, minDist=max(p.min_radius * 1.6, 10),
                               param1=110, param2=p.sensitivity, minRadius=p.min_radius, maxRadius=p.max_radius)
    if circles is not None:
        found += [(float(x), float(y), float(r)) for x, y, r in circles[0][:80]]
    k = max(3, int(p.min_radius * 1.2)) | 1
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    for c in cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]:
        area, per = cv2.contourArea(c), cv2.arcLength(c, True)
        if per == 0 or area < math.pi * (p.min_radius * 0.8) ** 2:
            continue
        (x, y), r = cv2.minEnclosingCircle(c)
        if 4 * math.pi * area / per**2 >= 0.72 and p.min_radius * 0.8 <= r <= p.max_radius * 1.3:
            if all(math.hypot(x - fx, y - fy) > 0.8 * max(r, fr) for fx, fy, fr in found):
                found.append((float(x), float(y), float(r)))
    if found:
        row_h = max(1, int(np.median([r for *_, r in found]) * 2))
        found.sort(key=lambda t: (int(t[1] // row_h), t[0]))  # orden de lectura
    return found


def _dist_to_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _ink_density(img: np.ndarray, cx: float, cy: float, rad: float) -> float:
    h, w = img.shape
    x0, x1, y0, y1 = max(int(cx - rad), 0), min(int(cx + rad) + 1, w), max(int(cy - rad), 0), min(int(cy + rad) + 1, h)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    yy, xx = np.ogrid[y0:y1, x0:x1]
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= rad**2
    return float((img[y0:y1, x0:x1][mask] > 0).mean()) if mask.any() else 0.0


def detect_edges(binary: np.ndarray, nodes: list[tuple[float, float, float]], p: DetectParams) -> list[tuple[int, int, float]]:
    """Detecta aristas rectas: para cada par de nodos mide la tinta a lo largo del segmento que los une."""
    h, w = binary.shape
    lines = binary.copy()
    for x, y, r in nodes:
        cv2.circle(lines, (int(x), int(y)), int(r * 1.25) + 1, 0, -1)  # borra nodos y etiquetas
    tol = cv2.dilate(lines, np.ones((3, 3), np.uint8))
    edges: list[tuple[int, int, float]] = []
    for i, j in itertools.combinations(range(len(nodes)), 2):
        (x1, y1, r1), (x2, y2, r2) = nodes[i], nodes[j]
        d = math.hypot(x2 - x1, y2 - y1)
        s, e = r1 * 1.25 + 3, d - r2 * 1.25 - 3
        if e - s < 4:
            continue
        if any(k not in (i, j) and _dist_to_segment(nodes[k][0], nodes[k][1], x1, y1, x2, y2) < nodes[k][2] * 1.15
               for k in range(len(nodes))):
            continue  # un tercer nodo bloquea el segmento
        ux, uy = (x2 - x1) / d, (y2 - y1) / d
        ts = np.linspace(s, e, max(int(e - s) // 2, 3))
        xs = np.clip((x1 + ux * ts).astype(int), 0, w - 1)
        ys = np.clip((y1 + uy * ts).astype(int), 0, h - 1)
        cov = float((tol[ys, xs] > 0).mean())
        if cov < p.coverage:
            continue
        a, b = i, j
        if p.directed:  # la punta de flecha engrosa la tinta cerca del nodo destino
            rad = max(5.0, 0.5 * min(r1, r2))
            di = _ink_density(lines, x1 + ux * (s + rad), y1 + uy * (s + rad), rad)
            dj = _ink_density(lines, x2 - ux * (d - e + rad), y2 - uy * (d - e + rad), rad)
            if di - dj > 0.08:
                a, b = j, i
        edges.append((a, b, cov))
    return edges


def tables_from_detection(nodes: list[tuple[float, float, float]], edges: list[tuple[int, int, float]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convierte la detección en tablas editables (vértices y aristas)."""
    labels = [label_for(i) for i in range(len(nodes))]
    ndf = pd.DataFrame({"label": labels, "x": [round(n[0], 1) for n in nodes],
                        "y": [round(n[1], 1) for n in nodes], "r": [round(n[2], 1) for n in nodes]})
    edf = pd.DataFrame([(labels[a], labels[b], np.nan) for a, b, _ in edges], columns=["source", "target", "weight"])
    edf["weight"] = edf["weight"].astype(float)
    return ndf, edf


def draw_overlay(rgb: np.ndarray, ndf: pd.DataFrame, edf: pd.DataFrame, directed: bool) -> np.ndarray:
    """Superpone sobre la imagen original lo que el programa entendió."""
    img = rgb.copy()
    pts: dict[str, tuple[float, float, float]] = {}
    for _, row in ndf.iterrows():
        lab = _clean(row.get("label"))
        if lab and pd.notna(row.get("x")) and pd.notna(row.get("y")):
            pts[lab] = (float(row["x"]), float(row["y"]), float(row["r"]) if pd.notna(row.get("r")) else 15.0)
    for _, row in edf.iterrows():
        a, b = pts.get(_clean(row.get("source"))), pts.get(_clean(row.get("target")))
        if a and b:
            d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
            p1 = (int(a[0] + ux * a[2]), int(a[1] + uy * a[2]))
            p2 = (int(b[0] - ux * b[2]), int(b[1] - uy * b[2]))
            if directed:
                cv2.arrowedLine(img, p1, p2, (220, 38, 38), 3, tipLength=0.06)
            else:
                cv2.line(img, p1, p2, (220, 38, 38), 3)
    for lab, (x, y, r) in pts.items():
        cv2.circle(img, (int(x), int(y)), int(r), (22, 163, 74), 3)
        cv2.putText(img, lab, (int(x - r * 0.5), int(y + r * 0.35)), cv2.FONT_HERSHEY_SIMPLEX,
                    max(0.5, r / 28), (30, 64, 175), 2, cv2.LINE_AA)
    return img


AI_PROMPT = (
    "Analiza esta imagen de un grafo (nodos y aristas dibujados). Responde ÚNICAMENTE con JSON válido, sin texto "
    'adicional ni bloques de código, con este esquema: {"directed": true|false, "nodes": ["A","B"], '
    '"edges": [{"source": "A", "target": "B", "weight": null}]}. Usa las etiquetas visibles en los nodos; si no hay, '
    "usa A, B, C... Incluye 'weight' sólo si hay un número junto a la arista; si no, null. No inventes aristas."
)


def analyze_with_claude(rgb: np.ndarray, api_key: str) -> dict:
    """Fallback multimodal: pide a Claude la estructura del grafo y la devuelve como dict."""
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("Instale el SDK con: pip install anthropic") from exc
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="JPEG", quality=90)
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"), max_tokens=2000,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                         "data": base64.b64encode(buf.getvalue()).decode()}},
            {"type": "text", "text": AI_PROMPT}]}])
    text = "".join(getattr(b, "text", "") for b in msg.content)
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < a:
        raise RuntimeError("La respuesta del modelo no contiene JSON.")
    return json.loads(text[a:b + 1])



# ============================================================================
# 9. SESIÓN, TEMA Y COMPONENTES DE INTERFAZ
# ============================================================================
BUDGETS = [100_000, 500_000, 1_000_000, 3_000_000, 10_000_000]


class Session:
    """Estado compartido de la aplicación (equivale al antiguo st.session_state)."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.graph: nx.Graph = PRESETS[0].build()
        self.graph_name: str = PRESETS[0].name
        self.budget: int = 1_000_000
        self.memo: dict = {}


SS = Session()

# Tema inspirado en el dashboard "Finexy": fondo gris claro, tarjetas blancas,
# azul marino para lo activo y naranja como acento.
UI_BG, UI_CARD, UI_NAVY = "#f3f4f6", "#ffffff", "#1e293b"
UI_ORANGE, UI_TEXT, UI_MUTED, UI_LINE = "#ff5722", "#111827", "#6b7280", "#e5e7eb"
UI_TINT, UI_SOFT = "#ffe3d3", "#f9fafb"
FONT, MONO = "Segoe UI", "Consolas"
BANNER = {  # tipo → (fondo, texto, icono)
    "success": ("#dcfce7", "#166534", "✔"),
    "error": ("#fee2e2", "#991b1b", "✖"),
    "warning": ("#fef3c7", "#92400e", "⚠"),
    "info": ("#dbeafe", "#1e40af", "ℹ"),
}
SUBTITLE = "Caminos y ciclos de Euler y Hamilton, métricas de grafos y reconocimiento desde imágenes"


def F(size: int = 12, weight: str = "normal", mono: bool = False) -> ctk.CTkFont:
    return ctk.CTkFont(family=MONO if mono else FONT, size=size, weight=weight)


def init_styles() -> None:
    """Estilo de las tablas (ttk.Treeview) acorde al tema."""
    st = ttk.Style()
    st.theme_use("clam")
    st.configure("Graph.Treeview", background=UI_CARD, fieldbackground=UI_CARD, foreground=UI_TEXT,
                 rowheight=30, borderwidth=0, font=(FONT, 10))
    st.configure("Graph.Treeview.Heading", background=UI_BG, foreground=UI_TEXT, font=(FONT, 10, "bold"),
                 relief="flat", borderwidth=0, padding=(8, 7))
    st.map("Graph.Treeview", background=[("selected", UI_TINT)], foreground=[("selected", UI_TEXT)])
    st.map("Graph.Treeview.Heading", background=[("active", UI_LINE)])
    st.layout("Graph.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])


def card(parent, **kw) -> ctk.CTkFrame:
    return ctk.CTkFrame(parent, fg_color=UI_CARD, corner_radius=14, **kw)


def heading(parent, text: str, size: int = 14) -> ctk.CTkLabel:
    return ctk.CTkLabel(parent, text=text, font=F(size, "bold"), text_color=UI_TEXT, anchor="w")


def hr(parent) -> ctk.CTkFrame:
    fr = ctk.CTkFrame(parent, height=1, fg_color=UI_LINE)
    fr.pack(fill="x", pady=14)
    return fr


def labeled(parent, text: str) -> ctk.CTkFrame:
    fr = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(fr, text=text, font=F(11), text_color=UI_MUTED, anchor="w").pack(anchor="w", pady=(0, 3))
    return fr


def btn(parent, text: str, command, primary: bool = True, width: int = 0) -> ctk.CTkButton:
    kw = dict(width=width) if width else {}
    if primary:
        return ctk.CTkButton(parent, text=text, command=command, height=38, corner_radius=10, font=F(12, "bold"),
                             fg_color=UI_NAVY, hover_color="#0f172a", text_color="white", **kw)
    return ctk.CTkButton(parent, text=text, command=command, height=38, corner_radius=10, font=F(12),
                         fg_color=UI_LINE, hover_color="#d1d5db", text_color=UI_TEXT, **kw)


def entry(parent, value: str = "", width: int = 0, **kw) -> ctk.CTkEntry:
    e = ctk.CTkEntry(parent, height=34, corner_radius=8, fg_color=UI_SOFT, border_color=UI_LINE,
                     text_color=UI_TEXT, font=F(12), **({"width": width} if width else {}), **kw)
    if value:
        e.insert(0, value)
    return e


def menu(parent, values: list[str], command=None, width: int = 200) -> ctk.CTkOptionMenu:
    return ctk.CTkOptionMenu(parent, values=values or [""], command=command, width=width, height=34, corner_radius=8,
                             fg_color=UI_BG, button_color=UI_LINE, button_hover_color="#d1d5db", text_color=UI_TEXT,
                             font=F(12), dropdown_font=F(12), dropdown_fg_color=UI_CARD,
                             dropdown_text_color=UI_TEXT, dropdown_hover_color=UI_TINT)


def switch(parent, text: str, command=None, on: bool = False) -> ctk.CTkSwitch:
    sw = ctk.CTkSwitch(parent, text=text, command=command, font=F(12), text_color=UI_TEXT,
                       progress_color=UI_ORANGE, button_color=UI_CARD, button_hover_color=UI_SOFT)
    if on:
        sw.select()
    return sw


def checkbox(parent, text: str, command=None, on: bool = False) -> ctk.CTkCheckBox:
    cb = ctk.CTkCheckBox(parent, text=text, command=command, font=F(12), text_color=UI_TEXT, fg_color=UI_NAVY,
                         hover_color=UI_NAVY, checkbox_width=20, checkbox_height=20, corner_radius=5)
    if on:
        cb.select()
    return cb


def style_pill(b: ctk.CTkButton, active: bool) -> None:
    b.configure(fg_color=UI_NAVY if active else "transparent", text_color="white" if active else UI_MUTED,
                hover_color=UI_NAVY if active else UI_BG)


def pill(parent, text: str, command) -> ctk.CTkButton:
    b = ctk.CTkButton(parent, text=text, command=command, height=34, corner_radius=17, font=F(12), border_width=0)
    style_pill(b, False)
    return b


def fig_to_ctk(fig: plt.Figure, width: int) -> ctk.CTkImage:
    """Convierte una figura de Matplotlib en imagen para la interfaz (y la cierra)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, facecolor=fig.get_facecolor())
    plt.close(fig)
    img = Image.open(buf).convert("RGB")
    w, h = img.size
    return ctk.CTkImage(light_image=img, dark_image=img, size=(width, max(1, int(h * width / w))))


def np_to_ctk(arr: np.ndarray, max_w: int, max_h: int) -> ctk.CTkImage:
    """Convierte un arreglo (RGB o gris) en imagen escalada para la interfaz."""
    img = Image.fromarray(arr).convert("RGB")
    w, h = img.size
    s = min(max_w / w, max_h / h, 1.0)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(max(1, int(w * s)), max(1, int(h * s))))


class WrapLabel(ctk.CTkLabel):
    """Etiqueta que ajusta su salto de línea al ancho del contenedor."""

    def __init__(self, master, text: str = "", pad: int = 24, **kw) -> None:
        kw.setdefault("justify", "left")
        kw.setdefault("anchor", "w")
        super().__init__(master, text=text, **kw)
        self._pad, self._wl = pad, 0
        master.bind("<Configure>", self._fit, add="+")

    def _fit(self, e) -> None:
        try:
            scale = self._get_widget_scaling()
        except Exception:
            scale = 1.0
        w = int(e.width / scale) - self._pad
        if w > 80 and abs(w - self._wl) > 4:
            self._wl = w
            try:
                self.configure(wraplength=w)
            except tk.TclError:
                pass


def caption(parent, text: str, pad: int = 24) -> WrapLabel:
    return WrapLabel(parent, text=text, pad=pad, font=F(11), text_color=UI_MUTED)


def banner(parent, kind: str, title: str = "", text: str = "") -> ctk.CTkFrame:
    """Aviso de color (equivale a st.success / st.error / st.warning / st.info)."""
    bg, fg, icon = BANNER[kind]
    fr = ctk.CTkFrame(parent, fg_color=bg, corner_radius=10)
    if title:
        WrapLabel(fr, text=f"{icon}  {title}", pad=28, font=F(12, "bold"), text_color=fg).pack(
            fill="x", padx=14, pady=(8, 2 if text else 8))
        if text:
            WrapLabel(fr, text=text, pad=28, font=F(12), text_color=fg).pack(fill="x", padx=14, pady=(0, 8))
    else:
        WrapLabel(fr, text=f"{icon}  {text}", pad=28, font=F(12), text_color=fg).pack(fill="x", padx=14, pady=8)
    return fr


class MsgArea(ctk.CTkFrame):
    """Zona donde se muestran avisos que se reemplazan en cada acción."""

    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent", width=0, height=0)

    def clear(self) -> None:
        for w in self.winfo_children():
            w.destroy()

    def show(self, kind: str, title: str = "", text: str = "") -> None:
        self.clear()
        banner(self, kind, title, text).pack(fill="x", pady=(8, 2))

    def show_errors(self, exc: Exception) -> None:
        """Muestra errores de validación de forma amistosa (uno por línea)."""
        self.show("error", "No se pudo procesar la entrada:", "\n".join(f"• {line}" for line in str(exc).splitlines()))


def seq_box(parent, text: str) -> ctk.CTkFrame:
    """Secuencia de vértices resaltada (equivale a la clase CSS .seq)."""
    fr = ctk.CTkFrame(parent, fg_color="#fff1e6", corner_radius=8, border_width=1, border_color="#f3b183")
    WrapLabel(fr, text=text, pad=28, font=F(12, mono=True), text_color=UI_TEXT).pack(fill="x", padx=12, pady=9)
    return fr


def code_box(parent, text: str) -> ctk.CTkFrame:
    fr = ctk.CTkFrame(parent, fg_color=UI_BG, corner_radius=8)
    WrapLabel(fr, text=text, pad=28, font=F(12, mono=True), text_color=UI_TEXT).pack(fill="x", padx=12, pady=7)
    return fr


class Busy(ctk.CTkFrame):
    """Indicador de trabajo en curso (equivale a st.spinner)."""

    def __init__(self, master, text: str) -> None:
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text=text, font=F(12), text_color=UI_MUTED).pack(side="left", padx=(4, 10))
        bar = ctk.CTkProgressBar(self, mode="indeterminate", width=150, progress_color=UI_ORANGE)
        bar.pack(side="left")
        bar.start()


class StatCard(ctk.CTkFrame):
    """Tarjeta de métrica (equivale a st.metric)."""

    def __init__(self, master, title: str, value: object = "", sub: str = "", highlight: bool = False) -> None:
        if highlight:
            super().__init__(master, fg_color=UI_ORANGE, corner_radius=14)
        else:
            super().__init__(master, fg_color=UI_CARD, corner_radius=14, border_width=1, border_color=UI_LINE)
        fg, mu = ("white", "#ffe0d6") if highlight else (UI_TEXT, UI_MUTED)
        ctk.CTkLabel(self, text=title, font=F(11), text_color=mu, anchor="w").pack(fill="x", padx=14, pady=(10, 0))
        self.v = WrapLabel(self, text=str(value), pad=28, font=F(20, "bold"), text_color=fg)
        self.v.pack(fill="x", padx=14)
        self.s = WrapLabel(self, text=sub, pad=28, font=F(10), text_color=mu)
        self.s.pack(fill="x", padx=14, pady=(0, 10))

    def set(self, value: object, sub: str = "") -> None:
        self.v.configure(text=str(value))
        self.s.configure(text=sub)


class ChipFlow(ctk.CTkFrame):
    """Etiquetas (chips) que fluyen y saltan de línea según el ancho disponible."""

    def __init__(self, master, tags: Iterable[str] = ()) -> None:
        super().__init__(master, fg_color="transparent", height=30)
        self.chips: list[ctk.CTkLabel] = []
        self._last_w = 0                      
        self.bind("<Configure>", self._layout, add="+")
        self.set_tags(tags)

    def set_tags(self, tags: Iterable[str]) -> None:
        for c in self.chips:
            c.destroy()
        self.chips = [ctk.CTkLabel(self, text=f" {t} ", font=F(11), text_color="#1e3a5f", fg_color="#e3e9f1",
                                   corner_radius=6, height=26) for t in tags]
        self._last_w = 0                      
        self._layout()

    def _layout(self, _e=None) -> None:
        w = self.winfo_width()
        if w <= 1 or w == self._last_w:       
            return
        self._last_w = w                      
        x = y = rowh = 0
        for c in self.chips:
            c.update_idletasks()
            cw, ch = c.winfo_reqwidth() + 8, c.winfo_reqheight() + 6
            if x + cw > w and x > 0:
                x, y, rowh = 0, y + rowh, 0
            c.place(x=x, y=y)
            x, rowh = x + cw, max(rowh, ch)
        self.configure(height=max(30, y + rowh))


class Collapsible(ctk.CTkFrame):
    """Panel desplegable (equivale a st.expander)."""

    def __init__(self, master, title: str, open_: bool = False) -> None:
        super().__init__(master, fg_color=UI_SOFT, corner_radius=12, border_width=1, border_color=UI_LINE)
        self.title, self.open = title, open_
        self.head = ctk.CTkButton(self, text="", anchor="w", fg_color="transparent", hover_color=UI_BG,
                                  text_color=UI_TEXT, font=F(12, "bold"), height=34, command=self.toggle)
        self.head.pack(fill="x", padx=6, pady=4)
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self._sync()

    def toggle(self) -> None:
        self.open = not self.open
        self._sync()

    def _sync(self) -> None:
        self.head.configure(text=("▾  " if self.open else "▸  ") + self.title)
        if self.open:
            self.body.pack(fill="x", padx=14, pady=(0, 12))
        else:
            self.body.pack_forget()


class LabeledSlider(ctk.CTkFrame):
    """Deslizador con título y valor visible (equivale a st.slider)."""

    def __init__(self, master, label: str, lo, hi, value, step=1, command=None) -> None:
        super().__init__(master, fg_color="transparent")
        self.lo, self.hi, self.step, self.cmd = lo, hi, step, command
        self.is_int = isinstance(lo, int) and isinstance(step, int)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")
        self.title = ctk.CTkLabel(top, text=label, font=F(11), text_color=UI_MUTED, anchor="w")
        self.title.pack(side="left")
        self.val = ctk.CTkLabel(top, text="", font=F(12, "bold"), text_color=UI_ORANGE)
        self.val.pack(side="right")
        #icono
        self.iconbitmap("img/logo_umg.ico")
        self.slider = ctk.CTkSlider(self, from_=lo, to=hi, number_of_steps=max(1, int(round((hi - lo) / step))),
                                    command=self._moved, progress_color=UI_ORANGE, button_color=UI_NAVY,
                                    button_hover_color="#0f172a")
        self.slider.pack(fill="x", pady=(4, 0))
        self.set(value)

        

    def _snap(self, raw: float):
        v = self.lo + round((raw - self.lo) / self.step) * self.step
        return int(v) if self.is_int else round(v, 4)

    def _fmt(self, v) -> str:
        return f"{v:d}" if self.is_int else f"{v:.2f}"

    def get(self):
        return self._snap(self.slider.get())

    def set(self, value) -> None:
        self.slider.set(value)
        self.val.configure(text=self._fmt(self.get()))

    def _moved(self, raw: float) -> None:
        self.val.configure(text=self._fmt(self._snap(raw)))
        if self.cmd:
            self.cmd(self.get())

    def enable(self, on: bool) -> None:
        self.slider.configure(state="normal" if on else "disabled")
        self.title.configure(text_color=UI_MUTED if on else "#c4c8ce")
        self.val.configure(text_color=UI_ORANGE if on else "#c4c8ce")


def bind_wheel(tree: ttk.Treeview) -> None:
    """Hace que la rueda del ratón desplace la tabla (y no la página) mientras está encima."""
    def up_down(delta: int):
        def _h(_e):
            tree.yview_scroll(delta, "units")
            return "break"
        return _h

    tree.bind("<MouseWheel>", lambda e: up_down(-1 if e.delta > 0 else 1)(e))
    tree.bind("<Button-4>", up_down(-1))
    tree.bind("<Button-5>", up_down(1))


def _fmt_cell(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, (float, np.floating)):
        if math.isnan(v):
            return ""
        return str(int(v)) if float(v).is_integer() else f"{v:g}"
    return str(v)


class DataTable(ctk.CTkFrame):
    """Tabla de sólo lectura (equivale a st.dataframe)."""

    ROW_H = 30

    def __init__(self, master, df: pd.DataFrame, index: bool = False, max_rows: int = 10,
                 highlight: Callable[[dict], bool] | None = None, center: bool = False) -> None:
        super().__init__(master, fg_color="transparent")
        cols = ([str(df.index.name or "")] if index else []) + [str(c) for c in df.columns]
        rows, hl = [], []
        for t in df.itertuples(index=True, name=None):
            vals = list(t) if index else list(t[1:])
            rows.append([_fmt_cell(v) for v in vals])
            hl.append(bool(highlight(dict(zip(df.columns, t[1:])))) if highlight else False)
        n = len(rows)
        scroll_y = n > max_rows
        scroll_x = len(cols) > 7
        height = (min(max(n, 1), max_rows) + 1) * self.ROW_H + (16 if scroll_x else 0) + 4
        holder = tk.Frame(self, bg=UI_CARD, height=height, width=100, highlightthickness=1, highlightbackground=UI_LINE)
        holder.pack(fill="x")
        holder.grid_propagate(False)
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)
        tree = ttk.Treeview(holder, style="Graph.Treeview", columns=[f"c{i}" for i in range(len(cols))],
                            show="headings", selectmode="browse")
        font = tkfont.Font(family=FONT, size=10)
        for i, name in enumerate(cols):
            width = max([font.measure(name) + 34] + [font.measure(r[i]) + 24 for r in rows[:200]] + [56])
            first = i == 0 and not center
            tree.heading(f"c{i}", text=name, anchor="w" if first or not center else "center")
            tree.column(f"c{i}", width=width, minwidth=44, anchor="w" if not center or (index and i == 0) else "center",
                        stretch=True)
        tree.tag_configure("hl", background=UI_TINT)
        for r, h in zip(rows, hl):
            tree.insert("", "end", values=r, tags=("hl",) if h else ())
        tree.grid(row=0, column=0, sticky="nsew")
        if scroll_y:
            vsb = ctk.CTkScrollbar(holder, command=tree.yview, width=12)
            vsb.grid(row=0, column=1, sticky="ns")
            tree.configure(yscrollcommand=vsb.set)
            bind_wheel(tree)
        if scroll_x:
            hsb = ctk.CTkScrollbar(holder, command=tree.xview, orientation="horizontal", height=12)
            hsb.grid(row=1, column=0, sticky="ew")
            tree.configure(xscrollcommand=hsb.set)


class EditableTable(ctk.CTkFrame):
    """Tabla editable con filas dinámicas (equivale a st.data_editor con num_rows='dynamic').

    Doble clic sobre una celda para editarla; Enter confirma y Esc cancela.
    """

    def __init__(self, master, title: str, columns: list[str], headings: list[str], numeric: Iterable[str],
                 on_change: Callable[[], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self.columns, self.numeric, self.on_change = list(columns), set(numeric), on_change
        self.rows: list[list[str]] = []
        self._entry: tuple | None = None
        heading(self, title, 13).pack(anchor="w", pady=(0, 4))
        holder = tk.Frame(self, bg=UI_CARD, height=190, width=100, highlightthickness=1, highlightbackground=UI_LINE)
        holder.pack(fill="x")
        holder.grid_propagate(False)
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(holder, style="Graph.Treeview", columns=self.columns, show="headings",
                                 selectmode="extended")
        for c, h in zip(self.columns, headings):
            self.tree.heading(c, text=h, anchor="w")
            self.tree.column(c, width=70, minwidth=44, anchor="w", stretch=True)
        vsb = ctk.CTkScrollbar(holder, command=self.tree.yview, width=12)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        bind_wheel(self.tree)
        self.tree.bind("<Double-1>", self._edit)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(6, 0))
        btn(bar, "+ Agregar fila", self.add_row, primary=False, width=120).pack(side="left", padx=(0, 6))
        btn(bar, "− Eliminar selección", self.delete_selected, primary=False, width=150).pack(side="left")

    # -- datos ---------------------------------------------------------------
    def set_df(self, df: pd.DataFrame) -> None:
        self._close_entry(False)
        self.rows = [[_fmt_cell(v) for v in t] for t in df[self.columns].itertuples(index=False, name=None)]
        self._render()

    def get_df(self) -> pd.DataFrame:
        df = pd.DataFrame({c: [r[i] for r in self.rows] for i, c in enumerate(self.columns)}, columns=self.columns)
        for c in self.numeric:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
        return df

    def _render(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.rows):
            self.tree.insert("", "end", iid=str(i), values=r)

    # -- edición -------------------------------------------------------------
    def add_row(self) -> None:
        self._close_entry(True)
        self.rows.append(["" for _ in self.columns])
        self._render()
        last = str(len(self.rows) - 1)
        self.tree.selection_set(last)
        self.tree.see(last)

    def delete_selected(self) -> None:
        self._close_entry(False)
        idx = sorted((int(i) for i in self.tree.selection()), reverse=True)
        if not idx:
            return
        for i in idx:
            del self.rows[i]
        self._render()
        self.on_change()

    def _edit(self, ev) -> None:
        if self.tree.identify_region(ev.x, ev.y) != "cell":
            return
        iid, col = self.tree.identify_row(ev.y), self.tree.identify_column(ev.x)
        bbox = self.tree.bbox(iid, col) if iid else None
        if not bbox:
            return
        self._close_entry(True)
        ri, ci = int(iid), int(col[1:]) - 1
        x, y, w, h = bbox
        e = tk.Entry(self.tree, font=(FONT, 10), relief="flat", highlightthickness=1,
                     highlightbackground=UI_ORANGE, highlightcolor=UI_ORANGE)
        e.insert(0, self.rows[ri][ci])
        e.select_range(0, "end")
        e.place(x=x, y=y, width=w, height=h)
        e.focus_set()
        self._entry = (e, ri, ci)
        e.bind("<Return>", lambda _e: self._close_entry(True))
        e.bind("<Escape>", lambda _e: self._close_entry(False))
        e.bind("<FocusOut>", lambda _e: self._close_entry(True))

    def _close_entry(self, commit: bool) -> None:
        if not self._entry:
            return
        e, ri, ci = self._entry
        self._entry = None
        val = e.get().strip()
        e.destroy()
        if commit and ri < len(self.rows) and val != self.rows[ri][ci]:
            self.rows[ri][ci] = val
            self.tree.item(str(ri), values=self.rows[ri])
            self.on_change()


class Tabs(ctk.CTkFrame):
    """Pestañas en forma de píldora con contenido perezoso (equivale a st.tabs)."""

    def __init__(self, master, items: list[tuple[str, Callable[[ctk.CTkFrame], None]]], start: str | None = None,
                 on_select: Callable[[str], None] | None = None) -> None:
        super().__init__(master, fg_color="transparent")
        self.items = dict(items)
        self.buttons: dict[str, ctk.CTkButton] = {}
        self.frames: dict[str, ctk.CTkFrame] = {}
        self.built: set[str] = set()
        self.current: str | None = None
        self.on_select = on_select
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 10))
        for name in self.items:
            b = pill(bar, name, lambda n=name: self.select(n))
            b.pack(side="left", padx=(0, 4))
            self.buttons[name] = b
        self.host = ctk.CTkFrame(self, fg_color="transparent")
        self.host.pack(fill="x")
        self.select(start if start in self.items else next(iter(self.items)))

    def select(self, name: str) -> None:
        if self.current:
            self.frames[self.current].pack_forget()
            style_pill(self.buttons[self.current], False)
        self.current = name
        if name not in self.frames:
            self.frames[name] = ctk.CTkFrame(self.host, fg_color="transparent")
        f = self.frames[name]
        if name not in self.built:
            self.built.add(name)
            self.items[name](f)
        f.pack(fill="x")
        style_pill(self.buttons[name], True)
        if self.on_select:
            self.on_select(name)


# ----------------------------------------------------------------------------
# Lógica auxiliar del módulo C y de la batería de pruebas (sin cambios de lógica)
# ----------------------------------------------------------------------------

def run_suite() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejecuta todos los casos de prueba y las validaciones; devuelve dos tablas."""
    budget = int(SS.budget)
    rows = []
    for pr in PRESETS:
        res = get_analysis(pr.build(), budget)
        got = tuple(r.exists for r in res)
        verified = all(r.verified for r in res if r.exists)
        rows.append({"Caso": pr.name, "Camino Euler": yn(got[0]), "Ciclo Euler": yn(got[1]),
                     "Camino Hamilton": yn(got[2]), "Ciclo Hamilton": yn(got[3]),
                     "Recorridos verificados": "✅" if verified else "❌",
                     "Coincide con lo esperado": "✅" if got == pr.expected else "❌"})
    bad = [("Vértice inexistente", "A, B", "A-B, A-C"), ("Arista duplicada", "A, B", "A-B, B-A"),
           ("Lazo", "A, B", "A-A"), ("Entradas vacías", "", ""), ("Arista mal formada", "A, B", "AB")]
    vrows = []
    for name, v, e in bad:
        try:
            parse_graph_text(v, e, False, False)
            vrows.append({"Entrada inválida": name, "Resultado": "⚠️ no se detectó"})
        except GraphInputError as exc:
            vrows.append({"Entrada inválida": name, "Resultado": "✅ " + str(exc).splitlines()[0]})
    return pd.DataFrame(rows), pd.DataFrame(vrows)


def _tables_to_graph(ndf: pd.DataFrame, edf: pd.DataFrame, directed: bool) -> nx.Graph:
    nodes = [_clean(x) for x in ndf["label"].tolist()]
    edges = [(r["source"], r["target"], r.get("weight")) for _, r in edf.iterrows()]
    weighted = bool(edf["weight"].notna().any()) if len(edf) else False
    return build_graph(nodes, edges, directed, weighted)


def _ai_to_tables(data: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    nodes = [str(n) for n in data.get("nodes", [])]
    ndf = pd.DataFrame({"label": nodes, "x": np.nan, "y": np.nan, "r": np.nan})
    rows = [(str(e.get("source", "")), str(e.get("target", "")),
             float(e["weight"]) if e.get("weight") is not None else np.nan) for e in data.get("edges", [])]
    return ndf, pd.DataFrame(rows, columns=["source", "target", "weight"]).astype({"weight": float})


# ============================================================================
# 10. PÁGINAS — ANÁLISIS (MÓDULO B), CREADOR (A), IMAGEN (C) Y AJUSTES
# ============================================================================
class AnalysisView(ctk.CTkFrame):
    """Todas las métricas y visualizaciones de un grafo (antes: render_analysis)."""

    def __init__(self, master, app: "GraphLabApp", prefix: str) -> None:
        super().__init__(master, fg_color="transparent")
        self.app, self.prefix = app, prefix
        self.G: nx.Graph | None = None
        self.res: tuple[PathResult, ...] = ()
        self._token = 0
        self._last_tab: str | None = None
        self._pyvis_path: str | None = None

    # -- ciclo de vida ---------------------------------------------------------
    def clear(self) -> None:
        self._token += 1
        for w in self.winfo_children():
            w.destroy()

    def show(self, G: nx.Graph) -> None:
        self.clear()
        self.G = G
        if G.number_of_nodes() == 0:
            banner(self, "info", "", "El grafo está vacío. Agregue vértices en el módulo A.").pack(fill="x")
            return
        budget = int(SS.budget)
        if (signature(G), budget) in SS.memo:  # ya calculado: sin esperas
            self._build(get_analysis(G, budget))
            return
        tok = self._token
        busy = Busy(self, "Calculando Euler y Hamilton…")
        busy.pack(anchor="w", pady=8)

        def done(res, err) -> None:
            if tok != self._token or not self.winfo_exists():
                return
            busy.destroy()
            if err:
                banner(self, "error", "", f"Ocurrió un error inesperado: {err}").pack(fill="x")
            else:
                self._build(res)

        self.app.run_async(lambda: get_analysis(G, budget), done)

    def _build(self, res: tuple[PathResult, ...]) -> None:
        self.res = res
        items = [("Resumen", self.t_summary), ("Grados", self.t_degrees), ("Matrices", self.t_matrices),
                 ("Topología", self.t_topology), ("Euler", self.t_euler), ("Hamilton", self.t_hamilton),
                 ("Visualización", self.t_viz)]
        tabs = Tabs(self, items, start=self._last_tab, on_select=lambda n: setattr(self, "_last_tab", n))
        tabs.pack(fill="x")

    # -- presentación de resultados ---------------------------------------------
    @staticmethod
    def show_path_result(parent, title: str, res: PathResult) -> None:
        """Presenta un resultado de Euler/Hamilton con su secuencia y verificación."""
        if res.exists is True:
            banner(parent, "success", f"{title}: sí existe.").pack(fill="x", pady=(8, 2))
        elif res.exists is False:
            banner(parent, "error", f"{title}: no existe.", res.reason).pack(fill="x", pady=(8, 2))
        else:
            banner(parent, "warning", f"{title}: inconcluso.", res.reason).pack(fill="x", pady=(8, 2))
        if res.sequence:
            seq_box(parent, fmt_seq(res.sequence)).pack(fill="x", pady=(6, 2))
            caption(parent, ("✅ Verificado: " if res.verified else "❌ Falló la verificación: ") + res.verification
                    ).pack(fill="x")

    # -- pestañas ----------------------------------------------------------------
    def t_summary(self, f) -> None:
        """Pestaña de propiedades básicas y especiales."""
        G, res = self.G, self.res
        strip = ctk.CTkFrame(f, fg_color="transparent")
        strip.pack(fill="x")
        strip.columnconfigure((0, 1, 2, 3), weight=1, uniform="s")
        metrics = [("Orden |V|", G.number_of_nodes()), ("Tamaño |E|", G.number_of_edges()),
                   ("Componentes", n_components(G)), ("Grado máximo", max(dict(G.degree).values()))]
        for i, (t, v) in enumerate(metrics):
            StatCard(strip, t, v, highlight=i == 0).grid(row=0, column=i, sticky="nsew", padx=4)
        heading(f, "Tipo de grafo", 13).pack(anchor="w", pady=(14, 4))
        ChipFlow(f, describe_type(G)).pack(fill="x")
        try:
            bip: bool | None = nx.is_bipartite(G)
        except Exception:
            bip = None
        acyc = nx.is_directed_acyclic_graph(G) if G.is_directed() else nx.is_forest(G)
        rows = [("Camino de Euler", yn(res[0].exists)), ("Ciclo de Euler", yn(res[1].exists)),
                ("Camino de Hamilton", yn(res[2].exists)), ("Ciclo de Hamilton", yn(res[3].exists)),
                ("Planar", yn(is_planar(G))), ("Bipartito", yn(bip)),
                ("Acíclico", yn(acyc))]
        DataTable(f, pd.DataFrame(rows, columns=["Propiedad", "Resultado"]), max_rows=8).pack(fill="x", pady=(12, 0))

    def t_degrees(self, f) -> None:
        """Pestaña de análisis de grados."""
        G = self.G
        df = degree_table(G)
        deg = dict(G.degree)
        mx, mn = max(deg.values()), min(deg.values())
        odd = [v for v in sort_nodes(G) if deg[v] % 2]
        strip = ctk.CTkFrame(f, fg_color="transparent")
        strip.pack(fill="x")
        strip.columnconfigure((0, 1, 2), weight=1, uniform="d")
        for i, (title, val, who) in enumerate([
            ("Mayor grado", mx, [v for v in deg if deg[v] == mx]),
            ("Menor grado", mn, [v for v in deg if deg[v] == mn]),
            ("Vértices de grado impar", len(odd), odd),
        ]):
            StatCard(strip, title, val, ", ".join(map(str, sort_nodes(who))) or "ninguno",
                     highlight=i == 2).grid(row=0, column=i, sticky="nsew", padx=4)
        if G.is_directed():
            caption(f, "En grafos dirigidos el grado es entrada + salida. Para Euler importa el balance "
                       "(salida − entrada).").pack(fill="x", pady=(8, 0))
        DataTable(f, df, max_rows=12, highlight=lambda r: r["Paridad"] == "impar").pack(fill="x", pady=(10, 0))

    def t_matrices(self, f) -> None:
        """Pestaña de matrices de adyacencia e incidencia."""
        G = self.G
        heading(f, "Matriz de adyacencia" + (" (pesos)" if is_weighted(G) else ""), 13).pack(anchor="w", pady=(0, 4))
        DataTable(f, adjacency_df(G), index=True, max_rows=12, center=True).pack(fill="x")
        heading(f, "Matriz de incidencia" + (" (−1 origen, +1 destino)" if G.is_directed() else ""), 13).pack(
            anchor="w", pady=(16, 4))
        if G.number_of_edges():
            DataTable(f, incidence_df(G), index=True, max_rows=12, center=True).pack(fill="x")
        else:
            banner(f, "info", "", "El grafo no tiene aristas.").pack(fill="x")

    def t_topology(self, f) -> None:
        """Pestaña de componentes, ciclos y planaridad."""
        G = self.G
        d = G.is_directed()

        def comp_table(comps: Iterable[Iterable[Node]]) -> pd.DataFrame:
            cs = sorted((sort_nodes(c) for c in comps), key=lambda c: (-len(c), str(c[0])))
            return pd.DataFrame({"#": range(1, len(cs) + 1), "Vértices": [", ".join(map(str, c)) for c in cs],
                                 "Tamaño": [len(c) for c in cs]})

        heading(f, "Componentes " + ("débilmente conexas" if d else "conexas"), 13).pack(anchor="w", pady=(0, 4))
        DataTable(f, comp_table(nx.weakly_connected_components(G) if d else nx.connected_components(G)),
                  max_rows=6).pack(fill="x")
        if d:
            heading(f, "Componentes fuertemente conexas", 13).pack(anchor="w", pady=(14, 4))
            DataTable(f, comp_table(nx.strongly_connected_components(G)), max_rows=6).pack(fill="x")
        heading(f, "Detección de ciclos", 13).pack(anchor="w", pady=(16, 0))
        info = cycle_info(G)
        if info["has_cycle"]:
            banner(f, "warning", "", "El grafo contiene al menos un ciclo.").pack(fill="x", pady=(6, 2))
            seq_box(f, fmt_seq(info["example"])).pack(fill="x", pady=(4, 2))  # type: ignore[arg-type]
        else:
            banner(f, "success", "", "El grafo no contiene ciclos.").pack(fill="x", pady=(6, 2))
        caption(f, str(info["detail"])).pack(fill="x")
        if info["basis"]:
            ex = Collapsible(f, "Base de ciclos fundamentales")
            ex.pack(fill="x", pady=(8, 0))
            for cyc in info["basis"]:  # type: ignore[attr-defined]
                code_box(ex.body, fmt_seq(list(cyc) + [cyc[0]])).pack(fill="x", pady=2)
        heading(f, f"Planaridad: {yn(is_planar(G))}", 13).pack(anchor="w", pady=(14, 0))

    def t_euler(self, f) -> None:
        """Pestaña de caminos y ciclos de Euler (algoritmo de Hierholzer)."""
        G = self.G
        path, cyc = self.res[0], self.res[1]
        caption(f, "Condición: grafo conexo y 0 o 2 vértices de grado impar (camino); todos pares (ciclo). "
                   "En dirigidos: in = out en todos (ciclo) o un único desbalance +1/−1 (camino). "
                   "Se construye con Hierholzer.").pack(fill="x")
        self.show_path_result(f, "Camino de Euler", path)
        self.show_path_result(f, "Ciclo de Euler", cyc)
        shown = cyc if cyc.exists else path
        if shown.sequence:
            heading(f, "Orden en que se recorre cada arista", 13).pack(anchor="w", pady=(16, 4))
            DataTable(f, pd.DataFrame([(k, u, v, f"{u}{'→' if G.is_directed() else '–'}{v}")
                                       for k, (u, v) in enumerate(zip(shown.sequence, shown.sequence[1:]), 1)],
                                      columns=["Paso", "Desde", "Hasta", "Arista"]), max_rows=12).pack(fill="x")

    def t_hamilton(self, f) -> None:
        """Pestaña de caminos y ciclos de Hamilton (backtracking)."""
        path, cyc = self.res[2], self.res[3]
        caption(f, "Búsqueda con retroceso (backtracking), poda por condiciones necesarias y límite de pasos "
                   "configurable.").pack(fill="x")
        self.show_path_result(f, "Camino de Hamilton", path)
        self.show_path_result(f, "Ciclo de Hamilton", cyc)
        if path.steps or cyc.steps:
            caption(f, f"Estados explorados: camino {path.steps:,} · ciclo {cyc.steps:,}").pack(fill="x", pady=(8, 0))

    # -- visualización -------------------------------------------------------------
    def t_viz(self, f) -> None:
        """Pestaña de visualización con resaltado de recorridos."""
        G, res = self.G, self.res
        names = ("Camino de Euler", "Ciclo de Euler", "Camino de Hamilton", "Ciclo de Hamilton")
        self.v_opts: dict[str, list[Node] | None] = {"Ninguno": None}
        self.v_opts.update({n: r.sequence for n, r in zip(names, res) if r.exists and r.sequence})
        bar = ctk.CTkFrame(f, fg_color="transparent")
        bar.pack(fill="x")
        bar.columnconfigure((0, 1, 2, 3), weight=1, uniform="v")
        c0, c1, c2, c3 = (labeled(bar, t) for t in ("Motor", "Disposición", "Resaltar recorrido", "Semilla"))
        for i, c in enumerate((c0, c1, c2, c3)):
            c.grid(row=0, column=i, sticky="new", padx=4)
        self.v_eng = ctk.CTkSegmentedButton(c0, values=["Matplotlib", "PyVis interactivo"], font=F(11),
                                            command=lambda _v: self._viz_draw(True), selected_color=UI_TINT,
                                            selected_hover_color=UI_TINT, unselected_color=UI_BG,
                                            unselected_hover_color=UI_LINE, text_color=UI_TEXT)
        self.v_eng.set("Matplotlib")
        self.v_eng.pack(fill="x")
        self.v_lay = menu(c1, LAYOUTS, command=lambda _v: self._viz_draw(), width=150)
        self.v_lay.pack(fill="x")
        self.v_hl = menu(c2, list(self.v_opts), command=lambda _v: self._viz_draw(), width=150)
        self.v_hl.pack(fill="x")
        self.v_seed = entry(c3, "7")
        self.v_seed.pack(fill="x")
        self.v_seed.bind("<Return>", lambda _e: self._viz_draw())
        self.v_seed.bind("<FocusOut>", lambda _e: self._viz_draw())
        self.v_w = checkbox(f, "Mostrar pesos", lambda: self._viz_draw(), on=True) if is_weighted(G) else None
        if self.v_w:
            self.v_w.pack(anchor="w", padx=4, pady=(10, 0))
        self.v_msg = MsgArea(f)
        self.v_msg.pack(fill="x")
        self.v_cap = caption(f, "")
        self.v_cap.pack(fill="x", pady=(6, 0))
        self.v_holder = ctk.CTkFrame(f, fg_color="transparent", width=0, height=0)
        self.v_holder.pack(fill="x", pady=(6, 0))
        self._viz_draw()

    def _viz_draw(self, from_engine: bool = False) -> None:
        G = self.G
        self.v_msg.clear()
        for w in self.v_holder.winfo_children():
            w.destroy()
        try:
            seed = max(0, min(9999, int(self.v_seed.get())))
        except ValueError:
            seed = 7
        walk = self.v_opts.get(self.v_hl.get())
        show_w = bool(self.v_w.get()) if self.v_w else False
        self.v_cap.configure(text="Aristas resaltadas en ámbar con su orden (#). El vértice inicial va en verde."
                             if walk else "")
        if self.v_eng.get().startswith("PyVis"):
            if Network is None:
                self.v_msg.show("info", "", "PyVis no está instalado (pip install pyvis); se usa Matplotlib.")
            else:
                try:
                    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
                        fh.write(pyvis_html(G, walk))
                    uri = "file:///" + fh.name.replace("\\", "/").lstrip("/")
                    if from_engine:
                        webbrowser.open(uri)
                    box = ctk.CTkFrame(self.v_holder, fg_color=UI_SOFT, corner_radius=12)
                    box.pack(fill="x", pady=4)
                    ctk.CTkLabel(box, text="La visualización interactiva (PyVis) se abre en su navegador.",
                                 font=F(12), text_color=UI_TEXT).pack(side="left", padx=16, pady=16)
                    btn(box, "Abrir en el navegador", lambda: webbrowser.open(uri), width=180).pack(
                        side="right", padx=16, pady=12)
                    return
                except Exception as exc:
                    self.v_msg.show("warning", "", f"No se pudo renderizar PyVis ({exc}); se usa Matplotlib.")
        fig = draw_graph_mpl(G, self.v_lay.get(), seed, walk, show_w)
        img = fig_to_ctk(fig, 800)
        lbl = ctk.CTkLabel(self.v_holder, text="", image=img)
        lbl.image = img  # type: ignore[attr-defined]
        lbl.pack(anchor="w")


class PageB(ctk.CTkFrame):
    """Módulo B: análisis del grafo activo."""

    def __init__(self, master, app: "GraphLabApp") -> None:
        super().__init__(master, fg_color="transparent")
        c = card(self)
        c.pack(fill="x")
        heading(c, "B. Análisis del grafo activo", 16).pack(anchor="w", padx=18, pady=(14, 0))
        self.cap = caption(c, "", pad=36)
        self.cap.pack(fill="x", padx=18, pady=(0, 8))
        self.view = AnalysisView(c, app, "main")
        self.view.pack(fill="x", padx=18, pady=(0, 18))

    def refresh(self) -> None:
        self.cap.configure(text=f"Grafo: {SS.graph_name}")
        self.view.show(SS.graph)


class PageA(ctk.CTkFrame):
    """Módulo A: generador aleatorio, creador manual y casos de prueba."""

    def __init__(self, master, app: "GraphLabApp") -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._mod: ctk.CTkFrame | None = None
        c = card(self)
        c.pack(fill="x", pady=(0, 14))
        heading(c, "A. Creador y generador de grafos", 16).pack(anchor="w", padx=18, pady=(14, 10))
        tabs = Tabs(c, [("Generador aleatorio", self._build_gen), ("Creador manual", self._build_manual),
                        ("Casos de prueba", self._build_presets)])
        tabs.pack(fill="x", padx=18, pady=(0, 18))
        self.preview = card(self)
        self.preview.pack(fill="x")

    # -- generador aleatorio ---------------------------------------------------------
    def _build_gen(self, f) -> None:
        g = ctk.CTkFrame(f, fg_color="transparent")
        g.pack(fill="x")
        g.columnconfigure((0, 1), weight=1, uniform="g")
        c1, c2 = ctk.CTkFrame(g, fg_color="transparent"), ctk.CTkFrame(g, fg_color="transparent")
        c1.grid(row=0, column=0, sticky="new", padx=(0, 14))
        c2.grid(row=0, column=1, sticky="new", padx=(14, 0))
        lab = labeled(c1, "Tipo de grafo")
        lab.pack(fill="x", pady=(0, 10))
        self.g_kind = menu(lab, list(KINDS.values()), command=lambda _v: self._gen_toggle(), width=300)
        self.g_kind.pack(fill="x")
        self.g_dir = switch(c1, "Dirigido")
        self.g_dir.pack(anchor="w", pady=6)
        self.g_n = LabeledSlider(c1, "Número de nodos", 3, 40, 8)
        self.g_n.pack(fill="x", pady=6)
        self.g_m = LabeledSlider(c1, "Aristas por nodo nuevo (m)", 1, 6, 2)
        self.g_m.pack(fill="x", pady=6)
        self.g_w = switch(c2, "Ponderado", command=self._gen_toggle)
        self.g_w.pack(anchor="w", pady=(24, 6))
        self.g_conn = switch(c2, "Forzar conexo (reintenta semillas)", on=True)
        self.g_conn.pack(anchor="w", pady=6)
        self.g_p = LabeledSlider(c2, "Probabilidad de conexión p", 0.05, 1.0, 0.35, step=0.05)
        self.g_p.pack(fill="x", pady=6)
        self.g_n2 = LabeledSlider(c2, "Nodos del segundo grupo", 1, 20, 4)
        self.g_n2.pack(fill="x", pady=6)
        self.g_wr = ctk.CTkFrame(f, fg_color="transparent")
        self.g_wr.columnconfigure((0, 1), weight=1, uniform="r")
        self.g_wlo = LabeledSlider(self.g_wr, "Rango de pesos: mínimo", 1, 100, 1)
        self.g_wlo.grid(row=0, column=0, sticky="ew", padx=(0, 14))
        self.g_whi = LabeledSlider(self.g_wr, "Rango de pesos: máximo", 1, 100, 20)
        self.g_whi.grid(row=0, column=1, sticky="ew", padx=(14, 0))
        self.g_wr_holder = ctk.CTkFrame(f, fg_color="transparent", width=0, height=0)
        self.g_wr_holder.pack(fill="x")
        lab = labeled(f, "Semilla")
        lab.pack(anchor="w", pady=(8, 0))
        self.g_seed = entry(lab, "42", width=140)
        self.g_seed.pack(anchor="w")
        self.g_msg = MsgArea(f)
        self.g_msg.pack(fill="x")
        btn(f, "Generar grafo aleatorio", self._generate, width=240).pack(anchor="w", pady=(12, 0))
        self._gen_toggle()

    def _kind_key(self) -> str:
        return {v: k for k, v in KINDS.items()}[self.g_kind.get()]

    def _gen_toggle(self) -> None:
        kind = self._kind_key()
        self.g_p.enable(kind in ("er", "bip"))
        self.g_m.enable(kind == "ba")
        self.g_n2.enable(kind == "bip")
        if bool(self.g_w.get()):
            self.g_wr.pack(in_=self.g_wr_holder, fill="x", pady=6)
        else:
            self.g_wr.pack_forget()

    def _generate(self) -> None:
        self.g_msg.clear()
        kind, directed, weighted = self._kind_key(), bool(self.g_dir.get()), bool(self.g_w.get())
        connected = bool(self.g_conn.get())
        n, p, m, n2 = self.g_n.get(), self.g_p.get(), self.g_m.get(), self.g_n2.get()
        lo, hi = self.g_wlo.get(), self.g_whi.get()
        wr = (min(lo, hi), max(lo, hi)) if weighted else (1, 1)
        try:
            seed = max(0, min(99999, int(self.g_seed.get())))
        except ValueError:
            self.g_msg.show("error", "", "La semilla debe ser un número entero.")
            return
        new, note = None, ""
        try:
            for k in range(100 if connected and kind in ("er", "ba", "bip") else 1):
                new = generate_graph(kind, n, p, m, n2, directed, weighted, wr, seed + k)
                if not connected or is_connected(new):
                    break
            else:
                note = " (no se logró un grafo conexo; suba p)"
        except Exception as exc:
            new = None
            self.g_msg.show("error", "", f"No se pudo generar el grafo: {exc}")
        if new is not None:
            self.app.set_graph(new, KINDS[kind], f"Grafo generado: {KINDS[kind]}{note}")

    # -- creador manual -----------------------------------------------------------------
    def _build_manual(self, f) -> None:
        heading(f, "1. Definir un grafo desde texto", 14).pack(anchor="w", pady=(2, 8))
        g = ctk.CTkFrame(f, fg_color="transparent")
        g.pack(fill="x")
        g.columnconfigure((0, 1), weight=1, uniform="m")
        left, right = ctk.CTkFrame(g, fg_color="transparent"), ctk.CTkFrame(g, fg_color="transparent")
        left.grid(row=0, column=0, sticky="new", padx=(0, 14))
        right.grid(row=0, column=1, sticky="new", padx=(14, 0))
        lab = labeled(left, "Vértices (separados por comas)")
        lab.pack(fill="x")
        self.m_v = entry(lab, "A, B, C, D, E")
        self.m_v.pack(fill="x")
        self.m_d = switch(left, "Dirigido")
        self.m_d.pack(anchor="w", pady=(12, 0))
        lab = labeled(right, "Aristas (A-B, B-C; con peso A-B:5)")
        lab.pack(fill="x")
        self.m_e = ctk.CTkTextbox(lab, height=90, corner_radius=8, fg_color=UI_SOFT, border_width=1,
                                  border_color=UI_LINE, text_color=UI_TEXT, font=F(12))
        self.m_e.insert("1.0", "A-B, B-C, C-D, D-A, A-E, B-E")
        self.m_e.pack(fill="x")
        self.m_w = switch(right, "Ponderado")
        self.m_w.pack(anchor="w", pady=(12, 0))
        btn(f, "Cargar grafo", self._load_text, width=180).pack(anchor="w", pady=(12, 0))
        self.m_msg = MsgArea(f)
        self.m_msg.pack(fill="x")
        hr(f)
        heading(f, "2. Modificar el grafo activo", 14).pack(anchor="w", pady=(0, 8))
        self._mod = ctk.CTkFrame(f, fg_color="transparent", width=0, height=0)
        self._mod.pack(fill="x")
        self._build_mod()

    def _load_text(self) -> None:
        self.m_msg.clear()
        try:
            new = parse_graph_text(self.m_v.get(), self.m_e.get("1.0", "end"), bool(self.m_d.get()),
                                   bool(self.m_w.get()))
        except GraphInputError as exc:
            self.m_msg.show_errors(exc)
            return
        self.app.set_graph(new, "Grafo manual")

    def _form(self, parent, title: str) -> ctk.CTkFrame:
        fr = ctk.CTkFrame(parent, fg_color=UI_SOFT, corner_radius=12, border_width=1, border_color=UI_LINE)
        ctk.CTkLabel(fr, text=title, font=F(12, "bold"), text_color=UI_TEXT, anchor="w").pack(
            fill="x", padx=14, pady=(10, 6))
        return fr

    def _build_mod(self) -> None:
        if self._mod is None:
            return
        for w in self._mod.winfo_children():
            w.destroy()
        G = SS.graph
        nodes = [str(v) for v in sort_nodes(G.nodes)]
        self.mod_msg = MsgArea(self._mod)
        self.mod_msg.pack(fill="x")
        grid = ctk.CTkFrame(self._mod, fg_color="transparent")
        grid.pack(fill="x", pady=(4, 0))
        grid.columnconfigure((0, 1), weight=1, uniform="f")

        # Agregar vértice
        fa = self._form(grid, "Agregar vértice")
        fa.grid(row=0, column=0, sticky="nsew", padx=(0, 7), pady=(0, 10))
        lab = labeled(fa, "Nuevo vértice")
        lab.pack(fill="x", padx=14)
        self.f_name = entry(lab)
        self.f_name.pack(fill="x")
        btn(fa, "Agregar vértice", self._add_vertex, width=170).pack(anchor="w", padx=14, pady=12)

        # Agregar arista
        fb = self._form(grid, "Agregar arista")
        fb.grid(row=0, column=1, sticky="nsew", padx=(7, 0), pady=(0, 10))
        row = ctk.CTkFrame(fb, fg_color="transparent")
        row.pack(fill="x", padx=14)
        row.columnconfigure((0, 1), weight=1, uniform="e")
        l1, l2 = labeled(row, "Origen"), labeled(row, "Destino")
        l1.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        l2.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.f_src = menu(l1, nodes, width=100)
        self.f_src.pack(fill="x")
        self.f_dst = menu(l2, nodes, width=100)
        self.f_dst.pack(fill="x")
        row2 = ctk.CTkFrame(fb, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(8, 0))
        self.f_usew = checkbox(row2, "Con peso", on=is_weighted(G))
        self.f_usew.pack(side="left")
        self.f_wt = entry(row2, "1.0", width=90)
        self.f_wt.pack(side="right")
        ctk.CTkLabel(row2, text="Peso", font=F(11), text_color=UI_MUTED).pack(side="right", padx=8)
        btn(fb, "Agregar arista", self._add_edge, width=170).pack(anchor="w", padx=14, pady=12)

        # Eliminar vértice
        fc = self._form(grid, "Eliminar vértice")
        fc.grid(row=1, column=0, sticky="nsew", padx=(0, 7))
        lab = labeled(fc, "Vértice a eliminar")
        lab.pack(fill="x", padx=14)
        self.f_dv = menu(lab, nodes, width=160)
        self.f_dv.pack(fill="x")
        btn(fc, "Eliminar vértice", self._del_vertex, width=170).pack(anchor="w", padx=14, pady=12)

        # Eliminar arista
        fd = self._form(grid, "Eliminar arista")
        fd.grid(row=1, column=1, sticky="nsew", padx=(7, 0))
        self._edges = list(G.edges)
        lab = labeled(fd, "Arista a eliminar")
        lab.pack(fill="x", padx=14)
        self.f_de = menu(lab, [f"{u}–{v}" for u, v in self._edges], width=160)
        self.f_de.pack(fill="x")
        btn(fd, "Eliminar arista", self._del_edge, width=170).pack(anchor="w", padx=14, pady=12)

    def _add_vertex(self) -> None:
        G, name = SS.graph, self.f_name.get().strip()
        try:
            if not name:
                raise GraphInputError("Entrada vacía: escriba el nombre del vértice.")
            if name in G:
                raise GraphInputError(f"El vértice «{name}» ya existe.")
        except GraphInputError as exc:
            self.mod_msg.show_errors(exc)
            return
        H = G.copy()
        H.add_node(name)
        self.app.set_graph(H, SS.graph_name, f"Vértice {name} agregado")

    def _add_edge(self) -> None:
        G = SS.graph
        src, dst = self.f_src.get() or None, self.f_dst.get() or None
        try:
            if src is None or dst is None:
                raise GraphInputError("Agregue primero algún vértice.")
            try:
                wt = float(self.f_wt.get().replace(",", "."))
            except ValueError:
                raise GraphInputError("El peso debe ser un número.")
            H = G.copy()
            if src == dst:
                raise GraphInputError("No se permiten lazos (origen = destino).")
            if H.has_edge(src, dst):
                raise GraphInputError(f"La arista {src}–{dst} ya existe.")
            H.add_edge(src, dst, **({"weight": wt} if self.f_usew.get() else {}))
        except GraphInputError as exc:
            self.mod_msg.show_errors(exc)
            return
        self.app.set_graph(H, SS.graph_name, f"Arista {src}–{dst} agregada")

    def _del_vertex(self) -> None:
        rv = self.f_dv.get()
        if not rv:
            return
        H = SS.graph.copy()
        H.remove_node(rv)
        self.app.set_graph(H, SS.graph_name, f"Vértice {rv} eliminado")

    def _del_edge(self) -> None:
        labels = [f"{u}–{v}" for u, v in self._edges]
        sel = self.f_de.get()
        if sel not in labels:
            return
        u, v = self._edges[labels.index(sel)]
        H = SS.graph.copy()
        H.remove_edge(u, v)
        self.app.set_graph(H, SS.graph_name, f"Arista {u}–{v} eliminada")

    # -- casos de prueba -------------------------------------------------------------------
    def _build_presets(self, f) -> None:
        lab = labeled(f, "Caso de prueba")
        lab.pack(anchor="w")
        self.p_sel = menu(lab, [p.name for p in PRESETS], command=lambda _v: self._preset_changed(), width=440)
        self.p_sel.pack(anchor="w")
        self.p_desc = caption(f, "")
        self.p_desc.pack(fill="x", pady=(8, 0))
        self.p_exp = WrapLabel(f, text="", pad=24, font=F(12), text_color=UI_TEXT)
        self.p_exp.pack(fill="x", pady=(4, 0))
        self.p_msg = MsgArea(f)
        self.p_msg.pack(fill="x")
        btn(f, "Cargar este caso", self._load_preset, width=200).pack(anchor="w", pady=(10, 0))
        hr(f)
        btn(f, "▶ Ejecutar toda la batería de pruebas", self._run_battery, primary=False, width=300).pack(anchor="w")
        self.p_out = ctk.CTkFrame(f, fg_color="transparent", width=0, height=0)
        self.p_out.pack(fill="x")
        self._preset_changed()

    def _current_preset(self) -> Preset:
        names = [p.name for p in PRESETS]
        return PRESETS[names.index(self.p_sel.get())]

    def _preset_changed(self) -> None:
        pr = self._current_preset()
        self.p_desc.configure(text=pr.desc)
        self.p_exp.configure(text="Esperado: camino de Euler " + yn(pr.expected[0]) + " · ciclo de Euler "
                             + yn(pr.expected[1]) + " · camino de Hamilton " + yn(pr.expected[2])
                             + " · ciclo de Hamilton " + yn(pr.expected[3]))

    def _load_preset(self) -> None:
        self.p_msg.clear()
        pr = self._current_preset()
        try:
            new = pr.build()
        except Exception as exc:
            self.p_msg.show("error", "", f"No se pudo construir el caso: {exc}")
            return
        self.app.set_graph(new, pr.name)

    def _run_battery(self) -> None:
        for w in self.p_out.winfo_children():
            w.destroy()
        busy = Busy(self.p_out, "Ejecutando casos…")
        busy.pack(anchor="w", pady=10)

        def done(res, err) -> None:
            if not self.p_out.winfo_exists():
                return
            busy.destroy()
            if err:
                banner(self.p_out, "error", "", f"Ocurrió un error inesperado: {err}").pack(fill="x", pady=8)
                return
            t1, t2 = res
            DataTable(self.p_out, t1, max_rows=12).pack(fill="x", pady=(12, 0))
            heading(self.p_out, "Validación de entradas incorrectas", 13).pack(anchor="w", pady=(16, 4))
            DataTable(self.p_out, t2, max_rows=6).pack(fill="x")

        self.app.run_async(run_suite, done)

    # -- vista previa --------------------------------------------------------------------------
    def refresh(self) -> None:
        self._build_mod()
        for w in self.preview.winfo_children():
            w.destroy()
        heading(self.preview, f"Vista previa del grafo activo: {SS.graph_name}", 14).pack(
            anchor="w", padx=18, pady=(14, 8))
        G = SS.graph
        if G.number_of_nodes():
            fig = draw_graph_mpl(G, show_weights=True)
            img = fig_to_ctk(fig, 700)
            lbl = ctk.CTkLabel(self.preview, text="", image=img)
            lbl.image = img  # type: ignore[attr-defined]
            lbl.pack(anchor="w", padx=18, pady=(0, 18))
        else:
            banner(self.preview, "info", "", "El grafo está vacío.").pack(fill="x", padx=18, pady=(0, 18))


class PageC(ctk.CTkFrame):
    """Módulo C: reconstrucción de un grafo a partir de una imagen."""

    def __init__(self, master, app: "GraphLabApp") -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.rgb: np.ndarray | None = None
        self.fname = ""
        self.G: nx.Graph | None = None
        self.auto: tuple[int, int] | None = None
        self.origin = ""
        self.directed = False
        self._after: str | None = None
        self._built = False
        top = card(self)
        top.pack(fill="x", pady=(0, 14))
        heading(top, "C. Reconocimiento de grafos desde una imagen", 16).pack(anchor="w", padx=18, pady=(14, 8))
        if cv2 is None:
            banner(top, "error", "", "OpenCV no está instalado. Ejecute: pip install opencv-python").pack(
                fill="x", padx=18, pady=(0, 18))
            return
        row = ctk.CTkFrame(top, fg_color="transparent")
        row.pack(fill="x", padx=18)
        btn(row, "Seleccionar imagen (PNG, JPG o JPEG)…", self._choose, width=300).pack(side="left")
        self.file_lbl = ctk.CTkLabel(row, text="Ninguna imagen seleccionada", font=F(12), text_color=UI_MUTED)
        self.file_lbl.pack(side="left", padx=14)
        self.top_msg = MsgArea(top)
        self.top_msg.pack(fill="x", padx=18, pady=(0, 16))
        self.top_msg.show("info", "", "Suba un dibujo con nodos circulares y aristas rectas. Si el resultado no es "
                                      "exacto, podrá corregirlo en las tablas.")
        self.body = ctk.CTkFrame(self, fg_color="transparent")

    # -- carga de la imagen -----------------------------------------------------------------------
    def _choose(self) -> None:
        path = filedialog.askopenfilename(title="Imagen del grafo", filetypes=[
            ("Imágenes", "*.png *.jpg *.jpeg"), ("Todos los archivos", "*.*")])
        if not path:
            return
        try:
            with open(path, "rb") as fh:
                data = fh.read()
            rgb = load_image(data)
        except (ValueError, OSError) as exc:
            if self._built:
                self.body.pack_forget()
            self.G = None
            self.top_msg.show("error", "", f"⚠️ {exc}")
            return
        self.rgb, self.fname = rgb, os.path.basename(path)
        self.auto, self.origin, self.G = None, "", None
        self.file_lbl.configure(text=self.fname, text_color=UI_TEXT)
        self.top_msg.clear()
        self._ensure_body()
        self._reset_params()
        self.body.pack(fill="x")
        self._update_pre()
        self.node_tbl.set_df(pd.DataFrame(columns=["label", "x", "y", "r"]))
        self.edge_tbl.set_df(pd.DataFrame(columns=["source", "target", "weight"]))
        self._detect()

    def _ensure_body(self) -> None:
        if self._built:
            return
        self._built = True
        b = self.body
        ctrl = card(b)
        ctrl.pack(fill="x", pady=(0, 14))
        pad = dict(padx=18)
        self.dir_sw = switch(ctrl, "Las aristas del dibujo son dirigidas (flechas)", command=self._on_directed)
        self.dir_sw.pack(anchor="w", pady=(16, 2), **pad)
        caption(ctrl, "Si cambia esta opción, pulse «Detectar de nuevo» para que se reoriente cada arista.",
                pad=36).pack(fill="x", **pad)

        ex = Collapsible(ctrl, "Parámetros de detección")
        ex.pack(fill="x", pady=(12, 0), **pad)
        pg = ctk.CTkFrame(ex.body, fg_color="transparent")
        pg.pack(fill="x")
        pg.columnconfigure((0, 1, 2), weight=1, uniform="p")
        cols = [ctk.CTkFrame(pg, fg_color="transparent") for _ in range(3)]
        for i, c in enumerate(cols):
            c.grid(row=0, column=i, sticky="new", padx=8)
        self.s_min = LabeledSlider(cols[0], "Radio mínimo del nodo (px)", 4, 150, 8)
        self.s_min.pack(fill="x", pady=6)
        self.s_max = LabeledSlider(cols[0], "Radio máximo del nodo (px)", 10, 300, 30)
        self.s_max.pack(fill="x", pady=6)
        self.s_sens = LabeledSlider(cols[1], "Sensibilidad de círculos (menor = más nodos)", 10, 60, 28)
        self.s_sens.pack(fill="x", pady=6)
        self.s_cov = LabeledSlider(cols[1], "Cobertura mínima de una arista", 0.5, 0.99, 0.80, step=0.01)
        self.s_cov.pack(fill="x", pady=6)
        self.c_ada = checkbox(cols[2], "Umbral adaptativo (fotos con sombras)", command=self._update_pre)
        self.c_ada.pack(anchor="w", pady=(24, 0))

        ex = Collapsible(ctrl, "Preprocesamiento (escala de grises y binarización)")
        ex.pack(fill="x", pady=(8, 0), **pad)
        pr = ctk.CTkFrame(ex.body, fg_color="transparent")
        pr.pack(fill="x")
        pr.columnconfigure((0, 1), weight=1, uniform="q")
        self.pre_a, self.pre_b = ctk.CTkLabel(pr, text=""), ctk.CTkLabel(pr, text="")
        for i, (lbl, cap) in enumerate(((self.pre_a, "Escala de grises suavizada"),
                                        (self.pre_b, "Binarización (tinta en blanco)"))):
            lbl.grid(row=0, column=i, padx=8)
            ctk.CTkLabel(pr, text=cap, font=F(11), text_color=UI_MUTED).grid(row=1, column=i, padx=8)

        ex = Collapsible(ctrl, "Análisis multimodal con IA (opcional)")
        ex.pack(fill="x", pady=(8, 0), **pad)
        lab = labeled(ex.body, "API key de Anthropic")
        lab.pack(fill="x")
        self.ai_key = entry(lab, os.environ.get("ANTHROPIC_API_KEY", ""), show="•")
        self.ai_key.pack(fill="x")
        btn(ex.body, "Analizar con IA multimodal", self._ai, primary=False, width=240).pack(anchor="w", pady=(10, 0))

        self.c_msg = MsgArea(ctrl)
        self.c_msg.pack(fill="x", **pad)
        self.run_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        self.run_row.pack(fill="x", pady=(12, 18), **pad)
        btn(self.run_row, "Detectar de nuevo con OpenCV", self._detect, width=280).pack(side="left")
        self.busy_slot = ctk.CTkFrame(self.run_row, fg_color="transparent", width=0, height=0)
        self.busy_slot.pack(side="left", padx=14)

        st = card(b)
        st.pack(fill="x", pady=(0, 14))
        self.struct_lbl = heading(st, "", 14)
        self.struct_lbl.pack(anchor="w", padx=18, pady=(14, 4))
        self.warn_msg = MsgArea(st)
        self.warn_msg.pack(fill="x", padx=18)
        grid = ctk.CTkFrame(st, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=(8, 12))
        grid.columnconfigure(0, weight=3, uniform="s")
        grid.columnconfigure(1, weight=2, uniform="s")
        left = ctk.CTkFrame(grid, fg_color="transparent")
        left.grid(row=0, column=0, sticky="new", padx=(0, 10))
        right = ctk.CTkFrame(grid, fg_color="transparent")
        right.grid(row=0, column=1, sticky="new", padx=(10, 0))
        left.columnconfigure((0, 1), weight=1)
        self.img_a, self.img_b = ctk.CTkLabel(left, text=""), ctk.CTkLabel(left, text="")
        for i, (lbl, cap) in enumerate(((self.img_a, "Imagen original"), (self.img_b, "Lo que entendió el programa"))):
            lbl.grid(row=0, column=i, padx=4, sticky="n")
            ctk.CTkLabel(left, text=cap, font=F(11), text_color=UI_MUTED).grid(row=1, column=i, padx=4)
        self.node_tbl = EditableTable(right, "Vértices", ["label", "x", "y", "r"], ["Vértice", "x", "y", "r"],
                                      ["x", "y", "r"], self._edited)
        self.node_tbl.pack(fill="x")
        self.edge_tbl = EditableTable(right, "Aristas", ["source", "target", "weight"],
                                      ["Origen", "Destino", "Peso (opcional)"], ["weight"], self._edited)
        self.edge_tbl.pack(fill="x", pady=(12, 0))
        self.auto_lbl = caption(st, "", pad=36)
        self.auto_lbl.pack(fill="x", padx=18)
        self.err_msg = MsgArea(st)
        self.err_msg.pack(fill="x", padx=18)
        self.use_btn = btn(st, "Usar este grafo como grafo activo", self._use_graph, width=300)
        self.use_btn.pack(anchor="w", padx=18, pady=(10, 18))

        an = card(b)
        an.pack(fill="x")
        heading(an, "Análisis matemático del grafo reconstruido", 15).pack(anchor="w", padx=18, pady=(14, 8))
        self.analysis = AnalysisView(an, self.app, "img")
        self.analysis.pack(fill="x", padx=18, pady=(0, 18))

    def _reset_params(self) -> None:
        base = min(self.rgb.shape[:2])  # type: ignore[union-attr]
        self.s_min.set(max(8, int(base * 0.025)))
        self.s_max.set(max(30, int(base * 0.09)))
        self.s_sens.set(28)
        self.s_cov.set(0.80)
        self.c_ada.deselect()

    def _params(self) -> DetectParams:
        return DetectParams(self.s_min.get(), self.s_max.get(), self.s_sens.get(), self.s_cov.get(),
                            bool(self.c_ada.get()), self.directed)

    def _update_pre(self) -> None:
        blur, binary = preprocess(self.rgb, bool(self.c_ada.get()))  # type: ignore[arg-type]
        for lbl, arr in ((self.pre_a, blur), (self.pre_b, binary)):
            img = np_to_ctk(arr, 380, 280)
            lbl.configure(image=img)
            lbl.image = img  # type: ignore[attr-defined]

    def _on_directed(self) -> None:
        self.directed = bool(self.dir_sw.get())
        if self.rgb is not None:
            self._refresh_structure()

    # -- detección ----------------------------------------------------------------------------------
    def _detect(self) -> None:
        p = self._params()
        if p.min_radius >= p.max_radius:
            self.c_msg.show("warning", "", "El radio mínimo debe ser menor que el máximo.")
            return
        self.c_msg.clear()
        blur, binary = preprocess(self.rgb, p.adaptive)  # type: ignore[arg-type]
        busy = Busy(self.busy_slot, "Detectando…")
        busy.pack()

        def work():
            nodes = detect_nodes(blur, binary, p)
            if len(nodes) > 80:
                raise ValueError("Se detectaron demasiados nodos; suba el radio mínimo o reduzca la sensibilidad.")
            return nodes, tables_from_detection(nodes, detect_edges(binary, nodes, p))

        def done(res, err) -> None:
            if not self.winfo_exists():
                return
            busy.destroy()
            if err:
                self.c_msg.show("error", "", f"La detección automática falló: {err}")
                ndf = pd.DataFrame(columns=["label", "x", "y", "r"])
                edf = pd.DataFrame(columns=["source", "target", "weight"])
            else:
                nodes, (ndf, edf) = res
                self.origin = "OpenCV"
                self.auto = (len(ndf), len(edf))
            self._set_tables(ndf, edf)

        self.app.run_async(work, done)

    def _ai(self) -> None:
        key = self.ai_key.get().strip()
        if not key:
            self.c_msg.show("error", "", "El análisis con IA falló: Indique una API key de Anthropic.")
            return
        self.c_msg.clear()
        busy = Busy(self.busy_slot, "Consultando al modelo…")
        busy.pack()
        rgb = self.rgb

        def done(res, err) -> None:
            if not self.winfo_exists():
                return
            busy.destroy()
            if err:
                self.c_msg.show("error", "", f"El análisis con IA falló: {err}")
                return
            ndf, edf = _ai_to_tables(res)
            self.origin = "IA multimodal"
            self.auto = (len(ndf), len(edf))
            if res.get("directed") and not self.directed:
                self.c_msg.show("info", "", "El modelo percibe un grafo dirigido: active el interruptor «dirigidas».")
            self._set_tables(ndf, edf)

        self.app.run_async(lambda: analyze_with_claude(rgb, key), done)

    def _set_tables(self, ndf: pd.DataFrame, edf: pd.DataFrame) -> None:
        self.node_tbl.set_df(ndf)
        self.edge_tbl.set_df(edf)
        self._refresh_structure()

    # -- estructura estimada --------------------------------------------------------------------------
    def _edited(self) -> None:
        if self._after:
            self.after_cancel(self._after)
        self._after = self.after(250, self._refresh_structure)

    def _refresh_structure(self) -> None:
        self._after = None
        ndf, edf = self.node_tbl.get_df(), self.edge_tbl.get_df()
        self.struct_lbl.configure(text=f"Estructura estimada ({self.origin or 'manual'}) — edítela si hace falta")
        for lbl, arr in ((self.img_a, self.rgb), (self.img_b, draw_overlay(self.rgb, ndf, edf, self.directed))):
            img = np_to_ctk(arr, 330, 300)  # type: ignore[arg-type]
            lbl.configure(image=img)
            lbl.image = img  # type: ignore[attr-defined]
        self.warn_msg.clear()
        if len(ndf) == 0:
            self.warn_msg.show("warning", "", "No se detectaron nodos. Ajuste los radios o la sensibilidad, active el "
                                              "umbral adaptativo, use la IA, o agregue vértices a mano en la tabla.")
        self.err_msg.clear()
        try:
            G = _tables_to_graph(ndf, edf, self.directed)
        except GraphInputError as exc:
            self.G = None
            self.err_msg.show_errors(exc)
            self.auto_lbl.configure(text="")
            self.use_btn.configure(state="disabled")
            self.analysis.clear()
            return
        self.G = G
        self.use_btn.configure(state="normal")
        self.auto_lbl.configure(
            text=(f"Detección automática: {self.auto[0]} vértices y {self.auto[1]} aristas · "
                  f"tras su edición: {G.number_of_nodes()} vértices y {G.number_of_edges()} aristas.")
            if self.auto else "")
        self.analysis.show(G)

    def _use_graph(self) -> None:
        if self.G is not None:
            self.app.set_graph(self.G, f"Imagen: {self.fname}")

    def refresh(self) -> None:
        if self._built and self.G is not None:
            self.analysis.show(self.G)


class PageS(ctk.CTkFrame):
    """Ajustes: límite de búsqueda de Hamilton y reinicio de la aplicación."""

    def __init__(self, master, app: "GraphLabApp") -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        c = card(self)
        c.pack(fill="x")
        heading(c, "Ajustes", 16).pack(anchor="w", padx=18, pady=(14, 10))
        heading(c, "Límite de búsqueda de Hamilton (pasos)", 13).pack(anchor="w", padx=18)
        self.seg = ctk.CTkSegmentedButton(c, values=[f"{b:,}" for b in BUDGETS], font=F(12), command=self._set_budget,
                                          selected_color=UI_NAVY, selected_hover_color=UI_NAVY, unselected_color=UI_BG,
                                          unselected_hover_color=UI_LINE, text_color=UI_TEXT)
        self.seg.set(f"{SS.budget:,}")
        self.seg.pack(anchor="w", padx=18, pady=(8, 4))
        caption(c, "Se aplica a la búsqueda de camino y ciclo de Hamilton en los módulos B y C. Un límite mayor "
                   "puede tardar más en grafos grandes.", pad=36).pack(fill="x", padx=18)
        hr(c)
        btn(c, "Reiniciar aplicación", self.app.reset, primary=False, width=220).pack(anchor="w", padx=18, pady=(0, 18))

    def _set_budget(self, value: str) -> None:
        SS.budget = int(value.replace(",", ""))
        self.app.version += 1
        self.app.refresh_current()

    def refresh(self) -> None:
        self.seg.set(f"{SS.budget:,}")


# ============================================================================
# 11. APLICACIÓN PRINCIPAL (VENTANA) Y MAIN
# ============================================================================
NAV = [("A", "A. Creador", "✚"), ("B", "B. Análisis", "▥"), ("C", "C. Imagen", "▣"), ("S", "Ajustes", "⚙")]


class GraphLabApp(ctk.CTkToplevel):
    """Ventana principal: barra superior, riel lateral, resumen del grafo activo y páginas."""

    def __init__(self, master = None) -> None:
        super().__init__(master, fg_color=UI_BG)
        self.title("Euler y Hamilton")
        self.geometry("1360x880")
        self.minsize(1120, 720)
        init_styles()
        self._q: queue.Queue = queue.Queue()
        self.version = 0
        self.page_key = "A"
        self._toast: ctk.CTkFrame | None = None
        self._toast_id: str | None = None
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_nav()
        self._build_rail()
        self._build_content()
        self._make_pages()
        self.update_summary()
        self.after(60, self._poll)
        self.show_page("A")

    # -- construcción ------------------------------------------------------------------------------
    def _build_nav(self) -> None:
        bar = card(self)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(14, 8))
        ctk.CTkLabel(bar, text="Euler y Hamilton", font=F(20, "bold"), text_color=UI_ORANGE).pack(
            side="left", padx=(18, 24), pady=10)
        self.nav_btns: dict[str, ctk.CTkButton] = {}
        for key, text, _icon in NAV:
            b = pill(bar, text, lambda k=key: self.show_page(k))
            b.pack(side="left", padx=2)
            self.nav_btns[key] = b
        info = ctk.CTkFrame(bar, fg_color="transparent")
        info.pack(side="right", padx=18)
        self.nav_name = ctk.CTkLabel(info, text="", font=F(11, "bold"), text_color=UI_TEXT, anchor="e")
        self.nav_name.pack(anchor="e")
        self.nav_count = ctk.CTkLabel(info, text="", font=F(10), text_color=UI_MUTED, anchor="e")
        self.nav_count.pack(anchor="e")

    def _build_rail(self) -> None:
        rail = card(self, width=64)
        rail.grid(row=1, column=0, sticky="ns", padx=(16, 8), pady=(0, 14))
        self.rail_btns: dict[str, ctk.CTkButton] = {}
        for key, text, icon in NAV:
            b = ctk.CTkButton(rail, text=icon, width=42, height=42, corner_radius=12, font=F(18), border_width=0,
                              command=lambda k=key: self.show_page(k))
            style_pill(b, False)
            b.pack(padx=10, pady=(14, 4))
            self.rail_btns[key] = b

    def _build_content(self) -> None:
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll.grid(row=1, column=1, sticky="nsew", padx=(8, 8), pady=(0, 8))
        ctk.CTkLabel(self.scroll, text="Euler y Hamilton", font=F(26, "bold"), text_color=UI_TEXT, anchor="w").pack(
            fill="x", padx=4, pady=(0, 0))
        ctk.CTkLabel(self.scroll, text=SUBTITLE, font=F(12), text_color=UI_MUTED, anchor="w").pack(
            fill="x", padx=4, pady=(0, 12))
        strip = ctk.CTkFrame(self.scroll, fg_color="transparent")
        strip.pack(fill="x", pady=(0, 14))
        strip.columnconfigure(0, weight=3, uniform="top")
        strip.columnconfigure((1, 2), weight=1, uniform="top")
        strip.columnconfigure(3, weight=3, uniform="top")
        self.card_name = StatCard(strip, "Grafo activo", "", highlight=True)
        self.card_name.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.card_v = StatCard(strip, "Vértices", 0)
        self.card_v.grid(row=0, column=1, sticky="nsew", padx=6)
        self.card_e = StatCard(strip, "Aristas", 0)
        self.card_e.grid(row=0, column=2, sticky="nsew", padx=6)
        chips = card(strip, border_width=1, border_color=UI_LINE)
        chips.grid(row=0, column=3, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(chips, text="Tipo de grafo", font=F(11), text_color=UI_MUTED, anchor="w").pack(
            fill="x", padx=14, pady=(10, 4))
        self.chip_flow = ChipFlow(chips)
        self.chip_flow.pack(fill="x", padx=14, pady=(0, 10))
        self.host = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.host.pack(fill="x")

    def _make_pages(self) -> None:
        self.pages: dict[str, ctk.CTkFrame] = {
            "A": PageA(self.host, self), "B": PageB(self.host, self),
            "C": PageC(self.host, self), "S": PageS(self.host, self)}
        self.page_ver = {k: -1 for k in self.pages}

    # -- navegación ----------------------------------------------------------------------------------
    def show_page(self, key: str) -> None:
        for p in self.pages.values():
            p.pack_forget()
        self.page_key = key
        page = self.pages[key]
        page.pack(fill="x")
        if self.page_ver[key] != self.version:
            self.page_ver[key] = self.version
            page.refresh()  # type: ignore[attr-defined]
        for k in self.nav_btns:
            style_pill(self.nav_btns[k], k == key)
            style_pill(self.rail_btns[k], k == key)
        try:
            self.scroll._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def refresh_current(self) -> None:
        self.page_ver[self.page_key] = self.version
        self.pages[self.page_key].refresh()  # type: ignore[attr-defined]

    # -- estado -----------------------------------------------------------------------------------------
    def update_summary(self) -> None:
        G = SS.graph
        self.card_name.set(SS.graph_name)
        self.card_v.set(G.number_of_nodes())
        self.card_e.set(G.number_of_edges())
        self.chip_flow.set_tags(describe_type(G)[:4])
        self.nav_name.configure(text=SS.graph_name)
        self.nav_count.configure(text=f"{G.number_of_nodes()} vértices · {G.number_of_edges()} aristas")

    def set_graph(self, G: nx.Graph, name: str, msg: str | None = None) -> None:
        """Fija el grafo activo y actualiza la interfaz."""
        SS.graph, SS.graph_name = G, name
        self.version += 1
        self.update_summary()
        self.refresh_current()
        self.toast(msg or f"Grafo activo: {name}")

    def reset(self) -> None:
        """Reinicia la aplicación: grafo de ejemplo, ajustes y todas las entradas."""
        SS.reset()
        self.version += 1
        for p in self.pages.values():
            p.destroy()
        self._make_pages()
        self.update_summary()
        self.show_page("A")

    # -- avisos y tareas en segundo plano --------------------------------------------------------------
    def toast(self, msg: str) -> None:
        """Notificación breve (equivale a st.toast)."""
        if self._toast is not None:
            self._toast.destroy()
        if self._toast_id:
            self.after_cancel(self._toast_id)
        t = ctk.CTkFrame(self, fg_color=UI_NAVY, corner_radius=12)
        ctk.CTkLabel(t, text="✔  " + msg, font=F(12), text_color="white").pack(padx=18, pady=10)
        t.place(relx=1.0, y=84, x=-28, anchor="ne")
        t.lift()
        self._toast = t
        self._toast_id = self.after(3200, self._hide_toast)

    def _hide_toast(self) -> None:
        if self._toast is not None:
            self._toast.destroy()
            self._toast = None

    def run_async(self, fn: Callable[[], object], done: Callable[[object, Exception | None], None]) -> None:
        """Ejecuta ``fn`` en un hilo y llama a ``done(resultado, error)`` en el hilo de la interfaz."""
        def worker() -> None:
            try:
                out: tuple = (fn(), None)
            except Exception as exc:  # noqa: BLE001
                out = (None, exc)
            self._q.put((done, out))

        threading.Thread(target=worker, daemon=True).start()

    def _poll(self) -> None:
        try:
            while True:
                done, (res, err) = self._q.get_nowait()
                try:
                    done(res, err)
                except tk.TclError:
                    pass  # el widget ya no existe
        except queue.Empty:
            pass
        self.after(60, self._poll)


def main() -> None:
    """Punto de entrada de la aplicación de escritorio."""
    root = ctk.CTk()
    root.withdraw()
    app = GraphLabApp(root)
    app.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()

if __name__ == "__main__":
    main()
    