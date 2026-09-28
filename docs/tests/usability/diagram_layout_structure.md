# Mapeamento de Tela: diagram_layout_structure.html

> Componente Alpine da sidebar de **Estrutura** do Diagramador novo (`diagram_layout_edit.html` → `/provas/<uuid>/v2/imprimir/`). Contém seletores de cabeçalho, formato, imagem de fundo + switch **"Não adicionar imagem à primeira página"** (branch `feat/imagem-fundo-malote-pular-primeira-pagina-86ak8rz8j`).

## 1. URLs e Navegação
- **Diagramador (nova experiência):** `/provas/<uuid>/v2/imprimir/` (`exams:exam-print-v2`, view `ExamPrintV2View`)
- **Navegação:** Cadernos → Instrumentos avaliativos → abrir caderno → Diagramar/Imprimir v2 [verificar rótulo do menu de ações]
- **Permissão:** `exams.can_diagram_exam`; caderno não pode estar `is_printed=True`
- **Template pai:** `dashboard/exams/v2/exam_print_new.html` (nova experiência) com sidebar `diagram_layout_list` / `diagram_layout_edit`
- **Componente:** `fiscallizeon/exams/components/diagram/diagram_layout/diagram_layout_structure.html` registrado como `diagram_layout_structure` em `fiscallizeon/exams/components/diagram/diagram.py`
- **Botão de persistência/preview:** texto **"Salvar e visualizar"** (`diagram_layout_edit.html` / `diagram_preview.html`)

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.exams.models import Exam, ExamBackgroundImage
from fiscallizeon.clients.models import Client, ExamPrintConfig

client_obj = mixer.blend(Client)
unity = mixer.blend('clients.Unity', client=client_obj)
coordination = mixer.blend('clients.SchoolCoordination', unity=unity)
user = mixer.blend(User, user_type='coordination', two_factor_enabled=False, must_change_password=False)
mixer.blend('clients.CoordinationMember', user=user, coordination=coordination)
user.user_permissions.add(Permission.objects.get(codename='can_diagram_exam'))
user.user_permissions.add(Permission.objects.get(codename='view_exam'))
background = mixer.blend(ExamBackgroundImage, client=client_obj, name='Fundo QA')
config = ExamPrintConfig.objects.create(client=client_obj, name='Padrão QA', background_image=background, skip_background_first_page=False)
exam = mixer.blend(Exam, is_printed=False, exam_print_config=config, coordinations=[coordination])
```

## 3. Seletores DOM e Ações

### 3.1 Seção Estrutura (Alpine `examPrintConfig`)
| Controle | Binding | Rótulo UI |
|----------|---------|-----------|
| Cabeçalho (select) | `x-model="examPrintConfig.header"` | "**Cabeçalho**" (opção vazia "**Não aplicar cabeçalho**") |
| Formato Completo (radio value=1) | `x-model.number="examPrintConfig.headerFormat"` | "**Completo**" |
| Formato Apenas nome (radio value=0) | `x-model.number="examPrintConfig.headerFormat"` | "**Apenas nome do aluno**" |
| Imagem de fundo (select) | `x-model="examPrintConfig.backgroundImage"` | "**Imagem de fundo**" (opção vazia "**Não aplicar imagem de fundo**") |
| Skip primeira página (switch) | `x-model="examPrintConfig.skipBackgroundFirstPage"` | "**Não adicionar imagem à primeira página**" |
| Colunas Uma/Duas | `x-model.number="examPrintConfig.columnType"` | "**Uma coluna**" / "**Duas colunas**" |
| Tipo Única/Disciplina/Tipo questão | `x-model.number="examPrintConfig.kind"` | "**Única**" / "**Por disciplina**" / "**Por tipo de questão**" |

- Bloco da imagem: `x-show="(examBackgrounds || []).length > 0"`
- Bloco do switch skip: `x-show="examPrintConfig.backgroundImage"` (só visível com imagem selecionada)
- Switch skip: `input[type="checkbox"].tw-sr-only.tw-peer` + trilho `div.tw-w-9.tw-h-5` (laranja `tw-bg-orange-100`/`tw-bg-orange-500` quando ligado, cinza quando desligado)
- Bloco formato cabeçalho: `x-show="examPrintConfig.header !== null"`

### 3.2 Estado JS (`diagram_layout_list.js`)
- Defaults: `backgroundImage: null`, `skipBackgroundFirstPage: false`, `headerFormat: 1`, `columnType: 0`, `kind: 0`
- `sectionFieldsMap.structure`: `['header', 'headerFormat', 'backgroundImage', 'skipBackgroundFirstPage', 'customPages', 'columnType', 'kind', 'textQuestionFormat']`
- Payload de save (`saveLayoutSettings`): inclui `skipBackgroundFirstPage: this.examPrintConfig.skipBackgroundFirstPage || false`

> **Débito de seletor:** os `<input>`/`<select>` desta seção **não possuem `id`**. Para automação estável, adicionar IDs (ex.: `id="id-background-image"`, `id="id-skip-background-first-page"`), seguindo o padrão Vue de `exam_configs_form.html`.

## 4. API Interception & Fixtures
- Update de print config do caderno via `ExamPrintConfigUpdateApi` (`PATCH /api/v1/exams/<uuid>/print-config/` [verificar path exato]) — campo `skipBackgroundFirstPage` (camelCase) → `skip_background_first_page`
- Preview PDF: `ExamPdfPreviewApi` → `print_to_file` com `background_image_url` + `skip_background_first_page: bool`
- `Exam.get_filters_to_print()`: inclui `skip_background_first_page` como `0`/`1`
- Entidades: `Exam`, `ExamPrintConfig`, `ExamBackgroundImage`, questões com cabeçalho completo ou apenas-nome
