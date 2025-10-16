from django.db import models


class SentMessage(models.Model):
    payload = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SentMessage {self.id} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class MqConfig(models.Model):
    queue_manager = models.CharField(max_length=128, default='AUTORIZA')
    channel = models.CharField(max_length=128, default='SYSTEM.ADMIN.SVRCONN')
    host = models.CharField(max_length=128, default='ibmmq')
    port = models.CharField(max_length=10, default='1414')
    queue_name = models.CharField(max_length=128, default='BOFTD_ENV')
    user = models.CharField(max_length=128, default='admin')
    password = models.CharField(max_length=256, default='admin123')

    def __str__(self):
        return f"MQ Config ({self.queue_manager}@{self.host}:{self.port}/{self.queue_name})"
