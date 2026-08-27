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

Controles em grupos `btn-group-toggle` (Sim/Não ou opções):

| Controle | IDs | Binding |
|----------|-----|---------|
| Zebrado Não/Sim | `#id-alternatives-striped-false` / `#id-alternatives-striped-true` | `examPrintConfig.alternativesStriped` |
| Linha Não/Sim | `#id-alternatives-separator-line-false` / `#id-alternatives-separator-line-true` | `examPrintConfig.alternativesSeparatorLine` |
| Marcador Não/Sim | `#id-alternatives-marker-false` / `#id-alternatives-marker-true` | `examPrintConfig.alternativesMarker` |
| Cor Preta/Branca | `#id-marker-color-0` / `#id-marker-color-1` | `examPrintConfig.alternativesMarkerColor` |
| Borda Não/Sim | `#id-marker-border-false` / `#id-marker-border-true` | `examPrintConfig.alternativesMarkerBorder` |
| Alinhamento Centro/Topo | `#id-alignment-0` / `#id-alignment-1` | `examPrintConfig.alternativesAlignment` |

- Rótulos `h6`: **"Zebrado:"**, **"Linha separadora entre alternativas:"**, **"Marcador das alternativas:"**, **"Cor do marcador:"**, **"Borda no marcador:"**, **"Alinhamento das alternativas:"**
- Opções de alinhamento UI: **"Centro (Padrão)"**, **"Topo (Estilo ENEM)"**
- Bloco de cor/borda: `v-if="examPrintConfig.alternativesMarker"`
- Legado **"Remover cores das alternativas"**: **removido**

## 4. API Interception & Fixtures
- `fiscallizeon/distribution/api/exams_bag.py` propaga os mesmos `exam_params` de alternativas
- Status: endpoint `.../status-malote/`
- Entidades: `RoomDistribution`, parâmetros de print no Vue `examPrintConfig`, PDF via `print_mockup_exam`
