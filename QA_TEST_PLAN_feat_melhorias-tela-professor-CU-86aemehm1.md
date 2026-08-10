## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-08-10 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Teacher Dashboard / Painel do Professor |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐☆☆ (N/A — Refatoração e adição de componente visual Empty State no Painel) |

---

## 1. Summary of Changes (Resumo das Alterações)

- **Componente Empty State (`components/empty_state/`):**
  - Criado o componente reutilizável `empty_state` (`empty_state.html`, `empty_state.py`, `README.md`) para padronizar telas sem dados.
  - Criado o componente de ícone `clipboard-check` (`components/icons/clipboard-check.html`) exibindo o SVG de prancheta com marcação de verificação.
- **Refatoração do Componente `TeacherTabs` (`teacher_tabs.py` & `teacher_tabs.html`):**
  - **Aba Padrão:** O atributo `active_tab` passa a ser fixo em `"opened"` ("Elaborar"), garantindo que a aba Elaborar abra sempre como padrão.
  - **Visibilidade Contínua:** Removida a lógica condicional que ocultava abas do professor quando não havia itens. As abas permanecem acessíveis na interface.
  - **Inclusão dos Estados Vazios:** Adicionado o componente `empty_state` nos painéis das abas ("opened", "corrections", "review") para quando as contagens de cards forem zero (`<= 0`).
  - **Mensagens Específicas por Aba:**
    - **Elaborar:** *"Não há questões para elaboração"* | *"Parabéns! Você não possui questões para serem elaboradas."*
    - **Corrigir:** *"Não há questões para correção"* | *"Parabéns! Você não possui questões para serem corrigidas."*
    - **Revisar:** *"Não há questões para revisão"* | *"Parabéns! Você não possui questões para serem revisadas."*
- **Ajustes de Estilos Tailwind (`tw.css`):**
  - Adicionada a classe utilitária `.tw-text-[#F79009]` para a cor de alerta/status em badges e ajustada a hierarquia das bordas amarelas.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- **No Escopo:**
  - Carregamento inicial do Painel do Professor selecionando a aba "Elaborar" por padrão.
  - Exibição visual contínua das abas "Elaborar", "Corrigir" e "Revisar" no topo do componente de abas.
  - Renderização visual do componente `empty_state` com título, descrição e ícone `clipboard-check` em abas sem pendências.
  - Exibição correta de cards de tarefas quando existirem solicitações/provas pendentes.
  - Transição interativa entre as abas ao clicar nos gatilhos ("Elaborar", "Corrigir", "Revisar").
  - Funcionamento dos botões de rodapé ("Todas as solicitações", "Todas as correções", "Todas as revisões").
- **Fora de Escopo:**
  - Fluxo interno do elaborador de provas (criação/inserção de questões).
  - Interface interna de correção de redações ou digitação de notas de provas presenciais.
  - Regras de cálculo de prazo e relatórios avançados de produção de revisores.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Painel do Professor | Visão Geral / Painel do Professor | `/dashboard/` ou `/` | `core:dashboard_teacher` |
| Aba Elaborar | Elaborar | `/dashboard/` (Aba `#opened`) | Componente `TeacherTabs` |
| Aba Corrigir | Corrigir | `/dashboard/` (Aba `#corrections`) | Componente `TeacherTabs` |
| Aba Revisar | Revisar | `/dashboard/` (Aba `#review`) | Componente `TeacherTabs` |
| Listagem de Elaborações | Todas as solicitações | `/exams/examteachersubject/?v=2` | `exams:exam-teacher-subject-list` |
| Listagem de Pendências de Correção | Todas as correções | `/exams/pendences/` | `exams:exam-teacher-correction-pendence-list` |
| Listagem de Revisões | Todas as revisões | `/exams/review/?v=2` | `exams:exam-teacher-subject-to-review-list` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comando CLI pytest para Execução de Suíte Correlata:
```bash
pytest fiscallizeon/exams/tests/models/test_teacher_panel_deadline_filters.py
```

### Persona de Teste:
- **Usuário:** Professor (`User.TEACHER` / `Inspector.TEACHER`) associado a uma unidade e coordenação escolar.
- **Flags de permissão ativas:** `is_discipline_coordinator=True` (para visualizar a aba Revisar) e `client.has_followup_dashboard=True` (para a aba Corrigir).

### Python Mixer Setup Snippet:
```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.inspectors.models import Inspector
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination

# Setup do Professor com 0 solicitações (Estado Vazio)
client = mixer.blend(Client, has_followup_dashboard=True)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)

user = mixer.blend(User, client=client, user_type=User.TEACHER)
teacher = mixer.blend(
    Inspector,
    user=user,
    email=user.email,
    inspector_type=Inspector.TEACHER,
    is_discipline_coordinator=True,
)
teacher.coordinations.add(coordination)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Estado Vazio e Carregamento Padrão [Automatizável ✅]

#### Cenário 1 — Carregamento Inicial com Aba 'Elaborar' Padrão e Estado Vazio
- [X] Autenticar no sistema com a Persona Professor.
- [X] Acessar o Painel do Professor (`/dashboard/`).
- [X] Confirmar que a aba "Elaborar" vem selecionada como ativa por padrão.
- [ ] Em uma conta sem solicitações pendentes, verificar se o componente de estado vazio é exibido com o ícone de prancheta, título "Não há questões para elaboração" e texto "Parabéns! Você não possui questões para serem elaboradas.".

#### Cenário 2 — Navegação para Abas 'Corrigir' e 'Revisar' em Estado Vazio
- [ ] Na mesma tela do painel, clicar na aba "Corrigir".
- [ ] Validar que a aba é aberta e exibe o estado vazio com o título "Não há questões para correção" e a mensagem "Parabéns! Você não possui questões para serem corrigidas.".
- [ ] Clicar na aba "Revisar".
- [ ] Validar que a aba abre e exibe o estado vazio com o título "Não há questões para revisão" e a mensagem "Parabéns! Você não possui questões para serem revisadas.".

### 5.2 Renderização de Cards com Dados Pendentes [Automatizável ✅]

#### Cenário 3 — Renderização de Cards em Elaborar quando existem pendências
- [ ] Associar uma solicitação de elaboração de prova ao professor de teste.
- [ ] Recarregar a página `/dashboard/` e confirmar que a aba "Elaborar" renderiza o card da solicitação com o botão "Continuar", ocultando o componente de estado vazio.
- [ ] Confirmar que o contador numérico da aba reflete o número real de itens.

### 5.3 Redirecionamento dos Botões Globais de Listagem [Automatizável ✅]

#### Cenário 4 — Ações de Redirecionamento
- [ ] Na aba "Elaborar", clicar no botão de rodapé "Todas as solicitações" e validar o direcionamento para a página de listagem de provas.
- [ ] Na aba "Corrigir", clicar no botão de rodapé "Todas as correções" e validar o redirecionamento para a listagem de pendências.
- [ ] Na aba "Revisar", clicar no botão "Todas as revisões" e validar o redirecionamento para a página de revisões.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] Tirar screenshot da aba "Elaborar" em estado vazio e conferir a centralização dos elementos visuais.
- [ ] Tirar screenshot da aba "Corrigir" em estado vazio.
- [ ] Tirar screenshot da aba "Revisar" em estado vazio.
- [ ] Validar a legibilidade e o alinhamento das abas em resoluções de desktop (1920x1080 e 1366x768).

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Nenhum bug impeditivo identificado até o momento no componente de estado vazio ou no chaveamento de abas.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Adição de IDs estáveis no DOM para as Abas:** As abas "Corrigir" e "Revisar" no template `teacher_tabs.html` usam eventos Alpine `@click="active = 'corrections'"` e `@click="active = 'review'"` em elementos `div` genéricos sem atributos `id`. Recomenda-se adicionar `id="tab-corrections"` e `id="tab-review"` no HTML para facilitar localizadores diretos em autômatos Playwright.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML (`teacher_tabs.html`), e não a View ou o template raiz.
🔗 **[Ver Mapeamento de Tela](docs/tests/usability/teacher_tabs.md)**

### Automation Snippet (Python / Playwright):
```python
import pytest
from playwright.sync_api import Page, expect
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.inspectors.models import Inspector
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination

@pytest.mark.django_db
def test_teacher_dashboard_tabs_and_empty_states(page: Page, live_server):
    # Setup de dados via Mixer
    client = mixer.blend(Client, has_followup_dashboard=True)
    unity = mixer.blend(Unity, client=client)
    coordination = mixer.blend(SchoolCoordination, unity=unity)

    user = mixer.blend(User, client=client, user_type=User.TEACHER)
    teacher = mixer.blend(
        Inspector,
        user=user,
        email=user.email,
        inspector_type=Inspector.TEACHER,
        is_discipline_coordinator=True,
    )
    teacher.coordinations.add(coordination)

    # Navegação
    page.goto(f"{live_server.url}/dashboard/")

    # Aba Elaborar ativa por padrão com estado vazio
    expect(page.locator("button#opened")).to_be_visible()
    expect(page.get_by_text("Não há questões para elaboração")).to_be_visible()

    # Alternar para a aba Corrigir
    page.get_by_text("Corrigir").click()
    expect(page.get_by_text("Não há questões para correção")).to_be_visible()

    # Alternar para a aba Revisar
    page.get_by_text("Revisar").click()
    expect(page.get_by_text("Não há questões para revisão")).to_be_visible()
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Gargalo Principal:** Nenhum. A feature consistiu na criação de componente genérico de estado vazio e ajuste de fluxo no AlpineJS/Django Component.
- **Interações com Dev:** N/A.
- **Melhoria no Workflow:** Incluir IDs semânticos (`id="tab-..."`) na criação de novos componentes Django para simplificar a camada de testes autônomos.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
