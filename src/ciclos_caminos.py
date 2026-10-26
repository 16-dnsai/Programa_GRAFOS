"""
=============================================================
  ANÁLISIS DE GRAFOS - GUI 2x2 (Detección Mejorada)
=============================================================
"""

import cv2
import numpy as np
import networkx as nx
import pytesseract
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os, math, time, traceback


def select_image():
    root = tk.Tk(); root.withdraw()
    path = filedialog.askopenfilename(
        title="Selecciona la imagen del grafo",
        filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos", "*.*")]
    )
    root.destroy()
    return path

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return gray, thresh

def detect_nodes(gray, min_area=150, max_area=15000):
    """
    Detección robusta de nodos usando HoughCircles + fallback con RETR_TREE.
    """
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    nodes = []
    
    # 1. Intentar con HoughCircles (parámetros permisivos)
    circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, dp=1, minDist=25,
                               param1=50, param2=20, minRadius=12, maxRadius=60)
    
    if circles is not None:
        for (x, y, r) in np.round(circles[0]).astype(int):
            if min_area <= math.pi * r * r <= max_area:
                nodes.append((x, y, r))
        print(f"  [Debug] HoughCircles encontró {len(nodes)} posibles nodos.")
                
    # 2. Fallback: si Hough falla, usar contornos con RETR_TREE
    if not nodes:
        print("  [Debug] HoughCircles no detectó nodos. Usando contornos...")
        _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            for c in contours:
                area = cv2.contourArea(c)
                if area < min_area or area > max_area: continue
                perim = cv2.arcLength(c, True)
                if perim == 0: continue
                circ = 4 * math.pi * area / (perim ** 2)
                if circ < 0.65: continue # Filtro de circularidad
                x, y, w, h = cv2.boundingRect(c)
                if max(w,h) == 0: continue
                aspect = min(w,h) / max(w,h)
                if aspect < 0.7: continue # Filtro de aspecto
                nodes.append((x + w // 2, y + h // 2, int((w + h) / 4)))
            print(f"  [Debug] Contornos encontró {len(nodes)} posibles nodos.")

    # 3. Si aún no hay nodos pero Hough encontró algo, usarlos sin filtro estricto
    if not nodes and circles is not None:
        for (x, y, r) in np.round(circles[0]).astype(int):
            nodes.append((x, y, r))

    # Deduplicar nodos cercanos
    unique = []
    for n in nodes:
        if not any(math.hypot(n[0] - u[0], n[1] - u[1]) < max(n[2], u[2]) * 0.8 for u in unique):
            unique.append(n)
            
    return unique

def extract_labels(img, nodes):
    labels_raw = []
    for (x, y, r) in nodes:
        pad = int(r * 0.6) 
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(img.shape[1], x + pad), min(img.shape[0], y + pad)
        roi = img[y1:y2, x1:x2]
        if roi.size == 0:
            labels_raw.append(None); continue
        g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        if np.mean(th) > 127: th = 255 - th
        th = cv2.resize(th, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        try:
            txt = pytesseract.image_to_string(
                th, config="--psm 10 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            ).strip()
            
            # Corrección de errores comunes de OCR
            txt = txt.replace('O', '0').replace('o', '0')
            txt = txt.replace('l', '1').replace('I', '1').replace('i', '1')
            txt = txt.replace('Z', '2').replace('z', '2')
            txt = txt.replace('S', '5').replace('s', '5')
            txt = txt.replace('B', '8')
            txt = txt.replace('G', '6').replace('b', '6')
            txt = txt.replace('g', '9').replace('q', '9')
        except Exception: 
            txt = ""
        labels_raw.append(txt if txt else None)
    
    labels_final, seen, counter = [], set(), 1
    for lab in labels_raw:
        if lab and lab not in seen:
            labels_final.append(lab); seen.add(lab)
        else:
            while str(counter) in seen: counter += 1
            labels_final.append(str(counter)); seen.add(str(counter)); counter += 1
    return labels_final

def _edge_exists(gray, n1, n2, samples=70, dark_thresh=110, min_ratio=0.65):
    x1, y1, r1 = n1; x2, y2, r2 = n2
    L = math.hypot(x2 - x1, y2 - y1)
    if L <= (r1 + r2 + 4): return False
    t0, t1 = (r1 + 3) / L, 1 - (r2 + 3) / L
    if t1 <= t0: return False
    dark = 0
    for i in range(samples):
        t = t0 + (t1 - t0) * i / (samples - 1)
        px, py = int(round(x1 + t * (x2 - x1))), int(round(y1 + t * (y2 - y1)))
        reg = gray[max(0, py - 2):py + 3, max(0, px - 2):px + 3]
        if reg.size > 0 and reg.min() < dark_thresh: dark += 1
    return dark / samples >= min_ratio

def _has_arrow_near(gray, n1, n2, half=14):
    x1, y1, r1 = n1; x2, y2, r2 = n2
    L = math.hypot(x2 - x1, y2 - y1)
    if L < (r1 + r2 + 20): return False
    
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    px, py = -uy, ux
    
    def width_at(cx, cy):
        cnt = 0
        for w in range(-half, half + 1):
            xx, yy = int(round(cx + w * px)), int(round(cy + w * py))
            if 0 <= xx < gray.shape[1] and 0 <= yy < gray.shape[0] and gray[yy, xx] < 110:
                cnt += 1
        return cnt
        
    # Medir lejos del nodo para evitar el borde curvo del círculo
    t_end = 1 - (r2 + 15) / L
    if t_end <= 0.2: return False
        
    w_end = width_at(x1 + t_end * (x2 - x1), y1 + t_end * (y2 - y1))
    w_mid = width_at(x1 + 0.5 * (x2 - x1), y1 + 0.5 * (y2 - y1))
    
    # Un ensanchamiento claro indica flecha
    return w_end >= max(w_mid + 6, 12)

def detect_edges(gray, nodes):
    edges, n = [], len(nodes)
    for i in range(n):
        for j in range(i + 1, n):
            if not _edge_exists(gray, nodes[i], nodes[j]): continue
            to_j = _has_arrow_near(gray, nodes[i], nodes[j])
            to_i = _has_arrow_near(gray, nodes[j], nodes[i])
            if to_j and not to_i: edges.append((i, j, True))
            elif to_i and not to_j: edges.append((j, i, True))
            elif to_i and to_j: edges += [(i, j, True), (j, i, True)]
            else: edges.append((i, j, False))
    return edges

def build_graph(nodes, labels, edges):
    directed = any(e[2] for e in edges)
    G = nx.DiGraph() if directed else nx.Graph()
    for i, lab in enumerate(labels):
        G.add_node(lab, pos=(nodes[i][0], nodes[i][1]))
    for (i, j, _) in edges:
        G.add_edge(labels[i], labels[j])
    return G, directed

def analyze_euler(G, directed):
    res = {"path": None, "circuit": None}
    if G.number_of_edges() == 0 or G.number_of_nodes() == 0: return res
    if directed:
        if not nx.is_weakly_connected(G): return res
        diff = {v: G.out_degree(v) - G.in_degree(v) for v in G.nodes()}
        starts = [v for v, d in diff.items() if d == 1]
        ends = [v for v, d in diff.items() if d == -1]
        if any(d not in (-1, 0, 1) for d in diff.values()): return res
        if not starts and not ends:
            try:
                c = list(nx.eulerian_circuit(G)); res["circuit"] = c; res["path"] = c
            except Exception: pass
        elif len(starts) == 1 and len(ends) == 1:
            try: res["path"] = list(nx.eulerian_path(G))
            except Exception: pass
    else:
        if not nx.is_connected(G): return res
        odd = [v for v in G.nodes() if G.degree(v) % 2 == 1]
        if len(odd) == 0:
            try:
                c = list(nx.eulerian_circuit(G)); res["circuit"] = c; res["path"] = c
            except Exception: pass
        elif len(odd) == 2:
            try: res["path"] = list(nx.eulerian_path(G))
            except Exception: pass
    return res

def find_hamilton(G, max_nodes=22, time_limit=8.0):
    nodes = list(G.nodes()); n = len(nodes)
    res = {"path": None, "circuit": None}
    if n == 0 or n > max_nodes: return res
    start_t = time.time(); timed_out = [False]
    def dfs(v, visited, path, need_cycle):
        if time.time() - start_t > time_limit:
            timed_out[0] = True; return None
        if len(path) == n:
            if need_cycle: return path + [path[0]] if path[0] in G.neighbors(path[-1]) else None
            return path
        for w in G.neighbors(v):
            if w not in visited:
                visited.add(w); path.append(w)
                r = dfs(w, visited, path, need_cycle)
                if r: return r
                path.pop(); visited.remove(w)
                if timed_out[0]: return None
        return None
    for s in nodes:
        r = dfs(s, {s}, [s], False)
        if r: res["path"] = r; break
        if timed_out[0]: break
    if not timed_out[0]:
        for s in nodes:
            r = dfs(s, {s}, [s], True)
            if r: res["circuit"] = r; break
            if timed_out[0]: break
    return res

_COLOR_SEQ = [(0, 0, 255), (0, 128, 255), (0, 255, 255), (0, 255, 0),
              (255, 255, 0), (255, 128, 0), (255, 0, 0),
              (255, 0, 255), (128, 0, 255), (0, 128, 128)]

def draw_path(img, nodes, labels, seq, output_path):
    out = img.copy()
    lab2node = {lab: nodes[i] for i, lab in enumerate(labels)}
    for step in range(len(seq) - 1):
        u, v = seq[step], seq[step + 1]
        if u not in lab2node or v not in lab2node: continue
        p1, r1 = lab2node[u][:2], lab2node[u][2]
        p2, r2 = lab2node[v][:2], lab2node[v][2]
        L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        if L < 1: continue
        
        ux, uy = (p2[0] - p1[0]) / L, (p2[1] - p1[1]) / L
        a = (int(p1[0] + ux * r1), int(p1[1] + uy * r1))
        b = (int(p2[0] - ux * r2), int(p2[1] - uy * r2))
        
        col = _COLOR_SEQ[step % len(_COLOR_SEQ)]
        cv2.arrowedLine(out, a, b, col, 3, tipLength=0.15)
        
        mid = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
        cv2.putText(out, str(step + 1), (mid[0] + 6, mid[1] - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3)
        cv2.putText(out, str(step + 1), (mid[0] + 6, mid[1] - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2)
    cv2.imwrite(output_path, out)
    return out

def analyze_and_draw(img, path):
    results = {
        "euler_circuit": {"img": None, "seq": None},
        "euler_path": {"img": None, "seq": None},
        "hamilton_path": {"img": None, "seq": None},
        "hamilton_circuit": {"img": None, "seq": None}
    }

    gray, _ = preprocess(img)
    nodes = detect_nodes(gray)
    
    if not nodes:
        print("\n❌ ERROR CRÍTICO: No se detectaron nodos en la imagen.")
        print("   Posibles causas:")
        print("   1. La imagen es demasiado borrosa o los círculos no son claros.")
        print("   2. Los nodos son muy pequeños o muy grandes.")
        return results

    labels = extract_labels(img, nodes)
    edges = detect_edges(gray, nodes)
    G, directed = build_graph(nodes, labels, edges)

    print(f"\n[1] Nodos detectados: {len(nodes)}")
    for i, (x, y, r) in enumerate(nodes):
        print(f"    • Nodo '{labels[i]}' en ({x},{y}) r={r}")
    print(f"[2] Aristas detectadas: {len(edges)}")
    print(f"[3] Grafo {'DIRIGIDO' if directed else 'NO DIRIGIDO'}")
    
    euler = analyze_euler(G, directed)
    ham = find_hamilton(G)
    
    base = os.path.splitext(os.path.basename(path))[0]
    out_dir = os.path.dirname(path) or "."

    if euler["circuit"]:
        seq = [euler["circuit"][0][0]] + [e[1] for e in euler["circuit"]]
        p = os.path.join(out_dir, f"{base}_euler_circuit.png")
        results["euler_circuit"]["img"] = draw_path(img, nodes, labels, seq, p)
        results["euler_circuit"]["seq"] = seq
        seq_path = seq[:-1]
        p2 = os.path.join(out_dir, f"{base}_euler_path.png")
        results["euler_path"]["img"] = draw_path(img, nodes, labels, seq_path, p2)
        results["euler_path"]["seq"] = seq_path
    elif euler["path"]:
        seq = [euler["path"][0][0]] + [e[1] for e in euler["path"]]
        p = os.path.join(out_dir, f"{base}_euler_path.png")
        results["euler_path"]["img"] = draw_path(img, nodes, labels, seq, p)
        results["euler_path"]["seq"] = seq

    if ham["circuit"]:
        seq = ham["circuit"]
        p = os.path.join(out_dir, f"{base}_hamilton_circuit.png")
        results["hamilton_circuit"]["img"] = draw_path(img, nodes, labels, seq, p)
        results["hamilton_circuit"]["seq"] = seq
        seq_path = seq[:-1]
        p2 = os.path.join(out_dir, f"{base}_hamilton_path.png")
        results["hamilton_path"]["img"] = draw_path(img, nodes, labels, seq_path, p2)
        results["hamilton_path"]["seq"] = seq_path
    elif ham["path"]:
        seq = ham["path"]
        p = os.path.join(out_dir, f"{base}_hamilton_path.png")
        results["hamilton_path"]["img"] = draw_path(img, nodes, labels, seq, p)
        results["hamilton_path"]["seq"] = seq

    return results

def show_results_gui(results, base_name):
    root = tk.Tk()
    root.title(f"🔍 Análisis de Grafo — {base_name}")
    root.geometry("1400x900")
    root.configure(bg="#263238")

    header = tk.Label(root, text=f"Análisis del grafo: {base_name}",
                      font=("Arial", 16, "bold"), bg="#263238", fg="white")
    header.grid(row=0, column=0, columnspan=2, pady=8)

    PANEL_W, PANEL_H = 640, 340
    panels = [
        ("🟢 Ciclo de Euler",       "euler_circuit"),
        ("🟡 Camino de Euler",      "euler_path"),
        ("🔵 Camino de Hamilton",   "hamilton_path"),
        ("🔴 Ciclo de Hamilton",    "hamilton_circuit"),
    ]

    image_refs = []

    for idx, (title, key) in enumerate(panels):
        row, col = (idx // 2) + 1, idx % 2
        frame = tk.LabelFrame(root, text=title, font=("Arial", 13, "bold"),
                              fg="#0d47a1", bg="#eceff1", bd=2, relief="ridge")
        frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        data = results.get(key)
        img_array = data.get("img") if data else None
        seq = data.get("seq") if data else None

        if img_array is not None:
            rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            pil_img.thumbnail((PANEL_W, PANEL_H), Image.LANCZOS)
            photo = ImageTk.PhotoImage(pil_img)
            image_refs.append(photo)
            
            lbl_img = tk.Label(frame, image=photo, bg="#eceff1")
            lbl_img.image = photo
            lbl_img.pack(side="top", expand=True, fill="both", padx=5, pady=(5, 0))
            
            if seq:
                seq_str = " → ".join(str(s) for s in seq)
                lbl_seq = tk.Label(frame, text=f"Recorrido: {seq_str}",
                                   font=("Arial", 11, "bold"), bg="#eceff1", fg="#0d47a1",
                                   wraplength=PANEL_W - 20)
                lbl_seq.pack(side="top", pady=(0, 8))
        else:
            lbl_err = tk.Label(frame, text="❌ No existe", font=("Arial", 18, "italic"),
                               fg="#c62828", bg="#eceff1")
            lbl_err.pack(expand=True, pady=80)

    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    result = {"continue": False}

    def load_another():
        result["continue"] = True
        root.destroy()

    def exit_app():
        result["continue"] = False
        root.destroy()

    btn_frame = tk.Frame(root, bg="#263238")
    btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

    tk.Button(btn_frame, text="📂  Cargar otra imagen", command=load_another,
              bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
              padx=25, pady=10, relief="raised", bd=3,
              activebackground="#388e3c").pack(side="left", padx=20)
    tk.Button(btn_frame, text="🚪  Salir", command=exit_app,
              bg="#f44336", fg="white", font=("Arial", 12, "bold"),
              padx=25, pady=10, relief="raised", bd=3,
              activebackground="#c62828").pack(side="right", padx=20)

    root.protocol("WM_DELETE_WINDOW", exit_app)
    root.mainloop()
    return result["continue"]


# ==================================================================
# Esta es la que debes llamar pedazo de HOMOSEXUAL
# ==================================================================
def iniciar_analisis_grafo():
    while True:
        path = select_image()
        if not path:
            print("\n👋 No se seleccionó imagen. Saliendo.")
            break

        img = cv2.imread(path)
        if img is None:
            print(f"❌ No se pudo leer: {path}")
            continue

        print(f"\n{'='*60}\n📷 Procesando: {path}\n{'='*60}")
        try:
            results = analyze_and_draw(img, path)
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            traceback.print_exc()
            continue

        base = os.path.splitext(os.path.basename(path))[0]
        if not show_results_gui(results, base):
            print("\n👋 Programa finalizado.")
            break

# ==================================================================
if __name__ == "__main__":
    try:
        iniciar_analisis_grafo()
    except Exception:
        traceback.print_exc()