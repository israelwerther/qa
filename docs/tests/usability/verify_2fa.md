# Mapeamento de Tela: verify_2fa.html

> **Nota de Acervo:** Este arquivo mapeia seletores estáveis e comportamentos da tela de verificação de autenticação de dois fatores (2FA) do portal LizeEdu. O objetivo é consolidar rotas, fixtures do mixer e IDs do DOM para automação via Playwright.

## 1. URLs e Navegação
- **URL da tela:** `/conta/verify_2fa/`
- **Nome da rota Django:** `accounts:verify_2fa`
- **View:** `Verify2faFormView` (`fiscallizeon/accounts/views.py`)
- **Template subjacente:** `accounts/verify_2fa.html`
- **Gatilho de acesso:** Redirecionamento automático após login bem-sucedido via `/conta/entrar/` quando o usuário (`teacher` ou `coordination`) possui `two_factor_enabled=True` (no usuário ou no cliente) e **não** é `superuser`.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
- **Persona:** Usuário do tipo Professor (`teacher`) ou Coordenação (`coordination`) com 2FA habilitado.
- **Entidades de banco envolvidas:** `User`, `Client`, `TwoFactorAuth`.
- **Regra de bypass:** Usuários com `is_superuser=True` ou usuários sem 2FA no cadastro e sem 2FA no `Client` não são redirecionados para esta tela.
- **Setup via mixer (Python Shell / Testes):**
```python
from django.utils import timezone
from datetime import timedelta
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User, TwoFactorAuth
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity, CoordinationMember

client = mixer.blend(Client, two_factor_enabled=True)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)

user = mixer.blend(
    User,
    email="coord.2fa@lize.local",
    user_type="coordination",
    client=client,
    two_factor_enabled=True,
    must_change_password=False,
    can_access_app=False,
)
user.set_password("Senha@123")
user.save()

mixer.blend(CoordinationMember, user=user, coordination=coordination)

# Gerar registro de 2FA com código determinístico
two_factor = mixer.blend(
    TwoFactorAuth,
    user=user,
    two_factor_code="123456",
    is_verified=False,
    expire_in=timezone.localtime(timezone.now()) + timedelta(minutes=5)
)
```

## 3. Seletores DOM e Ações

### 3.1. Formulário de Verificação
- Container do formulário: `form#verify-2fa-form`
- Campo de código de 6 dígitos: `input#code` (name `code`, maxlength 6)
- Botão de envio: `form#verify-2fa-form button[type="submit"]:has-text("Verificar")`

### 3.2. Mensagens de Alerta e Erro
- Box de erro (geral): `div.tw-bg-amber-50`
- Texto de código inválido: `p:has-text("Código inválido.")`
- Texto de código expirado: `p:has-text("Código expirado, enviamos um novo código.")`
- Mensagem de validação de campo inline: `#error-message`

## 4. API Interception & Mailgun Dispatch
- Disparo de e-mail ao logar ou ao expirar código:
  - Função: `send_two_factor_code_email(to_email, code)` em `fiscallizeon.core.threadings.sendemail`
  - Template Mailgun: `settings.MAILGUN_TEMPLATE_TWO_FACTOR` (default `lize-transacional-token`)
  - Payload merge global: `{"code": "123456"}`
  - Assunto: `"Seu código de verificação Lize"`
  - Remetente: `Lize <contato@lizeedu.com.br>`
