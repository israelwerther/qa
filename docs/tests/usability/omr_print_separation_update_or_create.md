# Mapeamento de Tela — `omr_print_separation_update_or_create.html`

> **Status:** Em construção contínua
> **Finalidade:** Knowledge Base de usabilidade para automação Playwright e navegação humana.
> **Relacionado a:** Task CU-86ajqg20v (`feat/gabarito-aluno-separado-CU-86ajqg20v`) — switch "Separar arquivos de gabaritos" na geração de malote.

---

## 1. URLs e Navegação

| Ação | URL | View name |
|---|---|---|
| Editar configuração de malote do cliente | `/membros/configuracao/malotes/<uuid:pk>/` | `clients:update_client_omr_configuration` (`ConfigOMRConfigurationUpdateView`) |
| Pós-save (sucesso) | redireciona para `core:redirect_dashboard` | `core:redirect_dashboard` |

**Navegação na UI:**
1. Entrar em **Configurações** do cliente.
2. No header `includes/configurations_header.html`, clicar na aba **"Malotes"** (visível quando `user|has_perm:'clients.change_clientteacherobligationconfiguration'`).
3. A tela carrega com o título "Configurações", subtítulo "Gerencie as configurações abaixo" e os campos de separação de arquivos.

> **⚠ Divergência de permissão (mapear):** o link "Malotes" é renderizado sob `clients.change_clientteacherobligationconfiguration`, mas a view exige `clients.change_confignotification` (além de `user.client == self.get_object()`). Verificar impacto na automação.

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

**Persona:** Coordenador de Malotes — `user_type` em `COORDINATION`, `user.client == client`, permissões:

- `clients.change_confignotification` (obrigatório para a view).
- `clients.change_clientteacherobligationconfiguration` (para ver o link "Malotes").

```python
from mixer.backend.django import mixer
from django.contrib.auth.models import Permission
from fiscallizeon.clients.models import Client

client = mixer.blend(
    Client,
    has_omr=True,
    omr_print_file_separation=Client.BAG_SEPARATED_FILES,
    omr_print_separate_answer_sheets=True,
)

coord = mixer.blend("accounts.User", client=client, is_superuser=True)
coord.user_permissions.add(Permission.objects.get(codename="change_confignotification"))
coord.user_permissions.add(
    Permission.objects.get(codename="change_clientteacherobligationconfiguration")
)
```

> Para testar a visibilidade condicional do switch, basta variar `omr_print_file_separation` entre `Client.BAG_SEPARATED_FILES` ("Arquivos separados") e `Client.BAG_DEFAULT` ("Padrão (Arquivos juntos)").

---

## 3. Seletores DOM e Ações

> **Gold Standard:** os campos usam os `id` padrão do Django (`id_<campo>`), estáveis e únicos. O select é controlado por Vue (`v-model`), então a mudança de valor é reativa.

### 3.1 Select — Separação de arquivos na geração de malote
- **Seletor:** `select#id_omr_print_file_separation` (`name="omr_print_file_separation"`)
- **Binding Vue:** `v-model="omrPrintFileSeparation"`
- **Valores:**
  - `default` → "Padrão (Arquivos juntos)"
  - `separated` → "Arquivos separados"
- **Ação:** `select_option("separated")` mostra o switch de gabaritos; `select_option("default")` o oculta (`v-if`).

### 3.2 Switch — Separar arquivos de gabaritos
- **Seletor:** `input#id_omr_print_separate_answer_sheets` (`name="omr_print_separate_answer_sheets"`)
- **Classe:** `custom-control-input`
- **Visibilidade condicional:** somente quando `omrPrintFileSeparation === 'separated'` (`v-if` no `.form-row.mt-3`).
- **Texto de apoio:** "Ao marcar esta opção, cada aluno terá o seu arquivo de gabarito separado em uma pasta."
- **Ação:** `check()` / `uncheck()`; salvar via botão abaixo.

### 3.3 Switch — Incluir impressão do cartão resposta discursiva por padrão (referência de padrão visual)
- **Seletor:** `input#id_print_essay_questions_default`
- **Observação:** sempre visível (sem `v-if`), padrão de estilo `custom-switch` que o novo switch replica.

### 3.4 Botão Salvar configurações
- **Seletor:** `button.btn-warning` (texto "Salvar configurações")
- **Comportamento:** `:disabled="hasDateError()"` (Vue) — depende dos campos de notificação do `object`; com datas inválidas o botão fica desabilitado.

### 3.5 Outros elementos de contexto
- **Formulário:** `form` com `{% csrf_token %}` e hidden `input[name="client"]` com `{{user.get_clients_cache.0}}`.
- **App Vue:** `el: '#app'`, `delimiters: ['${', '}']`, data `omrPrintFileSeparation` inicializada com `{{ form.instance.omr_print_file_separation|default:'default' }}`.

### 3.6 Relações de backend (contexto para validação de dados)
- **Model:** `Client.omr_print_separate_answer_sheets` (`BooleanField`, default `False`) — `fiscallizeon/clients/models.py:312`.
- **Form:** `ClientForm` (`fiscallizeon/clients/forms.py:294`) — campos `['omr_print_file_separation', 'omr_print_separate_answer_sheets', 'print_essay_questions_default']`.
- **Choices (inalteradas):** `OMR_PRINT_SEPARATION_CHOICES = (BAG_DEFAULT 'default', BAG_SEPARATED_FILES 'separated')`.
- **Migração:** `clients/migrations/0203_client_omr_print_separate_answer_sheets.py`.

---

## 4. Estrutura do ZIP de malote (comportamento esperado pós-configuração)

| Modo (`omr_print_file_separation`) | `omr_print_separate_answer_sheets` | Resultado no ZIP |
|---|---|---|
| `default` | (ignorado) | PDF único por unidade — sem pastas `cadernos/` nem `gabaritos/` |
| `separated` | `False` (default) | `gabaritos_{sala|turma}.pdf` consolidado (comportamento atual) |
| `separated` | `True` | pasta `gabaritos/` com `gabarito_{slug-do-nome}.pdf` por aluno; **sem** consolidado |

**Path por aluno:** `{unidade}/{sala-ou-turma}/gabaritos/gabarito_{slugify(unidecode(nome))}.pdf` — helper `export_answer_generate_path` em `fiscallizeon/distribution/tasks/group_files.py:44` (reutilizado em `omr/tasks/group_answer_sheet_files.py`).

**Ordem das folhas no PDF individual (via `collect_student_paths`):**
1. Página customizada da objetiva (se houver).
2. Folha objetiva (`answer_{pk}.pdf`, + `_lize` se `sum_only` com objetivas).
3. Página customizada da discursiva (se houver).
4. Folha discursiva (`discursive_{id}.pdf`).
5. Rascunho (`draft_essay_{application_id}.pdf`) e redação (`essay_{id}.pdf`) — quando `include_discursives` e caderno tiver.

**Modelo `reduced` (A5):** no modo individual não há `merge_a5_files` entre alunos — cada PDF usa só as folhas do próprio aluno.

---

## 5. API Routes e Entidades Relevantes

| Recurso | Detalhe |
|---|---|
| Celery `group_files` | Ensalamento — ramo `BAG_SEPARATED_FILES` → `fiscallizeon/distribution/tasks/group_files.py` |
| Celery `group_answer_sheet_files` / `process_unity_separated_files` | Aplicação — ramo separado → `fiscallizeon/omr/tasks/group_answer_sheet_files.py` |
| Storage | PDFs intermediários em `PrivateMediaStorage` (`ensalamentos/tmp/...`, `omr/exports/...`); ZIP final via `fs.save` |
| Entidades | `Client`, `Unity`, `SchoolCoordination`, `Room`/`SchoolClass`, `ApplicationStudent`, `ClientCustomPage`, `Exam` (objetivas CHOICE/SUM, discursivas TEXTUAL, redação ESSAY) |

---

## 6. Observações de Automação

- **Vue reatividade:** ao trocar o select via `select_option`, o `v-model` é atualizado no evento `change` nativo → `expect(...).to_be_hidden()` funciona sem recarregar a página.
- **Cadernos por aluno no modo separado (referência):** com custom page usa `cadernos/{slugify(nome)}.pdf`; sem custom page usa `cadernos/{slugify(nome)}-{pk[:5]}.pdf` — **não confundir** com o filename de gabarito (sempre `gabarito_{slug}.pdf` sem PK).
- **Validação de PDF no fluxo completo:** para conferir a ordem das folhas, contar páginas e inspecionar visualmente o PDF baixado (não há API de metadados exposta).