# Mapeamento de Tela: diagram_layout_alternatives.html

> Componente Alpine incluído no acordeão **Layout de alternativas** do Diagramador (`diagram_layout_edit.html` → `/provas/<uuid>/v2/imprimir/`).

## 1. URLs e Navegação
- **Diagramador:** `/provas/<uuid>/v2/imprimir/` (`exams:exam-print-v2`, view `ExamPrintV2View`)
- **Navegação:** Cadernos → Instrumentos avaliativos → abrir caderno → Diagramar/Imprimir v2 [verificar rótulo do menu de ações]
- **Permissão:** `exams.can_diagram_exam`; caderno não pode estar `is_printed=True`
- **Template pai:** `dashboard/exams/v2/exam_print_new.html` (nova experiência) ou `exam_print.html` (legado), com sidebar `diagram_layout_list` / `diagram_layout_edit`
- **Botão de persistência/preview:** texto **"Salvar e visualizar"** (`diagram_layout_edit.html` / `diagram_preview.html`)

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.exams.models import Exam

client_obj = mixer.blend('clients.Client')
unity = mixer.blend('clients.Unity', client=client_obj)
coordination = mixer.blend('clients.SchoolCoordination', unity=unity)
user = mixer.blend(User, user_type='coordination', two_factor_enabled=False, must_change_password=False)
mixer.blend('clients.CoordinationMember', user=user, coordination=coordination)
user.user_permissions.add(Permission.objects.get(codename='can_diagram_exam'))
user.user_permissions.add(Permission.objects.get(codename='view_exam'))
exam = mixer.blend(Exam, is_printed=False, coordinations=[coordination])
```

## 3. Seletores DOM e Ações

### 3.1 Acordeão
- Trigger texto: `span` com **"Layout de alternativas"** em `diagram_layout_edit.html`
- Indicador de seção modificada: `span` com `x-show="modifiedSections.alternatives"` (dot laranja)

### 3.2 Controles (Alpine `examPrintConfig`)
| Controle | Binding | Rótulo UI |
|----------|---------|-----------|
| Zebrado | `x-model="examPrintConfig.alternativesStriped"` | Zebrado |
| Linha | `x-model="examPrintConfig.alternativesSeparatorLine"` | Linha separadora |
| Marcador | `x-model="examPrintConfig.alternativesMarker"` | Marcador das alternativas |
| Cor | `x-model.number="examPrintConfig.alternativesMarkerColor"` | Cor do marcador (`0` Preta / `1` Branca) |
| Borda | `x-model="examPrintConfig.alternativesMarkerBorder"` | Borda no marcador |
| Alinhamento | `x-model.number="examPrintConfig.alternativesAlignment"` | Alinhamento (`0` Centro / `1` Topo) |

> **Débito de seletor:** os `<input>` **não possuem `id`**. Para automação estável, adicionar IDs alinhados ao formulário Vue, ex.: `id="id-alternatives-striped"`, `id="id-alternatives-separator-line"`, `id="id-alternatives-marker"`, `id="id-alternatives-marker-border"`, selects com `id="id-marker-color"` / `id="id-alignment"`.

### 3.3 Estado JS (`diagram_layout_list.js`)
- Defaults: `alternativesStriped: true`, `alternativesSeparatorLine: true`, `alternativesMarker: true`, `alternativesMarkerColor: 0`, `alternativesMarkerBorder: false`, `alternativesAlignment: 0`
- `sectionFieldsMap.alternatives`: lista dos 6 campos acima
- Payload de save inclui as chaves camelCase correspondentes

## 4. API Interception & Fixtures
- Update de print config do caderno via API de exames (`ExamPrintConfigUpdateApi` / endpoints usados pelo diagramador) — campos `alternatives_striped`, `alternatives_separator_line`, `alternatives_marker`, `alternatives_marker_color`, `alternatives_marker_border`, `alternatives_alignment`
- Preview PDF: query params na `ExamPrintView` (`/provas/<uuid>/imprimir?...&alternatives_striped=0&...`)
- Entidades: `Exam`, `ExamPrintConfig`, questões objetivas com alternativas multilinha
