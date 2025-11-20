from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    # Autenticação
    path("signup/", views.signup_view, name="signup"),
    path("signin/", views.signin_view, name="signin"),
    path("logout/", views.logout_view, name="logout"),
    # Salas de chat
    path("", views.room_list, name="room_list"),
    path("room/<int:room_id>/join/", views.join_room, name="join_room"),
    path("room/<int:room_id>/", views.room_detail, name="room_detail"),
    path("leave/", views.leave_room, name="leave_room"),
    # Mensagens diretas
    path("direct/", views.direct_messages, name="direct_messages"),
    # APIs
    path("api/search-users/", views.search_users, name="search_users"),
    path("api/conversations/", views.get_conversations, name="get_conversations"),
    path("api/messages/direct/<int:user_id>/", views.get_direct_messages, name="get_direct_messages"),
]
