from django.urls import path
from .views import home, logs, config

urlpatterns = [
    path('', home, name='home'),
    path('logs/', logs, name='logs'),
    path('config/', config, name='config'),
]
