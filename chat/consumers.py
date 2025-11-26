import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Room, Message

"""
    Mensagens em Salas (Room Chat):
       -> Usuário se conecta a uma sala de chat via WebSocket
       -> Ele é conectado diretamente a um grupo (neste caso a sala)
       -> Mensagens enviadas são salvas com 'room' definido e 'user_to' = None
       -> As mensagens são enviadas para todos os usuários conectados ao grupo
    
    Mensagens Diretas (Direct Messages):
       -> Usuário se conecta a um chat privado com outro usuário
       -> Mensagens enviadas são salvas com 'user_to' definido e 'room' = None
       -> As mensagens são enviadas apenas para o destinatário específico
"""

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"].get("room_id")
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Determina o tipo de chat (sala ou dm)
        if self.room_id:
            self.chat_type = "room"
            self.group_name = f"chat_room_{self.room_id}"
        else:
            self.chat_type = "direct"
            self.group_name = f"chat_user_{self.user.id}"
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Formato esperado:
        - Para sala: {"message": "texto", "type": "room"}
        - Para dm: {"message": "texto", "type": "direct", "user_to_id": 123}
        """
        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json.get("message", "").strip()
            message_type = text_data_json.get("type", "room")
            user_to_id = text_data_json.get("user_to_id")
            
            if not message_content:
                return
            
            if message_type == "direct" and user_to_id:
                saved_message = await self.save_direct_message(message_content, user_to_id)
                
                recipient_group = f"chat_user_{user_to_id}"
                await self.channel_layer.group_send(
                    recipient_group,
                    {
                        "type": "direct_message",
                        "message_id": saved_message["id"],
                        "message": saved_message["content"],
                        "username": saved_message["username"],
                        "user_id": saved_message["user_id"],
                        "timestamp": saved_message["timestamp"],
                        "is_read": saved_message["is_read"],
                    },
                )
                
                # Envia também para o próprio remetente (para aparecer imediatamente)
                sender_group = f"chat_user_{self.user.id}"
                await self.channel_layer.group_send(
                    sender_group,
                    {
                        "type": "direct_message",
                        "message_id": saved_message["id"],
                        "message": saved_message["content"],
                        "username": saved_message["username"],
                        "user_id": saved_message["user_id"],
                        "timestamp": saved_message["timestamp"],
                        "is_read": True,
                    },
                )
                
            else:
                saved_message = await self.save_room_message(message_content)
                
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "room_message",
                        "message_id": saved_message["id"],
                        "message": saved_message["content"],
                        "username": saved_message["username"],
                        "user_id": saved_message["user_id"],
                        "timestamp": saved_message["timestamp"],
                    },
                )
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Formato JSON inválido"}))
        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))

    async def room_message(self, event):
        await self.send(
            text_data=json.dumps({
                "type": "room",
                "message_id": event["message_id"],
                "message": event["message"],
                "username": event["username"],
                "user_id": event["user_id"],
                "timestamp": event["timestamp"],
            })
        )

    async def direct_message(self, event):
        await self.mark_message_as_read(event["message_id"])
        
        await self.send(
            text_data=json.dumps({
                "type": "direct",
                "message_id": event["message_id"],
                "message": event["message"],
                "username": event["username"],
                "user_id": event["user_id"],
                "timestamp": event["timestamp"],
                "is_read": True,  # Marca como lida ao receber
            })
        )

    @database_sync_to_async
    def save_room_message(self, message_content):
        room = Room.objects.get(id=self.room_id)
        msg = Message.objects.create(
            room=room,
            user=self.user,
            content=message_content,
            user_to=None
        )
        return {
            "id": msg.id,
            "content": msg.content,
            "username": msg.user.username,
            "user_id": msg.user.id,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

    @database_sync_to_async
    def save_direct_message(self, message_content, user_to_id):
        user_to = User.objects.get(id=user_to_id)
        msg = Message.objects.create(
            room=None,
            user=self.user,
            user_to=user_to,
            content=message_content,
            is_read=False
        )
        return {
            "id": msg.id,
            "content": msg.content,
            "username": msg.user.username,
            "user_id": msg.user.id,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "is_read": msg.is_read,
        }

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            msg = Message.objects.get(id=message_id, user_to=self.user)
            if not msg.is_read:
                msg.is_read = True
                msg.save()
        except Message.DoesNotExist:
            pass
