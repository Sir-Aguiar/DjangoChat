from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Room

# Create your views here.

def room_list(request):
    """Lista todas as salas ativas"""
    rooms = Room.objects.filter(is_active=True)
    return render(request, 'chat/room_list.html', {'rooms': rooms})


def join_room(request, room_id):
    """Permite que o usuário entre em uma sala fornecendo um nome de usuário"""
    room = get_object_or_404(Room, id=room_id, is_active=True)
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        
        if username:
            # Salva o nome de usuário na sessão
            request.session['username'] = username
            request.session['room_id'] = room_id
            
            messages.success(request, f'Bem-vindo à sala {room.name}, {username}!')
            return redirect('chat:room_detail', room_id=room_id)
        else:
            messages.error(request, 'Por favor, insira um nome de usuário válido.')
    
    return render(request, 'chat/join_room.html', {'room': room})


def room_detail(request, room_id):
    """Exibe a sala de bate-papo"""
    room = get_object_or_404(Room, id=room_id, is_active=True)
    username = request.session.get('username')
    
    # Verifica se o usuário está autenticado na sessão
    if not username or request.session.get('room_id') != room_id:
        messages.warning(request, 'Por favor, entre na sala primeiro.')
        return redirect('chat:join_room', room_id=room_id)
    
    # Carrega o histórico de mensagens da sala (últimas 50 mensagens)
    message_history = room.messages.order_by('timestamp')[:50]
    
    return render(request, 'chat/room_detail.html', {
        'room': room,
        'username': username,
        'messages': message_history
    })


def leave_room(request):
    """Permite que o usuário saia da sala"""
    if 'username' in request.session:
        del request.session['username']
    if 'room_id' in request.session:
        del request.session['room_id']
    
    messages.info(request, 'Você saiu da sala.')
    return redirect('chat:room_list')
