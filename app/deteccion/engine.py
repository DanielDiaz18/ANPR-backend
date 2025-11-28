import threading
import queue
import cv2
import imutils
import re
import psycopg2
import psycopg2.errors
import sys
import os
import time
import numpy as np
import urllib.request
from ultralytics import YOLO
from paddleocr import PaddleOCR

# --- Variables Globales para compartir el video con el Frontend ---
output_frame = None
frame_lock = threading.Lock()

# --- Conexión BD (Adaptada para Docker) ---
def conectar_bd():
    """Conecta usando la variable de entorno del docker-compose"""
    try:
        # Docker inyecta DATABASE_URL. Si no está, se intenta con los hardcores como fallback
        db_url = os.getenv("DATABASE_URL")
        
        if db_url:
            conn = psycopg2.connect(db_url)
        else:
            # Fallback a las credenciales originales 
            conn = psycopg2.connect(
                dbname="deteccion", user="postgres", password="root123", host="localhost", port="5432"
            )
        return conn
    except Exception as e:
        print(f"--- ERROR BD: {e} ---", file=sys.stderr)
        return None

def crear_tabla(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS placas (
                id SERIAL PRIMARY KEY,
                placa VARCHAR(20) NOT NULL,
                fecha_registro TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        # Se evitan duplicados con esta restricción
        try:
            cur.execute("ALTER TABLE placas ADD CONSTRAINT placa_unica UNIQUE (placa);")
        except psycopg2.errors.DuplicateTable:
            pass 
        except Exception:
            conn.rollback() 
        
        conn.commit()

def insertar_placa(conn, texto_placa):
    sql = "INSERT INTO placas (placa) VALUES (%s)"
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (texto_placa,))
            conn.commit()
            print(f"--- GUARDADO: Placa '{texto_placa}' en BD. ---", file=sys.stderr)
    except psycopg2.errors.UniqueViolation:
        print(f"--- DUPLICADO: Placa '{texto_placa}' ya existe. Ignorando. ---", file=sys.stderr)
        conn.rollback()
    except Exception as e:
        print(f"--- ERROR INSERT: {e} ---", file=sys.stderr)
        conn.rollback()

# Hilo de OCR
def ocr_worker(q, ocr_model):
    conn = conectar_bd()
    if conn is None: return
    crear_tabla(conn)

    patron_placa = re.compile(r'[A-Z]{3}[0-9]{2,4}[A-Z]?')

    while True:
        item = q.get()
        if item is None: break
        track_id, placa_imagen = item

        print(f"Procesando ID {track_id}...", file=sys.stderr)
        
        try:
            result_ocr = ocr_model.predict(cv2.cvtColor(placa_imagen, cv2.COLOR_BGR2RGB))
            texto_full = ""
            
            if result_ocr and result_ocr[0]:
                cajas = result_ocr[0]['rec_boxes']
                textos = result_ocr[0]['rec_texts']
                # Se ordena de izquierda a derecha
                izq_der = sorted(zip(cajas,textos), key=lambda x: min(x[0][::2]))
                
                # Se une TODO lo que leyó (ej. "JALISCOJGL984AMEXICO")
                raw_text = ''.join([t for _, t in izq_der])
                
                # Limpia, solo deja texto alfanumérico y mayúsculas
                texto_full = ''.join(c for c in raw_text if c.isalnum()).upper()

            # Búsqueda de patrón de placa
            match = patron_placa.search(texto_full)
            
            if match:
                placa_detectada = match.group(0)
                
                # Filtro final de longitud (6 o 7 caracteres)
                if len(placa_detectada) in [6, 7]:
                    print(f"--- VÁLIDO ID {track_id}: '{placa_detectada}' (Extraído de '{texto_full}') ---", file=sys.stderr)
                    insertar_placa(conn, placa_detectada)
                else:
                    print(f"--- RARO ID {track_id}: '{placa_detectada}' (Longitud incorrecta) ---", file=sys.stderr)
            
            elif texto_full:
                 # Si leyó algo pero no parece placa 
                print(f"--- IGNORADO ID {track_id}: '{texto_full}' (No parece placa) ---", file=sys.stderr)
        
        except Exception as e:
            print(f"Error en OCR: {e}", file=sys.stderr)
        
        q.task_done()
    
    if conn: conn.close()

# Hilo de Detección y Tracking
def detector_thread(video_source, model_path, config_path, ocr_queue):
    global output_frame, frame_lock
    
    # Se carga YOLO aquí 
    model = YOLO(model_path)
    placas_ya_registradas = set()

    # Conversión automática de URL 
    # Esto evita que Docker se trabe.
    if "http" in str(video_source) and "/video" in str(video_source):
        url_fuente = video_source.replace("/video", "/shot.jpg")
    else:
        url_fuente = video_source
    
    print(f"--- INICIANDO DETECCIÓN (Modo Foto Estable) EN: {url_fuente} ---", file=sys.stderr)

    while True:
        try:
            # OBTENER IMAGEN 
            # Esto es inmune a desconexiones breves del WiFi
            img_resp = urllib.request.urlopen(url_fuente, timeout=5)
            img_arr = np.array(bytearray(img_resp.read()), dtype=np.uint8)
            frame = cv2.imdecode(img_arr, -1)

            if frame is None:
                time.sleep(0.1)
                continue


            # Tracking (confianza arriba de 72%)
            results = model.track(frame, persist=True, verbose=False, classes=[0], conf=0.72, tracker=config_path)

            if results[0].boxes.id is not None:
                boxes_xyxy = results[0].boxes.xyxy.cpu().numpy().astype(int)
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                confs = results[0].boxes.conf.cpu().numpy()

                for i in range(len(boxes_xyxy)):
                    track_id = track_ids[i]
                    confianza = confs[i]

                    if track_id not in placas_ya_registradas:
                        x1, y1, x2, y2 = boxes_xyxy[i]
                        altura = y2 - y1
                        
                        # recorte adaptativo según altura (falta especificar más)
                        if altura < 200:
                            placa_imagen = frame[y1+50:y2-45, x1:x2+20]
                        else:
                            placa_imagen = frame[y1+75:y2-70, x1:x2+20]
                        
                        if placa_imagen.size > 0:
                            print(f"Nueva placa ID {track_id}. Enviando a cola.", file=sys.stderr)
                            ocr_queue.put((track_id, placa_imagen.copy()))
                            placas_ya_registradas.add(track_id)

                    # Visualización 
                    x1, y1, x2, y2 = boxes_xyxy[i]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"ID: {track_id} | {confianza:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Redimensionado y guardado en variable global 
            frame_resized = imutils.resize(frame, width=1080)
            with frame_lock:
                output_frame = frame_resized.copy()
            
            # --- PEQUEÑA PAUSA ---
            time.sleep(0.01)

        except Exception as e:
            # Si falla la red, solo espera y reintenta sin crashear
            print(f"--- RECONECTANDO CAMARA ({e})... ---", file=sys.stderr)
            time.sleep(2)

# --- Función de Arranque ---
def start_background_tasks():
    # Rutas absolutas para evitar errores en Docker
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_pt = os.path.join(base_dir, "license_plate_detector.pt")
    tracker_cfg = os.path.join(base_dir, "tracker_config.yaml")

    ocr_model = PaddleOCR(use_angle_cls=True, lang='en')
    q = queue.Queue()

    t_ocr = threading.Thread(target=ocr_worker, args=(q, ocr_model), daemon=True)
    t_ocr.start()

    # La url cambia respecto a la ip asiganda
    URL_CAMARA = "http://10.52.143.207:8080/video" 
    
    t_det = threading.Thread(target=detector_thread, args=(URL_CAMARA, model_pt, tracker_cfg, q), daemon=True)
    t_det.start()