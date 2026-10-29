import os
import sys
import subprocess
import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppGeneradorGrafos(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GrafoVision UMG - Generador de Grafos Formales")
        self.geometry("980x660")
        self.minsize(850, 550)

        # Diccionario seguro exclusivo para el visor emergente
        self.popup_images = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO: CONTROLES ---
        self.frame_controles = ctk.CTkFrame(self, width=310, corner_radius=0, fg_color=("#f0f0f0", "#121214"))
        self.frame_controles.grid(row=0, column=0, sticky="nsew")
        self.frame_controles.grid_rowconfigure(4, weight=1)

        self.label_titulo = ctk.CTkLabel(
            self.frame_controles, 
            text="GrafoVision UMG", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.label_titulo.grid(row=0, column=0, padx=20, pady=(35, 20), sticky="w")

        # Botón para ejecutar la lógica del generador de grafos
        self.btn_lanzar = ctk.CTkButton(
            self.frame_controles, 
            text="▶ Iniciar Cámara (Dibujar)", 
            command=self.llamar_logica_generador,
            fg_color="#ff5500",
            hover_color="#e04b00",
            height=42,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_lanzar.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_actualizar = ctk.CTkButton(
            self.frame_controles, 
            text="🔄 Actualizar Galería", 
            command=self.cargar_galeria_grafos,
            fg_color=("gray80", "#26262b"),
            hover_color=("gray70", "#36363d"),
            text_color=("black", "white"),
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=13)
        )
        self.btn_actualizar.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Tarjeta informativa integrada estéticamente en la barra lateral
        self.frame_info = ctk.CTkFrame(self.frame_controles, fg_color=("#e4e4e7", "#1a1a1e"), corner_radius=10)
        self.frame_info.grid(row=3, column=0, padx=20, pady=15, sticky="ew")

        self.label_info_titulo = ctk.CTkLabel(
            self.frame_info,
            text="Instrucciones de Uso:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#ff5500", "#ff7733")
        )
        self.label_info_titulo.pack(anchor="w", padx=12, pady=(10, 5))

        self.label_info = ctk.CTkLabel(
            self.frame_info, 
            text="1. Haz clic en 'Iniciar Cámara'.\n2. Mueve un objeto AZUL para trazar.\n3. Oculta el objeto para registrar arista.\n4. Presiona 'G' para guardar grafo.\n5. Presiona 'ESC' para cerrar cámara.\n6. Clic en la galería para ver en grande.", 
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray50")
        )
        self.label_info.pack(anchor="w", padx=12, pady=(0, 12))

        # --- PANEL DERECHO: GALERÍA ---
        self.frame_galeria_container = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_galeria_container.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)
        self.frame_galeria_container.grid_columnconfigure(0, weight=1)
        self.frame_galeria_container.grid_rowconfigure(1, weight=1)

        self.label_galeria_titulo = ctk.CTkLabel(
            self.frame_galeria_container, 
            text="Grafos Guardados (Galería — Clic para ampliar)", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.label_galeria_titulo.grid(row=0, column=0, sticky="w", pady=(0, 15))

        self.scroll_galeria = ctk.CTkScrollableFrame(self.frame_galeria_container, label_text="", fg_color="transparent")
        self.scroll_galeria.grid(row=1, column=0, sticky="nsew")
        self.scroll_galeria.grid_columnconfigure((0, 1), weight=1)

        self.cargar_galeria_grafos()

    def obtener_carpeta_raiz(self):
        """Retorna la ruta absoluta de la carpeta raíz del proyecto (Programa_GRAFOS)."""
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(directorio_actual, ".."))

    def llamar_logica_generador(self):
        """Llama de forma segura a Gerador_grafos.py usando la ruta absoluta dentro de src/."""
        try:
            directorio_actual = os.path.dirname(os.path.abspath(__file__))
            ruta_generador = os.path.join(directorio_actual, "Gerador_grafos.py")
            subprocess.Popen([sys.executable, ruta_generador])
        except Exception as e:
            print(f"Error al invocar la lógica del generador: {e}")

    def obtener_carpeta_grafos(self):
        """Localiza y asegura la existencia de la carpeta 'grafos_guardados' en la raíz."""
        raiz = self.obtener_carpeta_raiz()
        carpeta_grafos = os.path.join(raiz, "grafos_guardados")
        os.makedirs(carpeta_grafos, exist_ok=True)
        return carpeta_grafos

    def mostrar_grafo_completo(self, nombre_archivo):
        """Abre una ventana emergente para visualizar el grafo seleccionado a gran tamaño."""
        ventana_visor = ctk.CTkToplevel(self)
        ventana_visor.title(f"Visualización: {nombre_archivo}")
        ventana_visor.geometry("620x680")
        ventana_visor.grab_set()

        frame_visor = ctk.CTkFrame(ventana_visor, fg_color="transparent")
        frame_visor.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_titulo = ctk.CTkLabel(frame_visor, text=nombre_archivo, font=ctk.CTkFont(size=16, weight="bold"))
        lbl_titulo.pack(pady=(0, 10))

        try:
            carpeta_grafos = self.obtener_carpeta_grafos()
            ruta_imagen = os.path.join(carpeta_grafos, nombre_archivo)

            if not os.path.exists(ruta_imagen):
                raise FileNotFoundError(f"No se encontró el archivo en: {ruta_imagen}")

            img_pil = Image.open(ruta_imagen)
            
            img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(520, 520))
            self.popup_images[nombre_archivo] = img_ctk

            lbl_imagen = ctk.CTkLabel(frame_visor, text="", image=img_ctk)
            lbl_imagen.pack(padx=10, pady=10)
        except Exception as e:
            lbl_error = ctk.CTkLabel(frame_visor, text=f"No se pudo cargar la imagen:\n{e}", text_color="red")
            lbl_error.pack(pady=20)
            print(f"Error en visor: {e}")

        def cerrar_visor():
            if nombre_archivo in self.popup_images:
                del self.popup_images[nombre_archivo]
            ventana_visor.destroy()

        ventana_visor.protocol("WM_DELETE_WINDOW", cerrar_visor)

        btn_cerrar = ctk.CTkButton(
            frame_visor, 
            text="Cerrar", 
            command=cerrar_visor,
            fg_color=("gray70", "#36363d"),
            hover_color=("gray60", "#45454f"),
            height=38,
            corner_radius=8
        )
        btn_cerrar.pack(pady=(15, 0))

    def cargar_galeria_grafos(self):
        # Limpiar widgets previos
        for widget in self.scroll_galeria.winfo_children():
            widget.destroy()

        carpeta_grafos = self.obtener_carpeta_grafos()
        archivos = [f for f in os.listdir(carpeta_grafos) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        archivos.sort(reverse=True)

        if not archivos:
            label_vacio = ctk.CTkLabel(self.scroll_galeria, text="No hay grafos guardados todavía.\n¡Genera uno nuevo con la cámara!", text_color="gray", font=ctk.CTkFont(size=13))
            label_vacio.grid(row=0, column=0, padx=20, pady=40, sticky="nsew")
            return

        row = 0
        col = 0
        for i, archivo in enumerate(archivos):
            ruta_imagen = os.path.join(carpeta_grafos, archivo)
            
            card = ctk.CTkFrame(
                self.scroll_galeria, 
                fg_color=("#ffffff", "#18181b"),
                border_color=("#e4e4e7", "#27272a"),
                border_width=1,
                corner_radius=12
            )
            card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

            card.bind("<Button-1>", lambda e, a=archivo: self.mostrar_grafo_completo(a))

            try:
                img_pil = Image.open(ruta_imagen)
                img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(190, 190))
                
                # Enlace directo de la referencia a la tarjeta para evitar que el recolector de basura la elimine
                card.img_ref = img_ctk

                lbl_img = ctk.CTkLabel(card, text="", image=img_ctk, fg_color="transparent")
                lbl_img.pack(padx=12, pady=(12, 4))
                lbl_img.bind("<Button-1>", lambda e, a=archivo: self.mostrar_grafo_completo(a))
            except Exception as e:
                print(f"Error cargando miniatura {archivo}: {e}")

            lbl_nombre = ctk.CTkLabel(card, text=archivo, font=ctk.CTkFont(size=11, weight="bold"), text_color=("gray50", "gray40"), fg_color="transparent")
            lbl_nombre.pack(padx=12, pady=(0, 12))
            lbl_nombre.bind("<Button-1>", lambda e, a=archivo: self.mostrar_grafo_completo(a))

            col += 1
            if col > 1:
                col = 0
                row += 1

def iniciar_app_grafos():
    app = AppGeneradorGrafos()
    app.mainloop()

if __name__ == "__main__":
    iniciar_app_grafos()