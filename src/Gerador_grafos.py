import cv2
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os
from datetime import datetime

def generar_imagen_grafo(grafo, posiciones, nombre_archivo):
    plt.figure(figsize=(6, 6))
    nx.draw(
        grafo, 
        pos=posiciones, 
        with_labels=True, 
        node_size=1200,          
        node_color='white',      
        edgecolors='black',      
        linewidths=2.5,          
        font_size=14,            
        font_weight='bold',      
        font_color='black',      
        edge_color='black',      
        width=2.5,               
        alpha=1.0
    )
    plt.axis('off')
    plt.savefig(nombre_archivo, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✅ Imagen de grafo generada exitosamente: {nombre_archivo}")

def ejecutar_generador():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("⚠️ No se pudo acceder a la cámara.")
        return

    umbral_distancia_nodos = 50 
    grafo_actual = nx.Graph()
    posiciones_nodos = {}       
    contador_nodos = 1          
    dibujando = False
    coordenadas_trazo_actual = []
    lienzo_persistencia = None

    # Guardar en la carpeta grafos_guardados en la raíz del proyecto
    os.makedirs('grafos_guardados', exist_ok=True)
    print("Iniciando creador de grafos interactivo (Modo Objeto Azul)...")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        
        if lienzo_persistencia is None:
            lienzo_persistencia = np.zeros((h, w, 3), dtype=np.uint8)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([90, 60, 60])
        upper_blue = np.array([130, 255, 255])
        
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        punto_actual = None
        if contours:
            c_max = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c_max) > 300:
                ((x, y), radius) = cv2.minEnclosingCircle(c_max)
                if radius > 5:
                    punto_actual = (int(x), int(y))
                    cv2.circle(frame, punto_actual, int(radius), (255, 0, 0), 2)
                    cv2.circle(frame, punto_actual, 5, (0, 0, 255), -1)

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

if __name__ == "__main__":
    ejecutar_generador()