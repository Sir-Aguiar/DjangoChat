import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Room, Message

"""
    Chat Consumer - Suporta dois tipos de comunicação:
    
    1. Mensagens em Salas (Room Chat):
       -> Usuário se conecta a uma sala de chat via WebSocket
       -> Ele é conectado diretamente a um grupo (neste caso a sala)
       -> Mensagens enviadas são salvas com 'room' definido e 'user_to' = None
       -> As mensagens são enviadas para todos os usuários conectados ao grupo
    
    2. Mensagens Diretas (Direct Messages):
       -> Usuário se conecta a um chat privado com outro usuário
       -> Mensagens enviadas são salvas com 'user_to' definido e 'room' = None
       -> As mensagens são enviadas apenas para o destinatário específico
"""

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Obtém parâmetros da URL
        self.room_id = self.scope["url_route"]["kwargs"].get("room_id")
        self.user = self.scope["user"]
        
        # Verifica se é autenticado
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Determina o tipo de chat (sala ou direto)
        if self.room_id:
            # Chat de sala
            self.chat_type = "room"
            self.group_name = f"chat_room_{self.room_id}"
        else:
            # Chat direto - será configurado quando receber a primeira mensagem
            self.chat_type = "direct"
            self.group_name = f"chat_user_{self.user.id}"
        
        # Adiciona ao grupo apropriado
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        await self.accept()

    async def disconnect(self, close_code):
        # Remove do grupo ao desconectar
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Recebe mensagem do WebSocket
        Formato esperado:
        - Para sala: {"message": "texto", "type": "room"}
        - Para direto: {"message": "texto", "type": "direct", "user_to_id": 123}
        """
        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json.get("message", "").strip()
            message_type = text_data_json.get("type", "room")
            user_to_id = text_data_json.get("user_to_id")
            
            if not message_content:
                return
            
            # Salva a mensagem no banco de dados
            if message_type == "direct" and user_to_id:
                # Mensagem direta
                saved_message = await self.save_direct_message(message_content, user_to_id)
                
                # Envia para o destinatário
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
                        "is_read": True,  # Para o remetente, sempre marca como lido
                    },
                )
                
            else:
                # Mensagem em sala
                saved_message = await self.save_room_message(message_content)
                
                # Envia mensagem para o grupo da sala
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
        """Recebe mensagem do grupo da sala e envia para o WebSocket"""
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
        """Recebe mensagem direta e envia para o WebSocket"""
        # Marca a mensagem como lida
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
        """Salva mensagem em uma sala"""
        room = Room.objects.get(id=self.room_id)
        msg = Message.objects.create(
            room=room,
            user=self.user,
            content=message_content,
            user_to=None  # Mensagem de sala não tem destinatário específico
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
        """Salva mensagem direta para outro usuário"""
        user_to = User.objects.get(id=user_to_id)
        msg = Message.objects.create(
            room=None,  # Mensagem direta não pertence a uma sala
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
        """Marca uma mensagem como lida"""
        try:
            msg = Message.objects.get(id=message_id, user_to=self.user)
            if not msg.is_read:
                msg.is_read = True
                msg.save()
        except Message.DoesNotExist:
            pass
