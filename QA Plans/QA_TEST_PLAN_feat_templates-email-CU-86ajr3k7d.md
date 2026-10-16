## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-15 |
| **Natureza da Tarefa:** | `[Technical/Internal]` |
| **Área da Feature:** | Accounts / Authentication / 2FA / Password Reset / Mailgun Templates |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐ (Card ClickUp + Alinhamento Técnico em Comentários) |
| **Branch Backend (lizeedu):** | `feat/templates-email-CU-86ajr3k7d` |
| **Branch Student (lize-student):** | N/A (não afeta o app do aluno) |
| **Card ClickUp:** | [86ajr3k7d](https://app.clickup.com/t/86ajr3k7d) |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend (`lizeedu`)
- **Settings & Configurações de Templates (`fiscallizeon/settings.py`):**
  - Adicionadas configurações de templates Mailgun com fallback para defaults:
    - `MAILGUN_TEMPLATE_TWO_FACTOR = config('MAILGUN_TEMPLATE_TWO_FACTOR', default='lize-transacional-token')`
    - `MAILGUN_TEMPLATE_PASSWORD_RESET = config('MAILGUN_TEMPLATE_PASSWORD_RESET', default='lize-transacional-reset-senha')`
    - `MAILGUN_TEMPLATE_SURVEY = config('MAILGUN_TEMPLATE_SURVEY', default='lize-campanha-pesquisa')`
- **Mecanismo de Disparo de E-mail (`fiscallizeon/core/threadings/sendemail.py`):**
  - Atualização da classe `EmailThread` para suportar templates do Mailgun (`django-anymail`):
    - Parâmetros `template_id`, `merge_global_data` e `from_email` adicionados.
    - Se `template_id` estiver preenchido, define `msg.template_id = self.template_id` e `msg.merge_global_data = self.merge_global_data`, despachando pelo motor nativo de templates do Mailgun.
    - Novas funções utilitárias:
      - `send_mailgun_template(subject, to, template_id, merge_global_data)`
      - `send_two_factor_code_email(to_email, code)`: envia o assunto `"Seu código de verificação Lize"` para `[to_email]` usando o template `settings.MAILGUN_TEMPLATE_TWO_FACTOR` com `merge_global_data={'code': code}`.
      - `send_password_reset_email(to_email, subject, reset_url)`: envia o assunto do formulário para `[to_email]` usando o template `settings.MAILGUN_TEMPLATE_PASSWORD_RESET` com `merge_global_data={'reset_url': reset_url}`.
- **Autenticação em Dois Fatores 2FA (`fiscallizeon/accounts/models.py`):**
  - Em `TwoFactorAuth.send_code_email()`, remoção da renderização local do template legado em HTML (`accounts/email_template/send_email_two_factor.html`).
  - Chamada direta a `send_two_factor_code_email(self.user.email, self.two_factor_code)`.
- **Formulário e View de Redefinição de Senha (`fiscallizeon/accounts/forms.py` e `views.py`):**
  - Criação da classe `MailgunPasswordResetForm(PasswordResetForm)` que sobrescreve `send_mail(...)`:
    - Monta o caminho reverso `accounts:password_reset_confirm` com `uidb64` e `token`.
    - Constrói a URL absoluta HTTPS: `f"{context['protocol']}://{context['domain']}{reset_path}"`.
    - Dispara via `send_password_reset_email(to_email, subject, reset_url)`.
  - Em `ResetPassword` (`views.py`), substituição do formulário padrão por `MailgunPasswordResetForm` e remoção dos templates de e-mail HTML locais (`email_template_name` e `html_email_template_name`).
- **Assets e Design do E-mail (`fiscallizeon/core/static/email/`):**
  - Adicionado logotipo oficial da Lize (`logo-lize-orange.png`).
  - Adicionados ícones oficiais de redes sociais (`instagram.png`, `linkedin.png`, `whatsapp.png`, `youtube.png`) para consumo no rodapé dos templates hospedados no Mailgun.
- **Testes Automatizados:**
  - Novo arquivo de testes unitários: `fiscallizeon/accounts/tests/test_mailgun_template_email.py` cobrindo o envio de 2FA e construção da `reset_url`.
  - Ajustes de smoke em `fiscallizeon/accounts/tests/usability/test_login.py`.

---

## 2. Scope Boundaries (Diferenças de Escopo: Confronto Task vs Comentários)

> [!IMPORTANT]
> **Alinhamento Crítico de Escopo (Task vs Comentários):**
> - **O que a Task Original pedia:** A descrição inicial da task no ClickUp propunha um "template mestre único montado em blocos para qualquer comunicação da Lize", abrangendo pesquisas de CSAT/NPS, alertas operacionais para revisores e professores, além de um retrofit completo e imediato de **todos** os e-mails disparados pela plataforma.
> - **O que foi decidido nos Comentários:** Conforme alinhamento entre Dioney Vitor, Franklin Dias e Giovanna Rodrigues Nogueira, optou-se por utilizar o motor de templates do **Mailgun** (`django-anymail`). O time levantou um mapa de migração (`Mapa de Migração de Templates — Mailgun.pdf`) e deliberou que os copies e disposições visuais dos demais e-mails serão refinados pelo Marketing/Produto em um **pitch futuro separado**.
> - **Escopo Efetivo Desta Branch:** O escopo desta entrega foi intencionalmente delimitado à infraestrutura de templates Mailgun e à migração cirúrgica de **apenas 2 e-mails transacionais críticos**: (1) Código de verificação 2FA e (2) Redefinição de senha ("Esqueci minha senha").

### Dentro do Escopo
- Envio do e-mail de código 2FA via template Mailgun (`lize-transacional-token` ou variável `MAILGUN_TEMPLATE_TWO_FACTOR`) com injeção da variável `code`.
- Envio do e-mail de redefinição de senha via template Mailgun (`lize-transacional-reset-senha` ou variável `MAILGUN_TEMPLATE_PASSWORD_RESET`) com injeção da variável `reset_url`.
- Garantia de geração de link absoluto HTTPS válido apontando para o domínio da aplicação no reset de senha.
- Validação do fluxo completo de 2FA: solicitação no login, recebimento do código, validação de código correto, tratamento de código incorreto e reenvio de novo código ao expirar (> 5 minutos).
- Validação do fluxo completo de reset de senha: solicitação, recebimento do link, redefinição da nova senha e login subsequente.
- Testes de não-regressão de login para usuários sem 2FA ativo e para superusuários (bypass de 2FA).
- Validação visual do corpo do e-mail recebido em clientes reais (Gmail/Outlook/Web/Mobile).

### Fora do Escopo
- Disparo de pesquisas de CSAT ou campanhas de NPS (o template `MAILGUN_TEMPLATE_SURVEY` / `lize-campanha-pesquisa` foi apenas registrado em `settings.py` como pré-requisito arquitetural, mas nenhum fluxo da plataforma o consome nesta entrega).
- Retrofit dos demais e-mails transacionais da plataforma (boas-vindas/conta nova, alertas para revisores de questões, notificações de malote, relatórios de notas). Estes continuam como antes e serão migrados no próximo pitch.
- Telas ou interfaces web administrativas no Django para edição ou criação de templates de e-mail (a edição e montagem dos templates ocorrem diretamente no painel do Mailgun).
- Alterações em regras de negócio de login, expiração de sessão ou permissões de usuários.
- Classes CSS utilitárias em `tw.css` e `output.css` não impactam as telas de login do produto nesta entrega.

---

## 3. Navegação e Camada Técnica (Canonical Navigation Map)

| Destino | Rótulo real no menu UI / Ação | URL Django | View name | Template Subjacente |
|---|---|---|---|---|
| Tela de Login | Acesso direto ao sistema | `/conta/entrar/` | `accounts:login` | `redesign/login.html` |
| Verificação 2FA | Redirecionamento automático pós-login | `/conta/verify_2fa/` | `accounts:verify_2fa` | `accounts/verify_2fa.html` |
| Solicitar Reset de Senha | Link `"Esqueci minha senha"` na tela de login | `/conta/resetar-senha/` | `accounts:password_reset` | `accounts/password-reset/password_reset.html` |
| Confirmação de Solicitação | Redirecionamento após enviar e-mail de reset | `/conta/resetar-senha/concluido/` | `accounts:password_reset_done` | `accounts/password-reset/password_reset_done.html` |
| Confirmar Nova Senha | Acesso via link recebido no e-mail (`reset_url`) | `/conta/confirmar-redefinicao/<uidb64>/<token>/` | `accounts:password_reset_confirm` | `accounts/password-reset/password_reset_confirm.html` |
| Conclusão do Reset | Redirecionamento pós-alteração de senha | `/conta/redefinicao-concluida/` | `accounts:password_reset_complete` | `accounts/password-reset/password_reset_complete.html` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Testes Automatizados no Backend
Execute os testes que cobrem o despacho via Anymail/Mailgun e os testes de regressão de login:
```bash
source venv/bin/activate && pytest fiscallizeon/accounts/tests/test_mailgun_template_email.py fiscallizeon/accounts/tests/usability/test_login.py --reuse-db
```

### Personas Requeridas para o QA Manual
1. **Persona Coordenação com 2FA:** Usuário com `user_type='coordination'`, `two_factor_enabled=True` (ou cliente com `two_factor_enabled=True`) e e-mail real acessível pelo testador.
2. **Persona Professor com 2FA:** Usuário com `user_type='teacher'`, `two_factor_enabled=True` e e-mail real acessível.
3. **Persona Coordenação/Professor SEM 2FA (Regressão):** Usuário com `two_factor_enabled=False` e cliente com `two_factor_enabled=False`.
4. **Persona Superuser (Regressão):** Usuário com `is_superuser=True` em cliente com 2FA ativado (para validação do bypass).
5. **Persona Aluno (Regressão):** Aluno ativo para validação de login direto no painel legado ou SPA.

### Setup de Dados via Mixer (Python Shell)
Execute `python manage.py shell` no container da aplicação para criar o ecossistema exato de teste:

```python
from django.utils import timezone
from datetime import timedelta
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User, TwoFactorAuth
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity, CoordinationMember

# 1. Configurar Cliente com 2FA ativo
client_2fa = Client.objects.filter(two_factor_enabled=True).first()
if not client_2fa:
    client_2fa = mixer.blend(Client, name="[QA] Escola 2FA Mailgun", two_factor_enabled=True)

unity = client_2fa.unities.first() or mixer.blend(Unity, client=client_2fa)
coordination = unity.coordinations.first() or mixer.blend(SchoolCoordination, unity=unity)

# 2. Criar Usuário Coordenador com 2FA ativo e e-mail acessível pelo QA
email_qa = "qa.teste@suaempresa.com"  # SUBSTITUIR PELO SEU E-MAIL REAL DE TESTE
coord_user = User.objects.filter(email=email_qa).first()
if not coord_user:
    coord_user = mixer.blend(
        User,
        username="qa.coord.2fa",
        email=email_qa,
        user_type="coordination",
        client=client_2fa,
        two_factor_enabled=True,
        must_change_password=False,
        can_access_app=False,
        is_active=True,
    )
    coord_user.set_password("SenhaForte@123")
    coord_user.save()
    mixer.blend(CoordinationMember, user=coord_user, coordination=coordination)
else:
    coord_user.two_factor_enabled = True
    coord_user.client = client_2fa
    coord_user.save()

# 3. Criar Usuário SEM 2FA para teste de regressão
user_sem_2fa = mixer.blend(
    User,
    username="qa.sem2fa",
    email="qa.sem2fa@lize.local",
    user_type="teacher",
    client=client_2fa,
    two_factor_enabled=False,
    must_change_password=False,
    can_access_app=False,
    is_active=True,
)
user_sem_2fa.set_password("SenhaForte@123")
user_sem_2fa.save()

# 4. Criar Superusuário para teste de bypass
superuser = mixer.blend(
    User,
    username="qa.superuser",
    email="qa.superuser@lize.local",
    user_type="coordination",
    client=client_2fa,
    is_superuser=True,
    is_staff=True,
    must_change_password=False,
    is_active=True,
)
superuser.set_password("SenhaForte@123")
superuser.save()

print("Setup de QA concluído com sucesso!")
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 E-mail e Validação de Código 2FA [Automatizável ✅]

#### Cenário 1 — Disparo e Recebimento de E-mail de Código 2FA no Login
**Ação humana:**
- [x] Acessar a tela de login do sistema em `/conta/entrar/`.
- [x] Informar o usuário e senha da **Persona Coordenação com 2FA** configurada com e-mail real.
- [x] Clicar no botão `"**Entrar**"` (botão laranja com cantos arredondados).
- [x] Confirmar o redirecionamento automático para a tela de verificação 2FA em `/conta/verify_2fa/`.
- [x] Verificar que a tela exibe o título `"**Bem-vindo de volta**"` e o campo `"**Insira o código enviado para o seu e-mail:**"`.
- [x] Acessar a caixa de entrada do e-mail do usuário e aguardar a chegada da mensagem (esperado em até ~1 a 2 minutos).
- [x] Conferir o remetente: `"**Lize <contato@lizeedu.com.br>**"` (ou o domínio Mailgun configurado no ambiente).
- [x] Conferir o assunto do e-mail: `"**Seu código de verificação Lize**"`.
- [x] Abrir o e-mail e constatar que o layout renderiza com o novo padrão Mailgun:
  - Logotipo oficial laranja da Lize visível e centralizado no topo.
  - Bloco de conteúdo destacando o código de segurança de 6 dígitos numéricos.
  - Rodapé com identificação institucional da Lize e ícones de redes sociais.
  - Inexistência de placeholders crus sem interpolação (ex: não deve aparecer texto literal `{{code}}`).
![alt text](../evidencias/image-18.png)

**Referência técnica (para automação):**
- URL: `/conta/entrar/` ➔ `/conta/verify_2fa/`
- Seletor do Campo de Código: `input#code`
- Seletor do Botão Verificar: `form#verify-2fa-form button[type="submit"]:has-text("Verificar")`
- Estado esperado: `TwoFactorAuth.objects.filter(user=user, is_verified=False).exists() == True`
- Fixture: `mixer.blend(TwoFactorAuth, user=user, two_factor_code="123456", expire_in=timezone.now() + timedelta(minutes=5))`

#### Cenário 2 — Conclusão de Login com Código 2FA Correto
**Ação humana:**
- [x] Na tela `/conta/verify_2fa/`, digitar exatamente o código numérico de 6 dígitos recebido no e-mail dentro do prazo de validade (5 minutos).
- [x] Clicar no botão `"**Verificar**"` (botão laranja abaixo do campo).
- [x] Verificar que o formulário é submetido com sucesso e ocorre o redirecionamento imediato para o painel principal do usuário (`/dashboard/`).
- [x] Confirmar que a sessão foi autenticada e o usuário tem acesso total aos módulos autorizados.

**Referência técnica (para automação):**
- URL: `/conta/verify_2fa/`
- Ação: `page.fill('input#code', '123456')`, `page.click('button:has-text("Verificar")')`
- Estado esperado: Redirecionamento com URL contendo `/dashboard/` ou view `core:redirect_dashboard`. Registro no banco com `two_factor_auth.is_verified == True`.

#### Cenário 3 — Tentativa de Login com Código 2FA Incorreto
**Ação humana:**
- [x] Realizar novo login com a **Persona Coordenação com 2FA** e acessar a tela `/conta/verify_2fa/`.
- [x] Informar deliberadamente um código de 6 dígitos errado (ex: `"000000"`).
- [x] Clicar no botão `"**Verificar**"`.
- [x] Confirmar que o sistema permanece na tela `/conta/verify_2fa/`.
- [x] Observar a exibição da mensagem de erro destacada no container âmbar: `"**Código inválido.**"`.
- [x] Verificar que **nenhum** novo e-mail foi disparado para a caixa postal (o código original permanece vigente durante os 5 minutos).
![alt text](../evidencias/image-19.png)

**Referência técnica (para automação):**
- URL: `/conta/verify_2fa/`
- Seletor do Erro: `div.tw-bg-amber-50 p:has-text("Código inválido.")`
- Estado esperado: HTTP 200, sem alteração de `TwoFactorAuth.is_verified`.

#### Cenário 4 — Tentativa com Código 2FA Expirado e Reenvio Automático
**Ação humana:**
- [x] Na tela `/conta/verify_2fa/`, aguardar a expiração natural da validade do código (> 5 minutos) ou forçar a expiração no banco (`expire_in = timezone.now() - timedelta(minutes=1)`).
- [x] Digitar qualquer código de 6 dígitos no campo e clicar no botão `"**Verificar**"`.
- [x] Verificar que o sistema permanece na tela de verificação e exibe a mensagem de aviso: `"**Código expirado, enviamos um novo código.**"`.
- [x] Acessar a caixa de e-mail e confirmar a chegada de um **segundo e-mail** com assunto `"**Seu código de verificação Lize**"`, contendo um **novo código de 6 dígitos**.
- [x] Inserir o novo código na tela e clicar em `"**Verificar**"`.
- [x] Confirmar que o login é concluído com sucesso e o usuário é redirecionado ao painel.

**Referência técnica (para automação):**
- URL: `/conta/verify_2fa/`
- Seletor do Erro/Aviso: `div.tw-bg-amber-50 p:has-text("Código expirado, enviamos um novo código.")`
- Validação backend: Novo registro `TwoFactorAuth` gerado com código diferente e `expire_in` renovado para +5 min.
![alt text](../evidencias/image-20.png)

---

### 5.2 E-mail e Fluxo de Redefinição de Senha [Automatizável ✅]

#### Cenário 5 — Solicitação de Nova Senha e Recebimento de E-mail com Link HTTPS
**Ação humana:**
- [x] Acessar a tela de login em `/conta/entrar/`.
- [x] Clicar no link `"**Esqueci minha senha**"` (link em cinza localizado abaixo do campo de senha).
- [x] Confirmar o redirecionamento para a tela `/conta/resetar-senha/`.
- [x] Verificar o título da página `"**Redefinição de senha**"` e a instrução `"Insira o endereço de e-mail associado à sua conta. Um link para redefinição de senha será enviado."`.
- [x] Digitar o endereço de e-mail real da conta de teste no campo `"**E-mail**"`.![alt text](../evidencias/image-21.png)
- [x] Clicar no botão `"**Enviar link**"` (botão laranja abaixo do formulário).
- [x] Confirmar o redirecionamento para a página de sucesso `/conta/resetar-senha/concluido/` exibindo o título `"**Solicitação enviada com sucesso!**"`.
- [x] Acessar a caixa de entrada do e-mail do usuário e verificar o recebimento da mensagem:
  - Assunto exato: `"**Lize Edu - Alteração de senha**"`.
  - Remetente oficial: `"**Lize <contato@lizeedu.com.br>**"`.![alt text](../evidencias/image-22.png)
- [x] Abrir o e-mail e checar os elementos visuais:
  - Logotipo laranja da Lize no topo.
  - Mensagem explicativa de redefinição de credenciais.
  - Botão de ação destacado para alterar/redefinir senha.
  - Link de redefinição deve ser uma URL absoluta segura (`https://...`), com rota contendo `/conta/confirmar-redefinicao/<uidb64>/<token>/`.
  - **Atenção especial:** O link **não** deve apontar para `localhost` ou `http://` em ambientes de homologação ou produção.

**Referência técnica (para automação):**
- URL Inicial: `/conta/resetar-senha/`
- Seletor do Campo de E-mail: `input#id_email` (ou `input[name="email"]`)
- Seletor do Botão: `form button[type="submit"]:has-text("Enviar link")`
- URL de Destino (Done): `/conta/resetar-senha/concluido/`
- Verificação do Link gerado: Inspecionar chamada mockada ou payload Anymail contendo `merge_global_data={'reset_url': ...}`.

#### Cenário 6 — Conclusão da Alteração de Senha via Link do E-mail
**Ação humana:**
- [x] No e-mail recebido, clicar no botão/link de redefinição de senha.
- [x] Confirmar a abertura da tela de confirmação em `/conta/confirmar-redefinicao/<uidb64>/<token>/`.
- [x] Constatar que a página exibe o título `"**Criar nova senha**"` e os campos `"**Nova senha**"` e `"**Confirmar nova senha**"`.![alt text](../evidencias/image-23.png)
- [x] Informar uma nova senha segura atendendo aos requisitos mínimos (ao menos 8 caracteres, uma letra maiúscula e um caractere especial) em ambos os campos.
- [x] Clicar no botão `"**Alterar senha**"` (botão laranja).
- [x] Confirmar o redirecionamento para a página de conclusão `/conta/redefinicao-concluida/` ou direto para a tela de login.
- [x] Na tela de login, inserir o usuário e a **nova senha** recém-definida.
- [x] Confirmar que o login é efetuado com sucesso (passando pelo 2FA, se o usuário possuir o recurso ativo).

**Referência técnica (para automação):**
- URL: `/conta/confirmar-redefinicao/<uidb64>/<token>/`
- Seletores: `input#id_new_password1`, `input#id_new_password2`, `button[type="submit"]:has-text("Alterar senha")`
- Validação backend: `user.check_password("NovaSenha@123") == True`.

#### Cenário 7 — Tentativa de Reutilização de Token ou Link Expirado de Reset
**Ação humana:**
- [x] Com o link de redefinição de senha que já foi utilizado com sucesso no Cenário 6, abrir novamente a mesma URL no navegador (ou clicar de novo no e-mail).
- [x] Constatar que o sistema **não** exibe o formulário de definição de senha.
- [x] Verificar a exibição da mensagem de erro em vermelho: `"**Link inválido! O link para alteração de senha é inválido ou já foi utilizado.**"`.
- [x] Confirmar que nenhuma alteração de credenciais é permitida com tokens reutilizados.![alt text](../evidencias/image-24.png)

**Referência técnica (para automação):**
- URL: `/conta/confirmar-redefinicao/<uidb64>/<token_ja_usado>/`
- Seletor do Alerta: `div.tw-text-red-500:has-text("Link inválido!")`
- Estado esperado: Template renderiza bloco `{% else %}` com `validlink == False`.

---

### 5.3 Testes de Não-Regressão e Casos de Borda [Automatizável ✅]

#### Cenário 8 — Login Direto de Usuário SEM 2FA Habilitado
**Ação humana:**
- [x] Acessar `/conta/entrar/`.
- [x] Efetuar login com a **Persona Coordenação/Professor SEM 2FA**.
- [x] Clicar no botão `"**Entrar**"`.
- [x] Confirmar que o usuário é redirecionado diretamente para o painel de coordenação/professor (`/dashboard/` ou similar).
- [x] Confirmar que a tela `/conta/verify_2fa/` **não** é apresentada em nenhum momento e **nenhum** e-mail de código 2FA é disparado.

**Referência técnica (para automação):**
- URL: `/conta/entrar/`
- Asserção: URL final não contém `/verify_2fa/`. Nenhuma thread de e-mail de 2FA disparada.

#### Cenário 9 — Login de Superusuário em Cliente com 2FA Ativo (Bypass de 2FA)
**Ação humana:**
- [x] Acessar `/conta/entrar/`.
- [x] Efetuar login com a **Persona Superuser** (`is_superuser=True`) associada a um cliente que possui `two_factor_enabled=True`.
- [x] Clicar no botão `"**Entrar**"`.
- [x] Confirmar que o superusuário é direcionado direto ao painel, sem interrupção pela tela de 2FA e sem envio de e-mail de token (garantindo que o bypass de segurança para administradores continua operacional).

**Referência técnica (para automação):**
- Validação em `fiscallizeon/accounts/views.py`: `if getattr(user, 'is_superuser', False): return response`.

#### Cenário 10 — Solicitação de Reset para E-mail Inexistente ou Inativo
**Ação humana:**
- [x] Acessar a tela `/conta/resetar-senha/`.
- [x] Digitar um e-mail aleatório que não existe na base de dados (ex: `usuario.fantasma.inexistente@lize.local`).
- [x] Clicar no botão `"**Enviar link**"`.
- [x] Confirmar que o sistema exibe a página `/conta/resetar-senha/concluido/` com a mesma mensagem neutra de sucesso (impedindo enumeração maliciosa de e-mails válidos).
- [x] Confirmar que **nenhum** e-mail de reset é despachado via Mailgun.

**Referência técnica (para automação):**
- Comportamento padrão seguro do `PasswordResetForm`: `get_users()` retorna queryset vazio e não dispara `send_mail()`.

---

### 5.4 Checklist Visual dos E-mails no Mailgun (Desktop e Mobile) [Apenas Manual 👁]

#### Cenário 11 — Validação Visual e Responsiva do E-mail de 2FA
**Ação humana:**
- [x] Abrir o e-mail de código 2FA no cliente web desktop (ex: Gmail Web ou Outlook Web).
- [x] Validar que o logotipo Lize carrega com proporção nítida (sem distorção de aspect ratio) e sem quebra de imagem.
- [x] Checar o alinhamento centralizado do código de 6 dígitos, com tipografia legível e contraste adequado.
- [x] Abrir o mesmo e-mail no aplicativo de celular (Gmail ou Apple Mail no smartphone).
- [x] Confirmar que o e-mail se adapta fluidamente à largura da tela sem exigir rolagem horizontal (scroll horizontal proibido).
- [x] Validar que os links de redes sociais do rodapé são clicáveis e direcionam para os perfis oficiais corretos da Lize.

#### Cenário 12 — Validação Visual e Responsiva do E-mail de Reset de Senha
**Ação humana:**
- [x] Abrir o e-mail de alteração de senha no cliente desktop e mobile.
- [x] Constatar que o botão de ação principal (ex: `"Redefinir senha"`) possui tamanho de toque confortável em telas touchscreen (mínimo de 44x44px de área de toque).
- [x] Checar se há texto auxiliar ou link textual alternativo abaixo do botão para o caso de o cliente de e-mail desativar estilos CSS.
- [x] Validar que não existem sobras de moldura ou caixas vazias remanescentes no template.

#### Cenário 13 — Exibição com Bloqueio de Imagens no Cliente de E-mail
**Ação humana:**
- [x] No cliente de e-mail, configurar o bloqueio do download automático de imagens externas (ou abrir em modo texto/segurança).
- [x] Abrir o e-mail de 2FA e o e-mail de reset de senha.
- [x] Confirmar que a mensagem principal permanece 100% compreensível:
  - O código numérico de 2FA continua visível em texto selecionável.
  - A ação de redefinir senha e o link continuam claramente identificáveis e acessíveis.
  - As tags `alt` das imagens (ex: logotipo da Lize) informam o nome da plataforma sem quebrar o layout.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] **Logotipo Oficial:** O arquivo de logotipo laranja (`logo-lize-orange.png`) deve carregar via CDN/URL pública do Mailgun com renderização límpida em alta densidade de pixels (Retina display).
- [x] **Variáveis e Placeholders:** Garantir ausência total de variáveis brutas do template engine do Mailgun sem substituição (ex: `{{code}}`, `{{reset_url}}`, `%recipient.code%`).
- [x] **Layout Mobile (360px a 420px):** Testar visualização em viewport reduzido garantindo que o padding lateral não esmague os números do código 2FA.
- [x] **Consistência de Cores da Marca:** O botão de ação e elementos em destaque devem seguir a paleta oficial da Lize (`#FF6900` / laranja primário).
- [x] **Telhas Web Locais:** As telas Django de login, 2FA e reset de senha devem manter o visual padronizado do design system (Tailwind `tw-*`), sem quebras de alinhamento ou artefatos visuais.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Nenhum bug bloqueante identificado na suíte automatizada unitária (`TestMailgunTemplateEmail`). Registrar abaixo qualquer anomalia de layout ou falha de entrega observada durante a execução manual em homologação:

> [!WARNING]
> ### OBS-01: Dependência de Templates Publicados Ativos no Mailgun `[Backend Logic]` `[Ambiente]`
> - **1. Title:** Falha de envio silenciosa se o template não existir no domínio Mailgun do ambiente de teste.
> - **2. Context/Root Cause:** O disparo via Anymail utiliza `msg.template_id = settings.MAILGUN_TEMPLATE_TWO_FACTOR` (default `lize-transacional-token`). Caso o ambiente de homologação ou local aponte para um domínio do Mailgun onde o template com esse exato slug não foi criado/publicado, a API do Mailgun rejeitará o envio com erro HTTP 400.
> - **3. Expected Behavior:** O ambiente de QA/homologação deve ter os templates `lize-transacional-token` e `lize-transacional-reset-senha` devidamente cadastrados e ativos no Mailgun, ou as variáveis `MAILGUN_TEMPLATE_TWO_FACTOR` e `MAILGUN_TEMPLATE_PASSWORD_RESET` no `.env` devem apontar para os nomes de templates existentes.
> - **4. Workaround:** Caso o Mailgun de homologação não esteja configurado, o desenvolvedor ou QA pode verificar o log do Celery/Django ou simular o envio utilizando o backend de console (`EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`) para inspecionar os argumentos da mensagem mockada.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Migração dos Demais Templates Transacionais (Pitch 2):** Conforme registrado no comentário de Dioney Vitor e no documento `Mapa de Migração de Templates — Mailgun.pdf`, implementar a migração dos templates de boas-vindas/criação de conta, alertas para revisores de cadernos e e-mails de notificação aos professores assim que os copies forem homologados pelo Marketing/Produto.

> [!NOTE]
> **Ativação dos Disparos de Pesquisa/NPS:** A configuração `MAILGUN_TEMPLATE_SURVEY = config('MAILGUN_TEMPLATE_SURVEY', default='lize-campanha-pesquisa')` já foi adicionada em `settings.py`. O próximo passo será plugar esse template nos fluxos de pesquisa de satisfação coordenados pelo módulo de NPS/CSAT.

> [!NOTE]
> **Fallback para E-mail HTML Legado (Circuit Breaker):** Avaliar a implementação de um mecanismo de fallback em caso de indisponibilidade transitória da API de templates do Mailgun, permitindo que a aplicação renderize o HTML localmente se a API retornar erro de template ausente.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
- 🔗 **[Ver Mapeamento de Tela: verify_2fa.md](docs/tests/usability/verify_2fa.md)**
- 🔗 **[Ver Mapeamento de Tela: password_reset.md](docs/tests/usability/password_reset.md)**

### Automation Snippet (Python / Playwright + Mixer Setup)
Snippet demonstrando o setup de banco com `mixer` e a validação do fluxo de 2FA via Playwright:

```python
from playwright.sync_api import sync_playwright
from django.utils import timezone
from datetime import timedelta
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User, TwoFactorAuth
from fiscallizeon.clients.models import Client, SchoolCoordination, Unity, CoordinationMember
from fiscallizeon.core.utils import CustomPlaywrightTransactionTestCase

class TestTwoFactorAuthenticationFlow(CustomPlaywrightTransactionTestCase):
    def setUp(self):
        self.client_obj = mixer.blend(Client, two_factor_enabled=True)
        unity = mixer.blend(Unity, client=self.client_obj)
        coordination = mixer.blend(SchoolCoordination, unity=unity)

        self.password = "SenhaSegura@123"
        self.user = mixer.blend(
            User,
            username="coordenador_qa",
            email="coord.qa@lize.local",
            user_type="coordination",
            client=self.client_obj,
            two_factor_enabled=True,
            must_change_password=False,
            can_access_app=False,
            is_active=True,
        )
        self.user.set_password(self.password)
        self.user.save()
        mixer.blend(CoordinationMember, user=self.user, coordination=coordination)

    def test_two_factor_login_and_code_validation(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 1. Login na plataforma
            page.goto(f"{self.live_server_url}/conta/entrar/")
            page.locator('input[name="username"]').fill(self.user.username)
            page.locator('input[name="password"]').fill(self.password)
            page.locator('button[type="submit"]:has-text("Entrar")').click()

            # 2. Esperar redirecionamento para verify_2fa
            page.wait_for_url("**/conta/verify_2fa/**")
            self.assertIn("/conta/verify_2fa/", page.url)

            # 3. Consultar código gerado no banco de testes
            two_factor = TwoFactorAuth.objects.get(user=self.user)
            self.assertIsNotNone(two_factor.two_factor_code)

            # 4. Inserir código de 6 dígitos e verificar
            page.locator("input#code").fill(two_factor.two_factor_code)
            page.locator('form#verify-2fa-form button[type="submit"]:has-text("Verificar")').click()

            # 5. Confirmar redirecionamento ao painel
            page.wait_for_timeout(2000)
            two_factor.refresh_from_db()
            self.assertTrue(two_factor.is_verified)

            browser.close()
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal Gargalo:** A necessidade de confrontar a especificação original do ClickUp com os comentários da task foi essencial. A task prometia um retrofit global de todos os e-mails da empresa, enquanto os comentários demonstraram que o time de engenharia e produto concordou em limitar esta entrega inicial aos 2 fluxos transacionais mais críticos (2FA e Reset de Senha), evitando esforço desnecessário de testes em fluxos não migrados.
- **Comunicação com o Time:** O alinhamento documentado no ClickUp entre Giovanna, Dioney e Franklin forneceu limites técnicos claros para o escopo.
- **Eficiência:** A centralização do envio no `sendemail.py` (`send_two_factor_code_email` e `send_password_reset_email`) isolou o acoplamento do Anymail e permitiu testes unitários limpos com mocks e validação precisa de parâmetros.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
<!-- Sugestão 1: Quando a task for de backend/infra de e-mail (Anymail/Mailgun/Celery), incluir uma seção explícita no plano de QA para validação do payload das variáveis dinâmicas (merge_global_data) antes de depender exclusivamente da caixa de entrada real, agilizando o teste em ambientes sem conexão externa com o Mailgun. -->
