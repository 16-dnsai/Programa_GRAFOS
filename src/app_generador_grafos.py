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
        self.geometry("950x650")
        self.minsize(850, 550)

        # Diccionarios seguros para retener las referencias de imágenes en memoria
        self.gallery_images = {}
        self.popup_images = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO: CONTROLES ---
        self.frame_controles = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.frame_controles.grid(row=0, column=0, sticky="nsew")
        self.frame_controles.grid_rowconfigure(4, weight=1)

        self.label_titulo = ctk.CTkLabel(
            self.frame_controles, 
            text="GrafoVision UMG", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.label_titulo.grid(row=0, column=0, padx=20, pady=(30, 20))

        # Botón para ejecutar la lógica del generador de grafos
        self.btn_lanzar = ctk.CTkButton(
            self.frame_controles, 
            text="Iniciar Cámara (Dibujar)", 
            command=self.llamar_logica_generador,
            fg_color="#1f538d",
            hover_color="#14375e",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_lanzar.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_actualizar = ctk.CTkButton(
            self.frame_controles, 
            text="Actualizar Galería", 
            command=self.cargar_galeria_grafos,
            fg_color="gray50",
            hover_color="gray40",
            height=35
        )
        self.btn_actualizar.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.label_info = ctk.CTkLabel(
            self.frame_controles, 
            text="Instrucciones:\n1. Haz clic en 'Iniciar Cámara'.\n2. Mueve un objeto AZUL para trazar.\n3. Oculta el objeto para registrar arista.\n4. Presiona 'G' para guardar grafo.\n5. Presiona 'ESC' para cerrar cámara.\n6. Clic en cualquier grafo de la\n   galería para visualizarlo en grande.", 
            justify="left",
            text_color="gray"
        )
        self.label_info.grid(row=3, column=0, padx=20, pady=20, sticky="sw")

        # --- PANEL DERECHO: GALERÍA ---
        self.frame_galeria_container = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_galeria_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.frame_galeria_container.grid_columnconfigure(0, weight=1)
        self.frame_galeria_container.grid_rowconfigure(1, weight=1)

        self.label_galeria_titulo = ctk.CTkLabel(
            self.frame_galeria_container, 
            text="Grafos Guardados (Galería - Clic para ver en grande)", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.label_galeria_titulo.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.scroll_galeria = ctk.CTkScrollableFrame(self.frame_galeria_container, label_text="")
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
        ventana_visor.geometry("600x650")
        ventana_visor.grab_set()

        frame_visor = ctk.CTkFrame(ventana_visor, fg_color="transparent")
        frame_visor.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_titulo = ctk.CTkLabel(frame_visor, text=nombre_archivo, font=ctk.CTkFont(size=15, weight="bold"))
        lbl_titulo.pack(pady=(0, 10))

        try:
            carpeta_grafos = self.obtener_carpeta_grafos()
            ruta_imagen = os.path.join(carpeta_grafos, nombre_archivo)

            if not os.path.exists(ruta_imagen):
                raise FileNotFoundError(f"No se encontró el archivo en: {ruta_imagen}")

            img_pil = Image.open(ruta_imagen)
            
            # Asignamos la imagen directamente como atributo de la ventana (ventana_visor) 
            # para evitar que Python la borre de memoria mientras la ventana esté abierta.
            ventana_visor.img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(500, 500))

            lbl_imagen = ctk.CTkLabel(frame_visor, text="", image=ventana_visor.img_ctk)
            lbl_imagen.pack(padx=10, pady=10)
        except Exception as e:
            lbl_error = ctk.CTkLabel(frame_visor, text=f"No se pudo cargar la imagen:\n{e}", text_color="red")
            lbl_error.pack(pady=20)
            print(f"Error en visor: {e}")

        btn_cerrar = ctk.CTkButton(
            frame_visor, 
            text="Cerrar", 
            command=ventana_visor.destroy,
            fg_color="gray40",
            hover_color="gray30",
            height=35
        )
        btn_cerrar.pack(pady=(10, 0))

    def cargar_galeria_grafos(self):
        # Limpiar diccionario de galería de manera segura
        self.gallery_images.clear()

        for widget in self.scroll_galeria.winfo_children():
            widget.destroy()

        carpeta_grafos = self.obtener_carpeta_grafos()

        archivos = [f for f in os.listdir(carpeta_grafos) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        archivos.sort(reverse=True)

        if not archivos:
            label_vacio = ctk.CTkLabel(self.scroll_galeria, text="No hay grafos guardados todavía.\n¡Genera uno nuevo con la cámara!", text_color="gray")
            label_vacio.grid(row=0, column=0, padx=20, pady=40)
            return

        row = 0
        col = 0
        for i, archivo in enumerate(archivos):
            ruta_imagen = os.path.join(carpeta_grafos, archivo)
            
            card = ctk.CTkFrame(
                self.scroll_galeria, 
                fg_color=("gray90", "gray17"),
                corner_radius=8
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            card.bind("<Button-1>", lambda e, a=archivo: self.mostrar_grafo_completo(a))

            try:
                img_pil = Image.open(ruta_imagen)
                img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(180, 180))
                
                # Almacenar referencia en memoria de la galería
                self.gallery_images[archivo] = img_ctk

                lbl_img = ctk.CTkLabel(card, text="", image=img_ctk, fg_color="transparent")
                lbl_img.pack(padx=10, pady=(10, 2))
                lbl_img.bind("<Button-1>", lambda e, a=archivo: self.mostrar_grafo_completo(a))
            except Exception as e:
                print(f"Error cargando miniatura {archivo}: {e}")

            lbl_nombre = ctk.CTkLabel(card, text=archivo, font=ctk.CTkFont(size=11), text_color="gray", fg_color="transparent")
            lbl_nombre.pack(padx=10, pady=(0, 10))
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