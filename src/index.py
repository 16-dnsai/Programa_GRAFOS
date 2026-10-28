import os
from PIL import Image
import customtkinter as ctk
from .ciclos_caminos import GraphLabApp
from .algoritmo_disktra import AppDijkstraTK

# Configurar el modo oscuro por defecto y el tema de color
ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Proyecto Grafos")
        self.geometry("1050x700")
        self.minsize(950, 650)

        try:
            self.iconbitmap("img/logo_umg.ico")
        except Exception:
            pass  # Evita errores si el ícono no se encuentra localmente

        # Configuración de la cuadrícula principal de la ventana
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Construir las secciones de la interfaz
        self.create_sidebar()
        self.create_main_content()

    def create_sidebar(self):
        # Barra lateral izquierda (Usa colores adaptativos: Claro / Oscuro)
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("#F4F5F7", "#18181B"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        # --- CARGA DEL LOGO (logo_umg) MÁS GRANDE ---
        try:
            ruta_logo = "img/logo_umg.jpg"  # Ajusta la extensión a .jpg si es necesario
            if os.path.exists(ruta_logo):
                imagen_pil = Image.open(ruta_logo)
                # Tamaño grande de 60x60 píxeles
                self.logo_image = ctk.CTkImage(light_image=imagen_pil, dark_image=imagen_pil, size=(60, 60))
                
                self.logo_img_label = ctk.CTkLabel(
                    self.sidebar_frame, 
                    text="", 
                    image=self.logo_image
                )
                self.logo_img_label.pack(pady=(20, 0), padx=20, anchor="w")
        except Exception as e:
            print(f"No se pudo cargar la imagen del logo: {e}")

        # Título de la app en la barra lateral
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Menú de analisis", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#111827", "#F9FAFB")
        )
        self.logo_label.pack(pady=(8, 20), padx=20, anchor="w")

        # Botones de navegación en la barra lateral
        nav_buttons = [
            ("Generar Grafo", self.mostrar_dashboard),
            ("Euler y Hamilton", self.abrir_nuevo_grafo),
            ("Algoritmo de Dijkstra", self.cargar_grafo),
        ]

        for text, comando in nav_buttons:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=text,
                command=comando,
                fg_color="transparent",
                hover_color=("#E5E7EB", "#27272A"),
                text_color=("#374151", "#D4D4D8"),
                anchor="w",
                font=ctk.CTkFont(size=13),
                height=38
            )
            btn.pack(fill="x", padx=12, pady=4)

        # --- BOTÓN PARA CAMBIAR DE TEMA (Inicia en Modo Claro ya que arrancamos en Oscuro) ---
        self.btn_tema = ctk.CTkButton(
            self.sidebar_frame,
            text="☀️  Modo Claro",
            command=self.alternar_tema,
            fg_color="transparent",
            hover_color=("#E5E7EB", "#27272A"),
            text_color=("#374151", "#D4D4D8"),
            anchor="w",
            font=ctk.CTkFont(size=13),
            height=38
        )
        self.btn_tema.pack(side="bottom", fill="x", padx=12, pady=(5, 0))

        # Botón de Salir al fondo de la barra lateral
        self.btn_salir = ctk.CTkButton(
            self.sidebar_frame,
            text="🚪   Salir",
            command=self.quit,
            fg_color="transparent",
            hover_color=("#FEE2E2", "#450A0A"),
            text_color=("#DC2626", "#F87171"),
            anchor="w",
            font=ctk.CTkFont(size=13),
            height=38
        )
        self.btn_salir.pack(side="bottom", fill="x", padx=12, pady=(0, 20))

    def alternar_tema(self):
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            ctk.set_appearance_mode("Light")
            self.btn_tema.configure(text="🌙  Modo Oscuro")
        else:
            ctk.set_appearance_mode("Dark")
            self.btn_tema.configure(text="☀️  Modo Claro")

    def create_main_content(self):
        # Panel principal derecho con colores adaptativos (Claro / Oscuro)
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("#F8FAFC", "#121212"))
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Cabecera superior de bienvenida
        self.welcome_label = ctk.CTkLabel(
            self.main_frame,
            text="¡Bienvenido, ¿Qué grafo analizaremos hoy?",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#0F172A", "#F9FAFB")
        )
        self.welcome_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=30, pady=(25, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Analizador de grafos",
            font=ctk.CTkFont(size=13),
            text_color=("#64748B", "#94A3B8")
        )
        self.subtitle_label.grid(row=1, column=0, columnspan=3, sticky="w", padx=30, pady=(0, 20))

        # --- Tarjetas Superiores Estilo Dashboard (Fila 2) ---
        self.create_highlight_card(
            2, 0, "Concepto Principal", "¿Qué es un grafo?", 
            "Estructura matemática formada por vértices y aristas que relacionan objetos.", 
            "#FF5A1F", "#FFFFFF"
        )
        self.create_card_info(
            2, 1, "Elemento Base", "¿Qué es un vértice?", 
            "Punto o nodo fundamental que representa una entidad o elemento dentro del grafo."
        )
        self.create_card_info(
            2, 2, "Conexión", "¿Qué es una arista?", 
            "Línea o enlace que conecta dos vértices, representando una relación o interacción."
        )

        # --- Sección de Teoría y Conceptos (Fila 3) ---
        self.section_label = ctk.CTkLabel(
            self.main_frame,
            text="Conceptos Clave de Grafos",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#0F172A", "#F9FAFB")
        )
        self.section_label.grid(row=3, column=0, columnspan=3, sticky="w", padx=30, pady=(25, 10))

        # --- Tarjetas Informativas Inferiores (Fila 4 y 5) ---
        self.create_card_info(4, 0, "Ruta de Aristas", "Camino de Euler", "Camino que recorre cada arista del grafo exactamente una vez.")
        self.create_card_info(4, 1, "Circuito Cerrado", "Ciclo de Euler", "Camino euleriano cerrado que empieza y termina en el mismo vértice.")
        self.create_card_info(4, 2, "Recorrido de Nodos", "Camino de Hamilton", "Camino que visita cada vértice del grafo exactamente una vez.")
        
        self.create_card_info(5, 0, "Ciclo de Nodos", "Ciclo de Hamilton", "Camino hamiltoniano cerrado que inicia y termina en el mismo vértice.")
        self.create_card_info(5, 1, "Ruta Óptima", "Algoritmo de Dijkstra", "Algoritmo para encontrar el camino más corto desde un nodo origen al resto.")

    def create_card_info(self, row, col, title, value, subtitle):
        card = ctk.CTkFrame(
            self.main_frame, 
            fg_color=("#FFFFFF", "#1E1E2E"), 
            corner_radius=12, 
            border_width=1, 
            border_color=("#E2E8F0", "#27272A")
        )
        card.grid(row=row, column=col, sticky="nsew", padx=12, pady=8)
        
        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color=("#64748B", "#A1A1AA"))
        lbl_title.pack(anchor="w", padx=20, pady=(15, 0))

        lbl_value = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=("#334155", "#F4F4F5"))
        lbl_value.pack(anchor="w", padx=20, pady=(5, 0))

        lbl_sub = ctk.CTkLabel(card, text=subtitle, font=ctk.CTkFont(size=11), text_color=("#94A3B8", "#71717A"), wraplength=220, justify="left")
        lbl_sub.pack(anchor="w", padx=20, pady=(5, 15))

    def create_highlight_card(self, row, col, title, value, subtitle, bg_color, text_color):
        card = ctk.CTkFrame(
            self.main_frame, 
            fg_color=bg_color, 
            corner_radius=12
        )
        card.grid(row=row, column=col, sticky="nsew", padx=12, pady=8)
        
        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color="#FFEDD5")
        lbl_title.pack(anchor="w", padx=20, pady=(15, 0))

        lbl_value = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=text_color)
        lbl_value.pack(anchor="w", padx=20, pady=(5, 0))

        lbl_sub = ctk.CTkLabel(card, text=subtitle, font=ctk.CTkFont(size=11), text_color="#FFEDD5", wraplength=220, justify="left")
        lbl_sub.pack(anchor="w", padx=20, pady=(5, 15))

    def mostrar_dashboard(self):
        print("Navegando al Dashboard principal")

    def abrir_nuevo_grafo(self):
        ventana = GraphLabApp(self)   # antes: GraphLabApp()
        ventana.lift()
        ventana.focus()

    def cargar_grafo(self):
        app = AppDijkstraTK()
        app.mainloop()
        print("Acción: Algoritmo de Dijkstra ejecutado y ventana cerrada")

    def mostrar_ayuda(self):
        print("Acción: Mostrar ayuda sobre ciclos y caminos de Hamilton y Euler")
