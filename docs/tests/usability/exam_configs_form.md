# Mapeamento de Tela: exam_configs_form.html

> Formulário Vue compartilhado de configurações de impressão. Usado no modal de malote de **Aplicações** (`application_list_new.html`) e no **Setup Global** de padrões (`print_defaults_create_update.html`).

## 1. URLs e Navegação
- **Aplicações presenciais:** `/aplicacoes/?category=presential` → menu **Aplicações → Presencial**
- **Modal malote:** ações **"Gerar malote"** / imprimir malote na listagem (`showPrintModal`, títulos *"Configure a impressão do malote…"* / *"Configure a impressão dos malotes"*)
- **Padrões:** `/membros/padrao/configuracao/cadastrar/` e `/membros/padrao/configuracao/atualizar/<uuid>/`
- **Menu padrões:** Gerenciamento → Provas → **Padrões de impressão**

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
- Persona: `user_type='coordination'`
- Permissões típicas: `exams.view_exam`, `exams.can_print_exam`, `clients.view_examprintconfig` (+ add/change para criar padrão)
- Fixture: `Application` vinculada a `Exam` com questões objetivas; para massa, 2+ applications compatíveis (mesmo modelo de caderno)

```python
from mixer.backend.django import mixer
# Reutilizar padrão de test_exam_alternatives_layout + Application conforme testes de malote existentes
exam = mixer.blend('exams.Exam', coordinations=[coordination], is_printed=False)
application = mixer.blend('applications.Application', exam=exam)
```

## 3. Seletores DOM e Ações

### Seção Layout de alternativas
- Divisor: texto **"Layout de alternativas"** (`div.divider-text`)

| Controle | Seletor estável | v-model |
|----------|-----------------|---------|
| Zebrado | `#id-alternatives-striped` | `examPrintConfig.alternativesStriped` |
| Linha separadora | `#id-alternatives-separator-line` | `examPrintConfig.alternativesSeparatorLine` |
| Marcador | `#id-alternatives-marker` | `examPrintConfig.alternativesMarker` |
| Cor Preta | `#id-marker-color-black` | `examPrintConfig.alternativesMarkerColor` (=0) |
| Cor Branca | `#id-marker-color-white` | `examPrintConfig.alternativesMarkerColor` (=1) |
| Borda | `#id-alternatives-marker-border` | `examPrintConfig.alternativesMarkerBorder` |
| Alinhamento Centro | `#id-alignment-center` | `examPrintConfig.alternativesAlignment` (=0) |
| Alinhamento Topo | `#id-alignment-top` | `examPrintConfig.alternativesAlignment` (=1) |

- Bloco avançado do marcador: `v-show="examPrintConfig.alternativesMarker"`
- Legado **"Remover cores das alternativas"**: **removido** deste template

### Ações do modal (contexto Aplicações)
- Botão confirmar: textos **"Imprimir malote"** / **"Imprimir malotes"**

## 4. API Interception & Fixtures
- Malote aplicações: handler em `fiscallizeon/applications/api/exams_bag.py` lê `alternativesStriped`, `alternativesSeparatorLine`, `alternativesMarker`, `alternativesMarkerColor`, `alternativesMarkerBorder`, `alternativesAlignment` de `raw_exam_params` e injeta em `exam_params`
- Mockup: `fiscallizeon/omr/mockup_utils.py` → context do `exam_print.html`
- Padrões escola: `POST/PATCH /api/v1/clients/print-configs/` (camelCase no body; snake_case no response serializer)
- Entidades: `ExamPrintConfig`, `Application`, fila Celery de malote
