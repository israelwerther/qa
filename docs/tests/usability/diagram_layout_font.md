# Mapeamento de Tela: diagram_layout_font.html

> Componente Alpine da sidebar de **Fonte** do Diagramador de Provas (`/provas/<uuid>/v2/imprimir/`). Permite selecionar o tipo de fonte (Padrão Lize 0–4 ou Fontes da Instituição ativas do cliente), tamanho e opções tipográficas (letras maiúsculas e hifenização).

## 1. URLs e Navegação
- **Diagramador (nova experiência):** `/provas/<uuid>/v2/imprimir/` (`exams:exam-print-v2`, view `ExamPrintV2View`)
- **Navegação na UI:** Menu lateral → **Cadernos** (ou **Instrumentos Avaliativos**) → abrir o caderno desejado → clicar em **"Diagramar"**
- **Sidebar de Layout:** Abrir o acordeon / seção **"Fonte"**
- **Permissão necessária:** `exams.can_diagram_exam` (o caderno não pode estar marcado como `is_printed=True`)
- **Componente:** `fiscallizeon/exams/components/diagram/diagram_layout/diagram_layout_font.html`
- **Script Alpine associado:** `fiscallizeon/exams/components/diagram/diagram_layout/diagram_layout_list.js`

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
- Usuário do tipo coordenação ou professor com permissão `can_diagram_exam` e `view_exam`
- Cliente (`Client`) com ou sem instâncias ativas de `ClientPrintFont`
- Caderno (`Exam`) associado à coordenação do usuário e com `is_printed=False`

```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, ClientPrintFont, ExamPrintConfig
from fiscallizeon.exams.models import Exam

client_obj = mixer.blend(Client, name="Escola Teste QA")
unity = mixer.blend('clients.Unity', client=client_obj)
coordination = mixer.blend('clients.SchoolCoordination', unity=unity)
user = mixer.blend(User, user_type='coordination', two_factor_enabled=False, must_change_password=False)
mixer.blend('clients.CoordinationMember', user=user, coordination=coordination)
user.user_permissions.add(Permission.objects.get(codename='can_diagram_exam'))
user.user_permissions.add(Permission.objects.get(codename='view_exam'))

# Fonte extra cadastrada para o cliente
custom_font = ClientPrintFont(
    client=client_obj,
    label='Minha Fonte Institucional',
    is_active=True,
    sort_order=1
)
custom_font.font_file.name = 'clients/print-fonts/minha_fonte.woff2'
custom_font.save()

# Caderno vinculado
config = ExamPrintConfig.objects.create(
    client=client_obj,
    name='Padrão QA',
    font_family=0,
    client_print_font=custom_font
)
exam = mixer.blend(Exam, is_printed=False, exam_print_config=config, coordinations=[coordination])
```

## 3. Seletores DOM e Ações

### 3.1 Seção Tipo de Fonte (Alpine `examPrintConfig`)
| Controle | Seletor DOM / Elemento | Binding / Evento | Opções / Valores |
|---|---|---|---|
| Select Tipo de fonte | `select:has(optgroup[label="Padrão Lize"])` | `:value="fontFamilySelectValue"`, `@change="onFontFamilySelect($event)"` | `std:0` (Plex Sans), `std:1` (Verdana), `std:2` (Times), `std:3` (Arial), `std:4` (Nunito Sans), `custom:<id>` (Fontes da instituição) |
| Optgroup Padrão Lize | `optgroup[label="Padrão Lize"]` | Iteração sobre `printFontChoices.standard` | Valores com prefixo `std:` |
| Optgroup Instituição | `optgroup[label="Fontes da instituição"]` | Renderizado condicionalmente com `x-if="printFontChoices.client && printFontChoices.client.length"` | Valores com prefixo `custom:<uuid>` |
| Texto auxiliar | `p:has-text("Fontes da instituição são liberadas pela Lize")` | `x-show="printFontChoices.client && printFontChoices.client.length"` | Rótulo explicativo para o usuário |
| Input Tamanho | `input[type="number"][step="1"]` | `x-model.number="examPrintConfig.fontSize"` | Tamanho em pt (ex: 12) |
| Toggle Maiúsculas | `input[type="checkbox"]` dentro da label "Imprimir caderno em letras maiúsculas" | `x-model="examPrintConfig.uppercaseLetters"` | Booleano |
| Toggle Hifenizar | `input[type="checkbox"]` dentro da label "Hifenizar texto automaticamente" | `x-model="examPrintConfig.hyphenate"` | Booleano |

> **Observação técnica sobre seletores:** O `<select>` de Tipo de fonte não possui atributo `id`. Recomenda-se para testes automatizados Playwright o seletor `select:has(optgroup[label="Padrão Lize"])` ou adicionar futuramente `id="id-diagram-font-family"`.

### 3.2 Estado JS e Ações (`diagram_layout_list.js`)
- `fontFamilySelectValue`: Retorna `custom:<id>` se `clientPrintFontId` estiver preenchido; caso contrário retorna `std:<fontFamily>`.
- `onFontFamilySelect($event)`: Ao selecionar opção com `custom:`, preenche `clientPrintFontId` e anula seleção padrão; ao selecionar `std:`, anula `clientPrintFontId` e preenche `fontFamily` numérico.
- `saveLayoutSettings()`: Envia via API `clientPrintFont: this.examPrintConfig.clientPrintFontId || null` e `fontFamily: this.examPrintConfig.fontFamily`.

## 4. API Interception & Fixtures
- **Choices de Fonte (View Context):** `print_font_choices_json` injetado no HTML via `get_print_font_choices(user.client)` no `ExamPrintV2View`.
- **API de Atualização:** `PATCH /api/v1/exams/<uuid>/print-config/` (ou `api:exams:exam-print-config-update`) com serializer `ExamPrintConfigUpdateApi.InputSerializer`.
- **Validação:** Tentativa de enviar `client_print_font` de outro cliente resulta em HTTP 400 (`"A fonte selecionada não pertence ao cliente deste caderno."`).
