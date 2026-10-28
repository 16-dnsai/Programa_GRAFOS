import tkinter as tk
from tkinter import ttk, messagebox
import heapq
import time
import threading

class GrafoDijkstra:
    def __init__(self, es_dirigido=False):
        self.adj = {}
        self.posiciones = {}
        self.es_dirigido = es_dirigido

    def agregar_vertice(self, nombre, x=100.0, y=100.0):
        if nombre not in self.adj:
            self.adj[nombre] = []
            self.posiciones[nombre] = (x, y)
            return True
        return False

    def agregar_arista(self, origen, destino, peso):
        if origen not in self.adj:
            self.agregar_vertice(origen)
        if destino not in self.adj:
            self.agregar_vertice(destino)

        actualizada = False
        for i, (v, w) in enumerate(self.adj[origen]):
            if v == destino:
                self.adj[origen][i] = (destino, peso)
                actualizada = True
                break
        if not actualizada:
            self.adj[origen].append((destino, peso))

        if not self.es_dirigido:
            actualizada_inv = False
            for j, (v2, w2) in enumerate(self.adj[destino]):
                if v2 == origen:
                    self.adj[destino][j] = (origen, peso)
                    actualizada_inv = True
                    break
            if not actualizada_inv:
                self.adj[destino].append((origen, peso))

    def resolver_dijkstra(self, origen):
        if origen not in self.adj:
            return {}, {}

        dist = {nodo: float('inf') for nodo in self.adj}
        prev = {nodo: None for nodo in self.adj}
        dist[origen] = 0.0

        pq = [(0.0, origen)]

        while pq:
            d_actual, u = heapq.heappop(pq)
            if d_actual > dist[u]:
                continue

            for vecino, peso in self.adj[u]:
                if dist[u] + peso < dist[vecino]:
                    dist[vecino] = dist[u] + peso
                    prev[vecino] = u
                    heapq.heappush(pq, (dist[vecino], vecino))

        return dist, prev

    def reconstruir_camino(self, prev, origen, destino):
        if destino not in prev or (prev[destino] is None and origen != destino):
            return []

        camino = []
        actual = destino
        while actual is not None:
            camino.append(actual)
            if actual == origen:
                break
            actual = prev[actual]

        camino.reverse()
        return camino if camino and camino[0] == origen else []


DATOS_INICIALES = {
    "nodos": [
        {"id": "Guatemala", "x": 480, "y": 380}, {"id": "Mixco", "x": 430, "y": 370},
        {"id": "VillaNueva", "x": 480, "y": 430}, {"id": "Petapa", "x": 530, "y": 420},
        {"id": "Amatitlan", "x": 470, "y": 480}, {"id": "Antigua", "x": 380, "y": 410},
        {"id": "Jocotenango", "x": 380, "y": 360}, {"id": "CiudadVieja", "x": 370, "y": 460},
        {"id": "Sumpango", "x": 380, "y": 310}, {"id": "Chimaltenango", "x": 330, "y": 310},
        {"id": "Tecpan", "x": 280, "y": 310}, {"id": "Solola", "x": 240, "y": 310},
        {"id": "Panajachel", "x": 230, "y": 370}, {"id": "Quetzaltenango", "x": 160, "y": 310},
        {"id": "Salcaja", "x": 170, "y": 250}, {"id": "Totonicapan", "x": 220, "y": 250},
        {"id": "Huehuetenango", "x": 160, "y": 180}, {"id": "Chiantla", "x": 160, "y": 120},
        {"id": "SantaCruzQuiche", "x": 240, "y": 200}, {"id": "Chichicastenango", "x": 270, "y": 250},
        {"id": "SanMarcos", "x": 90, "y": 280}, {"id": "SanPedroSac", "x": 90, "y": 220},
        {"id": "Escuintla", "x": 450, "y": 540}, {"id": "SantaLuciaCotz", "x": 360, "y": 530},
        {"id": "PuertoSanJose", "x": 450, "y": 620}, {"id": "Iztapa", "x": 520, "y": 620},
        {"id": "Mazatenango", "x": 250, "y": 530}, {"id": "Cuyotenango", "x": 210, "y": 580},
        {"id": "Retalhuleu", "x": 160, "y": 530}, {"id": "Champerico", "x": 140, "y": 620},
        {"id": "Coatepeque", "x": 90, "y": 470}, {"id": "TecunUman", "x": 40, "y": 530},
        {"id": "Sanarate", "x": 560, "y": 330}, {"id": "Guastatoya", "x": 620, "y": 300},
        {"id": "Zacapa", "x": 720, "y": 280}, {"id": "Teculutan", "x": 660, "y": 280},
        {"id": "Chiquimula", "x": 740, "y": 350}, {"id": "Esquipulas", "x": 800, "y": 410},
        {"id": "Jalapa", "x": 620, "y": 400}, {"id": "Cuilapa", "x": 570, "y": 470},
        {"id": "Jutiapa", "x": 660, "y": 470}, {"id": "Coban", "x": 470, "y": 200},
        {"id": "Carcha", "x": 530, "y": 200}, {"id": "PuertoBarrios", "x": 830, "y": 220},
        {"id": "Flores", "x": 580, "y": 80}
    ],
    "aristas": [
        ("Guatemala", "Mixco", 12), ("Guatemala", "VillaNueva", 18), ("Guatemala", "Petapa", 15), 
        ("Guatemala", "Sanarate", 52), ("Guatemala", "Amatitlan", 25), ("Guatemala", "Sumpango", 35),
        ("Mixco", "Sumpango", 22), ("Mixco", "Jocotenango", 28), ("Mixco", "Antigua", 25), ("Mixco", "VillaNueva", 16),
        ("VillaNueva", "Petapa", 8), ("VillaNueva", "Amatitlan", 12), ("VillaNueva", "Antigua", 28), ("VillaNueva", "Cuilapa", 55),
        ("Petapa", "Amatitlan", 14), ("Petapa", "Jalapa", 68), ("Petapa", "Cuilapa", 50), ("Petapa", "Sanarate", 58),
        ("Amatitlan", "CiudadVieja", 32), ("Amatitlan", "Escuintla", 28), ("Amatitlan", "Cuilapa", 42),
        ("Antigua", "Jocotenango", 5), ("Antigua", "CiudadVieja", 8), ("Antigua", "Sumpango", 14), ("Antigua", "Chimaltenango", 26),
        ("Jocotenango", "Sumpango", 16), ("Jocotenango", "Chimaltenango", 22), ("Jocotenango", "CiudadVieja", 10),
        ("CiudadVieja", "SantaLuciaCotz", 42), ("CiudadVieja", "Escuintla", 50),
        ("Sumpango", "Chimaltenango", 12), ("Sumpango", "Tecpan", 32),
        ("Chimaltenango", "Tecpan", 24), ("Chimaltenango", "Chichicastenango", 45), ("Chimaltenango", "SantaLuciaCotz", 58),
        ("Tecpan", "Solola", 35), ("Tecpan", "SantaCruzQuiche", 50), ("Tecpan", "Chichicastenango", 30), ("Tecpan", "Panajachel", 40),
        ("Solola", "Panajachel", 8), ("Solola", "Chichicastenango", 22), ("Solola", "SantaCruzQuiche", 38), ("Solola", "Totonicapan", 45), ("Solola", "Quetzaltenango", 65),
        ("Panajachel", "Chichicastenango", 28), ("Panajachel", "Mazatenango", 70), ("Panajachel", "SantaLuciaCotz", 65),
        ("Chichicastenango", "SantaCruzQuiche", 18), ("Chichicastenango", "Totonicapan", 32), ("Chichicastenango", "Salcaja", 38),
        ("SantaCruzQuiche", "Totonicapan", 30), ("SantaCruzQuiche", "Huehuetenango", 55), ("SantaCruzQuiche", "Coban", 78),
        ("Totonicapan", "Salcaja", 15), ("Totonicapan", "Huehuetenango", 70), ("Totonicapan", "Quetzaltenango", 26),
        ("Salcaja", "Quetzaltenango", 9), ("Salcaja", "SanPedroSac", 45), ("Salcaja", "Huehuetenango", 62),
        ("Huehuetenango", "Chiantla", 7), ("Huehuetenango", "SanPedroSac", 65),
        ("Chiantla", "SanPedroSac", 68),
        ("SanMarcos", "SanPedroSac", 5), ("SanMarcos", "Coatepeque", 48), ("SanMarcos", "TecunUman", 65), ("SanMarcos", "Quetzaltenango", 52),
        ("SanPedroSac", "Coatepeque", 52), ("SanPedroSac", "Quetzaltenango", 48),
        ("Quetzaltenango", "Retalhuleu", 54), ("Quetzaltenango", "Coatepeque", 42),
        ("Coatepeque", "TecunUman", 30), ("Coatepeque", "Champerico", 55), ("Coatepeque", "Retalhuleu", 45),
        ("TecunUman", "Champerico", 60), ("TecunUman", "Retalhuleu", 68),
        ("Retalhuleu", "Champerico", 38), ("Retalhuleu", "Cuyotenango", 18), ("Retalhuleu", "Mazatenango", 26),
        ("Champerico", "Cuyotenango", 42),
        ("Cuyotenango", "Mazatenango", 8), ("Cuyotenango", "SantaLuciaCotz", 55),
        ("Mazatenango", "SantaLuciaCotz", 62),
        ("SantaLuciaCotz", "Escuintla", 35), ("SantaLuciaCotz", "PuertoSanJose", 60),
        ("Escuintla", "PuertoSanJose", 52), ("Escuintla", "Cuilapa", 48), ("Escuintla", "Iztapa", 55),
        ("PuertoSanJose", "Iztapa", 18), ("PuertoSanJose", "Cuilapa", 70),
        ("Iztapa", "Cuilapa", 50),
        ("Sanarate", "Guastatoya", 16), ("Sanarate", "Jalapa", 42), ("Sanarate", "Teculutan", 55),
        ("Guastatoya", "Teculutan", 50), ("Guastatoya", "Zacapa", 68), ("Guastatoya", "Jalapa", 52),
        ("Teculutan", "Zacapa", 22), ("Teculutan", "Jalapa", 60), ("Teculutan", "Chiquimula", 45),
        ("Zacapa", "Chiquimula", 22), ("Zacapa", "Jalapa", 75),
        ("Chiquimula", "Esquipulas", 55), ("Chiquimula", "Jutiapa", 68), ("Chiquimula", "Jalapa", 50),
        ("Esquipulas", "Jutiapa", 72), ("Esquipulas", "Jalapa", 80),
        ("Jalapa", "Jutiapa", 43), ("Jalapa", "Cuilapa", 52),
        ("Cuilapa", "Jutiapa", 55),
        ("Coban", "Carcha", 7), ("Coban", "Sanarate", 75), ("Coban", "Guastatoya", 80),
        ("Carcha", "Guastatoya", 78), ("Carcha", "Teculutan", 75),
        ("Carcha", "Flores", 79), ("Coban", "Flores", 78), ("Chiantla", "Flores", 76),
        ("Flores", "PuertoBarrios", 78), ("Carcha", "PuertoBarrios", 77), ("Zacapa", "PuertoBarrios", 75)
    ]
}


class FilterCombobox(ttk.Entry):
    """Buscador con lista flotante emergente que filtra en tiempo real sin perder foco."""
    def __init__(self, master=None, width=None, **kw):
        super().__init__(master, width=width, **kw)
        self._completion_list = []
        self.popup = None
        self.listbox = None

        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<Down>', self._on_arrow_down)

    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list)

    def set(self, value):
        self.delete(0, tk.END)
        self.insert(0, value)

    def _on_keyrelease(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "FocusOut"):
            if event.keysym == "Escape":
                self._close_popup()
            elif event.keysym == "Return" and self.popup:
                self._select_current_listbox_item()
            return

        texto = self.get().strip().lower()

        if not texto:
            self._close_popup()
            return

        filtrados = [item for item in self._completion_list if texto in item.lower()]

        if filtrados:
            self._show_popup(filtrados)
        else:
            self._close_popup()

    def _show_popup(self, items):
        if not self.popup or not self.popup.winfo_exists():
            self.popup = tk.Toplevel(self)
            self.popup.wm_overrideredirect(True)
            self.popup.attributes("-topmost", True)

            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()
            w = self.winfo_width()
            self.popup.geometry(f"{w}x120+{x}+{y}")

            self.listbox = tk.Listbox(
                self.popup, bg="#1e293b", fg="#ffffff", selectbackground="#0284c7",
                selectforeground="#ffffff", highlightthickness=0, borderwidth=1, relief="solid", font=("Segoe UI", 9)
            )
            self.listbox.pack(fill=tk.BOTH, expand=True)

            self.listbox.bind("<ButtonRelease-1>", self._on_listbox_click)

        self.listbox.delete(0, tk.END)
        for item in items:
            self.listbox.insert(tk.END, item)

    def _close_popup(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
            self.popup = None
            self.listbox = None

    def _select_current_listbox_item(self):
        if self.listbox and self.listbox.curselection():
            index = self.listbox.curselection()[0]
            val = self.listbox.get(index)
            self.set(val)
            self._close_popup()

    def _on_listbox_click(self, event):
        self._select_current_listbox_item()

    def _on_arrow_down(self, event):
        if self.listbox:
            self.listbox.focus_set()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.activate(0)

    def _on_focus_out(self, event):
        self.after(150, self._close_popup)


class AppDijkstraTK(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Algoritmo de Dijkstra - Mapa Vial de Guatemala")
        self.geometry("1300x820")
        self.configure(bg="#0f172a")

        self.grafo = GrafoDijkstra(es_dirigido=False)
        self.camino_resaltado = []
        self.nodo_dragged = None

        self.nodo_explorando = None
        self.aristas_exploradas = set()
        self.aristas_descartadas = set()

        self.zoom_scale = 0.95
        self.pan_x = 20
        self.pan_y = 10

        self.aplicar_estilo_oscuro()
        self.crear_interfaz()
        self.cargar_datos_predeterminados()

    def aplicar_estilo_oscuro(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        BG_DARK = "#0f172a"
        CARD_BG = "#1e293b"
        TEXT_MAIN = "#f8fafc"
        TEXT_MUTED = "#94a3b8"
        ACCENT_CYAN = "#38bdf8"
        ACCENT_ORANGE = "#f97316"

        self.style.configure(".", background=BG_DARK, foreground=TEXT_MAIN, font=("Segoe UI", 9))
        self.style.configure("TFrame", background=BG_DARK)
        self.style.configure("Card.TFrame", background=CARD_BG)
        
        self.style.configure("Header.TLabel", background=CARD_BG, foreground=TEXT_MAIN, font=("Segoe UI", 15, "bold"))
        self.style.configure("SubHeader.TLabel", background=CARD_BG, foreground=TEXT_MUTED, font=("Segoe UI", 8, "italic"))
        self.style.configure("CardTitle.TLabel", background=CARD_BG, foreground=ACCENT_CYAN, font=("Segoe UI", 10, "bold"))

        self.style.configure("Primary.TButton", background="#334155", foreground="#ffffff", font=("Segoe UI", 9, "bold"), borderwidth=0, focuscolor="none")
        self.style.map("Primary.TButton", background=[("active", "#475569"), ("pressed", "#1e293b")])

        self.style.configure("Orange.TButton", background=ACCENT_ORANGE, foreground="#ffffff", font=("Segoe UI", 9, "bold"), borderwidth=0, focuscolor="none")
        self.style.map("Orange.TButton", background=[("active", "#ea580c"), ("pressed", "#c2410c")])

        self.style.configure("TEntry", fieldbackground="#0f172a", foreground="#ffffff", insertcolor="#ffffff")

        self.style.configure("Treeview", background="#0f172a", foreground="#ffffff", fieldbackground="#0f172a", rowheight=24)
        self.style.configure("Treeview.Heading", background="#1e293b", foreground=ACCENT_CYAN, font=("Segoe UI", 9, "bold"))
        self.style.map("Treeview", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])

    def crear_interfaz(self):
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        left_card = ttk.Frame(main_pane, style="Card.TFrame", padding=15, width=340)
        main_pane.add(left_card, weight=0)

        ttk.Label(left_card, text="Dijkstra Engine", style="Header.TLabel").pack(anchor="w")
        ttk.Label(left_card, text="Analisis de rutas viales", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 12))

        f_consulta = ttk.Frame(left_card, style="Card.TFrame")
        f_consulta.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(f_consulta, text="1. Consulta de Ruta", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))

        ttk.Label(f_consulta, text="Municipio Origen:", background="#1e293b", foreground="#94a3b8").pack(anchor="w")
        self.cb_origen = FilterCombobox(f_consulta)
        self.cb_origen.pack(fill=tk.X, pady=(2, 6))

        ttk.Label(f_consulta, text="Municipio Destino:", background="#1e293b", foreground="#94a3b8").pack(anchor="w")
        self.cb_destino = FilterCombobox(f_consulta)
        self.cb_destino.pack(fill=tk.X, pady=(2, 8))

        btn_calc = ttk.Button(f_consulta, text="Calcular Ruta Minima", style="Primary.TButton", command=self.ejecutar_consulta)
        btn_calc.pack(fill=tk.X, pady=2)

        btn_anim = ttk.Button(f_consulta, text="Animar Paso a Paso", style="Orange.TButton", command=self.iniciar_animacion)
        btn_anim.pack(fill=tk.X, pady=2)

        ttk.Separator(left_card, orient='horizontal').pack(fill='x', pady=10)

        f_edit = ttk.Frame(left_card, style="Card.TFrame")
        f_edit.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(f_edit, text="2. Registrar o Editar", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))

        ttk.Label(f_edit, text="Nuevo Municipio:", background="#1e293b", foreground="#94a3b8").pack(anchor="w")
        f_node = ttk.Frame(f_edit, style="Card.TFrame")
        f_node.pack(fill=tk.X, pady=(2, 8))
        self.txt_nodo = ttk.Entry(f_node)
        self.txt_nodo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(f_node, text="+ Nodo", style="Primary.TButton", command=self.gui_add_nodo).pack(side=tk.RIGHT)

        ttk.Label(f_edit, text="Conectar Municipios (U - V):", background="#1e293b", foreground="#94a3b8").pack(anchor="w")
        f_edge_uv = ttk.Frame(f_edit, style="Card.TFrame")
        f_edge_uv.pack(fill=tk.X, pady=(2, 4))
        self.cb_u = FilterCombobox(f_edge_uv, width=12)
        self.cb_u.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        self.cb_v = FilterCombobox(f_edge_uv, width=12)
        self.cb_v.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

        f_edge_w = ttk.Frame(f_edit, style="Card.TFrame")
        f_edge_w.pack(fill=tk.X, pady=(2, 4))
        self.txt_peso = ttk.Entry(f_edge_w)
        self.txt_peso.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(f_edge_w, text="+ Conexion", style="Primary.TButton", command=self.gui_add_arista).pack(side=tk.RIGHT)

        ttk.Separator(left_card, orient='horizontal').pack(fill='x', pady=10)

        f_zoom = ttk.Frame(left_card, style="Card.TFrame")
        f_zoom.pack(fill=tk.X)
        
        btn_box = ttk.Frame(f_zoom, style="Card.TFrame")
        btn_box.pack(fill=tk.X)
        ttk.Button(btn_box, text="Zoom +", style="Primary.TButton", command=self.zoom_in).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_box, text="Zoom -", style="Primary.TButton", command=self.zoom_out).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_box, text="Reset", style="Primary.TButton", command=self.reset_vista).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        right_container = ttk.Frame(main_pane)
        main_pane.add(right_container, weight=1)

        self.canvas = tk.Canvas(right_container, bg="#0b0f19", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.zoom_in())
        self.canvas.bind("<Button-5>", lambda e: self.zoom_out())
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan)

        f_res_card = ttk.Frame(right_container, style="Card.TFrame", padding=12)
        f_res_card.pack(fill=tk.X)

        f_top_res = ttk.Frame(f_res_card, style="Card.TFrame")
        f_top_res.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(f_top_res, text="Resumen de Resultados", style="CardTitle.TLabel").pack(side=tk.LEFT)
        
        self.lbl_costo_card = tk.Label(f_top_res, text="Costo Total: -- km", font=("Segoe UI", 10, "bold"), bg="#10b981", fg="#ffffff", padx=10, pady=2)
        self.lbl_costo_card.pack(side=tk.RIGHT)

        f_sec = ttk.Frame(f_res_card, style="Card.TFrame")
        f_sec.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(f_sec, text="Ruta:", font=("Segoe UI", 9, "bold"), background="#1e293b", foreground="#38bdf8").pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_ruta_str = ttk.Label(f_sec, text="Seleccione un origen y destino para calcular...", style="SubHeader.TLabel")
        self.lbl_ruta_str.pack(side=tk.LEFT, fill=tk.X, expand=True)

        f_table = ttk.Frame(f_res_card, style="Card.TFrame")
        f_table.pack(fill=tk.BOTH, expand=True)

        columns = ("tramo", "origen", "destino", "distancia", "acumulado")
        self.tree_tramos = ttk.Treeview(f_table, columns=columns, show="headings", height=4)
        
        self.tree_tramos.heading("tramo", text="Tramo")
        self.tree_tramos.heading("origen", text="Origen")
        self.tree_tramos.heading("destino", text="Destino")
        self.tree_tramos.heading("distancia", text="Distancia (km)")
        self.tree_tramos.heading("acumulado", text="Suma Acumulada")

        self.tree_tramos.column("tramo", width=70, anchor="center")
        self.tree_tramos.column("origen", width=150, anchor="w")
        self.tree_tramos.column("destino", width=150, anchor="w")
        self.tree_tramos.column("distancia", width=100, anchor="center")
        self.tree_tramos.column("acumulado", width=120, anchor="center")

        tree_scroll = ttk.Scrollbar(f_table, orient="vertical", command=self.tree_tramos.yview)
        self.tree_tramos.configure(yscrollcommand=tree_scroll.set)

        self.tree_tramos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def to_canvas_coords(self, x, y):
        return x * self.zoom_scale + self.pan_x, y * self.zoom_scale + self.pan_y

    def to_real_coords(self, cx, cy):
        return (cx - self.pan_x) / self.zoom_scale, (cy - self.pan_y) / self.zoom_scale

    def zoom_in(self):
        self.zoom_scale *= 1.2
        self.redibujar()

    def zoom_out(self):
        if self.zoom_scale > 0.3:
            self.zoom_scale /= 1.2
            self.redibujar()

    def reset_vista(self):
        self.zoom_scale = 0.95
        self.pan_x = 20
        self.pan_y = 10
        self.redibujar()

    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def start_pan(self, event):
        self.start_pan_x = event.x
        self.start_pan_y = event.y

    def do_pan(self, event):
        dx = event.x - self.start_pan_x
        dy = event.y - self.start_pan_y
        self.pan_x += dx
        self.pan_y += dy
        self.start_pan_x = event.x
        self.start_pan_y = event.y
        self.redibujar()

    def cargar_datos_predeterminados(self):
        for n in DATOS_INICIALES["nodos"]:
            self.grafo.agregar_vertice(n["id"], n["x"], n["y"])
        for u, v, w in DATOS_INICIALES["aristas"]:
            self.grafo.agregar_arista(u, v, w)

        self.actualizar_combos()
        self.redibujar()

    def actualizar_combos(self):
        nodos = sorted(list(self.grafo.adj.keys()))
        for cb in (self.cb_origen, self.cb_destino, self.cb_u, self.cb_v):
            cb.set_completion_list(nodos)

        if nodos:
            if not self.cb_origen.get() or self.cb_origen.get() not in nodos:
                self.cb_origen.set("Guatemala" if "Guatemala" in nodos else nodos[0])
            if not self.cb_destino.get() or self.cb_destino.get() not in nodos:
                self.cb_destino.set("Quetzaltenango" if "Quetzaltenango" in nodos else nodos[0])

    def gui_add_nodo(self):
        nombre = self.txt_nodo.get().strip()
        if not nombre:
            messagebox.showwarning("Entrada Vacia", "Ingrese un nombre para el nuevo municipio.")
            return

        if self.grafo.agregar_vertice(nombre, x=200.0, y=200.0):
            self.actualizar_combos()
            self.redibujar()
            self.txt_nodo.delete(0, tk.END)
        else:
            messagebox.showerror("Duplicado", f"El municipio '{nombre}' ya existe.")

    def gui_add_arista(self):
        u = self.cb_u.get().strip()
        v = self.cb_v.get().strip()
        p_str = self.txt_peso.get().strip()

        if not u or not v or not p_str:
            messagebox.showwarning("Vacio", "Complete Origen (U), Destino (V) y Peso.")
            return

        try:
            peso = float(p_str)
        except ValueError:
            messagebox.showerror("Peso Invalido", "El peso debe ser un numero valido.")
            return

        if peso < 0:
            messagebox.showerror("Peso Invalido", "No se permiten pesos negativos en Dijkstra.")
            return

        self.grafo.agregar_arista(u, v, peso)
        self.actualizar_combos()
        self.redibujar()
        self.txt_peso.delete(0, tk.END)

    def obtener_peso_arista(self, u, v):
        for vecino, peso in self.grafo.adj.get(u, []):
            if vecino == v:
                return peso
        return 0

    def ejecutar_consulta(self):
        origen = self.cb_origen.get().strip()
        destino = self.cb_destino.get().strip()

        if not origen or not destino:
            return

        self.nodo_explorando = None
        self.aristas_exploradas.clear()
        self.aristas_descartadas.clear()

        distancias, previos = self.grafo.resolver_dijkstra(origen)

        for item in self.tree_tramos.get_children():
            self.tree_tramos.delete(item)

        if origen == destino:
            self.camino_resaltado = [origen]
            self.redibujar()
            self.lbl_costo_card.config(text="Costo Total: 0.0 km", bg="#10b981")
            self.lbl_ruta_str.config(text=f"{origen} (Mismo punto de origen y destino)")
            return

        if distancias.get(destino, float('inf')) == float('inf'):
            self.camino_resaltado = []
            self.redibujar()
            self.lbl_costo_card.config(text="Sin Ruta", bg="#ef4444")
            self.lbl_ruta_str.config(text=f"No existe conexion entre '{origen}' y '{destino}'.")
            messagebox.showwarning("Vertice No Alcanzable", f"No existe ninguna ruta conectada entre '{origen}' y '{destino}'.")
            return

        camino = self.grafo.reconstruir_camino(previos, origen, destino)
        costo_total = distancias[destino]

        self.camino_resaltado = camino
        self.redibujar()

        self.lbl_costo_card.config(text=f"Costo Total: {costo_total:.1f} km", bg="#10b981")
        self.lbl_ruta_str.config(text=" -> ".join(camino))

        suma_acumulada = 0.0
        for i in range(len(camino) - 1):
            u_i = camino[i]
            v_i = camino[i+1]
            w_i = self.obtener_peso_arista(u_i, v_i)
            suma_acumulada += w_i
            self.tree_tramos.insert("", "end", values=(
                f"Tramo {i+1}", u_i, v_i, f"{w_i:.1f} km", f"{suma_acumulada:.1f} km"
            ))

    def iniciar_animacion(self):
        origen = self.cb_origen.get().strip()
        destino = self.cb_destino.get().strip()

        if not origen or not destino or origen == destino:
            return

        threading.Thread(target=self.animar_dijkstra_thread, args=(origen, destino), daemon=True).start()

    def animar_dijkstra_thread(self, origen, destino):
        dist = {nodo: float('inf') for nodo in self.grafo.adj}
        prev = {nodo: None for nodo in self.grafo.adj}
        dist[origen] = 0.0

        pq = [(0.0, origen)]
        self.camino_resaltado = []
        self.aristas_exploradas.clear()
        self.aristas_descartadas.clear()

        while pq:
            d_actual, u = heapq.heappop(pq)
            if d_actual > dist[u]:
                continue

            self.nodo_explorando = u
            self.after(0, self.redibujar)
            time.sleep(0.20)

            if u == destino:
                break

            for vecino, peso in self.grafo.adj[u]:
                clave_arista = tuple(sorted([u, vecino]))
                self.aristas_exploradas.add(clave_arista)

                if dist[u] + peso < dist[vecino]:
                    dist[vecino] = dist[u] + peso
                    prev[vecino] = u
                    heapq.heappush(pq, (dist[vecino], vecino))
                    self.after(0, self.redibujar)
                    time.sleep(0.10)
                else:
                    self.aristas_descartadas.add(clave_arista)
                    self.after(0, self.redibujar)
                    time.sleep(0.06)

        self.nodo_explorando = None
        self.aristas_exploradas.clear()
        self.aristas_descartadas.clear()
        
        self.after(0, self.ejecutar_consulta)

    def redibujar(self):
        self.canvas.delete("all")
        dibujadas = set()

        for u, vecinos in self.grafo.adj.items():
            x1_r, y1_r = self.grafo.posiciones[u]
            x1, y1 = self.to_canvas_coords(x1_r, y1_r)

            for v, peso in vecinos:
                clave = tuple(sorted([u, v]))
                if clave in dibujadas:
                    continue
                dibujadas.add(clave)

                x2_r, y2_r = self.grafo.posiciones[v]
                x2, y2 = self.to_canvas_coords(x2_r, y2_r)

                es_explorada = clave in self.aristas_exploradas
                es_descartada = clave in self.aristas_descartadas

                es_camino = False
                if len(self.camino_resaltado) > 1:
                    for i in range(len(self.camino_resaltado) - 1):
                        u_c, v_c = self.camino_resaltado[i], self.camino_resaltado[i+1]
                        if (u == u_c and v == v_c) or (u == v_c and v == u_c):
                            es_camino = True
                            break

                if es_camino:
                    color = "#00ff87"
                    ancho = max(2.0, 4.5 * self.zoom_scale)
                elif es_descartada:
                    color = "#ef4444"
                    ancho = max(1.5, 2.5 * self.zoom_scale)
                elif es_explorada:
                    color = "#f97316"
                    ancho = max(1.5, 3.0 * self.zoom_scale)
                else:
                    color = "#475569"
                    ancho = max(1.2, 2.0 * self.zoom_scale)

                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=ancho)

                mx, my = (x1 + x2)/2, (y1 + y2)/2
                self.canvas.create_rectangle(mx-12, my-6, mx+12, my+6, fill="#1e293b", outline="#38bdf8")
                self.canvas.create_text(mx, my, text=f"{peso}k", font=("Segoe UI", max(6, int(7.0 * self.zoom_scale)), "bold"), fill="#f8fafc")

        r = max(6.0, 11.0 * self.zoom_scale)
        for nodo, (x_r, y_r) in self.grafo.posiciones.items():
            x, y = self.to_canvas_coords(x_r, y_r)

            fill_col = "#1e293b"
            outline_col = "#38bdf8"
            ancho_borde = 2

            if nodo == self.nodo_explorando:
                fill_col = "#f97316"; outline_col = "#ffedd5"; ancho_borde = 3
            elif nodo in self.camino_resaltado:
                fill_col = "#00ff87"; outline_col = "#ffffff"; ancho_borde = 3
                if nodo == self.camino_resaltado[0]:
                    fill_col = "#0284c7"; outline_col = "#e0f2fe"
                elif nodo == self.camino_resaltado[-1]:
                    fill_col = "#f97316"; outline_col = "#ffedd5"

            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill_col, outline=outline_col, width=ancho_borde, tags=("nodo", nodo))
            self.canvas.create_text(x, y - r - 8, text=nodo, font=("Segoe UI", max(6, int(8.0 * self.zoom_scale)), "bold"), fill="#ffffff")

    def on_click(self, event):
        item = self.canvas.find_withtag("current")
        if item:
            tags = self.canvas.gettags(item[0])
            for t in tags:
                if t in self.grafo.adj:
                    self.nodo_dragged = t
                    return
        self.nodo_dragged = None

    def on_drag(self, event):
        if self.nodo_dragged:
            rx, ry = self.to_real_coords(event.x, event.y)
            self.grafo.posiciones[self.nodo_dragged] = (rx, ry)
            self.redibujar()

if __name__ == "__main__":
    app = AppDijkstraTK()
    app.mainloop()