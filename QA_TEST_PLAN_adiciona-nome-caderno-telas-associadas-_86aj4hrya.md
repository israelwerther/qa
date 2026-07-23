---
Date: 2026-07-23
Feature Area: UI/UX (Identificação Contextual)
Risk Level: Low
OpenSpec Quality: 5 stars (Tarefas e specs muito bem definidas)
---

# QA Test Plan: Adiciona Nome do Caderno em Telas Associadas

## 1. Resumo das Alterações (Summary of Changes)
- **Frontend / UI:** Inclusão do nome do caderno (Exam Name) como identificador contextual nas seguintes telas:
  - **Aplicações:** `application_detail.html`, `application_add_del_students.html`, `application_create_update.html`
  - **Elaboração de Prova (Professor):** `before_exam_request_teacher_subject_edit_v2.html`, `examteachersubject_questions_bank_introduction.html`, `examteachersubject_update_form.html`
  - **Correção:** `exam_essay_correction.html`
  - **Gestão de Cadernos:** `exam_request_create_update_new.html`
- A formatação adotada padroniza o nome truncado em até 50 caracteres (`truncatechars:50`) com estilo visual cinza (`text-[#64748b]`) e inserido estrategicamente próximo a títulos ou breadcrumbs.

## 2. Diferenças de Escopo (Scope Boundaries)
**IN SCOPE:**
- Verificação visual da presença e formatação do nome do caderno nas 8 telas modificadas.
- Validação se a quebra/truncamento (50 caracteres) está funcionando.
- Comportamento no formulário de criação/edição de aplicação (renderização via Django na edição, via Vue na criação).

**OUT OF SCOPE:**
- Funcionalidade principal de cada tela (ex: não é preciso testar se a correção de redação salva a nota corretamente, apenas se a tela exibe o nome do caderno).
- Telas que foram descartadas no Spec (`examteachersubject_view_questions.html`, `inspector-new.html`, `omr_correction.html`, `room_distribution_detail.html`, `distribution_create_update.html`, `exam_teacher_create_update_v2.html`, `exam_teacher_create_update.html`, `omr_upload_detail_new.html`).

## 3. Navegação e Camada Técnica
| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Detalhes da Aplicação | Aplicações > Ver | `/applications/<uuid>/` [verificar] | `application_detail` |
| Editar Alunos da Aplicação | Aplicações > Alunos | `/applications/<uuid>/students/` [verificar] | `application_add_del_students` |
| Cadastrar/Editar Aplicação | Aplicações > Novo/Editar | `/applications/create/` ou `/applications/<uuid>/update/` [verificar] | `application_create` / `application_update` |
| Professor: Nova Prova | (Acesso via link para professor) | `/examteachersubject/<uuid>/before-edit/` [verificar] | `before_exam_request_teacher_subject_edit` |
| Professor: Banco de Questões | (Acesso via link para professor) | `/examteachersubject/<uuid>/questions-bank-intro/` [verificar] | `examteachersubject_questions_bank_introduction` |
| Professor: Editar Disciplina | (Acesso via link para professor) | `/examteachersubject/<uuid>/update/` [verificar] | `examteachersubject_update` |
| Correção de Redação | Correção > Redações | `/exams/<uuid>/essay-correction/` [verificar] | `exam_essay_correction` |
| Editar Caderno | Instrumentos Avaliativos > Novo/Editar | `/exams/create/` ou `/exams/<uuid>/update/` [verificar] | `exam_request_create` / `exam_request_update` |

## 4. Testes Automatizados e Setup de Dados
Para validar essas telas, é necessário ter Cadernos criados, Aplicações vinculadas e Disciplinas de Professor associadas.

**Exemplo de setup de dados via Mixer (pytest):**
```python
# Fixture para gerar dados necessários para as telas
from mixer.backend.django import mixer
from fiscallizeon.exams.models import Exam, Application, ExamTeacherSubject

def test_setup_contextual_names(client, admin_user):
    # Criar caderno com nome longo
    exam = mixer.blend(Exam, name="Caderno de Teste Muito Longo Para Validar Truncamento de Cinquenta Caracteres")
    
    # Criar aplicação
    app = mixer.blend(Application, exam=exam)
    
    # Criar disciplina de professor
    ets = mixer.blend(ExamTeacherSubject, exam=exam, teacher=admin_user)
    
    client.force_login(admin_user)
    # Agora o client pode navegar para as URLs descritas e validar o response.content
```

## 5. Roteiro de Testes (Execution Test Script)

### Telas de Aplicação (Application)
- [x] **Acessar Detalhes da Aplicação (`application_detail.html`)** `[Apenas Manual 👁]`
  - Persona: Administrador / Coordenador
  - Ação: Abrir detalhes de uma aplicação existente.
  - Resultado Esperado: O nome do caderno (truncado se maior que 50 chars) deve aparecer abaixo do título "Aplicação do dia..."
- [ ] **Acessar Gerenciamento de Alunos (`application_add_del_students.html`)** `[Apenas Manual 👁]`
  - Persona: Administrador / Coordenador
  - Ação: Abrir a tela de adicionar/remover alunos de uma aplicação.
  - Resultado Esperado: O nome do caderno (truncado) deve estar visível no topo, abaixo do título.
- [x] **Criar/Editar Aplicação (`application_create_update.html`)** `[Automatizável ✅]`
  - Persona: Administrador / Coordenador
  - Ação: Acessar formulário de criação e de edição.
  - Resultado Esperado (Edição): Nome do caderno é renderizado.
  - Resultado Esperado (Criação): Ao selecionar o caderno no dropdown (Vue), o nome deve refletir corretamente na tela (se aplicável na UI).

### Telas do Professor (Elaboração)
- [ ] **Acessar Tela "Opa! Hora de elaborar..." (`before_exam_request_teacher_subject_edit_v2.html`)** `[Apenas Manual 👁]`
  - Persona: Professor
  - Ação: Abrir link de elaboração enviado para o professor.
  - Resultado Esperado: O nome do caderno aparece em texto cinza e subtítulo abaixo de "Opa! Hora de elaborar uma nova prova."
- [ ] **Acessar Introdução Banco de Questões (`examteachersubject_questions_bank_introduction.html`)** `[Apenas Manual 👁]`
  - Persona: Professor
  - Ação: Navegar para a tela de banco de questões da elaboração.
  - Resultado Esperado: O nome do caderno é exibido como contexto no bloco principal.
- [ ] **Acessar Atualização de Disciplina (`examteachersubject_update_form.html`)** `[Apenas Manual 👁]`
  - Persona: Professor
  - Ação: Abrir formulário de edição de dados da disciplina do professor para a prova.
  - Resultado Esperado: Nome do caderno como referência contextual no topo do form.

### Correção de Redação e Revisão de Questões
- [ ] **Acessar Correção de Redação (`exam_essay_correction.html`)** `[Apenas Manual 👁]`
  - Persona: Corretor / Professor
  - Ação: Acessar interface de correção de redações.
  - Resultado Esperado: Nome do caderno presente no topo da tela, no limite de 50 caracteres.
- [ ] **Acessar Cadastro/Edição de Caderno (`exam_request_create_update_new.html`)** `[Automatizável ✅]`
  - Persona: Administrador / Coordenador
  - Ação: Acessar a tela grande de edição do caderno Vue.js.
  - Resultado Esperado: Nome do caderno (ex: "Editar caderno: NOME DO CADERNO") deve ser visível no header, seja em edição ou criação (após digitar o nome).

## 6. Validação Visual e de Layout
- [ ] Tirar screenshot da tela `application_detail.html` para checar truncamento de string.
- [ ] Tirar screenshot da tela `before_exam_request_teacher_subject_edit_v2.html` para checar cor `#64748b`.
- [ ] Tirar screenshot da tela de edição do Caderno em Vuejs (`exam_request_create_update_new.html`) para garantir que layout não quebrou com a inclusão.

## 7. Problemas Encontrados (Bugs and Observations)
*(A ser preenchido pelo QA humano durante a execução)*

## 8. Melhorias Futuras (Future Improvements & Tech Debt)
> [!NOTE]
> Mapear se em telas legadas a inclusão do nome empurra muito o conteúdo para baixo no mobile.

> [!NOTE]
> **[UX/UI] Badge de Histórico:** Na tela de editar aplicação (`application_create_update.html`), o badge de histórico de alterações ficaria melhor posicionado se ficasse ao lado do botão "Salvar aplicação" no cabeçalho ou rodapé.

### 8.1. Mapeamento Contínuo de Usabilidade
Não se aplica a criação de um novo mapeamento de tela exato aqui, visto que foram alterações de texto simples em múltiplas telas diferentes. Para automações E2E focadas nisso, a prioridade seria checar o innerText dos elementos `h1`/`h2`/`span` no topo do `.container`.

## 9. Retrospectiva de QA
*(A ser preenchido ao final da validação)*
- **Bottleneck:** (Preencher depois)
- **Reflexão:** As instruções foram diretas e claras. O OpenSpec eliminou o trabalho de procurar telas redundantes (ex: `inspector-new.html`), economizando tempo no escopo.
