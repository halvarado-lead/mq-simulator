import os
import json
import time
import random
import pymqi

queue_manager = os.getenv("MQ_QMGR_NAME", "AUTORIZA")
channel = os.getenv("MQ_CHANNEL", "SYSTEM.ADMIN.SVRCONN")
host = os.getenv("MQ_HOST", "ibmmq")
port = os.getenv("MQ_PORT", "1414")
queue_name = os.getenv("MQ_QUEUE", "BOFTD_ENV")
user = os.getenv("MQ_USER", "admin")
password = os.getenv("MQ_PASSWORD", "admin123")
send_mode = os.getenv("SEND_MODE", "documents").lower()  # 'file' | 'documents' | 'print'

# Modo "print": solo imprime un mensaje cada N segundos y termina aquí
if send_mode == "print":
    msg = os.getenv("PRINT_MESSAGE", "Producer activo")
    try:
        interval = float(os.getenv("PRINT_INTERVAL", "2"))
    except ValueError:
        interval = 2.0
    try:
        while True:
            print(msg)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.")
    raise SystemExit(0)

conn_info = f"{host}({port})"

# Esperar a que MQ esté disponible con reintentos (otros modos)
qmgr = None
attempt = 0
while qmgr is None:
    try:
        attempt += 1
        print(f"Conectando a MQ {queue_manager} en {conn_info} (intento {attempt})...")
        qmgr = pymqi.connect(queue_manager, channel, conn_info, user, password)
        print("Conexión a MQ exitosa.")
    except Exception as e:
        print(f"Conexión fallida: {e}. Reintentando en 3s...")
        time.sleep(3)

queue = pymqi.Queue(qmgr, queue_name)

def iter_json_documents(fp):
    """Lee múltiples documentos JSON concatenados en un archivo."""
    decoder = json.JSONDecoder()
    buf = fp.read()
    idx = 0
    length = len(buf)
    while idx < length:
        # Saltar espacios en blanco entre documentos
        while idx < length and buf[idx].isspace():
            idx += 1
        if idx >= length:
            break
        obj, end = decoder.raw_decode(buf, idx)
        yield obj
        idx = end

def _randomize_celcupid(obj):
    """Recorre recursivamente el objeto y reemplaza cada valor de la clave
    'CELCUPID' por un número aleatorio de 9 dígitos (100000000-999999999).

    Se mantiene como entero para que el JSON resultante sea válido sin ceros
    a la izquierda (los números JSON no permiten ceros a la izquierda). Como
    todos los generados están en el rango indicado, siempre tendrán 9 dígitos.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "CELCUPID" and isinstance(v, int):
                obj[k] = random.randint(100_000_000, 999_999_999)
            else:
                _randomize_celcupid(v)
    elif isinstance(obj, list):
        for item in obj:
            _randomize_celcupid(item)

try:
    while True:
        if send_mode == "file":
            # En modo 'file' se envía el archivo completo tal cual. Si también
            # quieres randomizar CELCUPID aquí, habría que parsear y re-escribir
            # el archivo; por ahora se mantiene el comportamiento original.
            with open("data.json", "rb") as f:
                content = f.read()
            queue.put(content)
            print(f"Enviado archivo data.json ({len(content)} bytes)")
            time.sleep(1)
            continue

        # Modo 'documents': envía un documento/lote por segundo
        with open("data.json", "r") as f:
            documentos = list(iter_json_documents(f))
        for doc in documentos:
            lotes = doc if isinstance(doc, list) else [doc]
            for lote in lotes:
                # Randomizar todos los CELCUPID dentro del lote
                _randomize_celcupid(lote)
                payload = json.dumps(lote)
                queue.put(payload.encode("utf-8"))
                try:
                    celcupid = lote.get("CELCUPID")
                    print(f"Enviado lote {lote['id_lote']} CELCUPID={celcupid}")
                except Exception:
                    print("Enviado lote (sin id_lote)")
                time.sleep(1)
except KeyboardInterrupt:
    print("Interrumpido por el usuario.")
finally:
    try:
        queue.close()
    finally:
        if qmgr is not None:
            qmgr.disconnect()
