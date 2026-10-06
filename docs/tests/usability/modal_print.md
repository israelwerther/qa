# Mapeamento de Tela: modal_print.html

> Modal legado Vue de impressão de malote usado na listagem de **Ensalamento** (`distribution_list.html`).

## 1. URLs e Navegação
- **Listagem:** `/ensalamento/` (`distribution:distribution_list`)
- **Menu:** Aplicações → **Ensalamento** (requer `user.client_has_distribution`)
- **API gerar malote:** `POST .../ensalamento/api/ensalamentos/<uuid>/gerar-malote/` (`distribution:export_distribution_exams_bag`)
- **Include:** `fiscallizeon/exams/templates/dashboard/exams/includes/exam/print/modal_print.html`

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
- Cliente com distribuição habilitada
- `RoomDistribution` com aplicações/alunos alocados o suficiente para gerar malote
- Persona coordination com permissões de ensalamento/impressão

```python
from mixer.backend.django import mixer
# RoomDistribution + RoomDistributionStudent conforme testes do app distribution
client_obj = mixer.blend('clients.Client')  # garantir flag de distribution no client real de QA
```

## 3. Seletores DOM e Ações

### Seção Imagem de fundo (branch skip-first-page)
- Select: `#id_background_image` (`v-model="examPrintConfig.backgroundImage"`, opção vazia "**Não há imagem de fundo**")
- Switch skip: `#id_skip_background_first_page` (`v-model="examPrintConfig.skipBackgroundFirstPage"`), visível só com `v-show="examPrintConfig.backgroundImage"`
- Rótulo do switch: "**Não adicionar imagem à primeira página**" (classe `custom-control custom-switch mt-2`)

Controles em grupos `btn-group-toggle` (Sim/Não ou opções):

| Controle | IDs | Binding |
|----------|-----|---------|
| Zebrado Não/Sim | `#id-alternatives-striped-false` / `#id-alternatives-striped-true` | `examPrintConfig.alternativesStriped` |
| Linha Não/Sim | `#id-alternatives-separator-line-false` / `#id-alternatives-separator-line-true` | `examPrintConfig.alternativesSeparatorLine` |
| Marcador Não/Sim | `#id-alternatives-marker-false` / `#id-alternatives-marker-true` | `examPrintConfig.alternativesMarker` |
| Cor Preta/Branca | `#id-marker-color-0` / `#id-marker-color-1` | `examPrintConfig.alternativesMarkerColor` |
| Borda Não/Sim | `#id-marker-border-false` / `#id-marker-border-true` | `examPrintConfig.alternativesMarkerBorder` |
| Alinhamento Centro/Topo | `#id-alignment-0` / `#id-alignment-1` | `examPrintConfig.alternativesAlignment` |

### Seção Tipo de fonte (branch fonte-cliente-diagramacao)
- Rótulo `h6`: **"Tipo de fonte:"**
- Botões padrão (`btn-group-toggle`):
  - IBM Plex Sans: `#font_family_0` (style `font-family: IBM Plex Sans;`)
  - Verdana: `#font_family_1` (style `font-family: Verdana;`)
  - Times: `#font_family_2` (style `font-family: Times;`)
  - Arial: `#font_family_3` (style `font-family: Arial;`)
  - Nunito Sans: `#font_family_4` (style `font-family: 'Nunito Sans', sans-serif;`)
- Botões institucionais (`v-for="font in printFontChoices.client"`):
  - Rótulo anterior: `p.form-text.text-muted` "**Fontes da instituição**"
  - Elementos: `label.btn.btn-outline-primary.btn-lg` com `@click="examPrintConfig.clientPrintFont = font.id"` e classe `.active` quando selecionada.
  - Texto auxiliar: `p.form-text.text-muted` "**Fontes liberadas pela Lize para sua instituição.**"
- Binding: `examPrintConfig.clientPrintFont` (ID da fonte ou `null` quando padrão) e `examPrintConfig.fontFamily` (inteiro 0–4).

## 4. API Interception & Fixtures
- `fiscallizeon/distribution/api/exams_bag.py` propaga os mesmos `exam_params` de alternativas
- Status: endpoint `.../status-malote/`
- Entidades: `RoomDistribution`, parâmetros de print no Vue `examPrintConfig`, PDF via `print_mockup_exam`
