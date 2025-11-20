from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # WebSocket para chat em salas (room chat)
    re_path(r"ws/chat/room/(?P<room_id>\w+)/$", consumers.ChatConsumer.as_asgi()),
    
    # WebSocket para mensagens diretas (direct messages)
    re_path(r"ws/chat/direct/$", consumers.ChatConsumer.as_asgi()),
]
