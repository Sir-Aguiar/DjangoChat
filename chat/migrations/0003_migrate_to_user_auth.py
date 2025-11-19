# Generated migration for user authentication
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_default_user(apps, schema_editor):
    """
    Cria um usuário padrão para mensagens antigas se necessário
    """
    User = apps.get_model(settings.AUTH_USER_MODEL)
    if not User.objects.filter(username='sistema').exists():
        User.objects.create_user(
            username='sistema',
            first_name='Sistema',
            password='sistema123'
        )


def migrate_messages_to_users(apps, schema_editor):
    """
    Migra mensagens antigas para o sistema de usuários
    """
    Message = apps.get_model('chat', 'Message')
    User = apps.get_model(settings.AUTH_USER_MODEL)
    
    # Pega ou cria o usuário sistema
    sistema_user, _ = User.objects.get_or_create(
        username='sistema',
        defaults={
            'first_name': 'Sistema',
        }
    )
    
    # Atualiza todas as mensagens para o usuário sistema
    for message in Message.objects.all():
        message.user = sistema_user
        message.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0002_room_message_room'),
    ]

    operations = [
        # Adiciona o campo user como nullable temporariamente
        migrations.AddField(
            model_name='message',
            name='user',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='messages',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Cria usuário padrão e migra mensagens
        migrations.RunPython(create_default_user),
        migrations.RunPython(migrate_messages_to_users),
        # Torna o campo user obrigatório
        migrations.AlterField(
            model_name='message',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='messages',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Remove o campo sender antigo
        migrations.RemoveField(
            model_name='message',
            name='sender',
        ),
    ]
