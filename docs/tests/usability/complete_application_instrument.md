# Mapeamento de Usabilidade: complete_application_instrument.html

> Template: `fiscallizeon/applications/templates/dashboard/applications/complete_application_instrument.html`
> Feature: Criação e Edição Unificada de Instrumentos Avaliativos (Caderno + Aplicação) (task CU-86ak8r20g / branch `feat/instrumentos-avaliativos-CU-86ak8r20g`)
> Base da seção 8.1 dos planos de QA. Mapeamento de seletores DOM estáveis e dados para automação.

---

## 1. URLs e Navegação

| Ação | URL | View Django |
|---|---|---|
| Nova Criação | `/aplicacoes/instrumento-avaliativo/` | `applications:application_instrument` |
| Edição Existente | `/aplicacoes/instrumento-avaliativo/<uuid>/` | `applications:application_instrument_update` |
| Retorno | Link `"← Voltar"` no cabeçalho | Retorna para `/aplicacoes/instrumentos-avaliativos/` |

**Fluxo de navegação e bloqueio de etapas:**
1. A tela possui 5 etapas navegáveis na barra de navegação superior (`application-instrument-steps`):
   - **Etapa 1:** `"Configurações"` (Configurações do Caderno / Exam). Sempre liberada.
   - **Etapa 2:** `"Questões"` (Solicitações, IA, Cadernos anteriores e Revisão). Bloqueada até o `Exam` ser criado.
   - **Etapa 3:** `"Aplicação"` (Configurações de data, horários, dispositivos e divulgação da Application). Bloqueada até o `Exam` ser criado.
   - **Etapa 4:** `"Diagramação"`. Bloqueada e vazia no momento (pendência de produto).
   - **Etapa 5:** `"Conferência"`. Bloqueada e vazia no momento (pendência de produto).
2. Na criação nova:
   - O usuário preenche a Etapa 1 e clica em `"**Continuar**"`. O frontend executa `POST /aplicacoes/api/instrumentos/cadernos/`.
   - Com o `exam.id` retornado, as etapas 2 e 3 são desbloqueadas (`canOpenStep(...) === true`).
   - Na Etapa 3, ao clicar em `"**Continuar**"`, o frontend executa `POST /aplicacoes/api/instrumentos/aplicacoes/`, vinculando o caderno à aplicação recém-criada.
3. Na edição existente (`<uuid>`):
   - A página hidrata os dados de `Exam` e `Application` via GET.
   - O cabeçalho exibe o botão `"**Salvar alterações**"` (`@click="saveChanges"`), que envia `PUT` para caderno e aplicação sem mudar de etapa.
   - O botão `"**Continuar**"` salva a etapa ativa e avança para a próxima.

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Persona
- **Coordenação** vinculada à mesma coordenação do cliente.
- `user.user_type = 'coordination'` ou `user.is_superuser = True`.
- `user.client.has_new_application_experience = True`.
- Permissões: `exams.add_exam`, `exams.change_exam`, `applications.add_application`, `applications.change_application`.
- 2FA desativado (`two_factor_enabled=False`).

### Fixture via Mixer (Python)
```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, Coordination
from fiscallizeon.applications.models import Application
from fiscallizeon.exams.models import Exam

client = mixer.blend(Client, name="Colégio Exemplo", has_new_application_experience=True)
coord = mixer.blend(Coordination, client=client, name="Coordenação Geral")

coord_user = mixer.blend(
    User,
    client=client,
    user_type="coordination",
    two_factor_enabled=False,
    must_change_password=False,
)
coord_user.coordinations.add(coord)

# Para cenário de edição:
exam = mixer.blend(Exam, client=client, coordination=coord, name="Prova Bimestral 1", category=1)
app = mixer.blend(Application, client=client, coordination=coord, exam=exam, category=1)
# page.goto(f"/aplicacoes/instrumento-avaliativo/{app.pk}/")
```

---

## 3. Seletores DOM e Ações

### 3.1. Cabeçalho e Ações Globais
| Elemento | Seletor DOM estável | Descrição |
|---|---|---|
| Link Voltar | `a[href*="/aplicacoes/instrumentos-avaliativos/"]` | Retorna para a listagem. |
| Título do cabeçalho | `h1.tw-text-xl.tw-font-semibold` | "Novo instrumento avaliativo" ou nome do caderno. |
| Botão Salvar alterações | `button:has-text("Salvar alterações")` | Visível na edição. Salva caderno e aplicação (`@click="saveChanges"`). |
| Botão Continuar | `button:has-text("Continuar")` | Salva a etapa atual e avança para a seguinte (`@click="continueStep"`). |

### 3.2. Etapa 1 — Configurações do Caderno (Exam)
| Campo / Ação | Seletor DOM estável | Descrição |
|---|---|---|
| Título da Prova | `#application-title` | Input textual (`v-model="exam.name"`). |
| Categoria | `#application-category` | Select de categoria da prova (`exam.category`). |
| Etapa de Ensino | `#application-teaching-stage` | Select da etapa escolar (`exam.teaching_stage`). |
| Nota Geral | `#application-total-grade` | Input numérico (`min="0"`, `v-model.number="exam.total_grade"`). |
| Card Coordenações | `.instrument-coordination-card` | Seleção de coordenações autorizadas. |
| Toggle Opções Avançadas | `button#exam-advanced-options-toggle` | Abre/fecha o card sanfona de opções avançadas de caderno. |
| Data Limite de Elaboração | `#application-elaboration-deadline` | Input de data limite para elaboração (`exam.elaboration_deadline`). |

### 3.3. Etapa 2 — Questões do Caderno
| Elemento / Ação | Seletor DOM estável | Descrição |
|---|---|---|
| Botão Solicitar ao professor | `button:has-text("Solicitar ao professor")` | Abre o modal de solicitação a docentes (`modal_review.html` / `request_question.html`). |
| Botão Gerar com IA | `button:has-text("Gerar com IA")` | Abre modal de criação assistida por IA. |
| Botão Cadernos anteriores | `button:has-text("Cadernos anteriores")` | Abre modal de importação de questões de provas anteriores. |
| Lista de Professores Solicitados | `div.instrument-selected-teachers` | Grade de professores (`selectedTeachers`), disciplina, série e botões de editar/remover. |
| Botão Revisar questões | `button:has-text("Revisar questões")` | Abre o modal completo de revisão (`modal_review.html`). |

### 3.4. Etapa 3 — Configurações da Aplicação (Application)
| Campo / Ação | Seletor DOM estável | Descrição |
|---|---|---|
| Formato Presencial | `button:has-text("Presencial")` | Define `application.category = 1`. |
| Formato Online | `button:has-text("Online")` | Define `application.category = 2`. |
| Formato Híbrida | `button:has-text("Híbrida")` | Define `application.category = 5`. |
| Switch Habilitar tokens online | `#application-enable-online-token` | Visível apenas no formato Online. |
| Horário de Início | `#application-start` | Input `type="time"` (`application.start`). |
| Horário de Término | `#application-end` | Input `type="time"` (`application.end`). |
| Tolerância de atraso | `#application-max-time-tolerance` | Input `type="time"` (`application.max_time_tolerance`). |
| Tempo mínimo de permanência | `#application-min-time-finish` | Input `type="time"` (`application.min_time_finish`). |
| Switch Liberar resultado ao fim | `#application-release-result-at-end` | Toggle `application.release_result_at_end`. |
| Data de divulgação do resultado | `#application-student-stats-permission-date` | Input `type="datetime-local"`. |

### 3.5. Etapa 3 — Participantes da Aplicação (Turmas e Alunos)
| Elemento / Ação | Seletor DOM estável | Descrição |
|---|---|---|
| Contêiner de Participantes | `div.instrument-participants` | Componente `instrument_participants`. |
| Checkbox de Turma | `input[type="checkbox"]` na linha da turma | Seleciona/desmarca todos os alunos da turma. |
| Botão Expandir Alunos | `button.instrument-participants-expand` | Abre o painel retrátil de alunos da turma. |
| Checkbox de Aluno Individual na Turma | `input[type="checkbox"]` dentro do collapse | Seleciona/desmarca aluno específico. |
| Seção Alunos Individuais | `section.instrument-individual-students` | Alunos avulsos sem vínculo obrigatório à turma. |
| Seletor de Busca de Alunos | `search-students-component` | Input com autocomplete para inclusão avulsa. |

### 3.6. Etapa 5 — Conferência e Geração de Malote
| Elemento / Ação | Seletor DOM estável | Descrição |
|---|---|---|
| Botão Status Aplicação | `button:has-text("Aplicação")` no resumo | Exibe status "Pendente" ou "Concluído", direciona para Etapa 2/3. |
| Botão Status Questões | `button:has-text("Questões")` no resumo | Exibe contagem de pendências/reprovações de questões. |
| Card Malote Completo | `button:has-text("Gerar malote")` no card 1 | `@click="openInstrumentPrint('complete')"`. Caderno + gabaritos. |
| Card Apenas Gabaritos | `button:has-text("Gerar malote")` no card 2 | `@click="openInstrumentPrint('answers')"`. Folhas de resposta. |
| Card Aluno Específico | `button:has-text("Gerar malote")` no card 3 | `@click="openInstrumentPrint('student')"`. Folha avulsa nominal. |
| Barra de Progresso do Malote | `div[role="progressbar"]` | Exibe porcentagem `${ instrumentPrintStatus.progress }%` ao vivo. |
| Diálogo de Impressão | `.instrument-print-dialog` | Modal refatorado com seleção de modelo de folha e switches. |

### 3.7. Marcadores de Alteração (`v-changed`) e Foco em Erros
- **Destaque Visual:** Na edição, campos alterados em relação ao snapshot original recebem a diretiva `v-changed`, aplicando uma borda/ring visual laranja e tooltip indicando alterações não salvas.
- **Foco Automático:** Ao tentar avançar ou salvar com campos obrigatórios pendentes, o formulário rola e foca automaticamente no primeiro campo com erro (`baf731264`).

---

## 4. Rotas de API Críticas
- `POST /aplicacoes/api/instrumentos/cadernos/` (criação do Exam no primary com transação e lock).
- `PUT /aplicacoes/api/instrumentos/cadernos/<uuid>/` (edição do Exam existente).
- `POST /aplicacoes/api/instrumentos/aplicacoes/` (criação da Application com `students` e `school_classes`).
- `PUT /aplicacoes/api/instrumentos/aplicacoes/<uuid>/` (edição da Application e sincronização M2M de participantes).
- `GET /aplicacoes/api/instrumentos/cadernos/<uuid>/` (hidratação do Exam na edição).
- `GET /aplicacoes/api/instrumentos/aplicacoes/<uuid>/` (hidratação da Application e `participants` na edição).
- `GET /aplicacoes/api/aplicacao/<uuid>/status-malote/` (acompanhamento de progresso do malote).

