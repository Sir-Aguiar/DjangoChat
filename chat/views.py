from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q, Max
from .models import Room, Message
from .forms import SignUpForm, SignInForm


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("chat:room_list")

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Bem-vindo, {user.first_name}! Sua conta foi criada com sucesso.",
            )
            return redirect("chat:room_list")
    else:
        form = SignUpForm()

    return render(request, "chat/signup.html", {"form": form})


def signin_view(request):
    if request.user.is_authenticated:
        return redirect("chat:room_list")

    if request.method == "POST":
        form = SignInForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bem-vindo de volta, {user.first_name}!")
                next_page = request.GET.get("next", "chat:room_list")
                return redirect(next_page)
    else:
        form = SignInForm()

    return render(request, "chat/signin.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "Você saiu da sua conta.")
    return redirect("chat:signin")


@login_required(login_url="chat:signin")
def room_list(request):
    rooms = Room.objects.filter(is_active=True)
    return render(request, "chat/room_list.html", {"rooms": rooms})


@login_required(login_url="chat:signin")
def join_room(request, room_id):
    request.session["room_id"] = room_id

    return redirect("chat:room_detail", room_id=room_id)


@login_required(login_url="chat:signin")
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id, is_active=True)

    if request.session.get("room_id") != room_id:
        messages.warning(request, "Por favor, entre na sala primeiro.")
        return redirect("chat:join_room", room_id=room_id)

    # Carrega o histórico de mensagens da sala (últimas 50 mensagens)
    message_history = room.messages.order_by("timestamp")[:50]

    return render(
        request,
        "chat/room_detail.html",
        {"room": room, "username": request.user.username, "messages": message_history},
    )


@login_required(login_url="chat:signin")
def leave_room(request):
    if "room_id" in request.session:
        del request.session["room_id"]

    messages.info(request, "Você saiu da sala.")
    return redirect("chat:room_list")


@login_required(login_url="chat:signin")
def direct_messages(request):
    return render(request, "chat/direct_messages.html")


@login_required(login_url="chat:signin")
def search_users(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse([], safe=False)

    users = User.objects.filter(
        Q(username__icontains=query) | Q(first_name__icontains=query)
    ).exclude(id=request.user.id)[:10]

    users_data = [
        {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name or user.username,
        }
        for user in users
    ]

    return JsonResponse(users_data, safe=False)


@login_required(login_url="chat:signin")
def get_conversations(request):
    # Buscar todas as mensagens diretas do usuário
    messages_query = Message.objects.filter(
        Q(user=request.user, user_to__isnull=False) | Q(user_to=request.user)
    ).select_related("user", "user_to")

    # Agrupar por usuário e pegar a última mensagem
    conversations = {}
    for msg in messages_query:
        other_user = msg.user_to if msg.user == request.user else msg.user

        if other_user.id not in conversations:
            conversations[other_user.id] = {
                "user_id": other_user.id,
                "username": other_user.username,
                "first_name": other_user.first_name or other_user.username,
                "last_message": msg.content[:50],
                "timestamp": msg.timestamp,
                "has_unread": False,
            }
        else:
            # Atualizar se esta mensagem for mais recente
            if msg.timestamp > conversations[other_user.id]["timestamp"]:
                conversations[other_user.id]["last_message"] = msg.content[:50]
                conversations[other_user.id]["timestamp"] = msg.timestamp

        # Verificar se há mensagens não lidas
        if msg.user_to == request.user and not msg.is_read:
            conversations[other_user.id]["has_unread"] = True

    conversations_list = list(conversations.values())
    conversations_list.sort(key=lambda x: x["timestamp"], reverse=True)

    for conv in conversations_list:
        conv["timestamp"] = conv["timestamp"].isoformat()

    return JsonResponse(conversations_list, safe=False)


@login_required(login_url="chat:signin")
def get_direct_messages(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    # Buscar mensagens entre os dois usuários
    messages_query = (
        Message.objects.filter(
            (
                Q(user=request.user, user_to=other_user)
                | Q(user=other_user, user_to=request.user)
            )
        )
        .select_related("user")
        .order_by("timestamp")[:100]
    )

    # Marcar mensagens como lidas
    Message.objects.filter(user=other_user, user_to=request.user, is_read=False).update(
        is_read=True
    )

    messages_data = [
        {
            "id": msg.id,
            "user_id": msg.user.id,
            "username": msg.user.username,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "is_read": msg.is_read,
        }
        for msg in messages_query
    ]

    return JsonResponse(messages_data, safe=False)
