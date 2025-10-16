import os
import json
import pymqi
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.encoding import force_str
from .models import SentMessage, MqConfig
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


def _defaults_from_env():
    return {
        'queue_manager': os.getenv('MQ_QMGR_NAME', 'AUTORIZA'),
        'channel': os.getenv('MQ_CHANNEL', 'SYSTEM.ADMIN.SVRCONN'),
        'host': os.getenv('MQ_HOST', 'ibmmq'),
        'port': os.getenv('MQ_PORT', '1414'),
        'queue_name': os.getenv('MQ_QUEUE', 'BOFTD_ENV'),
        'user': os.getenv('MQ_USER', 'admin'),
        'password': os.getenv('MQ_PASSWORD', 'admin123'),
    }


def get_mq_config():
    # Si hay un registro MqConfig, usarlo; si no, devolver defaults de env
    cfg = MqConfig.objects.first()
    if cfg:
        return {
            'queue_manager': cfg.queue_manager,
            'channel': cfg.channel,
            'host': cfg.host,
            'port': cfg.port,
            'queue_name': cfg.queue_name,
            'user': cfg.user,
            'password': cfg.password,
        }
    return _defaults_from_env()


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


@basic_auth_required
def config(request):
    # Cargar o crear por defecto (en memoria para el form)
    cfg = MqConfig.objects.first()
    if request.method == 'POST':
        data = {
            'queue_manager': request.POST.get('queue_manager', '').strip() or 'AUTORIZA',
            'channel': request.POST.get('channel', '').strip() or 'SYSTEM.ADMIN.SVRCONN',
            'host': request.POST.get('host', '').strip() or 'ibmmq',
            'port': request.POST.get('port', '').strip() or '1414',
            'queue_name': request.POST.get('queue_name', '').strip() or 'BOFTD_ENV',
            'user': request.POST.get('user', '').strip() or 'admin',
            'password': request.POST.get('password', '').strip() or 'admin123',
        }
        if cfg is None:
            cfg = MqConfig.objects.create(**data)
        else:
            for k, v in data.items():
                setattr(cfg, k, v)
            cfg.save()
        return render(request, 'config.html', {**data, 'success': 'Configuración guardada.'})

    # GET: si no hay registro, mostrar defaults de env
    initial = cfg.__dict__ if cfg else _defaults_from_env()
    ctx = {
        'queue_manager': initial.get('queue_manager'),
        'channel': initial.get('channel'),
        'host': initial.get('host'),
        'port': initial.get('port'),
        'queue_name': initial.get('queue_name'),
        'user': initial.get('user'),
        'password': initial.get('password'),
    }
    return render(request, 'config.html', ctx)
