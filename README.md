**Ative o ambiente virtual**:
```powershell
.\.venv\Scripts\Activate.ps1
```

**Instale as dependências**:
```bash
pip install django channels daphne
```

**Execute as migrações**:
```bash
python manage.py migrate
```

**Crie salas de teste** (opcional):
```bash
python create_test_data.py
```

**Crie um superusuário** (para acessar o admin):
```bash
python manage.py createsuperuser
```

## Fundamental
É de extrema importância que se rode este comando ao invés de `python manage.py runserver` pois os websockets não funcionam corretamente com ele.

> A página de admin não carrega o CSS com o daphne, ou seja para usar ela tem que ser com o runserver

```bash
$env:DJANGO_SETTINGS_MODULE="djangochat.settings"
daphne djangochat.asgi:application
```
