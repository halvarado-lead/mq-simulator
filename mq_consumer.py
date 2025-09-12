import os
import time
import json
import pymqi

queue_manager = os.getenv("MQ_QMGR_NAME", "AUTORIZA")
channel = os.getenv("MQ_CHANNEL", "SYSTEM.ADMIN.SVRCONN")
host = os.getenv("MQ_HOST", "ibmmq")
port = os.getenv("MQ_PORT", "1414")
queue_name = os.getenv("MQ_QUEUE", "BOFTD_ENV")
user = os.getenv("MQ_USER", "admin")
password = os.getenv("MQ_PASSWORD", "admin123")

conn_info = f"{host}({port})"

# Esperar a que MQ esté disponible con reintentos
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

queue_open_opts = pymqi.CMQC.MQOO_INPUT_AS_Q_DEF | pymqi.CMQC.MQOO_FAIL_IF_QUIESCING
queue = pymqi.Queue(qmgr, queue_name, queue_open_opts)

md = pymqi.MD()
gmo = pymqi.GMO()
gmo.Options = (
    pymqi.CMQC.MQGMO_WAIT
    | pymqi.CMQC.MQGMO_NO_SYNCPOINT
    | pymqi.CMQC.MQGMO_FAIL_IF_QUIESCING
)
gmo.WaitInterval = 2000  # 2 segundos

print(f"Escuchando cola '{queue_name}' con espera de {gmo.WaitInterval}ms...")

try:
    while True:
        try:
            # Lee hasta 1MB por mensaje
            msg = queue.get(1024 * 1024, md, gmo)
        except pymqi.MQMIError as e:
            if e.comp == 2 and e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                continue
            raise

        try:
            text = msg.decode("utf-8")
        except Exception:
            text = str(msg)

        # Intentar parsear JSON para mostrarlo bonito
        try:
            obj = json.loads(text)
            resumen = obj.get("id_lote") if isinstance(obj, dict) else None
            if resumen is not None:
                print(f"Recibido id_lote={resumen}")
            else:
                print(f"Recibido JSON: {obj}")
        except Exception:
            print(f"Recibido (texto): {text}")

except KeyboardInterrupt:
    print("Interrumpido por el usuario.")
finally:
    try:
        queue.close()
    finally:
        if qmgr is not None:
            qmgr.disconnect()

