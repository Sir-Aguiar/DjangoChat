import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Room, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        # Obtém o usuário da sessão
        self.user = self.scope["user"]

        # Adiciona o canal ao grupo da sala
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Remove o canal do grupo da sala
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Recebe mensagem do WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Salva a mensagem no banco de dados
        saved_message = await self.save_message(message)

        # Envia mensagem para o grupo da sala
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": saved_message["username"],
                "timestamp": saved_message["timestamp"],
            },
        )

    # Recebe mensagem do grupo da sala
    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]
        timestamp = event["timestamp"]

        # Envia mensagem para o WebSocket
        await self.send(
            text_data=json.dumps(
                {"message": message, "username": username, "timestamp": timestamp}
            )
        )

    @database_sync_to_async
    def save_message(self, message):
        room = Room.objects.get(id=self.room_id)
        msg = Message.objects.create(room=room, user=self.user, content=message)
        return {
            "id": msg.id,
            "username": msg.user.username,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
