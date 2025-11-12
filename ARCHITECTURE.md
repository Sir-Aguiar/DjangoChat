# Arquitetura do Sistema de Chat em Tempo Real

## Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE (Browser)                        │
│                                                                  │
│  ┌────────────────┐                    ┌───────────────────┐   │
│  │  Interface Web  │◄──────────────────►│  WebSocket Client │   │
│  │  (Tailwind CSS) │                    │   (JavaScript)    │   │
│  └────────────────┘                    └───────────────────┘   │
└───────────────────────────┬──────────────────┬──────────────────┘
                            │                  │
                    HTTP    │                  │  WebSocket (ws://)
                            │                  │
┌───────────────────────────▼──────────────────▼──────────────────┐
│                    SERVIDOR ASGI (Daphne)                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              ASGI Application Router                      │  │
│  │                                                            │  │
│  │  ┌──────────────┐              ┌──────────────────────┐  │  │
│  │  │  HTTP Router │              │  WebSocket Router    │  │  │
│  │  │   (Django)   │              │   (Channels)         │  │  │
│  │  └──────┬───────┘              └──────────┬───────────┘  │  │
│  └─────────┼─────────────────────────────────┼──────────────┘  │
│            │                                  │                 │
│  ┌─────────▼─────────┐            ┌──────────▼──────────────┐  │
│  │   Django Views    │            │   Chat Consumer         │  │
│  │                   │            │   (AsyncWebsocket)      │  │
│  │  - room_list()    │            │                         │  │
│  │  - join_room()    │            │  - connect()            │  │
│  │  - room_detail()  │            │  - disconnect()         │  │
│  │  - leave_room()   │            │  - receive()            │  │
│  └─────────┬─────────┘            └──────────┬──────────────┘  │
│            │                                  │                 │
│            │                                  │                 │
│            │        ┌────────────────────┐   │                 │
│            └────────►  Channel Layers    ◄───┘                 │
│                     │  (InMemory)        │                     │
│                     │                    │                     │
│                     │  Group: chat_1     │                     │
│                     │  Group: chat_2     │                     │
│                     └──────────┬─────────┘                     │
│                                │                               │
│                     ┌──────────▼─────────┐                     │
│                     │   Django Models    │                     │
│                     │                    │                     │
│                     │  ┌──────────────┐  │                     │
│                     │  │    Room      │  │                     │
│                     │  ├──────────────┤  │                     │
│                     │  │ - name       │  │                     │
│                     │  │ - description│  │                     │
│                     │  │ - is_active  │  │                     │
│                     │  └──────────────┘  │                     │
│                     │                    │                     │
│                     │  ┌──────────────┐  │                     │
│                     │  │   Message    │  │                     │
│                     │  ├──────────────┤  │                     │
│                     │  │ - room       │  │                     │
│                     │  │ - sender     │  │                     │
│                     │  │ - content    │  │                     │
│                     │  │ - timestamp  │  │                     │
│                     │  └──────────────┘  │                     │
│                     └────────────────────┘                     │
│                                │                               │
│                     ┌──────────▼─────────┐                     │
│                     │   Database         │                     │
│                     │   (SQLite)         │                     │
│                     └────────────────────┘                     │
└──────────────────────────────────────────────────────────────┘
```

## Fluxo de Envio de Mensagem

```
1. USUÁRIO DIGITA E ENVIA MENSAGEM
   │
   ├─► Frontend captura evento (JavaScript)
   │
2. WEBSOCKET ENVIA JSON
   │
   ├─► {
   │     "message": "Olá!",
   │     "username": "João"
   │   }
   │
3. CONSUMER RECEBE (receive())
   │
   ├─► Valida dados
   ├─► Salva no banco (save_message)
   │   │
   │   └─► Message.objects.create(...)
   │
4. BROADCAST PARA GRUPO
   │
   ├─► channel_layer.group_send(
   │     group_name='chat_1',
   │     message_data={...}
   │   )
   │
5. TODOS NO GRUPO RECEBEM (chat_message())
   │
   ├─► self.send(text_data=json.dumps(...))
   │
6. FRONTEND ATUALIZA INTERFACE
   │
   └─► Adiciona mensagem ao chat
       Scroll automático
       Exibe timestamp
```

## Estrutura de Grupos WebSocket

```
┌──────────────────────────────────────────┐
│         Channel Layer (InMemory)          │
│                                           │
│  ┌────────────────────────────────────┐  │
│  │  Group: chat_1 (Sala Geral)        │  │
│  │                                     │  │
│  │  ├─► User1_channel_xyz123          │  │
│  │  ├─► User2_channel_abc456          │  │
│  │  └─► User3_channel_def789          │  │
│  └────────────────────────────────────┘  │
│                                           │
│  ┌────────────────────────────────────┐  │
│  │  Group: chat_2 (Tecnologia)        │  │
│  │                                     │  │
│  │  ├─► User4_channel_ghi012          │  │
│  │  └─► User5_channel_jkl345          │  │
│  └────────────────────────────────────┘  │
│                                           │
│  ┌────────────────────────────────────┐  │
│  │  Group: chat_3 (Jogos)             │  │
│  │                                     │  │
│  │  └─► User6_channel_mno678          │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘

Quando uma mensagem é enviada em chat_1,
todos os canais nesse grupo recebem!
```

## Tecnologias e Responsabilidades

| Componente | Tecnologia | Responsabilidade |
|------------|-----------|------------------|
| **Frontend** | HTML/CSS/JS + Tailwind | Interface, captura de eventos, WebSocket client |
| **Servidor ASGI** | Daphne | Gerencia conexões HTTP e WebSocket |
| **Roteamento HTTP** | Django URLs/Views | Lida com requisições HTTP (páginas, formulários) |
| **Roteamento WS** | Channels Routing | Direciona conexões WebSocket para consumers |
| **Consumers** | Channels AsyncConsumer | Gerencia conexões WebSocket, eventos de mensagens |
| **Channel Layers** | InMemoryChannelLayer | Sistema de pub/sub para broadcast de mensagens |
| **ORM** | Django Models | Abstração do banco de dados |
| **Banco de Dados** | SQLite | Armazenamento persistente |
| **Sessões** | Django Sessions | Controle de estado do usuário |

## Estados da Conexão WebSocket

```
┌──────────┐
│  IDLE    │  Usuário na lista de salas ou formulário de entrada
└────┬─────┘
     │ Usuário entra na sala
     ▼
┌──────────────┐
│ CONNECTING   │  JavaScript inicia WebSocket
└────┬─────────┘
     │ onopen()
     ▼
┌──────────────┐
│  CONNECTED   │  ✓ Pronto para enviar/receber mensagens
└────┬─────────┘  ✓ Indicador verde "Online"
     │            ✓ Carrega histórico
     │            ✓ Foca no input
     │
     ├─► onmessage() ──► Recebe mensagem de outro usuário
     │
     ├─► send() ───────► Envia mensagem
     │
     │ onerror() / close()
     ▼
┌──────────────┐
│ DISCONNECTED │  ✗ Indicador vermelho "Desconectado"
└──────────────┘  ✗ Não pode enviar mensagens
```

## Segurança e Controle de Acesso

```
HTTP Request (Entrar na Sala)
     │
     ├─► View: join_room()
     │   ├─► POST com username
     │   ├─► Valida entrada
     │   └─► Salva na sessão:
     │       ├─ session['username'] = 'João'
     │       └─ session['room_id'] = 1
     │
     ├─► Redirect para room_detail()
     │
     └─► View: room_detail()
         ├─► Verifica sessão
         │   ├─ session['username'] existe?
         │   └─ session['room_id'] == room_id atual?
         │
         ├─► Se SIM: Renderiza chat
         └─► Se NÃO: Redirect para join_room()

WebSocket Connection
     │
     ├─► Consumer.connect()
     │   └─► Aceita conexão (pode adicionar validação aqui)
     │
     └─► Consumer.receive()
         ├─► Recebe username do cliente
         ├─► Valida e processa
         └─► Salva no banco + broadcast
```
