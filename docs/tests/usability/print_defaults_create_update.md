# Mapeamento de Tela: print_defaults_create_update.html

> Tela de criar/editar **padrão de impressão** da escola. Reutiliza o bloco Vue de `exam_configs_form.html` (inclui **Layout de alternativas**).

## 1. URLs e Navegação
- **Listagem:** `/membros/padrao/configuracao/` → `clients:print-configs-list`
- **Criar:** `/membros/padrao/configuracao/cadastrar/` → `clients:print-configs-create`
- **Editar:** `/membros/padrao/configuracao/atualizar/<uuid>/` → `clients:print-configs-update`
- **Menu:** Gerenciamento → Provas → **Padrões de impressão**
- **Breadcrumb na tela:** link **"Padrões de impressão"**
- **Títulos:** *"Cadastrar um novo padrão de impressão"* / *"Editar o padrão de impressão"*; botões *"Cadastrar padrão de impressão"* / *"Atualizar padrão de impressão"*

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
- `clients.view_examprintconfig` (e `add_examprintconfig` / `change_examprintconfig` conforme ação)
- Persona coordination do mesmo `Client`

```python
from mixer.backend.django import mixer
from fiscallizeon.clients.models import Client, ExamPrintConfig

client_obj = mixer.blend(Client)
config = ExamPrintConfig.objects.create(
    client=client_obj,
    name='Padrão QA',
    is_default=True,
    alternatives_striped=True,
    alternatives_separator_line=True,
    alternatives_marker=True,
    alternatives_marker_color=0,
    alternatives_marker_border=False,
    alternatives_alignment=0,
)
```

## 3. Seletores DOM e Ações
- Controles de layout: **mesmos IDs** de `exam_configs_form.md` (`#id-alternatives-striped`, etc.)
- Persistência: Vue app da página posta/atualiza via API `print-configs` e redireciona para a listagem

## 4. API Interception & Fixtures
- `GET/POST /api/v1/clients/print-configs/`
- `GET/PATCH /api/v1/clients/print-configs/<uuid>/`
- Body camelCase exemplo: `{"alternativesStriped": false, "alternativesSeparatorLine": false, "alternativesMarker": true, "alternativesMarkerColor": 0, "alternativesMarkerBorder": false, "alternativesAlignment": 1}`
- Cobertura automatizada: `TestExamAlternativesLayoutAPI` em `test_exam_alternatives_layout.py`
- Entidade crítica: `ExamPrintConfig` (defaults da escola herdados por cadernos/modais quando selecionados)
