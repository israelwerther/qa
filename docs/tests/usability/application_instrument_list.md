# Mapeamento de Usabilidade: application_instrument_list.html

> Template: `fiscallizeon/applications/templates/dashboard/applications/application_instrument_list.html`
> Feature: Versão 2.0 da listagem de instrumentos avaliativos (task CU-86ak8r20g / branch `feat/instrumentos-avaliativos-CU-86ak8r20g`)
> Base da seção 8.1 dos planos de QA. Alimentado incrementalmente para suporte a automação Playwright.

---

## 1. URLs e Navegação

| URL | View Django | Descrição |
|---|---|---|
| `/aplicacoes/instrumentos-avaliativos/` | `applications:application_instruments` | Listagem unificada de instrumentos avaliativos (nova tela 2.0). |
| `/aplicacoes/instrumento-avaliativo/` | `applications:application_instrument` | Tela de criação unificada de caderno + aplicação. |
| `/aplicacoes/instrumento-avaliativo/<uuid>/` | `applications:application_instrument_update` | Tela de edição unificada da aplicação existente. |
| `/aplicacoes/importar-alunos/` | `applications:application_students_import` | Importação em lote de alunos (ação secundária). |
| `/aplicacoes/importar/` | `applications:applications_import` | Importação em lote de aplicações (ação secundária). |

**Fluxo de navegação:**
1. Usuário de Coordenação ou Staff acessa a sidebar → grupo **Aplicações** → item **"Avaliações"** (ou **"Instrumentos avaliativos"**) → rota `/aplicacoes/instrumentos-avaliativos/`.
2. Nota de feature flag: a rota e o item de menu só são visíveis quando `client.has_new_application_experience = True` (ou `user.has_new_application_experience = True`).
3. Botão primário no cabeçalho: `"**+ Nova aplicação**"` (em laranja `#EA580C`) direciona para `/aplicacoes/instrumento-avaliativo/`.
4. Botão de edição na linha: abre o menu de opções (`...`) e clica em `"**Editar**"`, redirecionando para `/aplicacoes/instrumento-avaliativo/<uuid>/`.

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Persona
- **Coordenação** ou **Staff/Admin** do cliente selecionado.
- Requisitos: `user.user_type = 'coordination'` ou `user.is_superuser = True`.
- Flag de experiência ativa: `user.client.has_new_application_experience = True`.
- Permissões mínimas no grupo: `applications.view_application`, `applications.add_application`, `applications.can_change`, `applications.can_print_bag_application`, `applications.can_disclose_application`.
- 2FA desativado (`two_factor_enabled=False`) para testes automatizados.

### Fixture mínima via Mixer (Python)
```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Coordination
from fiscallizeon.applications.models import Application
from fiscallizeon.exams.models import Exam

# 1. Cliente com a feature flag habilitada
client = mixer.blend(Client, name="Escola Teste QA", has_new_application_experience=True)
coord = mixer.blend(Coordination, client=client, name="Coordenação Ensino Médio")

# 2. Usuário coordenador
coordinator = mixer.blend(
    User,
    client=client,
    user_type="coordination",
    two_factor_enabled=False,
    must_change_password=False,
)
coordinator.coordinations.add(coord)

# 3. Caderno e Aplicação vinculada
exam = mixer.blend(
    Exam,
    client=client,
    coordination=coord,
    name="Simulado 1º Bimestre",
    category=1,
)
application = mixer.blend(
    Application,
    client=client,
    coordination=coord,
    exam=exam,
    category=1,  # 1: Presencial
    name="Aplicação Simulado 1º Bimestre",
    release_result_at_end=False,
)
```

---

## 3. Seletores DOM e Ações

### 3.1. Cabeçalho e Ações Principais
| Elemento | Seletor DOM estável | Descrição |
|---|---|---|
| Botão Nova aplicação | `a[href*="/aplicacoes/instrumento-avaliativo/"]` | Botão laranja primário com texto `"**Nova aplicação**"`. |
| Botão Importar alunos | `a[href*="application_students_import"]` | Botão secundário cinza com ícone de upload. |
| Botão Importar aplicações | `a[href*="applications_import"]` | Botão secundário cinza com ícone de upload. |

### 3.2. Abas de Categoria (Tabs)
| Aba | Seletor / Ação | Comportamento |
|---|---|---|
| Todas | `button:has-text("Todas")` | `@click="selectCategory(null)"`. Exibe todas as categorias. |
| Presencial | `button:has-text("Presencial")` | `@click="selectCategory('presential')"`. Salva no `localStorage`. |
| Online | `button:has-text("Online")` | `@click="selectCategory('online')"`. Salva no `localStorage`. |
| Exercícios | `button:has-text("Exercícios")` | `@click="selectCategory('homework')"`. Salva no `localStorage`. |
| Híbrida | `button:has-text("Híbrida")` | `@click="selectCategory('hibrid')"`. Salva no `localStorage`. |

### 3.3. Barra de Filtros e Busca
| Elemento | Seletor DOM estável | Descrição |
|---|---|---|
| Campo de Busca | `#instruments-search` | Input `type="search"`, `v-model="search"`, debounce 300ms. |
| Filtro Ano | `select[name="year"]` | Filtro por ano letivo. |
| Filtro Unidade | `select[name="units"]` | Filtro por unidade escolar. |
| Filtro Turmas | `select[name="classes"]` | Filtro por turma. |
| Filtro Etapa | `select[name="levels"]` | Filtro por etapa de ensino. |
| Filtro Situação Malote | `select[name="bundle"]` | Filtro por situação do malote. |

### 3.4. Barra Flutuante de Ações em Lote (Card de Seleção)
Aparece somente quando `selectionList.length > 0`:
| Elemento | Seletor DOM estável | Descrição |
|---|---|---|
| Contêiner do Card | `.application-instruments-bulk` | `v-if="selectionList.length > 0"` |
| Contagem de selecionados | `span:has-text("selecionado")` | `${ selectedApplicationsCountLabel }` |
| Botão Limpar seleção | `button:has-text("Limpar seleção")` | `@click="clearSelection"` |
| Botão Marcar para impressão | `button:has-text("Marcar para impressão")` | `@click="bulkMarkAndUnmarkReadyForPrinting('mark')"` |
| Botão Divulgar resultados | `button:has-text("Divulgar resultados")` | `@click="bulkDisseminationOfResults"` |
| Botão Gerar malotes | `button:has-text("Gerar malotes")` | `@click="bulkBagCreate"` |
| Botão Mais opções | `button:has-text("Mais opções")` | Dropdown com desmarcar, remover malote, prazo e apagar. |

### 3.5. Linhas da Tabela e Menu Unitário de Opções
| Elemento | Seletor DOM estável | Descrição |
|---|---|---|
| Tabela principal | `table.application-instruments-table` | `table-layout: fixed` |
| Checkbox da linha | `input[type="checkbox"]` na coluna 1 | Seleciona/desmarca a aplicação. |
| Nome do Caderno | `td:nth-child(2) div.tw-font-medium` | Nome do caderno associado. |
| Turmas expansíveis | `button.application-instrument-expand` | Exibe turmas vinculadas em tooltip/popover. |
| Coluna Malote | `td.application-instruments-malote` | Badges: Gerando, Download, Erro, Pronto. |
| Botão de Opções | `button[data-toggle="dropdown"]` | Abre o menu `.application-instrument-options`. |
| Item Editar | `.application-instrument-options a[href*="instrumento-avaliativo"]` | Texto `"**Editar**"` (redireciona para edição). |
| Item Duplicar | `.application-instrument-options button:has-text("Duplicar")` | Aciona modal de duplicar aplicação. |
| Item Divulgar resultado | `.application-instrument-options button:has-text("Divulgar resultado")` | Confirmação de divulgação imediata. |

---

## 4. Rotas de API Críticas
- `GET /aplicacoes/api/instrumentos/`: Lista paginada das aplicações com filtros.
- `GET /aplicacoes/api/instrumentos/<uuid>/`: Detalhe da aplicação e permissões/opções unitárias.

