import os
import json
import time
import pymqi

queue_manager = os.getenv("MQ_QMGR_NAME", "AUTORIZA")
channel = os.getenv("MQ_CHANNEL", "SYSTEM.ADMIN.SVRCONN")
host = os.getenv("MQ_HOST", "ibmmq")
port = os.getenv("MQ_PORT", "1414")
queue_name = os.getenv("MQ_QUEUE", "BOFTC_ENV")
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

try:
    while True:
        if send_mode == "file":
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
                payload = json.dumps(lote)
                queue.put(payload.encode("utf-8"))
                try:
                    print(f"Enviado lote {lote['id_lote']}")
                except Exception:
                    print("Enviado lote")
                time.sleep(1)
except KeyboardInterrupt:
    print("Interrumpido por el usuario.")
finally:
    try:
        queue.close()
    finally:
        if qmgr is not None:
            qmgr.disconnect()
