from django.contrib import admin
from .models import Room, Message


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    ordering = ("-created_at",)
    fieldsets = (
        ("Informações da Sala", {"fields": ("name", "description", "is_active")}),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("user", "room", "content_preview", "timestamp")
    list_filter = ("room", "timestamp")
    search_fields = ("user__username", "user__first_name", "content")
    ordering = ("-timestamp",)

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Conteúdo"
