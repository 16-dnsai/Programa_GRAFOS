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

class AppDijkstraTK(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Proyecto Final - Algoritmo de Dijkstra (45 Municipios)")
        self.geometry("1280x780")
        self.configure(bg="#121212")

        self.grafo = GrafoDijkstra(es_dirigido=False)
        self.camino_resaltado = []
        self.nodo_dragged = None

        # Banderas visuales para la animación paso a paso
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

        PANEL_BG = "#1e1e1e"
        TEXT_LIGHT = "#e0e0e0"
        BORDER_COL = "#2c2c2c"

        self.style.configure(".", background=PANEL_BG, foreground=TEXT_LIGHT, font=("Helvetica", 9))
        self.style.configure("TFrame", background=PANEL_BG)
        self.style.configure("TLabelframe", background=PANEL_BG, foreground="#00e676", bordercolor=BORDER_COL)
        self.style.configure("TLabelframe.Label", background=PANEL_BG, foreground="#00e676", font=("Helvetica", 9, "bold"))
        self.style.configure("TLabel", background=PANEL_BG, foreground=TEXT_LIGHT)
        self.style.configure("TButton", background="#2d2d2d", foreground="#ffffff", bordercolor=BORDER_COL, focuscolor="none")
        self.style.map("TButton", background=[("active", "#3d3d3d"), ("pressed", "#4d4d4d")])
        self.style.configure("TEntry", fieldbackground="#2b2b2b", foreground="#ffffff", insertcolor="#ffffff")
        self.style.configure("TCombobox", fieldbackground="#2b2b2b", background="#3d3d3d", foreground="#ffffff", arrowcolor="#ffffff")
        self.style.map("TCombobox", fieldbackground=[("readonly", "#2b2b2b")], foreground=[("readonly", "#ffffff")])

    def crear_interfaz(self):
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_pane, padding=10, width=320)
        main_pane.add(left_frame, weight=0)

        ttk.Label(left_frame, text="Algoritmo de Dijkstra", font=("Helvetica", 14, "bold"), foreground="#00e676").pack(anchor="w", pady=2)
        ttk.Label(left_frame, text="Análisis de Rutas Mínimas (Aristas <= 80 km)", font=("Helvetica", 8, "italic"), foreground="#a0a0a0").pack(anchor="w", pady=(0, 10))

        f_consulta = ttk.LabelFrame(left_frame, text=" 1. Consulta de Ruta ", padding=8)
        f_consulta.pack(fill=tk.X, pady=4)

        ttk.Label(f_consulta, text="Origen:").grid(row=0, column=0, sticky="w", pady=2)
        self.cb_origen = ttk.Combobox(f_consulta, state="readonly")
        self.cb_origen.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(f_consulta, text="Destino:").grid(row=1, column=0, sticky="w", pady=2)
        self.cb_destino = ttk.Combobox(f_consulta, state="readonly")
        self.cb_destino.grid(row=1, column=1, sticky="ew", pady=2)

        f_consulta.columnconfigure(1, weight=1)

        btn_calc = ttk.Button(f_consulta, text="Calcular Ruta Mínima", command=self.ejecutar_consulta)
        btn_calc.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 2))

        btn_anim = ttk.Button(f_consulta, text="Animar Paso a Paso", command=self.iniciar_animacion)
        btn_anim.grid(row=3, column=0, columnspan=2, sticky="ew", pady=2)

        f_edit = ttk.LabelFrame(left_frame, text=" 2. Registrar/Editar ", padding=8)
        f_edit.pack(fill=tk.X, pady=4)

        ttk.Label(f_edit, text="Municipio:").grid(row=0, column=0, sticky="w")
        self.txt_nodo = ttk.Entry(f_edit, width=12)
        self.txt_nodo.grid(row=0, column=1, sticky="ew")
        ttk.Button(f_edit, text="+ Nodo", command=self.gui_add_nodo).grid(row=0, column=2, padx=2)

        ttk.Label(f_edit, text="Arista (U-V):").grid(row=1, column=0, sticky="w", pady=4)
        self.txt_u = ttk.Entry(f_edit, width=5)
        self.txt_u.grid(row=1, column=1, sticky="w")
        self.txt_v = ttk.Entry(f_edit, width=5)
        self.txt_v.grid(row=1, column=1, sticky="e")

        ttk.Label(f_edit, text="Peso:").grid(row=2, column=0, sticky="w")
        self.txt_peso = ttk.Entry(f_edit, width=12)
        self.txt_peso.grid(row=2, column=1, sticky="ew")
        ttk.Button(f_edit, text="+ Conexión", command=self.gui_add_arista).grid(row=2, column=2, padx=2)

        f_edit.columnconfigure(1, weight=1)

        f_zoom = ttk.LabelFrame(left_frame, text=" Controles de Vista ", padding=8)
        f_zoom.pack(fill=tk.X, pady=4)
        
        btn_box = ttk.Frame(f_zoom)
        btn_box.pack(fill=tk.X)
        ttk.Button(btn_box, text="Zoom +", command=self.zoom_in).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_box, text="Zoom -", command=self.zoom_out).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_box, text="Reset Vista", command=self.reset_vista).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        right_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(right_frame, weight=1)

        self.canvas = tk.Canvas(right_frame, bg="#181818", highlightthickness=1, highlightbackground="#2c2c2c")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.zoom_in())
        self.canvas.bind("<Button-5>", lambda e: self.zoom_out())
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.do_pan)

        f_log = ttk.LabelFrame(right_frame, text=" Resultados de la Consulta ", padding=4)
        f_log.pack(fill=tk.X, pady=(6, 0))

        self.txt_log = tk.Text(f_log, height=6, font=("Consolas", 9), bg="#1e1e1e", fg="#00e676", insertbackground="#ffffff", highlightthickness=0)
        self.txt_log.pack(fill=tk.BOTH, expand=True)

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
        self.log(f"Grafo cargado exitosamente con {len(self.grafo.adj)} municipios de Guatemala.")

    def actualizar_combos(self):
        nodos = sorted(list(self.grafo.adj.keys()))
        self.cb_origen['values'] = nodos
        self.cb_destino['values'] = nodos

        if nodos:
            if not self.cb_origen.get() or self.cb_origen.get() not in nodos:
                self.cb_origen.set("Guatemala" if "Guatemala" in nodos else nodos[0])
            if not self.cb_destino.get() or self.cb_destino.get() not in nodos:
                self.cb_destino.set("Quetzaltenango" if "Quetzaltenango" in nodos else nodos[0])

    def gui_add_nodo(self):
        nombre = self.txt_nodo.get().strip()
        if not nombre:
            messagebox.showwarning("Entrada Vacía", "Ingrese un nombre para el nuevo municipio.")
            return

        if self.grafo.agregar_vertice(nombre, x=200.0, y=200.0):
            self.actualizar_combos()
            self.redibujar()
            self.txt_nodo.delete(0, tk.END)
            self.log(f"Municipio registrado: '{nombre}'")
        else:
            messagebox.showerror("Duplicado", f"El municipio '{nombre}' ya existe.")

    def gui_add_arista(self):
        u = self.txt_u.get().strip()
        v = self.txt_v.get().strip()
        p_str = self.txt_peso.get().strip()

        if not u or not v or not p_str:
            messagebox.showwarning("Vacío", "Complete Origen (U), Destino (V) y Peso.")
            return

        try:
            peso = float(p_str)
        except ValueError:
            messagebox.showerror("Peso Inválido", "El peso debe ser un número válido.")
            return

        if peso < 0:
            messagebox.showerror("Peso Inválido", "No se permiten pesos negativos en el algoritmo de Dijkstra.")
            self.log(f"Rechazado intento de ingresar peso negativo ({peso}).")
            return

        self.grafo.agregar_arista(u, v, peso)
        self.actualizar_combos()
        self.redibujar()
        self.log(f"Conexión registrada/actualizada: {u} <-> {v} (Peso: {peso} km)")

    def obtener_peso_arista(self, u, v):
        for vecino, peso in self.grafo.adj.get(u, []):
            if vecino == v:
                return peso
        return 0

    def ejecutar_consulta(self):
        origen = self.cb_origen.get()
        destino = self.cb_destino.get()

        if not origen or not destino:
            return

        self.nodo_explorando = None
        self.aristas_exploradas.clear()
        self.aristas_descartadas.clear()

        distancias, previos = self.grafo.resolver_dijkstra(origen)

        self.txt_log.delete("1.0", tk.END)

        if origen == destino:
            self.camino_resaltado = [origen]
            self.redibujar()
            self.log(f"=== RESULTADO DE CONSULTA: {origen} ➔ {destino} ===")
            self.log(" Costo Total Mínimo: 0.0 km")
            self.log("• El origen y el destino son el mismo municipio.")
            self.log(f"• Secuencia de Vértices (1):\n   {origen}")
            return

        if distancias.get(destino, float('inf')) == float('inf'):
            self.camino_resaltado = []
            self.redibujar()
            self.log(f"=== RESULTADO DE CONSULTA: {origen} ➔ {destino} ===")
            self.log(f" EL VÉRTICE DESTINO '{destino}' NO ES ALCANZABLE DESDE '{origen}'.")
            self.log("• No existe ninguna secuencia de conexiones disponible.")
            messagebox.showwarning("Vértice No Alcanzable", f"No existe ninguna ruta conectada entre '{origen}' y '{destino}'.")
            return

        camino = self.grafo.reconstruir_camino(previos, origen, destino)
        costo_total = distancias[destino]

        self.camino_resaltado = camino
        self.redibujar()

        self.log(f"=== RESULTADO DE CONSULTA: {origen} ➔ {destino} ===")
        self.log(f" Costo Total Mínimo: {costo_total:.1f} km")
        self.log(f"- Secuencia de Vértices ({len(camino)}):")
        self.log("   " + " ➔ ".join(camino))
        self.log("\nDesglose de tramos:")

        for i in range(len(camino) - 1):
            u_i = camino[i]
            v_i = camino[i+1]
            w_i = self.obtener_peso_arista(u_i, v_i)
            self.log(f"   • {u_i} ➔ {v_i}: {w_i} km")

    # METODOS DE ANIMACION PASO A PASO
    def iniciar_animacion(self):
        origen = self.cb_origen.get()
        destino = self.cb_destino.get()

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
            time.sleep(0.3)

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
                    time.sleep(0.15)
                else:
                    self.aristas_descartadas.add(clave_arista)
                    self.after(0, self.redibujar)
                    time.sleep(0.1)

        self.nodo_explorando = None
        self.aristas_exploradas.clear()
        self.aristas_descartadas.clear()
        
        camino = self.grafo.reconstruir_camino(prev, origen, destino)
        self.camino_resaltado = camino
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

                # Jerarquía visual de colores
                if es_camino:
                    color = "#00e676"  # Verde (Ruta Definitiva)
                    ancho = max(1.0, 3.5 * self.zoom_scale)
                elif es_descartada:
                    color = "#ff1744"  # Rojo (Ruta Descartada)
                    ancho = max(1.0, 2.0 * self.zoom_scale)
                elif es_explorada:
                    color = "#ffab00"  # Amarillo/Naranja (En Evaluación)
                    ancho = max(1.0, 2.5 * self.zoom_scale)
                else:
                    color = "#424242"  # Gris (Sin Visitar)
                    ancho = max(1.0, 1.2 * self.zoom_scale)

                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=ancho)

                mx, my = (x1 + x2)/2, (y1 + y2)/2
                self.canvas.create_rectangle(mx-11, my-5, mx+11, my+5, fill="#212121", outline="#333333")
                self.canvas.create_text(mx, my, text=f"{peso}k", font=("Helvetica", max(5, int(6.5 * self.zoom_scale)), "bold"), fill="#b0bec5")

        r = max(4.0, 10.0 * self.zoom_scale)
        for nodo, (x_r, y_r) in self.grafo.posiciones.items():
            x, y = self.to_canvas_coords(x_r, y_r)

            fill_col = "#263238"
            outline_col = "#80deea"

            if nodo == self.nodo_explorando:
                fill_col = "#ff6d00"   # Naranja (Nodo Activo)
                outline_col = "#ffd600"
            elif nodo in self.camino_resaltado:
                fill_col = "#1b5e20"   # Verde
                outline_col = "#00e676"
                if nodo == self.camino_resaltado[0]:
                    fill_col = "#b71c1c"  # Rojo (Origen)
                    outline_col = "#ff5252"
                elif nodo == self.camino_resaltado[-1]:
                    fill_col = "#f57f17"  # Amarillo (Destino)
                    outline_col = "#ffeb3b"

            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill_col, outline=outline_col, width=2, tags=("nodo", nodo))
            self.canvas.create_text(x, y - r - 6, text=nodo, font=("Helvetica", max(5, int(7.5 * self.zoom_scale)), "bold"), fill="#e0e0e0")

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

    def log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)

# if __name__ == "__main__":
#     app = AppDijkstraTK()
#     app.mainloop()