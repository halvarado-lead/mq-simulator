from django.db import models


class SentMessage(models.Model):
    payload = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SentMessage {self.id} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
