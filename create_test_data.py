"""
Script para criar dados de teste para o Django Chat
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangochat.settings')
django.setup()

from chat.models import Room

# Cria salas de exemplo
rooms_data = [
    {
        'name': 'Sala Geral',
        'description': 'Conversa sobre assuntos gerais e diversos tópicos',
        'is_active': True
    },
    {
        'name': 'Tecnologia',
        'description': 'Discussões sobre programação, desenvolvimento e tecnologia',
        'is_active': True
    },
    {
        'name': 'Jogos',
        'description': 'Fale sobre seus jogos favoritos',
        'is_active': True
    },
]

print("Criando salas de exemplo...")
for room_data in rooms_data:
    room, created = Room.objects.get_or_create(
        name=room_data['name'],
        defaults={
            'description': room_data['description'],
            'is_active': room_data['is_active']
        }
    )
    if created:
        print(f"✓ Sala '{room.name}' criada com sucesso!")
    else:
        print(f"- Sala '{room.name}' já existe.")

print("\nDados de teste criados com sucesso!")
print("\nAcesse: http://127.0.0.1:8000/")
