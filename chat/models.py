from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# Create your models here.
class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Sala"
        verbose_name_plural = "Salas"


class Message(models.Model):
    room = models.ForeignKey(
        Room, null=True, blank=True, on_delete=models.CASCADE, related_name="messages"
    )
    user_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="received_messages",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        if self.room:
            return f"{self.user.username} em {self.room.name}: {self.content[:30]}..."
        else:
            return f"{self.user.username} → {self.user_to.username}: {self.content[:30]}..."

    def clean(self):
        """Validação: room OU user_to deve estar definido, mas não ambos"""
        if self.room and self.user_to:
            raise ValidationError(
                "Mensagem não pode ser para sala E usuário ao mesmo tempo."
            )
        if not self.room and not self.user_to:
            raise ValidationError("Mensagem deve ser para uma sala OU para um usuário.")

    def save(self, *args, **kwargs):
        self.clean()
        self.content = self.content.strip()
        super().save(*args, **kwargs)

    @property
    def is_private(self):
        return self.user_to is not None

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
