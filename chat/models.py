from django.db import models

# Create your models here.
class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=25)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content}..." 
      
    def save(self, *args, **kwargs):
        # Executar antes de salvar
        self.content = self.content.strip()
        super().save(*args, **kwargs)
        
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'