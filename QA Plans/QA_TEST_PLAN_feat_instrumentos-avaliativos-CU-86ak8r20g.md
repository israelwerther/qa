## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-11-03 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Applications / Exams / Instrumentos Avaliativos |
| **Nível de Risco:** | Alto |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ |

---

## 1. Summary of Changes (Resumo das Alterações)

Branch `feat/instrumentos-avaliativos-CU-86ak8r20g` referente à task ClickUp `CU-86ak8r20g` (**"Versão 2.0 da criação de avaliações"**), com continuidade e finalização acompanhada na task `17tu7rp42zh` (ciclo 9.2026). A mudança propõe unificar a criação e acompanhamento de cadernos e aplicações a partir de um fluxo centralizado ("Instrumentos Avaliativos").

### Backend (`fiscallizeon/applications/`, `accounts/`, `clients/`)
- **Controle de Feature Flag (`has_new_application_experience`)**: Adicionados campos em `Client` e `User` (sobrescrita individual), migrações `clients.0217_has_new_application_experience` e `accounts.0049_has_new_application_experience`. Admin e forms atualizados.
- **API de Caderno no Instrumento (`ApplicationInstrumentExamViewSet`)**: Exposta em `/aplicacoes/api/instrumentos/cadernos/` (POST) e `/cadernos/<uuid>/` (GET/PUT). Criação atômica no primary com lock de cliente, validação de unicidade de nome por ano, restrição de coordenações acessíveis e prefetch dos vínculos.
- **API de Aplicação no Instrumento (`ApplicationInstrumentApplicationViewSet`)**: Exposta em `/aplicacoes/api/instrumentos/aplicacoes/` (POST) e `/aplicacoes/<uuid>/` (GET/PUT). Persiste os campos configuráveis da aplicação (formato, horários, tolerâncias, divulgação, dispositivos) vinculando ao caderno criado, sem exigir seleção imediata de participantes.
- **API de Listagem de Instrumentos (`ApplicationInstrumentViewSet`)**: Exposta em `/aplicacoes/api/instrumentos/` e `/aplicacoes/api/instrumentos/<uuid>/`. Suporta busca, categoria, paginação simples (`SimpleAPIPagination`), filtros por ano, unidade, turmas, etapas e situação do malote.
- **Filtros (`ApplicationInstrumentFilterSet`)**: Implementados filtros em `fiscallizeon/applications/filters.py` com predicados para malote (gerando, pronto, download, erro).
- **Serializers**: `ApplicationInstrumentExamSerializer` (validação rica de opções avançadas de caderno) e `ApplicationInstrumentApplicationSerializer` (validações compartilhadas de aplicação).

### Frontend & UI (`fiscallizeon/applications/templates/`, `components/`)
- **Sidebar Dinâmica**: Itens de Coordenação e Professor adaptados para exibir `"**Avaliações**"` sob o menu Aplicações apontando para a nova rota quando a flag estiver ativa.
- **Nova Listagem (`application_instrument_list.html`)**:
  - Estende `redesign/base_component.html`.
  - Cabeçalho com botão primário `"**Nova aplicação**"` (`#EA580C`) e botões secundários `"**Importar alunos**"` e `"**Importar aplicações**"`.
  - Abas de categoria: Todas, Presencial, Online, Exercícios, Híbrida (persistência no `localStorage`).
  - Filtros estilizados via componente `application_instrument_list_filter` (truncamento de labels em 48 caracteres).
  - Tabela com linhas informativas: resumo e expansão de turmas abaixo do caderno, selo de categoria, coluna de malote com badges reais e divulgação de resultados abaixo da data.
  - Dropdown unitário de Ações (`application_instrument_list_options`) em 2 colunas (Geral e Impressão).
  - Card flutuante de ações em lote (`.application-instruments-bulk`) com seleção via componente global `checkbox`, contagem dinâmica e ações em massa.
- **Nova Tela Unificada de Cadastro e Edição (`complete_application_instrument.html`)**:
  - Navegação em etapas (Configurações, Questões, Aplicação, Diagramação, Conferência).
  - Bloqueio inteligente de etapas posteriores até a persistência do caderno (`exam.id`).
  - Etapa 1: dados do caderno, etapa de ensino, nota geral, coordenações autorizadas, card retrátil de Opções Avançadas e prazos com modal de exceção.
  - Etapa 2: solicitações ao professor com modal completo, geração com IA e cadernos anteriores; integração do modal completo de revisão de questões via mixin `application_instrument_review.js`.
  - Etapa 3: configurações da aplicação (formato, token online, horários, tolerâncias e divulgação).
  - Edição com hidratação via GET, comparação profunda de estado e destaque de campos alterados (`v-changed`) com tooltip explicativo.

---

## 2. Scope Boundaries (Diferenças de Escopo)

### O QUE FOI IMPLEMENTADO (IN SCOPE — Deve ser testado agora)
- **Ativação da Feature Flag**: Alternância no Admin e exibição condicional do menu "Avaliações" na sidebar.
- **Nova Listagem de Instrumentos Avaliativos**: Carregamento assíncrono via API, paginação, busca com debounce e filtros de ano, unidade, turmas, etapas e malote.
- **Persistência da Aba de Categoria**: Seleção da aba (Presencial, Online, Exercícios, Híbrida) salva no `localStorage`.
- **Coluna Malote e Detalhes da Linha**: Badges de status do malote, turmas expansíveis e token online com botão de copiar.
- **Menu Unitário de Opções (Dropdown em 2 colunas)**: Ações de Editar (redireciona para o editor), Duplicar, Divulgar resultado e ações de impressão.
- **Card de Ações em Lote**: Seleção unitária/geral com componente `checkbox`, contagem dinâmica, "Marcar para impressão", "Divulgar resultados", "Gerar malotes" e submenu "Mais opções".
- **Criação de Novo Instrumento (Etapa 1 — Caderno)**: Criação do `Exam` ao clicar em Continuar, validação de nome e persistência das opções avançadas.
- **Criação de Novo Instrumento (Etapa 2 — Questões & Revisão)**: Solicitação a professores (modal), geração com IA, importação de questões anteriores e **Modal de Revisão de Questões**.
- **Criação de Novo Instrumento (Etapa 3 — Aplicação)**: Criação da `Application` vinculada ao caderno existente e persistência dos parâmetros de aplicação.
- **Edição de Instrumento Existente**: Carregamento de dados pré-existentes, detecção de alterações com borda/ring (`v-changed`), botão "Salvar alterações" e "Continuar".

### O QUE AINDA NÃO FOI IMPLEMENTADO (OUT OF SCOPE — NÃO validar no momento)
Conforme documentado na OpenSpec (`tasks.md`), nos comentários do ClickUp e repassado para a task de finalização `17tu7rp42zh`:
- **Definição de Participantes da Aplicação (Turmas/Alunos)**: A seção 2 da etapa 3 ("Aplicação") está propositalmente vazia no momento (item 6.13 do OpenSpec). A aplicação é criada e editada sem a seleção de participantes. Na edição de aplicação existente que já possui turmas, as turmas são preservadas no banco, mas não há formulário de seleção na tela.
- **Ação "Utilizar caderno existente" no Cabeçalho**: O seletor de cadernos prontos a partir de "Meus cadernos" no topo da nova criação ainda não foi implementado (item 6.7 do OpenSpec).
- **Etapas de Diagramação (Etapa 4) e Conferência (Etapa 5)**: Essas etapas continuam com painéis vazios/bloqueados no fluxo atual (item 6.8 do OpenSpec).
- **Modos de Exibição "Quadro" (Kanban) e "Compacto"**: Os botões de alternância de modo na listagem permanecem comentados no template (item 4.3). Apenas a visualização em tabela está ativa.
- **Distribuição de Colaboradores Responsáveis por Etapa**: Alinhado no ClickUp como funcionalidade inexistente no backend atual ("Lógica de colaboradores responsáveis não existe hoje — nova implementação complexa"); não foi implementada.
- **Retomada de Caderno sem Aplicação na Listagem**: A listagem consulta a tabela `Application`. Se um caderno foi criado e o usuário fechou o navegador antes de avançar na etapa Aplicação, o caderno não é listado na tela de instrumentos (item 6.2 do OpenSpec).
- **Pesquisa In-App e Medição de CSAT**: A coleta de notas/satisfação pós-criação mencionada na descrição da task do ClickUp não faz parte do código entregue nesta branch.
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
- [x] Verificar se o item de menu exibido se chama `"**Avaliações**"` (ou `"**Instrumentos avaliativos**"`). *(Validado: exibe "Instrumentos avaliativos", ver Obs na Seção 7)*
- [x] Clicar no item e verificar se a navegação direciona para a URL `/aplicacoes/instrumentos-avaliativos/`.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `nav a[href*="/aplicacoes/instrumentos-avaliativos/"]`
- Estado esperado: `status_code === 200`, título contém "Aplicações" ou "Instrumentos avaliativos"
- Fixture: `user.client.has_new_application_experience = True`

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
- Estado esperado: `button[aria-selected="true"]`, `localStorage.getItem('application_instrument_category') === 'presential'`
- Fixture: `mixer.blend(Application, category=1)` e `mixer.blend(Application, category=2)`

#### Cenário 4 — Busca textual e filtros combinados
**Ação humana:**
- [x] Digitar parte do nome da avaliação no campo de busca com ícone de lupa (`placeholder="Buscar"`).
- [x] Aguardar brevemente (debounce de 300ms) e confirmar que a listagem filtra em tempo real sem recarregar a tela inteira.
- [x] Selecionar um ano específico no dropdown `"**Ano**"` e uma unidade no dropdown `"**Unidade**"`.
- [x] Confirmar que o filtro por URL/API é aplicado corretamente.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `#instruments-search`, `select[name="year"]`, `select[name="units"]`
- Estado esperado: requisição disparada para `/aplicacoes/api/instrumentos/?search=...&year=...` com dados correspondentes
- Fixture: duas aplicações com nomes e anos distintos

---

### 5.3 Nova Listagem: Coluna Malote, Turmas e Token Online [Automatizável ✅]

#### Cenário 5 — Visualização compacta e expansão de turmas
**Ação humana:**
- [x] Localizar uma avaliação que possua mais de uma turma vinculada.
- [x] Observar abaixo do nome do caderno a linha secundária: verificar se exibe um selo cinza com a categoria e um resumo de turmas (ex.: `"**2 turmas**"` com ícone chevron).
- [x] Clicar no botão expansor de turmas.
- [x] Confirmar que um popover/painel é aberto exibindo os nomes de todas as turmas vinculadas.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `button.application-instrument-expand`
- Estado esperado: elemento de popover visível contendo os nomes das turmas vinculadas
- Fixture: `application.classes.add(turma1, turma2)`

#### Cenário 6 — Copiar token online diretamente na listagem
**Ação humana:**
- [x] Na aba `"**Online**"`, localizar uma aplicação online que tenha o token aleatório habilitado.
- [x] Observar abaixo da data a indicação do token (ex.: `"**Token: ABC-123**"` acompanhado de um ícone de cópia).
- [x] Clicar no ícone de cópia.
- [x] Verificar se há feedback visual de confirmação (tooltip `"Copiado!"`).

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `button.application-instrument-copy`
- Estado esperado: texto copiado para o clipboard com sucesso
- Fixture: `mixer.blend(Application, category=2, is_token_online=True)`

---

### 5.4 Nova Listagem: Menu Unitário de Opções (`...`) [Automatizável ✅]

#### Cenário 7 — Estrutura em 2 colunas do menu de opções
**Ação humana:**
- [x] Em qualquer linha da listagem, clicar no botão de três pontos ou engrenagem no canto direito (`...`).
- [x] Verificar se o menu dropdown abre alinhado à direita, organizado em até duas colunas:
  - Coluna 1: `"**GERAL**"` (com ações de Editar, Duplicar, Divulgar resultado, etc.).
  - Coluna 2: `"**IMPRESSÃO**"` (com ações de configurações de impressão, malote e folhas avulsas).
- [x] Clicar em `"**Editar**"` e certificar-se de que a página é redirecionada para `/aplicacoes/instrumento-avaliativo/<uuid>/`.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `tr.application-instruments-row button[data-toggle="dropdown"]`, `.application-instrument-options`
- Estado esperado: `.application-instrument-options` visível com colunas Geral e Impressão
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

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `input[type="checkbox"]`, `.application-instruments-bulk`, `button:has-text("Limpar seleção")`
- Estado esperado: `.application-instruments-bulk` renderiza condicionalmente com base em `selectionList.length > 0`
- Fixture: ao menos 3 aplicações cadastradas

#### Cenário 9 — Operação em lote: Divulgar resultados
**Ação humana:**
- [x] Selecionar duas aplicações cuja divulgação de resultado esteja agendada para o futuro.
- [x] No card flutuante, clicar no botão `"**Divulgar resultados**"`.
- [x] Confirmar o diálogo/modal de confirmação.
- [x] Verificar se o status de divulgação é atualizado na listagem para `"Divulgado em: [Data atual]"`.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumentos-avaliativos/`
- Seletor: `.application-instruments-bulk button:has-text("Divulgar resultados")`
- Estado esperado: requisição POST de divulgação disparada com sucesso
- Fixture: `Application` com `student_stats_permission_date > now()`

---

### 5.6 Criação Unificada: Etapa 1 (Caderno & Opções Avançadas) [Automatizável ✅]

#### Cenário 10 — Preenchimento inicial e persistência do Caderno (Exam)
**Ação humana:**
- [x] Na listagem, clicar no botão laranja `"**+ Nova aplicação**"`.
- [x] Confirmar que a tela abre na Etapa 1: `"**Configurações**"` (com o passo marcado em laranja).
- [x] Tentar clicar na Etapa 2 (`"Questões"`) ou Etapa 3 (`"Aplicação"`): confirmar que o cursor exibe ícone de bloqueio e tooltip informando que o caderno deve ser criado antes.
- [x] Preencher o campo `"**Título da prova**"` com `"Simulado Geral 2026"`.
- [x] Selecionar a Etapa de ensino e informar Nota geral (ex.: `10.0`).
- [x] Clicar no toggle `"**Opções avançadas**"`: confirmar que o card sanfona expande exibindo as configurações (textos base, embaralhar questões, IA para discursivas, sigilo, etc.).
- [x] Preencher uma data limite de elaboração válida.
- [x] Clicar no botão inferior `"**Continuar**"`.
- [x] Observar o estado de loading e confirmar que o caderno é criado com sucesso (`POST /aplicacoes/api/instrumentos/cadernos/`).
- [x] Confirmar que o sistema transiciona automaticamente para a Etapa 2 (`"Questões"`), liberando o acesso às etapas 2 e 3.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/`
- Seletor: `#application-title`, `#application-total-grade`, `#exam-advanced-options-toggle`, `button:has-text("Continuar")`
- Estado esperado: `POST /aplicacoes/api/instrumentos/cadernos/` retorna 201 com `exam.id`, `currentStep` vira 2
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

### 5.8 Criação Unificada: Etapa 3 (Aplicação, Tempos e Divulgação) [Automatizável ✅]

#### Cenário 13 — Configuração de parâmetros e persistência da Aplicação
**Ação humana:**
- [ ] Clicar no botão `"**Continuar**"` da Etapa 2 para avançar para a Etapa 3 (`"**Aplicação**"`).
- [ ] Selecionar o formato `"**Online**"`.
- [ ] Confirmar que o switch `"**Habilitar tokens online**"` aparece na tela. Marcar o switch.
- [ ] Preencher Horário de Início (`08:00`), Término (`12:00`), tolerância de atraso e tempo mínimo.
- [ ] Configurar a data de divulgação dos resultados.
- [ ] Clicar no botão `"**Continuar**"`.
- [ ] Confirmar que a aplicação é salva no banco (`POST /aplicacoes/api/instrumentos/aplicacoes/`) vinculada ao caderno da Etapa 1.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/` (currentStep = 3)
- Seletor: `button:has-text("Online")`, `#application-enable-online-token`, `#application-start`, `#application-end`, `button:has-text("Continuar")`
- Estado esperado: `POST /aplicacoes/api/instrumentos/aplicacoes/` retorna 201 com `application.id`
- Fixture: `exam.id` presente no estado Vue

---

### 5.9 Edição Unificada: Hidratação, `v-changed` e Salvamento [Automatizável ✅]

#### Cenário 14 — Hidratação e detecção visual de alterações (`v-changed`)
**Ação humana:**
- [x] Acessar diretamente a rota de edição de uma aplicação existente: `/aplicacoes/instrumento-avaliativo/<uuid>/`.
- [x] Verificar se o cabeçalho exibe o botão `"**Salvar alterações**"` e se todos os campos vêm preenchidos com os dados salvos.
- [x] Alterar o título da prova no input `"**Título da prova**"`.
- [x] Verificar se o campo recebe imediatamente um destaque visual (borda/ring) indicando alteração não salva (`v-changed`).
- [x] Passar o mouse sobre o campo e confirmar o tooltip informativo orientando a salvar.
- [x] Clicar no botão `"**Salvar alterações**"` no cabeçalho.
- [x] Confirmar que uma requisição PUT é enviada e que o destaque visual de alteração desaparece após o sucesso.

**Referência técnica (para automação):**
- URL: `/aplicacoes/instrumento-avaliativo/<uuid>/`
- Seletor: `#application-title`, `[v-changed]`, `button:has-text("Salvar alterações")`
- Estado esperado: `changedFields.has('exam.name') === true` antes do submit; `PUT` bem-sucedido e `changedFields.size === 0` após resposta
- Fixture: `Application` e `Exam` criados via mixer

---

### 5.10 Responsividade e Comportamento Visual [Apenas Manual 👁]

#### Cenário 15 — Validação de layout em 1333x1080 e telas menores
**Ação humana:**
- [ ] Ajustar a viewport do navegador para resolução intermediária (`1333x1080`).
- [ ] Na listagem de instrumentos:
  - [ ] Verificar se nenhum texto de caderno, turma ou botão sofre quebra inadequada ou sobreposição.
  - [ ] Confirmar que o dropdown de opções unitárias de 2 colunas não transborda para fora da tela.
- [ ] Reduzir a largura para `768px` e `390px` (mobile):
  - [ ] Verificar se a barra de etapas do cadastro (`application-instrument-steps`) permite scroll horizontal ou compactação legível.
  - [ ] Confirmar que os cards de opções avançadas e seletores de horário não quebram o grid horizontal.

---

### 5.11 Itens Pendentes (Não Testar / Fora de Escopo no Momento) [Apenas Manual 👁]

> [!NOTE]
> Os itens a seguir foram conscientemente deixados para a task de finalização `17tu7rp42zh`. O QA NÃO deve apontar bug nem reprovar o fluxo caso observe as condições abaixo:

#### Cenário 16 — Conferência de itens declaradamente pendentes
**Ação humana:**
- [ ] **Seção 2 de Participantes na Etapa 3:** Observar que não há seleção de turmas/alunos. O QA **não deve** bloquear o teste por falta dessa seção.
- [ ] **Ação "Utilizar caderno existente":** Notar ausência do seletor de cadernos prontos no cabeçalho. Item planejado para etapa posterior.
- [ ] **Etapas 4 (Diagramação) e 5 (Conferência):** Os painéis estão vazios e bloqueados. Não considerar como falha.
- [ ] **Modos Quadro/Compacto na Listagem:** Os botões continuam desabilitados/comentados.

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

> [!NOTE] [Regra de Negócio / Validação de Lote] Divulgação de resultados em lote restrita a datas futuras
> **Evidência/Reprodução:** Ao selecionar na tabela avaliações que já possuem `results_release_date` anterior ao momento atual, o botão de "Divulgar resultados" exibe confirmação informando que nenhuma aplicação selecionada é elegível.
> **Comportamento Esperado:** Este é o comportamento correto previsto pela regra de negócio (apenas aplicações agendadas para o futuro podem ter a divulgação antecipada em lote). Registrado para fins de documentação de QA.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **[WONTFIX / Futuro — Task 17tu7rp42zh] Seleção de Participantes da Aplicação**  
> A seleção de turmas e alunos na etapa 3 será entregue na task de fechamento do fluxo 2.0.

> [!NOTE]
> **[WONTFIX / Futuro — Task 17tu7rp42zh] Utilizar Caderno Existente**  
> A importação de um caderno pronto a partir de "Meus cadernos" no cabeçalho será tratada na próxima entrega.

> [!NOTE]
> **[WONTFIX / Futuro — Task 17tu7rp42zh] Diagramação e Conferência**  
> As etapas 4 e 5 serão implementadas após a consolidação das etapas de elaboração e aplicação.

> [!NOTE]
> **[WONTFIX / Futuro — Task 17tu7rp42zh] Modos Quadro (Kanban) e Compacto na Listagem**  
> Visualizações alternativas da listagem foram adiadas para priorizar o modo Tabela com ações em lote.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

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

