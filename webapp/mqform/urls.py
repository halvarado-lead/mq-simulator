from django.urls import path
from .views import home, logs

urlpatterns = [
    path('', home, name='home'),
    path('logs/', logs, name='logs'),
]
