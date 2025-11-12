from django.db import models

# Create your models here.
class  Message (models.Model):
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