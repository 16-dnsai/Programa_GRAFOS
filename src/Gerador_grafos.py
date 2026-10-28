import cv2
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os
from datetime import datetime

# Configurar la cámara web
cap = cv2.VideoCapture(0)

# Parámetros de dibujo
ancho_lienzo = 640
alto_lienzo = 480
umbral_distancia_nodos = 50 # Distancia mínima para fusionar un punto con un nodo existente

# Variables de estado para el grafo
grafo_actual = nx.Graph()
posiciones_nodos = {}       # Diccionario {id_nodo: (x, y)}
contador_nodos = 1          # Empezamos desde 1 para que coincida con tu ejemplo numérico
dibujando = False
coordenadas_trazo_actual = []

# Lienzo persistente para mostrar los trazos en pantalla
lienzo_persistencia = None

def generar_imagen_grafo(grafo, posiciones, nombre_archivo="grafo_detectado.png"):
    """
    Toma el grafo de NetworkX y lo renderiza con un estilo formal y limpio 
    idéntico a los diagramas de matemáticas discretas.
    """
    plt.figure(figsize=(6, 6))
    
    nx.draw(
        grafo, 
        pos=posiciones, 
        with_labels=True, 
        node_size=1200,          # Tamaño del círculo del nodo
        node_color='white',      # Fondo blanco del nodo
        edgecolors='black',      # Borde negro alrededor del nodo
        linewidths=2.5,          # Grosor del borde
        font_size=14,            # Tamaño del número dentro del nodo
        font_weight='bold',      # Negrita para los números
        font_color='black',      # Color del texto
        edge_color='black',      # Color de las aristas
        width=2.5,               # Grosor de las aristas
        alpha=1.0
    )
    
    plt.axis('off')
    plt.savefig(nombre_archivo, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✅ Imagen de grafo generada exitosamente: {nombre_archivo}")

os.makedirs('grafos_guardados', exist_ok=True)
print("Iniciando creador de grafos interactivo (Modo Objeto Rojo)...")
print("👉 Mueve un objeto rojo brillante frente a la cámara para trazar y conectar nodos.")
print("⌨️ Controles: 'ESC' para salir, 'G' para guardar imagen formal, 'C' para limpiar lienzo.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("No se pudo acceder a la cámara.")
        break

    # Efecto espejo
    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    
    if lienzo_persistencia is None:
        lienzo_persistencia = np.zeros((h, w, 3), dtype=np.uint8)

    # Conversión a espacio HSV para detección precisa de color rojo
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Rango de color HSV para detectar ROJO (al estar en los extremos del espectro HSV, se usan dos rangos)
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2
    
    # Limpieza de ruido en la máscara
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    punto_actual = None
    if contours:
        # Encontrar el contorno más grande correspondiente al objeto rojo
        c_max = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c_max) > 300:
            ((x, y), radius) = cv2.minEnclosingCircle(c_max)
            if radius > 5:
                punto_actual = (int(x), int(y))
                cv2.circle(frame, punto_actual, int(radius), (0, 0, 255), 2)
                cv2.circle(frame, punto_actual, 5, (0, 255, 255), -1)

    # Lógica de dibujo interactivo
    tecla = cv2.waitKey(5) & 0xFF
    
    if punto_actual is not None:
        dibujando = True
        cv2.putText(frame, "TRAZANDO...", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        coordenadas_trazo_actual.append(punto_actual)
        
        if len(coordenadas_trazo_actual) > 1:
            cv2.line(lienzo_persistencia, coordenadas_trazo_actual[-2], coordenadas_trazo_actual[-1], (0, 255, 255), 3)
    else:
        if dibujando:
            dibujando = False
            if len(coordenadas_trazo_actual) > 5:
                punto_inicio = coordenadas_trazo_actual[0]
                punto_fin = coordenadas_trazo_actual[-1]
                
                # Nodo origen
                id_nodo_inicio = None
                for nid, pos in posiciones_nodos.items():
                    if np.sqrt((pos[0] - punto_inicio[0])**2 + (pos[1] - punto_inicio[1])**2) < umbral_distancia_nodos:
                        id_nodo_inicio = nid
                        break
                if id_nodo_inicio is None:
                    id_nodo_inicio = contador_nodos
                    grafo_actual.add_node(id_nodo_inicio)
                    posiciones_nodos[id_nodo_inicio] = punto_inicio
                    contador_nodos += 1

                # Nodo destino
                id_nodo_fin = None
                for nid, pos in posiciones_nodos.items():
                    if np.sqrt((pos[0] - punto_fin[0])**2 + (pos[1] - punto_fin[1])**2) < umbral_distancia_nodos:
                        id_nodo_fin = nid
                        break
                if id_nodo_fin is None:
                    id_nodo_fin = contador_nodos
                    grafo_actual.add_node(id_nodo_fin)
                    posiciones_nodos[id_nodo_fin] = punto_fin
                    contador_nodos += 1

                if id_nodo_inicio != id_nodo_fin:
                    grafo_actual.add_edge(id_nodo_inicio, id_nodo_fin)

            coordenadas_trazo_actual = []

    frame_con_lienzo = cv2.addWeighted(frame, 0.7, lienzo_persistencia, 0.3, 0)
    
    for nid, pos in posiciones_nodos.items():
        cv2.circle(frame_con_lienzo, pos, 18, (255, 255, 255), -1)
        cv2.circle(frame_con_lienzo, pos, 18, (0, 0, 0), 2)
        cv2.putText(frame_con_lienzo, str(nid), (pos[0] - 7, pos[1] + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    cv2.imshow('Generador de Grafos Formales', frame_con_lienzo)

    if tecla == 27:  # ESC
        break
    elif tecla == ord('g'):  # Guardar
        if len(grafo_actual.nodes) > 0:
            nombre_fichero = f"grafos_guardados/grafo_formal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            generar_imagen_grafo(grafo_actual, posiciones_nodos, nombre_fichero)
        else:
            print("⚠️ Dibuja al menos un nodo antes de guardar.")
    elif tecla == ord('c'):  # Limpiar
        grafo_actual.clear()
        posiciones_nodos.clear()
        contador_nodos = 1
        lienzo_persistencia = np.zeros((h, w, 3), dtype=np.uint8)
        print("🗑️ Lienzo reiniciado.")

cap.release()
cv2.destroyAllWindows()