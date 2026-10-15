# Mapeamento de Tela: password_reset.html

> **Nota de Acervo:** Este arquivo mapeia seletores estáveis e comportamentos da tela de solicitação de redefinição de senha do portal LizeEdu. O objetivo é consolidar rotas, fixtures do mixer e IDs do DOM para automação via Playwright.

## 1. URLs e Navegação
- **URL da tela de solicitação:** `/conta/resetar-senha/`
- **Nome da rota Django:** `accounts:password_reset`
- **View:** `ResetPassword` (`fiscallizeon/accounts/views.py`, subclasse de `auth_views.PasswordResetView`)
- **Form:** `MailgunPasswordResetForm` (`fiscallizeon/accounts/forms.py`)
- **Template subjacente:** `accounts/password-reset/password_reset.html`
- **Tela de sucesso (done):** `/conta/resetar-senha/concluido/` (`accounts:password_reset_done`, template `accounts/password-reset/password_reset_done.html`)
- **Tela de confirmação com link do e-mail:** `/conta/confirmar-redefinicao/<uidb64>/<token>/` (`accounts:password_reset_confirm`, template `accounts/password-reset/password_reset_confirm.html`)
- **Tela de conclusão final:** `/conta/redefinicao-concluida/` (`accounts:password_reset_complete`, template `accounts/password-reset/password_reset_complete.html`)
- **Gatilho de acesso:** Link `"Esqueci minha senha"` na tela de login (`/conta/entrar/`).

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
- **Persona:** Usuário cadastrado ativo com e-mail válido.
- **Entidades de banco envolvidas:** `User`.
- **Setup via mixer (Python Shell / Testes):**
```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity, CoordinationMember

client = mixer.blend(Client)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)

user = mixer.blend(
    User,
    email="usuario.reset@lize.local",
    user_type="coordination",
    client=client,
    is_active=True,
    must_change_password=False,
    can_access_app=False,
)
user.set_password("SenhaAntiga@123")
user.save()
mixer.blend(CoordinationMember, user=user, coordination=coordination)
```

## 3. Seletores DOM e Ações

### 3.1. Tela de Solicitação (`password_reset.html`)
- Campo de E-mail: `input#id_email` (ou `input[name="email"]`)
- Botão de envio: `form button[type="submit"]:has-text("Enviar link")`
- Mensagens de erro de validação: `.invalid-feedback`

### 3.2. Tela de Solicitação Enviada (`password_reset_done.html`)
- Título de confirmação: `h2:has-text("Solicitação enviada com sucesso!")`
- Link de retorno ao login: `a:has-text("Voltar para tela de login")`

### 3.3. Tela de Confirmação e Nova Senha (`password_reset_confirm.html`)
- Campo Nova Senha: `input#id_new_password1` (name `new_password1`)
- Campo Confirmar Nova Senha: `input#id_new_password2` (name `new_password2`)
- Botão de envio: `button[type="submit"]:has-text("Alterar senha")`
- Estado de link inválido/expirado: `div.tw-text-red-500:has-text("Link inválido!")`

## 4. API Interception & Mailgun Dispatch
- Disparo de e-mail de redefinição:
  - Form: `MailgunPasswordResetForm.send_mail()`
  - Função: `send_password_reset_email(to_email, subject, reset_url)` em `fiscallizeon.core.threadings.sendemail`
  - Template Mailgun: `settings.MAILGUN_TEMPLATE_PASSWORD_RESET` (default `lize-transacional-reset-senha`)
  - Variável de contexto enviada: `{"reset_url": "https://<dominio>/conta/confirmar-redefinicao/<uidb64>/<token>/"}`
  - Assunto: `"Lize Edu - Alteração de senha"`
  - Remetente: `Lize <contato@lizeedu.com.br>`
