from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import Room
from .forms import SignUpForm, SignInForm

# Create your views here.

def signup_view(request):
    """View de cadastro de novos usuários"""
    if request.user.is_authenticated:
        return redirect('chat:room_list')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Faz login automático após o cadastro
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.first_name}! Sua conta foi criada com sucesso.')
            return redirect('chat:room_list')
    else:
        form = SignUpForm()
    
    return render(request, 'chat/signup.html', {'form': form})


def signin_view(request):
    """View de login de usuários"""
    if request.user.is_authenticated:
        return redirect('chat:room_list')
    
    if request.method == 'POST':
        form = SignInForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo de volta, {user.first_name}!')
                # Redireciona para a próxima página ou para a lista de salas
                next_page = request.GET.get('next', 'chat:room_list')
                return redirect(next_page)
    else:
        form = SignInForm()
    
    return render(request, 'chat/signin.html', {'form': form})


def logout_view(request):
    """View de logout"""
    logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('chat:signin')

@login_required(login_url='chat:signin')
def room_list(request):
    """Lista todas as salas ativas"""
    rooms = Room.objects.filter(is_active=True)
    return render(request, 'chat/room_list.html', {'rooms': rooms})


@login_required(login_url='chat:signin')
def join_room(request, room_id):
    """Permite que o usuário entre em uma sala"""
    room = get_object_or_404(Room, id=room_id, is_active=True)
    
    # Salva o room_id na sessão
    request.session['room_id'] = room_id
    
    return redirect('chat:room_detail', room_id=room_id)


@login_required(login_url='chat:signin')
def room_detail(request, room_id):
    """Exibe a sala de bate-papo"""
    room = get_object_or_404(Room, id=room_id, is_active=True)
    
    # Verifica se o usuário entrou na sala
    if request.session.get('room_id') != room_id:
        messages.warning(request, 'Por favor, entre na sala primeiro.')
        return redirect('chat:join_room', room_id=room_id)
    
    # Carrega o histórico de mensagens da sala (últimas 50 mensagens)
    message_history = room.messages.order_by('timestamp')[:50]
    
    return render(request, 'chat/room_detail.html', {
        'room': room,
        'username': request.user.username,
        'messages': message_history
    })


@login_required(login_url='chat:signin')
def leave_room(request):
    """Permite que o usuário saia da sala"""
    if 'room_id' in request.session:
        del request.session['room_id']
    
    messages.info(request, 'Você saiu da sala.')
    return redirect('chat:room_list')
