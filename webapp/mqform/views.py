import os
import json
import pymqi
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.encoding import force_str
from .models import SentMessage
import base64


def basic_auth_required(view_func):
    USER = os.getenv('BASIC_AUTH_USER', 'admin')
    PASS = os.getenv('BASIC_AUTH_PASS', 'admin1234')

    def _wrapped(request, *args, **kwargs):
        auth = request.META.get('HTTP_AUTHORIZATION')
        if not auth or not auth.lower().startswith('basic '):
            response = HttpResponse(status=401)
            response['WWW-Authenticate'] = 'Basic realm="Restricted"'
            return response
        try:
            encoded = auth.split(' ', 1)[1].strip()
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
        except Exception:
            response = HttpResponse(status=401)
            response['WWW-Authenticate'] = 'Basic realm="Restricted"'
            return response
        if username == USER and password == PASS:
            return view_func(request, *args, **kwargs)
        response = HttpResponse(status=401)
        response['WWW-Authenticate'] = 'Basic realm="Restricted"'
        return response

    return _wrapped


def get_mq_config():
    return {
        'queue_manager': os.getenv('MQ_QMGR_NAME', 'AUTORIZA'),
        'channel': os.getenv('MQ_CHANNEL', 'SYSTEM.ADMIN.SVRCONN'),
        'host': os.getenv('MQ_HOST', 'ibmmq'),
        'port': os.getenv('MQ_PORT', '1414'),
        'queue_name': os.getenv('MQ_QUEUE', 'BOFTD_ENV'),
        'user': os.getenv('MQ_USER', 'admin'),
        'password': os.getenv('MQ_PASSWORD', 'admin123'),
    }


@basic_auth_required
def home(request):
    if request.method == 'POST':
        action = request.POST.get('action', 'preview')
        text = request.POST.get('payload', '').strip()
        if not text:
            return render(request, 'home.html', {
                'error': 'El textarea no puede estar vacío.'
            })

        # Intentar validar como JSON (opcional: permitir texto plano si falla)
        parsed = None
        error = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            error = f'JSON inválido: {e}'

        # Si es vista previa o hay error de JSON, no enviar aún
        if action == 'preview' or error:
            pretty = None
            if parsed is not None:
                pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
            return render(request, 'home.html', {
                'payload': text,
                'preview': pretty,
                'error': error,
                'show_confirm': parsed is not None and error is None,
            })

        # Confirmado: enviar a MQ
        cfg = get_mq_config()
        conn_info = f"{cfg['host']}({cfg['port']})"
        try:
            qmgr = pymqi.connect(cfg['queue_manager'], cfg['channel'], conn_info, cfg['user'], cfg['password'])
            queue = pymqi.Queue(qmgr, cfg['queue_name'])
            queue.put(text.encode('utf-8'))
            queue.close()
            qmgr.disconnect()
            # Guardar registro
            SentMessage.objects.create(payload=text)
            return render(request, 'home.html', {
                'success': 'Mensaje enviado a la cola.',
            })
        except Exception as e:
            return render(request, 'home.html', {
                'error': f'Error enviando a MQ: {e}'
            })

    return render(request, 'home.html')


def logs(request):
    items = SentMessage.objects.order_by('-created_at')[:200]
    return render(request, 'logs.html', {'items': items})
