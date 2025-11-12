# Django Chat - Aplicativo de Bate-papo em Tempo Real

Sistema de chat em tempo real desenvolvido com Django Channels e WebSockets, com interface moderna usando Tailwind CSS.

## ✨ Funcionalidades

### Para Usuários
- ✅ Visualizar lista de salas de chat disponíveis
- ✅ Entrar em uma sala fornecendo um nome de usuário
- ✅ Visualizar histórico de mensagens ao entrar na sala
- ✅ Enviar mensagens em tempo real
- ✅ Receber mensagens de outros usuários instantaneamente
- ✅ Interface responsiva e moderna

### Para Administradores
- ✅ Criar novas salas de chat pelo painel admin
- ✅ Editar salas existentes
- ✅ Ativar/desativar salas
- ✅ Visualizar todas as mensagens

## 🚀 Tecnologias Utilizadas

- **Backend**: Django 5.2.8
- **WebSocket**: Django Channels 4.3.1
- **Servidor ASGI**: Daphne 4.2.1
- **Frontend**: Tailwind CSS (CDN)
- **Banco de Dados**: SQLite (desenvolvimento)

## 📦 Instalação

1. **Clone o repositório** (se ainda não o fez):
```bash
git clone <seu-repositorio>
cd DjangoChat
```

2. **Ative o ambiente virtual**:
```powershell
.\.venv\Scripts\Activate.ps1
```

3. **Instale as dependências**:
```bash
pip install django channels daphne
```

4. **Execute as migrações**:
```bash
python manage.py migrate
```

5. **Crie salas de teste** (opcional):
```bash
python create_test_data.py
```

6. **Crie um superusuário** (para acessar o admin):
```bash
python manage.py createsuperuser
```

## 🎮 Como Usar

### Iniciar o Servidor

Para que os WebSockets funcionem corretamente, você precisa usar o Daphne ao invés do `runserver` padrão do Django:

```bash
daphne -b 127.0.0.1 -p 8000 djangochat.asgi:application
```

Ou simplesmente:

```bash
daphne djangochat.asgi:application
```

O servidor estará disponível em: **http://127.0.0.1:8000/**

### Acessar o Painel Admin

1. Acesse: **http://127.0.0.1:8000/admin/**
2. Faça login com suas credenciais de superusuário
3. Crie novas salas de chat em **Chat > Salas**

### Usar o Chat

1. Acesse a página inicial: **http://127.0.0.1:8000/**
2. Você verá todas as salas disponíveis
3. Clique em "Entrar na Sala" na sala desejada
4. Digite seu nome de usuário
5. Comece a conversar! 💬

### Testar Mensagens em Tempo Real

Para testar se as mensagens estão sendo enviadas em tempo real:

1. Abra duas abas/janelas do navegador
2. Em ambas, entre na mesma sala com nomes de usuários diferentes
3. Envie uma mensagem em uma aba
4. Veja a mensagem aparecer instantaneamente na outra aba! ✨

## 📁 Estrutura do Projeto

```
DjangoChat/
├── chat/                           # App principal
│   ├── consumers.py               # WebSocket consumers
│   ├── routing.py                 # Rotas WebSocket
│   ├── models.py                  # Modelos (Room, Message)
│   ├── views.py                   # Views HTTP
│   ├── urls.py                    # URLs HTTP
│   ├── admin.py                   # Configuração do admin
│   └── templates/
│       └── chat/
│           ├── base.html          # Template base
│           ├── room_list.html     # Lista de salas
│           ├── join_room.html     # Entrada na sala
│           └── room_detail.html   # Sala de chat (WebSocket)
├── djangochat/                     # Configurações do projeto
│   ├── settings.py                # Configurações Django
│   ├── asgi.py                    # Configuração ASGI/Channels
│   ├── urls.py                    # URLs principais
│   └── wsgi.py                    # Configuração WSGI
├── manage.py                       # Comando manage do Django
├── create_test_data.py            # Script para criar dados de teste
└── db.sqlite3                     # Banco de dados

```

## 🔧 Configurações Importantes

### settings.py

```python
INSTALLED_APPS = [
    'daphne',  # Deve ser o primeiro
    'django.contrib.admin',
    # ... outros apps
    'channels',
    'chat'
]

ASGI_APPLICATION = 'djangochat.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
```

### asgi.py

Configurado para rotear requisições HTTP e WebSocket:
- HTTP → Django ASGI application
- WebSocket → Chat consumers

## 🌐 URLs e Rotas

### HTTP
- `/` - Lista de salas
- `/room/<id>/join/` - Entrar na sala
- `/room/<id>/` - Sala de chat
- `/leave/` - Sair da sala
- `/admin/` - Painel administrativo

### WebSocket
- `ws://127.0.0.1:8000/ws/chat/<room_id>/` - Conexão WebSocket da sala

## 💡 Como Funciona

### Fluxo de Mensagens

1. **Usuário envia mensagem** → Frontend JavaScript envia via WebSocket
2. **Consumer recebe** → `ChatConsumer.receive()` processa a mensagem
3. **Salva no banco** → Mensagem é salva no modelo `Message`
4. **Broadcast** → Mensagem é enviada para todos os usuários no grupo da sala
5. **Todos recebem** → Cada cliente conectado recebe e exibe a mensagem

### Sistema de Sessões

- Nome de usuário é armazenado na sessão do Django
- Controle de acesso: usuário precisa "entrar" na sala antes de acessar o chat
- Botão "Sair" limpa a sessão

### WebSocket Groups

Cada sala tem um "grupo" no Channels:
- Formato: `chat_<room_id>`
- Usuários são adicionados ao grupo ao conectar
- Mensagens são transmitidas para todos no grupo

## 🎨 Interface

- **Design moderno** com gradientes e sombras
- **Responsivo** - funciona em desktop e mobile
- **Indicador de status** - mostra se está conectado ou desconectado
- **Auto-scroll** - mensagens novas aparecem automaticamente
- **Mensagens estilizadas** - diferencia mensagens próprias e de outros

## 🐛 Troubleshooting

### WebSocket não conecta

1. Certifique-se de usar **Daphne** ao invés de `runserver`
2. Verifique se o Channels está instalado
3. Confirme que `ASGI_APPLICATION` está configurado no settings.py

### Mensagens não aparecem

1. Abra o console do navegador (F12) e veja se há erros
2. Verifique se o WebSocket está conectado (indicador deve estar verde)
3. Confirme que ambos os usuários estão na mesma sala

### Erro ao iniciar servidor

Se aparecer erro sobre `INSTALLED_APPS`:
```bash
# Defina a variável de ambiente
$env:DJANGO_SETTINGS_MODULE="djangochat.settings"
daphne djangochat.asgi:application
```

## 📝 Próximas Melhorias

- [ ] Usar Redis para Channel Layer (produção)
- [ ] Sistema de notificações
- [ ] Upload de imagens
- [ ] Emojis e reações
- [ ] Typing indicators (indicador de digitação)
- [ ] Número de usuários online
- [ ] Histórico paginado de mensagens
- [ ] Busca de mensagens
- [ ] Salas privadas
- [ ] Sistema de autenticação completo

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais.

---

**Desenvolvido com ❤️ usando Django e Django Channels**
