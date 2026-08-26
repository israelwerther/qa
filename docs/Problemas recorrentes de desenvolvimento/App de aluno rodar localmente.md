# Setup Local: App do Aluno (`lize-student`)

Guia para quando o login do aluno em `http://localhost:3000/` ficar em **loop** redirecionando para `http://localhost:8000/conta/entrar/`.

---

## Por que isso acontece

O app do aluno (SPA em `localhost:3000`) não tem tela de login própria. Ele autentica via cookies OAuth2 gerados pelo Django (`localhost:8000`). O Django emite esses tokens usando uma **Application OAuth2 privada**, cujo `client_id` e `client_secret` são definidos no `.env`:

```
CLIENT_ID_PRIVATE=aJi99yYcSww5adMeCKoRhuMUhgHMKwNSQKB9AcaJ
CLIENT_SECRET_PRIVATE=pbkdf2_sha256$600000$Koov7MVr9xoIF1klx5VEes$H6ftsWdouo+6UutJM/9ugQf6LRTWVqJ4YpgftwtKc74=
```

Em um banco local zerado (ou em um checkout novo), essa Application **não existe** na tabela `oauth2_provider_application`. Resultado: o Django não consegue emitir tokens, o cookie nunca é setado, e o SPA continua redirecionando para o login eternamente.

---

## Diagnóstico Rápido

```bash
./venv/bin/python manage.py shell -c "
from django.conf import settings
from oauth2_provider.models import get_application_model
App = get_application_model()
app = App.objects.filter(client_id=settings.CLIENT_ID_PRIVATE).first()
print('App existe:', app)
"
```

Se o resultado for `App existe: None` → execute o **Fix** abaixo.

---

## Fix: Criar e Configurar a Application OAuth2

Execute o comando abaixo na raiz do projeto **uma única vez** por banco de dados:

```bash
./venv/bin/python manage.py shell -c "
from django.conf import settings
from oauth2_provider.models import get_application_model
from django.contrib.auth.hashers import make_password
from fiscallizeon.accounts.models import User

App = get_application_model()
admin_user = User.objects.filter(is_superuser=True).first()

# 1. Criar a Application (se não existir)
app, created = App.objects.get_or_create(
    client_id=settings.CLIENT_ID_PRIVATE,
    defaults={
        'name': 'Lize Student App (Private)',
        'client_type': App.CLIENT_CONFIDENTIAL,
        'authorization_grant_type': App.GRANT_PASSWORD,
        'user': admin_user,
    }
)
print('Application criada?', created, '| App:', app)

# 2. CRÍTICO: o client_secret no banco DEVE ser o hash do valor do .env
# O validador usa check_password(provided=settings.CLIENT_SECRET_PRIVATE, stored=db_value)
# Portanto, o DB precisa guardar make_password(CLIENT_SECRET_PRIVATE), não o valor bruto.
app.client_secret = make_password(settings.CLIENT_SECRET_PRIVATE)
app.save()
print('client_secret atualizado com hash correto!')

# 3. Validação: testar emissão de token
from fiscallizeon.accounts.views import issue_app_token_pair

# Substitua pelo e-mail e senha de qualquer aluno ativo no banco local:
pair = issue_app_token_pair('manuelah.a35801@aluno.decisaovirtual.com.br', '123456')
print('Teste de emissão de token:', 'OK' if pair else 'FALHOU')
"
```

---

## Por que o `make_password` é necessário

O `CLIENT_SECRET_PRIVATE` no `.env` já é uma string no formato `pbkdf2_sha256$...`. Isso confunde o validador interno do django-oauth-toolkit:

| Estado do DB                         | Comportamento do `_check_secret`                          |
|--------------------------------------|-----------------------------------------------------------|
| `pbkdf2_sha256$...` (hash do .env salvo bruto) | Tenta `check_password(hash_do_env, hash_do_env)` → **FALHA** (hash de hash) |
| `make_password(pbkdf2_sha256$...)`   | Tenta `check_password(pbkdf2_sha256$..., hash_correto)` → **OK** |

O validador usa `check_password(provided_secret, stored_secret)`, onde `provided_secret` é o valor do `.env` lido em runtime. O banco deve armazenar o **hash desse valor**, não o valor em si.

---

## Após o Fix: Fluxo de Login

```
localhost:3000 (SPA sem auth)
  └─→ redireciona para → localhost:8000/conta/entrar/
        ↓
      Você preenche e-mail/senha do aluno
        ↓
      Django gera AccessToken + RefreshToken via OAuth2 Application
        ↓
      Seta cookies HttpOnly (authorization, app_refresh) no domínio .localhost
        ↓
      Redireciona de volta para → localhost:3000/ (já autenticado!)
```

---

## Problemas Colaterais Comuns

### NotNullViolation em `clients_examprintconfig`

Ocorre ao criar provas em uma branch que não tem as colunas de diagramação avançada (`alternatives_striped`, etc.). Solução rápida:

```bash
./venv/bin/python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('''
        ALTER TABLE clients_examprintconfig
            ALTER COLUMN alternatives_striped SET DEFAULT false,
            ALTER COLUMN alternatives_striped DROP NOT NULL,
            ALTER COLUMN alternatives_separator_line SET DEFAULT false,
            ALTER COLUMN alternatives_separator_line DROP NOT NULL,
            ALTER COLUMN alternatives_marker SET DEFAULT false,
            ALTER COLUMN alternatives_marker DROP NOT NULL,
            ALTER COLUMN alternatives_marker_border SET DEFAULT false,
            ALTER COLUMN alternatives_marker_border DROP NOT NULL,
            ALTER COLUMN alternatives_marker_color SET DEFAULT 0,
            ALTER COLUMN alternatives_marker_color DROP NOT NULL,
            ALTER COLUMN alternatives_alignment SET DEFAULT 0,
            ALTER COLUMN alternatives_alignment DROP NOT NULL;
    ''')
print('Constraints relaxadas com sucesso!')
"
```

### Aluno com senha desconhecida

Para redefinir a senha de qualquer aluno local:

```bash
./venv/bin/python manage.py shell -c "
from fiscallizeon.accounts.models import User
user = User.objects.get(email='email-do-aluno@exemplo.com')
user.set_password('123456')
user.must_change_password = False
user.save()
print('Senha redefinida!')
"
```
