## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data de Criação:** | 2026-11-03 |
| **Última Revisão (v3):** | 2026-11-06 (Conferência dinâmica por categoria, Acompanhamento Online e renomeação da etapa Caderno — commit `30133d412`) |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Applications / Exams / Instrumentos Avaliativos |
| **Nível de Risco:** | Alto |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ |


---

## 1. Summary of Changes (Resumo das Alterações Atualizado)

Branch `feat/instrumentos-avaliativos-CU-86ak8r20g` referente à task ClickUp `CU-86ak8r20g` (**"Versão 2.0 da criação de avaliações"**) e `17tu7rp42zh` (**"Finalizar fluxo de caderno 2.0"**). A mudança unifica a criação e acompanhamento de cadernos e aplicações a partir de um fluxo centralizado ("Instrumentos Avaliativos"). 

*Atualização de 06/11/2026 (Commit 30133d412):*
- **Renomeação da Etapa 1**: De *"Configurações"* para **`"Caderno"`** no stepper e em todos os tooltips/mensagens de validação.
- **Conferência Dinâmica por Categoria (Etapa 5)**:
  - **Presencial (`category = 3`)**: Exibe os 3 cards de malote (*Malote completo*, *Apenas gabaritos*, *Aluno específico*).
  - **Híbrida (`category = 5`)**: Exibe apenas o card *Malote completo*.
  - **Online (`category = 2`) e Lista de Exercícios (`category = 4`)**: Substitui os cards de malote físico pelo **Painel de Acompanhamento Online**, consumindo `/resumo-online/` com métricas de alunos iniciados, concluídos, não presentes, duração média, além de pausas solicitadas e saídas de tela (específicos de Online).
- **Listagem de Instrumentos**: Remoção da duplicidade do rótulo "Pronto para impressão" na coluna Situação, mantendo exibição limpa de indicadores.
- **Preservação de Coordenação**: API do caderno aceita manter o ID da coordenação existente ao editar.

### Backend (`fiscallizeon/applications/`, `accounts/`, `clients/`)
- **Controle de Feature Flag (`has_new_application_experience`)**: Adicionados campos em `Client` e `User` (sobrescrita individual), migrações `clients.0217` e `accounts.0049`.
- **API de Caderno no Instrumento (`ApplicationInstrumentExamViewSet`)**: Em `/aplicacoes/api/instrumentos/cadernos/` (POST) e `/cadernos/<uuid>/` (GET/PUT). Criação atômica no primary com lock de cliente, validação de unicidade de nome por ano e opções avançadas.
- **API de Aplicação e Participantes (`ApplicationInstrumentApplicationViewSet`)**: Em `/aplicacoes/api/instrumentos/aplicacoes/` (POST/PUT). Recebe `students` e `school_classes`, grava relações M2M, valida permissão de gestão de alunos e sincroniza turmas via `sync_school_classes_from_students()`.
- **API de Resumo Online (`application_instrument_online_summary`)**: Em `/aplicacoes/api/instrumentos/aplicacoes/<uuid>/resumo-online/` (GET). Retorna contagens de alunos inscritos, iniciados, concluídos, ausências, duração média de prova e dados de anti-cola (pausas e saídas da aplicação).
- **API de Listagem de Instrumentos (`ApplicationInstrumentViewSet`)**: Em `/aplicacoes/api/instrumentos/`. Busca com debounce, paginação, filtros por ano, unidade, turmas, etapas e situação do malote.
- **Serializers**: `ApplicationInstrumentExamSerializer`, `ApplicationInstrumentApplicationSerializer` e `ApplicationInstrumentOnlineSummarySerializer`.

### Frontend & UI (`fiscallizeon/applications/templates/`, `components/`)
- **Sidebar Dinâmica**: Itens de Coordenação e Professor adaptados para exibir `"**Avaliações**"` sob Aplicações.
- **Nova Listagem (`application_instrument_list.html`)**: Abas de categoria com `localStorage`, filtros estilizados, linhas com turmas expansíveis, badges de malote/situação limpos, dropdown unitário em 2 colunas e card flutuante de ações em lote.
- **Nova Tela Unificada (`complete_application_instrument.html`)**:
  - **Etapa 1 (Caderno)**: Dados do caderno, nota, prazos e sanfona de opções avançadas (renomeada de "Configurações" para "Caderno").
  - **Etapa 2 (Questões)**: Solicitações a docentes, IA, cadernos anteriores e modal de revisão de questões (só abre após entrega concluída).
  - **Etapa 3 (Aplicação & Participantes)**: Formato (presencial/online/híbrida), horários, tokens, componente `instrument_participants` (seleção por turma com collapse de alunos sob demanda) e seção de alunos avulsos com `search-students-component`.
  - **Etapa 5 (Conferência Dinâmica)**:
    - Para **Presencial**: 3 cards de Malote (*Malote completo*, *Apenas gabaritos*, *Aluno específico*), diálogo de impressão refatorado (`instrument_print_dialogs.html`) e barra de progresso em tempo real.
    - Para **Híbrida**: Apenas card de *Malote completo*.
    - Para **Online / Exercícios**: Painel com métricas de execução em tempo real (`resumo-online`) e botão *"Acompanhar aplicação"*.
  - **UX & Validações**: Foco e scroll automático no primeiro campo com erro; bloqueio inteligente de abas; detecção de alterações `v-changed`.


---

## 2. Scope Boundaries (Diferenças de Escopo Atualizadas)

### O QUE FOI IMPLEMENTADO (IN SCOPE — Deve ser testado agora)
- **Ativação da Feature Flag**: Alternância no Admin e exibição condicional do menu na sidebar.
- **Nova Listagem de Instrumentos Avaliativos**: Carregamento assíncrono via API, paginação, busca com debounce e filtros de ano, unidade, turmas, etapas e malote.
- **Persistência da Aba de Categoria**: Seleção da aba (Presencial, Online, Exercícios, Híbrida) salva no `localStorage`.
- **Coluna Situação Limpa**: Exibição limpa de status do caderno ou malote, sem concorrência com "Pronto para impressão" (fix validado).
- **Menu Unitário de Opções (Dropdown em 2 colunas)**: Ações de Editar, Duplicar, Divulgar resultado e ações de impressão.
- **Card de Ações em Lote**: Seleção múltipla, contagem dinâmica, marcar para impressão, divulgar resultados e gerar malotes.
- **Criação de Novo Instrumento (Etapa 1 — Caderno)**: Criação do `Exam` ao clicar em Continuar, validação de nome e persistência das opções avançadas (etapa renomeada para "Caderno").
- **Criação de Novo Instrumento (Etapa 2 — Questões & Revisão)**: Solicitação a professores, geração com IA, cadernos anteriores e modal de revisão.
- **Criação de Novo Instrumento (Etapa 3 — Aplicação & Participantes)**: Configurações de horários, tolerâncias, seleção de turmas com alunos recolhíveis e inclusão de alunos avulsos.
- **Conferência Dinâmica por Categoria (Etapa 5)**:
  - Presencial: 3 cards de malote e barra de progresso.
  - Híbrida: card de malote completo.
  - Online / Exercícios: painel de acompanhamento online com métricas de participantes, ausências, duração média, pausas e saídas de tela.
- **Edição de Instrumento Existente**: Hidratação de caderno, aplicação e participantes; detecção de alterações com `v-changed` e botão "Salvar alterações".
- **Foco Automático em Erros de Validação**: Redirecionamento automático do foco para o primeiro campo inválido ao tentar avançar ou salvar.

### O QUE AINDA NÃO FOI IMPLEMENTADO (OUT OF SCOPE — NÃO validar no momento)
- **Ação "Utilizar caderno existente" no Cabeçalho**: O seletor de cadernos prontos a partir de "Meus cadernos" no topo da nova criação ainda não foi implementado (item 6.7 do OpenSpec).
- **Etapa de Diagramação (Etapa 4)**: Continua com painel vazio/bloqueado no fluxo atual (item 6.8 do OpenSpec).
- **Modos de Exibição "Quadro" (Kanban) e "Compacto"**: Os botões de alternância de modo na listagem permanecem desativados. Apenas a visualização em tabela está ativa.
- **Distribuição de Colaboradores Responsáveis por Etapa**: Funcionalidade inexistente no backend atual; mantida fora de escopo.
- **Fluxo Legado (`application_list_new.html`)**: A listagem antiga e o cadastro antigo continuam intactos e não devem ser afetados.


---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

### Canonical Navigation Map

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Nova Listagem de Instrumentos | **Avaliações** (sidebar Aplicações) [verificar] | `/aplicacoes/instrumentos-avaliativos/` | `applications:application_instruments` |
| Criação de Novo Instrumento | **Nova aplicação** (botão laranja no cabeçalho) | `/aplicacoes/instrumento-avaliativo/` | `applications:application_instrument` |
| Edição de Instrumento Existente | **Editar** (no menu de opções `...` da linha) | `/aplicacoes/instrumento-avaliativo/<uuid>/` | `applications:application_instrument_update` |
| Importar Alunos (Legado) | **Importar alunos** (botão secundário) | `/aplicacoes/importar-alunos/` | `applications:application_students_import` |
| Importar Aplicações (Legado) | **Importar aplicações** (botão secundário) | `/aplicacoes/importar/` | `applications:applications_import` |
| API Listagem Instrumentos | (endpoint REST) | `/aplicacoes/api/instrumentos/` | `applications:application_instrument_api-list` |
| API Criação/Edição Caderno | (endpoint REST) | `/aplicacoes/api/instrumentos/cadernos/` | `applications:application_instrument_exam-list` |
| API Criação/Edição Aplicação | (endpoint REST) | `/aplicacoes/api/instrumentos/aplicacoes/` | `applications:application_instrument_application-list` |

### Mapeamentos de Usabilidade Criados

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django), e não a View.
- 🔗 **[Ver Mapeamento de Tela: Listagem](docs/tests/usability/application_instrument_list.md)**
- 🔗 **[Ver Mapeamento de Tela: Cadastro e Edição](docs/tests/usability/complete_application_instrument.md)**


---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comandos de Testes Automatizados

Execução dos testes unitários e de integração desenvolvidos nesta branch:

```bash
# Testes de View e listagem HTML
source venv/bin/activate && pytest fiscallizeon/applications/tests/test_application_instrument_view.py --reuse-db

# Testes de Edição e detecção de alterações (v-changed)
source venv/bin/activate && pytest fiscallizeon/applications/tests/test_application_instrument_edit_view.py fiscallizeon/applications/tests/test_application_instrument_changes.py --reuse-db

# Testes de API (Criação, Edição de Caderno e Aplicação)
source venv/bin/activate && pytest fiscallizeon/applications/tests/api/test_application_instrument_api.py fiscallizeon/applications/tests/api/test_application_instrument_exam_edit.py fiscallizeon/applications/tests/api/test_application_instrument_application_edit.py --reuse-db

# Testes de Acesso e Sidebar
source venv/bin/activate && pytest fiscallizeon/applications/tests/test_application_instrument_access_flag.py fiscallizeon/core/tests/test_sidebar_application_experience.py --reuse-db
```

### Personas

- **Coordenação do Piloto (Principal):** Usuário do tipo Coordenação (`user.user_type = 'coordination'`) com `user.client.has_new_application_experience = True` e coordenações atribuídas. Tem acesso à criação, edição e listagem de instrumentos.
- **Coordenação Legada (Controle):** Usuário de Coordenação cujo cliente possui `has_new_application_experience = False`. Deve continuar vendo o menu e as telas legadas.
- **Professor Autor:** Usuário do tipo Professor (`user.user_type = 'teacher'`) com permissão de elaborar e autor do caderno. Acessa a API ou edição pontual caso possua permissão de alteração.

### Setup de Dados via Mixer (Python Shell)

Para testar manualmente no ambiente local com uma aplicação pronta:

```python
from mixer.backend.django import mixer
from django.utils import timezone
from datetime import timedelta
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Coordination, TeachingStage, SchoolGrade, SchoolClass
from fiscallizeon.applications.models import Application
from fiscallizeon.exams.models import Exam, Subject

# 1. Configura Cliente Piloto
client = Client.objects.filter(name="Escola Piloto 2.0").first()
if not client:
    client = mixer.blend(Client, name="Escola Piloto 2.0", has_new_application_experience=True)
else:
    client.has_new_application_experience = True
    client.save()

coord = Coordination.objects.filter(client=client).first() or mixer.blend(Coordination, client=client, name="Coordenação Médio")
stage = TeachingStage.objects.filter(client=client).first() or mixer.blend(TeachingStage, client=client, name="Ensino Médio")
grade = SchoolGrade.objects.filter(teaching_stage=stage).first() or mixer.blend(SchoolGrade, teaching_stage=stage, name="1ª Série")
turma = SchoolClass.objects.filter(school_grade=grade).first() or mixer.blend(SchoolClass, school_grade=grade, name="Turma A", client=client)

# 2. Configura Usuário de Coordenação
user = User.objects.filter(email="coord.piloto@lize.local").first()
if not user:
    user = mixer.blend(
        User,
        email="coord.piloto@lize.local",
        client=client,
        user_type="coordination",
        two_factor_enabled=False,
        must_change_password=False,
    )
    user.set_password("123456")
    user.save()
user.coordinations.add(coord)

# 3. Cria Instrumento para Teste de Edição e Listagem
exam = mixer.blend(
    Exam,
    client=client,
    coordination=coord,
    name="Avaliação Diagnóstica 2026",
    category=1,
    total_grade=10.0,
    elaboration_deadline=timezone.now().date() + timedelta(days=5),
)
app = mixer.blend(
    Application,
    client=client,
    coordination=coord,
    exam=exam,
    category=1,
    name="Aplicação Diagnóstica 2026",
    start="08:00",
    end="11:30",
    release_result_at_end=False,
    student_stats_permission_date=timezone.now() + timedelta(days=2),
)
app.classes.add(turma)

print(f"✅ Setup concluído! Login: coord.piloto@lize.local | Senha: 123456 | App ID: {app.id}")
```


---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Controle de Acesso e Sidebar [Automatizável ✅]

#### Cenário 1 — Visibilidade do novo menu com Feature Flag ativa
**Ação humana:**
- [x] Logar com o usuário de teste da Coordenação Piloto (`coord.piloto@lize.local`).
- [x] Expandir o menu **"Aplicações"** na barra lateral (sidebar esquerda).
- [x] Verificar se o item de menu exibido se chama `"**Instrumentos avaliativos**"` (em ambiente local com `DEBUG=True`, o atalho `"**Aplicação legada**"` também é exibido abaixo).
- [x] Clicar no item e verificar se a navegação direciona para a URL `/aplicacoes/instrumentos-avaliativos/`.

**Referência técnica (para automação):**
- URL de destino: `/aplicacoes/instrumentos-avaliativos/`
- Seletor da sidebar: `a.sidebar-menu-submenu-item[href="/aplicacoes/instrumentos-avaliativos/"]` (ou `a:has-text("Instrumentos avaliativos")`)
- Estado esperado:
  - `status_code === 200`
  - Item ativo na sidebar: classe `.sidebar-menu-submenu-item-active`
  - Cabeçalho e Título: `<title>` contém `"Instrumentos avaliativos"`, `<h1>` exibe `"Aplicações"` e breadcrumb contém `"Aplicações > Instrumentos avaliativos"`
- Requisitos de Fixture / Permissão:
  - `user.client_has_new_application_experience = True` (`client.has_new_application_experience = True` ou `user.has_new_application_experience = True`)
  - Permissão de acesso: `applications.view_application` (papel de Coordenação ou Professor)

#### Cenário 2 — Isolamento para clientes sem Feature Flag (Retrocompatibilidade)
**Ação humana:**
- [x] Logar com usuário de cliente com a flag desmarcada (`has_new_application_experience = False`).
- [x] Observar o menu **"Aplicações"** na sidebar.
- [x] Confirmar que o item direciona para a rota legada `/aplicacoes/` e que a nova interface não é exposta.

**Referência técnica (para automação):**
- URL: `/aplicacoes/`
- Seletor: `nav a[href="/aplicacoes/"]`
- Estado esperado: não existe link para `application_instruments`
- Fixture: `user.client.has_new_application_experience = False`


---

### 5.2 Nova Listagem: Filtros, Abas e Busca [Automatizável ✅]

#### Cenário 3 — Filtragem por categoria nas abas e persistência no localStorage
**Ação humana:**
- [x] Na tela `/aplicacoes/instrumentos-avaliativos/`, observar a barra de abas superiores (`"**Todas**"`, `"**Presencial**"`, `"**Online**"`, `"**Exercícios**"`, `"**Híbrida**"`).
- [x] Clicar na aba `"**Presencial**"`.
- [x] Verificar visualmente se a aba selecionada recebe a borda inferior laranja e se a listagem exibe apenas aplicações presenciais.
- [x] Recarregar a página (F5) e confirmar que a aba `"**Presencial**"` permaneceu selecionada automaticamente.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `button:has-text("Presencial")`
- Estado esperado: `button[aria-selected="true"]`, `localStorage.getItem('applicationInstrumentListCategory') === 'presential'`
- Fixture: `mixer.blend(Application, category=1)` e `mixer.blend(Application, category=2)`

#### Cenário 4 — Busca textual e filtros combinados
**Ação humana:**
- [x] Digitar parte do nome da avaliação no campo de busca com ícone de lupa (`placeholder="Buscar"`).
- [x] Aguardar brevemente (debounce de 300ms) e confirmar que a listagem filtra em tempo real sem recarregar a tela inteira.
- [x] Selecionar um ano específico no dropdown `"**Ano**"` e uma unidade no dropdown `"**Unidade**"`.
- [x] Confirmar que o filtro por URL/API é aplicado corretamente (validado com ano 2025, retornando os mesmos 4.096 registros da listagem legada).

> [!NOTE]
> *Observação de QA / UX:* A busca atual via API (`ApplicationInstrumentFilterSet`) exige correspondência literal contínua de caracteres (`exam__name__icontains`), falhando quando o usuário digita fragmentos de palavras separadas (ex.: `"simu mul"` retorna vazio mesmo existindo `"Simulado Multi-Áreas"`). Na busca global do cabeçalho (`/api/v1/search/`), os termos são divididos e combinados via `AND`, localizando com facilidade. Melhoria registrada na Seção 8.1.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `#instruments-search`, `select[name="year"]`, `select[name="units"]`
- Estado esperado: requisição disparada para `/aplicacoes/api/instrumentos/?search=...&year=...` com dados correspondentes
- Fixture: duas aplicações com nomes e anos distintos


---

### 5.3 Nova Listagem: Coluna Malote, Turmas e Token Online [Automatizável ✅]

#### Cenário 5 — Visualização compacta e expansão de turmas
**Ação humana:**
- [x] Localizar uma avaliação que possua mais de uma turma vinculada (ex.: `P6_LÍNGUA INGLESA_F3_MACMILLAN_2026`).
- [x] Observar abaixo do nome do caderno a linha secundária: verificar se exibe um selo cinza com a categoria e um resumo de turmas (ex.: `"**13 turmas**"`).
- [x] Clicar no botão expansor de turmas (ícone chevron `v` na primeira coluna da linha).
- [x] Confirmar que uma sub-linha acordeão (`sub-row`) é aberta logo abaixo com detalhe laranja lateral, exibindo os badges de todas as turmas vinculadas.
![alt text](../evidencias/image-35.png)

> [!NOTE]
> *Achado de Validação (Paridade de Turmas):* Na tela legada, a mesma avaliação exibia 3 tags e `+ 9` (totalizando 12). A investigação direta no banco de dados confirmou que **existem exatamente 13 turmas vinculadas**. A divergência foi causada por um bug histórico de *off-by-one* no componente Vue legado (`tooltip-component` em `vue-tooltip.html`, que usava `slice(showNumber, length - 1)` descartando o último item). A contagem da nova tela (`13 turmas`) é a correta.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `button.application-instrument-expand`
- Estado esperado: sub-linha `tr` visível contendo container `.tw-border-primary-600` com os badges `.tw-rounded-full` das turmas vinculadas
- Fixture: `application.classes.add(turma1, turma2)`

#### Cenário 5.1 — Exibição e contagem de alunos avulsos na ausência de turmas [BUG CRÍTICO ABERTO ❌]
**Ação humana:**
- [x] Localizar na listagem uma avaliação aplicada diretamente para estudantes individuais sem turmas vinculadas (ex.: `EXAME FINAL_Geografia_F9_ANGLO_2025`).
- [ ] Verificar se abaixo do nome do caderno é exibido o selo de participantes com o total de alunos avulsos (ex.: `"**4 aluno(s) avulso(s)**"`).
  - **Comportamento Atual (Falha):** A linha renderiza unicamente o badge da modalidade (`Presencial`), ocultando completamente a informação de alunos vinculados.
  - **Comportamento Esperado:** Paridade com a tela legada (`application.studentsCount aluno(s) avulso(s)`).
- [ ] Após a correção do desenvolvedor, retestar e homologar a exibição da tag de alunos avulsos.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Endpoint API: `/aplicacoes/api/instrumentos/`
- Problema identificado: O serializer `ApplicationInstrumentListSerializer` não retorna `students_count` e o template `application_instrument_list.html` só renderiza participantes se `school_classes.length > 0`.
- Detalhes e evidências comparativas: [**Seção 7 (Bugs Encontrados)**](#7-bugs-and-observations-problemas-encontrados-na-validação-prática)

#### Cenário 6 — Copiar token online diretamente na listagem
**Ação humana:**
- [x] Na aba `"**Online**"`, localizar uma aplicação online que tenha o token aleatório habilitado.
- [x] Observar abaixo da data a indicação do token (ex.: `"**Token QA77TEST**"` acompanhado de um ícone de cópia).
- [x] Clicar no ícone de cópia.
- [x] Verificar se há feedback visual de confirmação (alerta toast no topo `"Token copiado."`, ícone alternando para o check verde e `title="Token copiado"` por ~1.6s).
  - **Evidência validada:** Token `QA77TEST` exibido com ícone de cópia na aplicação online `Caderno pra rayssa colocar audio` (arquivo: `cenario6_token_online_sucesso.png`).

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `button.application-instrument-copy`
- Estado esperado: texto copiado para o clipboard, `copiedTokenId === application.id` disparando SVG de check com classe `.tw-text-primary-600` e toast `.alertTop('Token copiado.')`
- Fixture: `mixer.blend(Application, category=2, is_token_online=True)`

#### Cenário 6.1 — Coluna Situação sem duplicidade de status em aplicações Online [Validação de Fix Commit 30133d412]
**Ação humana:**
- [x] Na aba `"**Online**"` da listagem, inspecionar a coluna `"**Situação**"` de várias aplicações.
- [x] Confirmar que **NÃO** há duplicidade de indicadores na mesma célula (ex.: não deve haver o texto `"✓ Pronto para impressão"` colado abaixo do badge de status do caderno).
- [x] Verificar que cada linha exibe um indicador único e limpo:
  - Para cadernos em elaboração: badge azul `"Elaborando"`.
  - Para cadernos concluídos: badge verde `"Fechada"`.
- [x] Certificar-se de que a célula está alinhada, sem poluição visual ou concorrência de mensagens verdes.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/?category=online`
- Seletor: `tr.application-instruments-row td:nth-child(4)`
- Estado esperado: não existe elemento `<p>` com texto `"Pronto para impressão"` na coluna quando a aplicação for Online; exibe apenas o badge correspondente ou malote
- Fixture: aplicação Online vinculada a caderno com status `CLOSED` ou `ELABORATING` e `print_ready=True`


---

### 5.4 Nova Listagem: Menu Unitário de Opções (`Opções ⌵`) [Automatizável ✅]

#### Cenário 7 — Estrutura em 2 colunas do menu de opções
**Ação humana:**
- [x] Em qualquer linha da listagem, clicar no botão **"Opções ⌵"** no canto direito da linha.
- [x] Verificar se o menu dropdown abre alinhado à direita, organizado em até duas colunas:
  - Coluna 1: `"**GERAL**"` (com ações de Editar, Duplicar, Divulgar resultado, etc.).
  - Coluna 2: `"**IMPRESSÃO**"` (com ações de configurações de impressão, malote e folhas avulsas).
- [x] Clicar em `"**Editar**"` e certificar-se de que a página é redirecionada para `/aplicacoes/instrumento-avaliativo/<uuid>/editar/`.
![alt text](../evidencias/image-36.png)
**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `button.application-instrument-options-toggle[data-toggle="dropdown"]`, `.dropdown-menu.application-instrument-options`
- Estado esperado: `.application-instrument-options` visível com colunas Geral e Impressão (via CSS grid quando colunas secundárias existirem)
- Redirecionamento de Editar: URL corresponde a `/aplicacoes/instrumento-avaliativo/[a-f0-9-]+/editar/`
- Fixture: aplicação com caderno diagramado e malote permitido


---

### 5.5 Nova Listagem: Ações em Lote e Card Flutuante [Automatizável ✅]

#### Cenário 8 — Seleção múltipla e exibição do card flutuante
**Ação humana:**
- [x] Marcar o checkbox na primeira linha da tabela.
- [x] Verificar se o card flutuante de ações em lote surge no topo/base da listagem (`.application-instruments-bulk`).
- [x] Confirmar o texto de contagem: `"**1 selecionado**"`.
- [x] Marcar mais duas linhas e verificar se a contagem atualiza para `"**3 selecionados**"`.
- [x] Clicar no link `"**Limpar seleção**"` e confirmar que todos os checkboxes são desmarcados e o card flutuante desaparece.
![alt text](../evidencias/image-37.png)
**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `input[type="checkbox"]`, `.application-instruments-bulk`, `button:has-text("Limpar seleção")`
- Estado esperado: `.application-instruments-bulk` renderiza condicionalmente com base em `selectionList.length > 0`
- Fixture: ao menos 3 aplicações cadastradas

#### Cenário 9 — Operação em lote: Divulgar resultados [Comportamento Legado / Sugestão UX 💡]
**Ação humana:**
- [x] Selecionar duas aplicações cuja divulgação de resultado esteja agendada para o futuro (ex.: `P6_LITERATURA_M2_SAE_2026` e `[QA] Caderno Rayssa Rodrigues - 02`).
- [x] No card flutuante, clicar no botão `"**Divulgar resultados**"`.![alt text](../evidencias/image-38.png)
- [x] Confirmar o diálogo/modal de confirmação.![alt text](../evidencias/image-39.png)
- [x] Verificar se o status de divulgação é atualizado na listagem para `"Divulgado em: [Data atual]"`.
  - **Comportamento no Backend (Sucesso):** Ambas as aplicações foram antecipadas com sucesso no banco de dados para a data atual (`09/11/2026`). Ao recarregar a tela (F5), o texto `"Divulgado em: 09/11/2026"` é exibido perfeitamente.
  - **Comportamento em Tela (Paridade com Legado):** No front-end (sem recarregar), a linha é removida da tabela pelo callback (`.filter()`), reproduzindo exatamente o comportamento histórico da tela legada (`application_list_new.html:1817` via jQuery `.remove()`).
  - **Registro de Melhoria de UX:** Registrado como oportunidade de melhoria para a versão 2.0 na [Seção 8.1 (Sugestões de Melhorias de UX)](#81-sugestões-de-melhorias-visuais-e-de-ux-feedback-de-produto--design).

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `.application-instruments-bulk button:has-text("Divulgar resultados")`
- Estado esperado: requisição POST de divulgação disparada com sucesso
- Fixture: `Application` com `student_stats_permission_date > now()`


---

### 5.6 Criação Unificada: Etapa 1 (Caderno, Prazos & Opções Avançadas) [Automatizável ✅]

#### Cenário 10 — Preenchimento inicial e persistência do Caderno (Exam)
**Ação humana:**
- [x] Na listagem, clicar no botão laranja `"**+ Nova aplicação**"`.
- [x] Confirmar que a tela abre na Etapa 1 intitulada **`"Caderno"`** (com o passo marcado em laranja).
- [x] Tentar clicar nas etapas seguintes no stepper (Aplicação, Questões, etc.): confirmar que o cursor exibe ícone de bloqueio e tooltip informando: *"Crie o caderno para abrir esta etapa."*.
- [x] **Card 1 (Informações do caderno):** Preencher o campo `"**Título da prova**"` com `"Simulado Geral 2026"`, selecionar a Etapa de ensino e informar Nota geral (ex.: `10.0`).
- [x] **Card 2 (Prazos):** Clicar no acordeão `"**Prazos**"` para expandir o card:
  - Preencher a Data de elaboração (`De` e `Até`) com prazo futuro válido.
  - (Opcional) Informar prazos de Revisão e testar o toggle `"Alteração automática de status"`.
  - (Validação de conflito) Simular data de início de revisão anterior ao fim da elaboração e confirmar a exibição do alerta de sobreposição de etapas (`Prazos de etapas sobrepostos`).
- [x] **Card 3 (Opções avançadas):** Clicar no acordeão `"**Opções avançadas**"`: confirmar que o card expande exibindo as configurações (textos base, embaralhar questões/alternativas, IA para discursivas, sigilo, etc.). Testado preenchimento e expansão de campos dinâmicos (ex.: editor de Orientações da prova).
- [x] Clicar no botão `"**Continuar**"` no cabeçalho superior direito da tela (registrada sugestão de botão de rodapé na Seção 8.1).
- [x] Observar o estado de loading e confirmar que o caderno é criado com sucesso (`POST /aplicacoes/api/instrumentos/cadernos/`).
- [x] Confirmar que o sistema transiciona automaticamente para a **Etapa 2 (`"Aplicação"`)**, liberando o acesso no stepper.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/`
- Seletor: `#application-title`, `#application-total-grade`, `#exam-advanced-options-toggle`, `button:has-text("Continuar")`
- Estado esperado: `POST /aplicacoes/api/instrumentos/cadernos/` retorna 201 com `exam.id`, `currentStep` vira 2 (Etapa de Aplicação)
- Fixture: dados básicos de cliente e coordenação


---

### 5.7 Criação Unificada: Etapa 2 (Questões, Solicitações e Revisão) [Automatizável ✅]

#### Cenário 11 — Solicitar questão ao professor e listar na tabela
**Ação humana:**
- [ ] Na Etapa 2 (`"Questões"`), clicar no card `"**+ Solicitar ao professor**"`.
- [ ] Verificar se o modal em tela cheia é aberto com os campos de Série, Disciplina, Professor, Quantidade de questões e Configurações avançadas.
- [ ] Preencher a solicitação para um professor existente e clicar em Salvar.
- [ ] Confirmar que a solicitação aparece na listagem de professores da tela (`selectedTeachers`) com os botões de editar e remover.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/` (currentStep = 2)
- Seletor: `button:has-text("Solicitar ao professor")`, modal `#request-question-modal`, lista `.instrument-selected-teachers`
- Estado esperado: solicitação persistida vinculada ao `exam.id`
- Fixture: `Exam` previamente criado no passo anterior

#### Cenário 12 — Modal de Revisão de Questões no Instrumento
**Ação humana:**
- [ ] Na Etapa 2, clicar no botão de revisão de questões.
- [ ] Verificar se o modal de revisão abre renderizando o conteúdo completo de questões, com suporte a troca de status, ajuste de notas e reordenação.
- [ ] Fechar o modal e confirmar que o estado geral da tela é mantido sem recarregar.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/` (currentStep = 2)
- Seletor: `button:has-text("Revisar questões")`, `#modal-review`
- Estado esperado: modal renderizado com mixin `application_instrument_review.js` ativo
- Fixture: `Exam` com ao menos uma questão vinculada


---

### 5.8 Criação Unificada: Etapa 3 (Aplicação, Tempos, Divulgação e Participantes) [Automatizável ✅]

#### Cenário 13 — Configuração de parâmetros e persistência da Aplicação com Participantes
**Ação humana:**
- [ ] Clicar no botão `"**Continuar**"` da Etapa 2 para avançar para a Etapa 3 (`"**Aplicação**"`).
- [ ] Selecionar o formato `"**Presencial**"` (ou `"**Online**"`).
- [ ] Preencher Horário de Início (`08:00`), Término (`12:00`), tolerância de atraso e tempo mínimo.
- [ ] Configurar a data de divulgação dos resultados.
- [ ] Na seção **Participantes**, marcar ao menos uma turma na listagem de turmas.
- [ ] Clicar no botão `"**Continuar**"`.
- [ ] Confirmar que a aplicação é salva no banco (`POST /aplicacoes/api/instrumentos/aplicacoes/`) vinculando o caderno da Etapa 1 e os participantes selecionados.
- [ ] Confirmar que o sistema avança para a **Etapa 5: Conferência**.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/` (currentStep = 3)
- Seletor: `button:has-text("Presencial")`, `#application-start`, `#application-end`, `.instrument-participants input[type="checkbox"]`, `button:has-text("Continuar")`
- Estado esperado: `POST /aplicacoes/api/instrumentos/aplicacoes/` retorna 201 com `application.id`, `students` e `school_classes` vinculados; `currentStep` vira 5
- Fixture: `exam.id` presente no estado Vue, turmas e alunos cadastrados

#### Cenário 17 — Gestão de Participantes: Seleção em Lote, Alunos sob Demanda e Alunos Avulsos
**Ação humana:**
- [ ] Na Etapa 3, na seção **Participantes**, localizar uma turma e clicar no botão expansor de alunos.
- [ ] Confirmar que a lista de alunos daquela turma é carregada sob demanda (`v-if`) e exibida de forma recolhível.
- [ ] Desmarcar um aluno individual dentro da turma e verificar se o checkbox da turma assume estado indeterminado (parcial).
- [ ] Na seção **Alunos individuais**, utilizar o campo de busca de alunos (`search-students-component`) para adicionar um aluno avulso (não pertencente às turmas selecionadas).
- [ ] Confirmar que o aluno adicionado aparece na lista de participantes individuais.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/` (currentStep = 3)
- Seletor: `.instrument-participants-expand`, `.instrument-individual-students search-students-component`
- Estado esperado: `participantSelectedStudentIds` e `participantIndividualStudents` sincronizados no estado Vue

#### Cenário 18 — Validação de Seleção Vazia e Foco Automático no Erro
**Ação humana:**
- [ ] Na Etapa 3, desmarcar todas as turmas e remover qualquer aluno avulso (deixar participantes completamente vazio).
- [ ] Clicar no botão `"**Continuar**"` (ou `"**Salvar alterações**"`).
- [ ] Verificar se o sistema impede o envio e exibe mensagem de alerta informando a obrigatoriedade de ao menos um participante.
- [ ] Confirmar que a tela executa scroll automático e posiciona o foco diretamente sobre a seção com erro.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/` (currentStep = 3)
- Seletor: `button:has-text("Continuar")`, `[role="alert"]`
- Estado esperado: `POST` bloqueado no frontend com foco levado ao campo; caso enviado, API retorna 400 Bad Request


---

### 5.9 Etapa 5: Conferência e Geração de Malote vs Acompanhamento Online [Automatizável ✅]

#### Cenário 19 — Painel de Conferência: Cards de Malote por Categoria (Presencial vs Híbrida)
**Ação humana:**
- [ ] Na navegação superior de etapas, clicar na **Etapa 5: Conferência** (liberada após criar caderno e aplicação).
- [ ] Verificar os cards superiores de status:
  - Card **Aplicação**: exibe status `"Pendente"` ou `"Concluído"` (clicar nele deve redirecionar para a etapa correspondente).
  - Card **Questões**: exibe contagem de pendências/reprovações de questões com link direto para revisão.
- [ ] **Validação em Formato Presencial (`category = 3`):**
  - Confirmar a exibição da seção **Malote** com os 3 cards:
    - Card 1: `"**Malote completo**"` (com botão *"Gerar malote"*).
    - Card 2: `"**Apenas gabaritos**"` (com botão *"Gerar malote"*).
    - Card 3: `"**Aluno específico**"` (com botão *"Gerar malote"*).
- [ ] **Validação em Formato Híbrido (`category = 5`):**
  - Mudar para uma aplicação Híbrida ou editar o formato.
  - Confirmar que a seção de Malote exibe **exclusivamente** o card `"**Malote completo**"`, ocultando os cards de gabarito avulso e aluno específico (regra de híbrida onde não se imprime cartão de resposta isolado).

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/` (currentStep = 5)
- Seletor: `button:has-text("Aplicação")`, `button:has-text("Questões")`, `#instrument-conference-bundle-title`
- Estado esperado: `currentStep === 5`; quando `category === 3` renderiza 3 cards; quando `category === 5` renderiza apenas 1 card (Malote completo)

#### Cenário 19.1 — Painel de Conferência: Acompanhamento Online e Métricas de Anti-cola (Online e Lista de Exercícios)
**Ação humana:**
- [ ] Acessar a Etapa 5 (Conferência) de uma aplicação com formato **Online (`category = 2`)** ou **Lista de exercícios (`category = 4`)**.
- [ ] Confirmar que os cards de geração de malote físico **NÃO são exibidos**.
- [ ] Verificar a exibição do **Painel de Acompanhamento**:
  - Título `"**Acompanhamento**"`.
  - Botão secundário `"**Acompanhar aplicação**"` com link para a tela de fiscalização online (`/aplicacoes/<uuid>/acompanhamento/`).
- [ ] Confirmar a renderização dos cards com as métricas em tempo real (`/resumo-online/`):
  - `"**Alunos que iniciaram**"`
  - `"**Alunos que concluíram**"`
  - `"**Alunos não presentes**"`
  - `"**Duração média de prova**"`
- [ ] **Validação específica de Formato Online (`category = 2`):**
  - Confirmar que a tela exibe adicionalmente os 3 blocos de auditoria/anti-cola:
    - `"**Pausas solicitadas**"`
    - `"**Alunos com saídas da aplicação**"`
    - `"**Duração média das pausas**"`
- [ ] **Validação específica de Lista de Exercícios (`category = 4`):**
  - Confirmar que os blocos de pausas e saídas da aplicação são ocultados, mantendo apenas as métricas de início, conclusão e ausência.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/` (currentStep = 5)
- Endpoint consumido: `GET /aplicacoes/api/instrumentos/aplicacoes/<uuid>/resumo-online/`
- Seletor: `dt:has-text("Alunos que iniciaram")`, `button:has-text("Acompanhar aplicação")`
- Estado esperado: status 200 na API; cards de malote ausentes; quando `category === 2` exibe `dt:has-text("Pausas solicitadas")`; quando `category === 4` omite pausas e saídas

#### Cenário 20 — Abertura dos Diálogos de Impressão e Acompanhamento de Progresso (Fluxo Presencial)
**Ação humana:**
- [ ] Em aplicação Presencial ou Híbrida, no card `"**Malote completo**"`, clicar em `"**Gerar malote**"`.
- [ ] Verificar se o diálogo `.instrument-print-dialog` abre com cabeçalho e rodapé fixos, seleção de modelo de folha (radios clicáveis em laranja) e switches.
- [ ] Confirmar o disparo da geração e fechar o modal.
- [ ] Verificar se a barra de progresso da geração surge na tela (`div[role="progressbar"]`), exibindo o status `"Gerando malote"` e a porcentagem dinâmica `${ instrumentPrintStatus.progress }%`.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/` (currentStep = 5)
- Seletor: `.instrument-print-dialog`, `div[role="progressbar"]`
- Estado esperado: requisição disparada para geração de malote e polling de status em `/aplicacoes/api/aplicacao/<uuid>/status-malote/`


---

### 5.10 Edição Unificada: Hidratação, `v-changed` e Gestão de Participantes [Automatizável ✅]

#### Cenário 14 — Hidratação e detecção visual de alterações (`v-changed`)
**Ação humana:**
- [ ] Acessar diretamente a rota de edição de uma aplicação existente: `/aplicacoes/instrumento-avaliativo/<uuid>/`.
- [ ] Verificar se o cabeçalho exibe o botão `"**Salvar alterações**"` e se todos os campos (inclusive turmas e participantes) vêm preenchidos com os dados salvos.
- [ ] Alterar o título da prova no input `"**Título da prova**"`.
- [ ] Verificar se o campo recebe imediatamente um destaque visual (borda/ring) indicando alteração não salva (`v-changed`).
- [ ] Passar o mouse sobre o campo e confirmar o tooltip informativo orientando a salvar.
- [ ] Clicar no botão `"**Salvar alterações**"` no cabeçalho.
- [ ] Confirmar que uma requisição PUT é enviada e que o destaque visual de alteração desaparece após o sucesso.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/<uuid>/`
- Seletor: `#application-title`, `[v-changed]`, `button:has-text("Salvar alterações")`
- Estado esperado: `changedFields.has('exam.name') === true` antes do submit; `PUT` bem-sucedido e `changedFields.size === 0` após resposta
- Fixture: `Application` e `Exam` criados via mixer


---

### 5.11 Responsividade e Comportamento Visual [Apenas Manual 👁]

#### Cenário 15 — Validação de layout em 1333x1080 e telas menores
**Ação humana:**
- [ ] Ajustar a viewport do navegador para resolução intermediária (`1333x1080`).
- [ ] Na listagem de instrumentos:
  - [ ] Verificar se nenhum texto de caderno, turma ou botão sofre quebra inadequada ou sobreposição.
  - [ ] Confirmar que o dropdown de opções unitárias de 2 colunas não transborda para fora da tela.
- [x] Reduzir a largura para `768px` e `390px` (mobile - validado em 527x840):
  - [ ] Verificar a listagem `/aplicacoes/instrumentos-avaliativos/`: filtros colapsam em caixas ilegíveis de 2 caracteres (`Ar...`, `Un...`) e colunas `"Situação"` e `"Opções"` ficam cortadas e inacessíveis ([Bug registrado na Seção 7](#7-bugs-and-observations-problemas-encontrados-na-validação-prática)).
  - [ ] Verificar se a barra de etapas do cadastro (`application-instrument-steps`) permite scroll horizontal ou compactação legível.
  - [ ] Confirmar que os cards de opções avançadas e seletores de horário não quebram o grid horizontal.
  - [ ] Confirmar que os cards de malote e os modelos de folha no diálogo passam para formato responsivo/empilhado.


---

### 5.12 Itens Pendentes (Não Testar / Fora de Escopo no Momento) [Apenas Manual 👁]

> [!NOTE]
> Os itens a seguir continuam conscientemente fora do escopo desta branch e foram mantidos para tasks futuras:

#### Cenário 16 — Conferência de itens declaradamente pendentes
**Ação humana:**
- [ ] **Ação "Utilizar caderno existente":** Notar ausência do seletor de cadernos prontos no cabeçalho da criação.
- [ ] **Etapa 4 (Diagramação):** O painel permanece vazio e bloqueado. Não considerar como falha.
- [ ] **Modos Quadro/Compacto na Listagem:** Os botões continuam desabilitados/comentados no template.


---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **Comparação de Cores e Padrão Design System:**
  - Botão `"**+ Nova aplicação**"` no padrão `orange-600` (`#EA580C`), hover `orange-700`.
  - Botões secundários (`Importar alunos`, `Importar aplicações`) com estilo neutro/cinza compartilhado.
- [ ] **Truncate em Textos Dinâmicos:**
  - Garantir que nomes longos de cadernos ou turmas extensas apliquem reticências (`truncate`), sem quebrar a altura das linhas da tabela (altura fixa de `94px`).
- [ ] **Alinhamento do Dropdown de Opções:**
  - O dropdown de opções unitárias deve se posicionar corretamente via Popper, respeitando o limite direito da tela.


---

## 7. Bugs and Observations (Problemas Encontrados na Validação Prática)

> [!WARNING] [UX/UI / Label] Discrepância entre rótulo da sidebar e especificação do produto
> **Evidência/Reprodução:** Ao logar com perfil de Coordenação em cliente com a feature flag ativa, a barra lateral esquerda (`coordination.html`) renderiza o item como `"Instrumentos avaliativos"`.
> **Causa Raiz:** No card ClickUp CU-86ak8r20g, o alinhamento de produto registrou expressamente: *"Chama só de 'Avaliações'"*.
> **Comportamento Esperado:** O rótulo da sidebar deve refletir a nomenclatura de produto acordada: `"Avaliações"`.

> [!TIP] [Bug UI/Regra de Negócio] Duplicidade de status e concorrência indevida na coluna "Situação" [RESOLVIDO E HOMOLOGADO ✅]
> **Evidência/Reprodução:** Ao comparar a listagem legada (`/aplicacoes/?category=online`) com a nova listagem (`/aplicacoes/instrumentos-avaliativos/`), a coluna "Situação" de aplicações de categoria Online estava renderizando simultaneamente o badge de status do caderno (ex.: verde `"Fechada"`) e logo abaixo o texto verde `"✓ Pronto para impressão"`. Em provas futuras (ex.: maio/2026), o termo "Fechada" gerava ambiguidade grave de que a aplicação inteira estava encerrada, além de poluição visual na mesma célula.
> **Causa Raiz:** No template `application_instrument_list.html`, havia um bloco `<p v-if="application.print_ready">` concorrendo diretamente abaixo do `${ application.exam_status }`.
> **Resolução Aplicada:** O desenvolvedor removeu o bloco redundante no commit `30133d412`, garantindo que a coluna exiba um indicador único e limpo.
> **Status de Homologação:** Homologado com sucesso via Cenário 6.1. A célula agora renderiza de forma limpa apenas o badge correto da situação.
> **Evidência de Resolução:**  
> ![Evidência de Resolução - Coluna Situação Limpa](../evidencias/image-33.png)

> [!WARNING] [Bug Crítico / Regressão Funcional] Omissão da exibição e contagem de alunos avulsos na listagem [BUG ABERTO ❌]
> **Cenário de Homologação:** [Cenário 5.1](#cenário-51--exibição-e-contagem-de-alunos-avulsos-na-ausência-de-turmas-bug-crítico-aberto-)
> **Evidência/Reprodução:** Ao listar aplicações realizadas diretamente para alunos específicos (sem turma vinculada, como provas finais/recuperação ex.: `EXAME FINAL_Geografia_F9_ANGLO_2025`), a nova tela renderiza apenas o badge de modalidade (`Presencial`), ocultando completamente a informação de que existem alunos participantes vinculados.  
> Na listagem legada (`/aplicacoes/`), a interface exibia com clareza a etiqueta informativa (ex.: `4 aluno(s) avulso(s)`, `14 aluno(s) avulso(s)`).
> 
> **Causa Raiz Técnica:**
> - No serializer `ApplicationInstrumentListSerializer` (`fiscallizeon/applications/serializers/application_instrument.py`), o campo de contagem de alunos avulsos (`students_count`) não foi implementado nem retornado no payload JSON.
> - No template `application_instrument_list.html` (linhas 306-315), a exibição de participantes abaixo do título do caderno condiciona-se unicamente a `application.school_classes.length`. Quando não há turmas (`school_classes: []`), nenhum indicador de estudantes é renderizado.
>
> **Comportamento Esperado:** Quando `school_classes` estiver vazio mas houver estudantes vinculados à aplicação (`app.students.exists()`), o serializer deve fornecer a contagem e o front deve renderizar a badge correspondente `${ application.students_count } aluno(s) avulso(s)`, mantendo a paridade com a tela legada.
>
> **Evidências Comparativas:**  
> 1. *Nova tela omitindo os estudantes avulsos:*  
>    ![Omissão de alunos avulsos na nova listagem](../evidencias/omissao_alunos_avulsos_nova_listagem.png)  
> 2. *Tela legada exibindo a tag de alunos avulsos:*  
>    ![Exibição de alunos avulsos na tela legada](../evidencias/exibicao_alunos_avulsos_tela_legada.png)

> [!TIP] [Paridade de Dados / Bug Legado Identificado] Divergência na contagem de turmas vinculadas (12 no legado vs 13 na nova tela)
> **Evidência/Reprodução:** Ao comparar a mesma avaliação com múltiplas turmas (`P6_LÍNGUA INGLESA_F3_MACMILLAN_2026`) entre as duas listagens:
> - **Na listagem legada:** A interface exibia 3 tags de turmas e um badge `+ 9`, totalizando **12 turmas**.
> - **Na nova listagem:** A interface exibe o resumo **`13 turmas`**.
>
> **Causa Raiz Técnica Identificada:**
> - Uma consulta direta ao banco de dados (`Application.objects.get(...).school_classes.count()`) confirmou que **existem exatamente 13 turmas reais** vinculadas a essa aplicação.
> - A tela legada utilizava o componente Vue `tooltip-component` (`fiscallizeon/core/templates/includes/vue-tooltip.html`), que continha um erro clássico de cálculo de array (*off-by-one*):
>   ```javascript
>   configs.objects.slice(configs.showNumber, configs.objects.length - 1)
>   ```
>   Como o método `.slice(start, end)` do JS não inclui o índice final (`end`), subtrair `- 1` do tamanho total (`13 - 1 = 12`) fez com que a última turma (índice 12) fosse descartada silenciosamente na tela legada (`slice(3, 12)` retornando 9 itens em vez de 10).
> - **Status no Novo Fluxo:** A nova tela (`application_instrument_list.html`) calcula diretamente `${ application.school_classes.length + ' turmas' }`, exibindo a quantidade **13** com 100% de precisão e corrigindo o bug visual do sistema legado.
>
> **Evidências Comparativas:**  
> 1. *Tela legada exibindo 3 tags + 9 turmas (total 12):*  
>    ![Contagem no Legado](../evidencias/contagem_turmas_tela_legada_12.png)  
> 2. *Nova listagem exibindo 13 turmas (correto):*  
>    ![Contagem na Nova Tela](../evidencias/contagem_turmas_tela_nova_13.png)

> [!NOTE] [Regra de Negócio / Validação de Lote] Divulgação de resultados em lote restrita a datas futuras
> **Evidência/Reprodução:** Ao selecionar na tabela avaliações que já possuem `results_release_date` anterior ao momento atual, o botão de "Divulgar resultados" exibe confirmação informando que nenhuma aplicação selecionada é elegível.
> **Comportamento Esperado:** Este é o comportamento correto previsto pela regra de negócio (apenas aplicações agendadas para o futuro podem ter a divulgação antecipada em lote). Registrado para fins de documentação de QA.

> [!WARNING] [Bug / Responsividade e Layout] Quebra severa de layout na listagem em dispositivos móveis e viewports reduzidas (<= 768px) [BUG ABERTO ❌]
> **Cenário de Homologação:** [Cenário 15 (Validação Mobile)](#cenário-15--validação-de-layout-em-1333x1080-e-telas-menores)  
> **Evidência/Reprodução:** Ao acessar `/aplicacoes/instrumentos-avaliativos/` em viewport mobile/reduzida (ex.: `527x840` no DevTools):
> 1. **Barra de Filtros:** Os seletores de filtro (`Ano`, `Unidade`, `Turmas`, `Etapa de ensino`, `Situação do malote`) colapsam em caixas minúsculas ilegíveis de 2 caracteres (`Ar...`, `Un...`, `Tu...`, `Et...`, `Si...`), sem quebra de linha fluida (`flex-wrap`) ou adaptação de grade.
> 2. **Tabela de Instrumentos:** A tabela não possui container com rolagem horizontal explícita (`overflow-x-auto`) ou formato adaptado de cards. As colunas críticas `"Situação"` e o menu `"Opções"` ficam completamente cortadas para fora da tela, impossibilitando a visualização do status e o acesso às ações de edição e malote pelo celular.
> 3. **Cabeçalho de Ações e Abas:** Os botões de importação e criação empilham desordenadamente e as abas superiores de modalidade cortam lateralmente.
>
> **Comportamento Esperado:** Em telas menores (<= 768px):
> - A barra de filtros deve empilhar em largura total (`w-full`) ou colapsar em um botão/offcanvas de filtros;
> - A tabela deve permitir rolagem horizontal suave com indicador de scroll ou converter as linhas em cards verticais no mobile;
> - Os botões de ação do cabeçalho devem se estender para preencher a largura total (`w-full sm:w-auto`).
>
> **Evidência Visual:**  
> ![Quebra de responsividade na listagem mobile](../evidencias/responsividade_mobile_quebra_listagem.jpg)


---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

### 8.1 Sugestões de Melhorias Visuais e de UX (Feedback de Produto & Design)

> [!TIP] [Melhoria de UX / Carregamento] Skeleton Screen e Prevenção de Layout Shift (CLS) na Listagem de Instrumentos
> **Cenário Observado:** Ao acessar ou recarregar a tela (`/aplicacoes/instrumentos-avaliativos/`), os elementos visuais são renderizados em estágios dessincronizados ("carregamento picado"):
> 1. O cabeçalho (breadcrumb e botões de ação) e a barra de filtros surgem imediatamente via Django SSR;
> 2. As abas superiores de modalidades de prova (*Todas*, *Presencial*, *Online*, etc.) e a tabela de dados demoram alguns instantes para montar via Vue.js, deixando um espaço em branco transitório;
> 3. Quando os dados chegam, os elementos "saltam" na tela (Cumulative Layout Shift - CLS), dando sensação de instabilidade ou lentidão visual.
>
> **Evidência Visual:**  
> ![Layout Shift no carregamento inicial da listagem](../evidencias/melhoria_skeleton_layout_shift_listagem.png)
>
> **Sugestão de Implementação / Melhoria:**
> - Adicionar um componente de **Skeleton Screen / Shimmer** (espaço reservado animado em cinza claro) simulando as abas e as linhas da tabela enquanto o Vue monta e a API responde;
> - Ou renderizar o esqueleto das abas estaticamente no template HTML, ativando a interatividade com `v-cloak` e transição suave de opacidade (`fade-in`), garantindo que o usuário veja a estrutura completa da página desde o primeiro milissegundo de carregamento.

> [!TIP] [Melhoria de UX / Busca Flexível] Busca Multi-termo com Quebra de Palavras (Consistência com a Busca Global)
> **Cenário Observado / Divergência de Usabilidade:**  
> Ao digitar múltiplos termos ou fragmentos de palavras separados por espaço no campo de busca da listagem (ex.: `"simu mul"`), o sistema exibe *"Nenhuma aplicação encontrada"*, mesmo existindo na listagem a aplicação com o nome correspondente (*"Simulado Multi-Áreas (Natureza, Humanas e Matemática) - QA"*).  
> Em contrapartida, a **Busca Global do cabeçalho da plataforma** localiza perfeitamente tanto o caderno quanto a aplicação ao receber exatamente os mesmos termos (`"simu mul"`), gerando uma inconsistência de experiência para o usuário.
>
> **Causa Raiz Técnica Identificada:**
> - No filtro da nova listagem (`ApplicationInstrumentFilterSet.filter_search` em `fiscallizeon/applications/filters.py`), a busca executa uma correspondência literal estrita: `exam__name__icontains=term`. Como `"Simulado Multi-Áreas"` contém `"lado "` entre `"Simu"` e `"mul"`, a string contínua falha.
> - Já a Busca Global (`SearchView` em `fiscallizeon/core/apis.py`) normaliza e quebra a entrada em termos individuais (`normalize_query`), combinando-os dinamicamente com operador `&` (AND): `Q(exam__name__icontains='simu') & Q(exam__name__icontains='mul')`.
>
> **Evidências Visuais Comparativas:**
> 1. *Busca Global reconhecendo os fragmentos e trazendo resultados:*  
>    ![Busca Global com múltiplos termos](../evidencias/busca_global_multi_termo.png)
> 2. *Busca na Listagem de Instrumentos falhando com o mesmo termo:*  
>    ![Busca local falhando](../evidencias/busca_instrumentos_sem_resultado_multi_termo.png)
> 3. *Aplicação presente na listagem ativa (Presencial):*  
>    ![Aplicação presente na listagem](../evidencias/listagem_instrumentos_presencial_com_simulado.jpg)
>
> **Sugestão de Implementação / Melhoria:**
> - Refatorar o método `filter_search` em `ApplicationInstrumentFilterSet` para dividir o termo digitado em palavras (`term.split()`) e aplicar múltiplos filtros `exam__name__icontains` encadeados, ou reutilizar o utilitário `normalize_query` já consolidado na plataforma. Dessa forma, a busca torna-se tolerante a fragmentos, mais amigável e 100% consistente com o comportamento global do Lize Edu.

> [!TIP] [Melhoria de UX / Paginação] Exibição do Totalizador de Resultados na Paginação da Listagem
> **Cenário Observado:** No rodapé da nova listagem de instrumentos avaliativos (`/aplicacoes/instrumentos-avaliativos/`), a paginação apresenta apenas os controles de navegação (`Anterior`, botões numéricos com reticências `1 ... 205`, `Próximo`).  
> O total de resultados encontrados (ex.: *"Mostrando de 1 até 20 de 4.096 resultados"*), que existia na tela legada, foi omitido na nova interface, dificultando a percepção da coordenação sobre o volume total de provas filtradas.
>
> **Causa Raiz Técnica:**
> - O backend (`SimpleAPIPagination` em `fiscallizeon/core/utils.py`) já retorna o atributo `count` com o total de registros (ex.: `4096`).
> - O frontend (`application_instrument_list.js`) consome `data.count` estritamente para computar a quantidade de páginas (`this.total`), mas o template `application_instrument_list.html` não renderiza um elemento textual com esse totalizador.
>
> **Sugestão de Implementação / Melhoria:**  
> Incluir no rodapé (à esquerda ou centralizado junto à paginação) uma legenda formatada no padrão do Design System:  
> `Mostrando de ${ (page - 1) * pageSize + 1 } até ${ Math.min(page * pageSize, totalCount) } de ${ totalCount } resultados`.
![alt text](../evidencias/image-34.png)

> [!TIP] [Melhoria de UX / Paridade com Legado] Manter linhas na listagem com status atualizado após divulgação em lote
> **Cenário Observado:** [Cenário 9 (Operação em lote: Divulgar resultados)](#cenário-9--operação-em-lote-divulgar-resultados-comportamento-legado--sugestão-ux-)  
> **Comportamento em Tela:** Ao divulgar resultados em lote via card flutuante, a requisição é processada com sucesso no backend e a data atualizada para o momento atual. Porém, na interface SPA, as linhas das aplicações divulgadas desaparecem imediatamente da listagem, reaparecendo apenas após recarregamento manual (F5).
> **Origem / Paridade Histórica:** A análise do código legado confirmou que esse comportamento é uma reprodução fiel da tela legada (`application_list_new.html`, linha 1817), onde o callback de sucesso chamava `$(`#tr-${item.id}`).remove()`. Na nova tela, o desenvolvedor converteu essa instrução diretamente para `this.applications = this.applications.filter((app) => app.id !== item.id)`.
> **Sugestão de Implementação para a Versão 2.0:** Em vez de remover a linha da tabela (o que causa no usuário a impressão errônea de exclusão do caderno), sugere-se:
> 1. Atualizar a propriedade reativa local da aplicação (`item.student_stats_permission_date = moment().toISOString()`), fazendo com que o texto da coluna de datas passe imediatamente para `"Divulgado em: [Data atual]"`; OU
> 2. Disparar `this.loadApplications(this.buildListUrl(this.page))` no fechamento da ação em lote para recarregar a listagem preservando a visibilidade dos cadernos na página.
>
> **Evidência Visual:**  
> ![Cadernos sumiram após divulgação em lote](../evidencias/cenario9_cadernos_sumiram_bug.jpg)

> [!TIP] [Melhoria de UX / Usabilidade e Ergonomia] Botão de ação "Continuar" duplicado ou fixo no rodapé da página
> **Cenário Observado:** [Cenário 10 (Preenchimento do Caderno, Prazos & Opções Avançadas)](#cenário-10--preenchimento-inicial-e-persistência-do-caderno-exam)  
> **Problema de Usabilidade (Scroll Reverso Obrigatório):**  
> Na tela de criação/edição de instrumentos avaliativos (`/aplicacoes/instrumento-avaliativo/`), os formulários são extensos e compostos por múltiplos cards empilhados (Informações básicas, Prazos detalhados e Opções avançadas com 16 campos).  
> O único botão disponível para avançar (`"Continuar"`) está localizado exclusivamente no cabeçalho superior direito da página. Após preencher todos os campos e descer até o final da tela, o usuário é obrigado a rolar a página inteira de volta para o topo apenas para conseguir clicar em `"Continuar"`, gerando atrito desnecessário e esforço repetitivo de navegação.
>
> **Sugestão de Implementação / Melhoria:**  
> 1. **Botão Duplicado no Rodapé:** Incluir um botão secundário/primário de `"Continuar"` alinhado à direita no rodapé, logo abaixo do último card da seção ativa; OU
> 2. **Barra Fixa (Sticky Footer/Header):** Tornar a barra de ações com o botão `"Continuar"` fixa no rodapé (`tw-sticky tw-bottom-0`) ou preservar o cabeçalho fixo no topo durante o scroll longo, permitindo avançar de qualquer ponto da tela sem rolagem reversa.
>
> **Evidências Visuais Comparativas:**  
> 1. *Botão "Continuar" isolado no cabeçalho superior:*  
>    ![Botão Continuar no cabeçalho](../evidencias/melhoria_botao_continuar_topo.png)  
> 2. *Fim do formulário sem botão de ação para avançar:*  
>    ![Rodapé sem botão de avançar](../evidencias/melhoria_botao_continuar_rodape_ausente.png)

> [!TIP] [Melhoria de UX / Consistência no Fluxo Unificado] Pré-seleção ou Destaque das Unidades das Coordenações do Caderno na Etapa 2 (Participantes)
> **Cenário Observado:** [Cenário 13 (Criação da Aplicação — Etapa 2: Aplicação & Participantes)](#cenário-13--configuração-de-horários-tolerância-e-participantes)  
> **Comportamento em Tela:**  
> Na Etapa 1 (*"Caderno"*), o usuário define as *Coordenações autorizadas* vinculadas à prova (ex.: marcando apenas a unidade `GRU - Rede Decisão`).  
> Ao avançar para a Etapa 2 (*"Aplicação"*), no card de *Participantes*, o campo *"Selecione uma unidade"* carrega e exibe todas as unidades da rede às quais o usuário logado possui acesso (`GRU`, `OSB`, `UNI`, `MAS`, `DAF`, etc.), sem nenhuma indicação ou pré-seleção alinhada à escolha feita no passo anterior.
>
> **Análise Técnica e de Domínio:**  
> - **Regra de Negócio Válida:** O comportamento atual é funcionalmente correto e intencional para permitir que um caderno elaborado por uma coordenação específica (ex.: polo pedagógico GRU) possa ser aplicado a alunos de toda a rede de escolas (`Application` multi-unidades).  
> - **Atrito de Usabilidade:** No entanto, no modelo mental do usuário dentro de um assistente unificado (Stepper), a ausência de conexão entre as duas etapas gera a percepção de desconexão de dados e obriga o usuário a rolar e buscar manualmente a mesma unidade que acabou de selecionar na etapa anterior.
>
> **Sugestão de Implementação para a Versão 2.0:**  
> 1. **Pré-seleção Inteligente:** Ao carregar a Etapa 2 pela primeira vez em uma nova criação, preencher o valor inicial de `participantFilters.unities` automaticamente com as unidades correspondentes às coordenações selecionadas no Caderno (mantendo o dropdown aberto para que o usuário possa marcar ou desmarcar livremente outras unidades da rede se desejar); OU  
> 2. **Agrupamento/Destaque Visual:** Posicionar no topo do selectpicker (ou com uma badge/seção de destaque *"Unidades da elaboração"*) as unidades que foram vinculadas na Etapa 1, facilitando a seleção rápida sem rolagem extensa em clientes de grande porte.
>
> **Evidências Visuais (Registro Jam [8f2e009d](https://jam.dev/c/8f2e009d-2f08-4bf9-af38-649daa786459)):**  
> 1. *Coordenação restrita selecionada na Etapa 1 (ex.: apenas GRU):*  
>    ![Coordenações autorizadas Etapa 1](../evidencias/melhoria_etapa1_coordenacoes_gru.png)  
> 2. *Todas as unidades da rede disponíveis sem pré-filtro na Etapa 2:*  
>    ![Todas as unidades da rede listadas na Etapa 2](../evidencias/melhoria_etapa2_unidades_todas_disponiveis.png)


---

### 8.2 Débitos Técnicos e Funcionalidades Posteriores

> [!NOTE]
> **[WONTFIX / Futuro — Task 17tu7rp42zh] Utilizar Caderno Existente**  
> A importação rápida de um caderno pronto a partir de "Meus cadernos" no cabeçalho será tratada na próxima entrega.

> [!NOTE]
> **[WONTFIX / Futuro — Task 17tu7rp42zh] Etapa de Diagramação (Etapa 4)**  
> A ferramenta de diagramação integrada à criação continuará desabilitada até a consolidação dos fluxos de elaboração e conferência.

> [!NOTE]
> **[WONTFIX / Futuro — Task 17tu7rp42zh] Modos Quadro (Kanban) e Compacto na Listagem**  
> Visualizações alternativas da listagem foram adiadas para priorizar o modo Tabela com ações em lote.


---

## 8.3. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django), e não a View.
- 🔗 **[Mapeamento: application_instrument_list.html](docs/tests/usability/application_instrument_list.md)**
- 🔗 **[Mapeamento: complete_application_instrument.html](docs/tests/usability/complete_application_instrument.md)**


---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo:** Amplo volume de regras distribuídas entre criação de caderno, criação de aplicação e listagem em lote no mesmo PR.
- **Relação entre especificação e código:** A separação clara entre o escopo da task de origem `86ak8r20g` e a task de finalização `17tu7rp42zh` no OpenSpec evitou que itens pendentes por design (ex.: participantes e diagramação) fossem classificados erroneamente como bugs.
- **Pontos de atenção para CI:** Garantir a cobertura dos novos testes de view e API nos fluxos de `predeploy.sh`.


---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias:
1. Incluir suporte nativo para rastreamento de tasks divididas entre múltiplos PRs ou tasks filhas de finalização (como a relação 86ak8r20g -> 17tu7rp42zh).
2. Adicionar verificação automática de comentários do ClickUp para identificação precoce de não-objetivos pactuados pela equipe.
-->

