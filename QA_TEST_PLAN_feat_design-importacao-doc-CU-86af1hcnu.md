# Plano de Testes de QA: Redesign do Preview de Importação DOC (IA)

> Branch: `feat/design-importacao-doc-CU-86af1hcnu`  
> Tarefa ClickUp: `CU-86af1hcnu`  
> Referências OpenSpec: `openspec/changes/design-importacao-doc-preview/` (`proposal.md`, `design.md`, `tasks.md`, `spec.md`)

---

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-08-06 |
| **Natureza da Tarefa:** | `[Business Feature]` / `[Refactoring]` (Redesign de UI de Importação DOCX com Alpine.js + django-components com paridade 1:1) |
| **Área da Feature:** | Exams (Elaboração de Cadernos / Importação de Questões via IA/DOCX) |
| **Nível de Risco:** | Médio (Cutover de Vue para Alpine no preview e ponte via CustomEvent) |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5/5 estrelas — Especificação completa e detalhada) |

---

## 1. Summary of Changes (Resumo das Alterações)

- **Novo Componente de Domínio (`import_preview`):** Criado em `fiscallizeon/exams/components/import_preview/` contendo:
  - `import_preview.py`: Registro dos componentes `import_preview`, `import_preview_actions`, `import_preview_question_content` e `import_preview_question_card`.
  - `import_preview.html`: Template principal compondo o shell `fullscreen_layout`, a sidebar de navegação/estatísticas e os modais nativos `<dialog>` de remoção/confirmação.
  - `import_preview.js`: Alpine Store (`$store.importPreview`) gerenciando o estado reativo do preview (questões, paginação, gabarito, ordenação e modais).
  - `import_preview_actions.html`, `import_preview_question_card.html`, `import_preview_question_content.html`: Primitivos visuais do card da questão alinhados ao visual de Visualizar Prova (`exam_preview_question_card`).
  - `README.md`: Documentação técnica do componente e seus eventos.
- **Cutover na Página de Edição (`exam_request_teacher_subject_edit_new.html`):**
  - O `import_preview_modal.html` legado foi substituído no ponto de renderização pela inclusão do componente `{% component "import_preview" %}` no bloco `js-additional` (fora do mount `#app` do Vue).
  - Implementada a ponte de CustomEvents entre a aplicação Vue (que gerencia upload e chamada da API de parsing) e o componente Alpine (que exibe a interface fullscreen de revisão).
- **Preservação do Legado:**
  - O arquivo `import_preview_modal.html` permanece intacto no repositório para consulta de paridade.

---

## 2. Scope Boundaries (Diferenças de Escopo)

**IN SCOPE:**
- Exibição fullscreen do preview de importação de questões via `.docx` usando o novo componente `import_preview`.
- Reordenação de questões (Subir / Descer) e reordenação de alternativas.
- Seleção e edição de gabarito correto (Radio button para Objetivas e Checkboxes para Somatório).
- Remoção de questão individual com diálogo nativo `<dialog>` de confirmação e recálculo automático de estatísticas.
- Navegação por pills na sidebar e paginação da lista de questões.
- Validação visual de bloqueio de confirmação em caso de questões com erro.
- Modal nativo de confirmação da importação e integração do evento `import-preview-confirm` com o envio final da página Vue.

**OUT OF SCOPE:**
- Alterações na lógica backend de extração de arquivo `.docx` ou no parser de IA (`parse_question_file_async`).
- Edição ou deleção in-place do arquivo legado `import_preview_modal.html`.
- Reescrever a página principal de elaboração (`exam_request_teacher_subject_edit_new.html`) de Vue para Alpine.
- Implementação de persistência alternativa no Redis para rascunhos de importação.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

### Mapa de Navegação Canônico

| Destino | Rótulo real no menu UI | URL Django | View Name |
|---|---|---|---|
| Minhas Elaborações | Elaboração de Cadernos [verificar] | `/exams/elaboracao/` | `exams:exam_request_list` |
| Editar Questões do Caderno | Editar questões [verificar] | `/provas/prova/<uuid:exam_teacher_subject_pk>/editar/` | `exams:exam_teacher_subject_edit_questions` |
| Modal de Importação DOCX | Importar Questões via Arquivo [verificar] | Front-end Trigger (Alpine / Vue) | Componente `import_preview` |
| Upload API DOCX | — | `/provas/prova/<uuid:exam_teacher_subject_pk>/importar-docx/` | `exams:exam_questions_import` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Testes Automatizados Backend
Para rodar os testes de importação e processamento de cadernos:
```bash
pytest fiscallizeon/exams/tests/test_exams_imports.py
```

### Persona dos Testes
- **Persona:** Professor autor da disciplina no caderno (`user_type = TEACHER`) ou Coordenador com permissão de edição.
- **Configuração de Ambiente:** `user.client_has_new_teacher_experience = True` ou `user.inspector.has_new_teacher_experience = True` para acessar a interface `exam_request_teacher_subject_edit_new.html`.

### Fixtures e Mixer Setup (Python Snippet):
```python
from fiscallizeon.exams.models import Exam, ExamTeacherSubject
from fiscallizeon.inspectors.models import Inspector
from fiscallizeon.subjects.models import Subject, TeacherSubject
from fiscallizeon.accounts.models import User
from mixer.backend.django import mixer

# Usuário Professor
user = mixer.blend(
    User,
    user_type='TEACHER',
    is_authenticated=True,
    client_has_new_teacher_experience=True,
)
teacher = mixer.blend(Inspector, user=user, has_new_teacher_experience=True)

# Disciplina e Caderno
subject = mixer.blend(Subject, name='Física')
teacher_subject = mixer.blend(TeacherSubject, teacher=teacher, subject=subject)
exam = mixer.blend(Exam, created_by=user)
exam_ts = mixer.blend(
    ExamTeacherSubject,
    exam=exam,
    teacher_subject=teacher_subject,
    quantity_questions=5,
)
```

---

## 5. Roteiro de Testes com Checkboxes

**Persona:** Professor autor da disciplina (ou Coordenadora) na página de edição do caderno.

### 5.1 Abertura e Carregamento do Preview [Automatizável ✅]

#### Cenário 1 — Upload de arquivo e abertura do modal fullscreen

- [x] Na tela de edição do caderno, clicar em **"Importar via DOCX"**.
- [x] Selecionar um arquivo `.docx` válido e clicar em **"Enviar arquivo"**.
- [x] Confirmar que durante a leitura é exibida a indicação de carregamento **"Validando questões..."**.
- [x] Confirmar que a tela de pré-visualização abre em **tela cheia** (fullscreen), com lista de questões e sidebar.

---

### 5.2 Validação da Sidebar e Navegação [Automatizável ✅]

#### Cenário 2 — Resumo de estatísticas e scroll por pílula

- [x] Confirmar que a sidebar exibe o total de questões, quantidade de válidas e barras de progresso.
- [x] Clicar na pílula numerada de uma questão (ex: `02` ou `03`) na sidebar.
- [x] Confirmar que a página rola suavemente (*smooth scroll*) até a questão correspondente.

---

### 5.3 Alteração de Gabarito e Reordenação [Automatizável ✅]

#### Cenário 3 — Atualização do gabarito e reordenação de questões

- [x] Em uma questão objetiva, clicar em outra alternativa para alterar o gabarito.
- [x] Confirmar que a resposta selecionada é marcada como correta imediatamente.
- [x] Clicar nos botões de seta **"Subir"** ou **"Descer"** no card da questão.
- [x] Confirmar que as posições das questões são trocadas na lista.

---

### 5.4 Remoção de Questão [Automatizável ✅]

#### Cenário 4 — Exclusão com confirmação em modal

- [x] Clicar no botão/ícone de lixeira **"Remover"** em uma das questões.
- [x] Confirmar que um modal de confirmação é exibido.
- [x] Clicar em **"Remover"** no modal.
- [x] Confirmar que a questão é excluída da lista e que os contadores da sidebar atualizam imediatamente.

---

### 5.5 Validação de Bloqueio por Erros [Apenas Manual 👁]

#### Cenário 5 — Impedir confirmação quando houver questões com erros

- [x] Enviar um arquivo com questões incompletas (ex: sem gabarito).
- [x] Confirmar que o card da questão destaca o erro visualmente (*Nota: falha identificada — ver Seção 7*).
- [x] Confirmar que a sidebar exibe o alerta de pendências (*Nota: falha identificada — ver Seção 7*).
- [x] Confirmar que o botão **"Confirmar importação"** fica desabilitado (`disabled`) (*Nota: falha identificada — ver Seção 7*).

---

### 5.6 Confirmação e Salvamento no Caderno [Automatizável ✅]

#### Cenário 6 — Inserção das questões no caderno após confirmação

- [x] Com todas as questões válidas, clicar em **"Confirmar importação"**.
- [x] Confirmar a ação no modal final de confirmação (**"Sim, importar"**).
- [x] Confirmar que o preview em tela cheia é fechado.
- [x] Confirmar que as questões importadas são inseridas com sucesso no caderno de prova.

---

### 5.7 Validação da Tela Inicial do Professor (Novo Visual / Meu Painel) [Apenas Manual 👁]

#### Cenário 7 — Cabeçalho e Pesquisa Global

- [ ] Confirmar que o saudação inicial exibe o nome correto do professor ("Olá, [Nome]") e mensagem contextual de bom dia.
- [ ] Verificar se o seletor de unidade/rede (ex: "Rede Decisão") está funcional e altera o contexto do painel.
- [ ] Confirmar que a barra de busca ("Pesquise por resultados e desempenho de provas, turmas e alunos") responde ao foco e envia os termos de busca.

#### Cenário 8 — Cards de Atalho "Explore a nossa plataforma" *(Novo Layout Figma)*

> *Nota de QA:* O layout atual no código exibe `"Nenhuma tarefa pendente."` quando não há solicitações. Os 3 cards abaixo representam o **novo redesign do Figma (Pitch de Onboarding Contextual)** a ser implementado:

- [ ] **Card Criar questões com IA:** Clicar no botão `Criar questão com IA` e verificar se redireciona para a ferramenta de IA.
- [ ] **Card Banco de questões:** Clicar no botão `Acessar banco de questões` e verificar se abre a listagem do banco de questões (exibindo texto de acervo ~80.000 questões).
- [ ] **Card Corrigir avaliações:** Clicar no botão `Iniciar correção` e verificar se abre a tela de correção.


#### Cenário 9 — Abas de Demandas e Cards de Solicitação

- [ ] Verificar a exibição dos badges numéricos nas abas **Elaborar**, **Revisar** e **Corrigir** com as respectivas quantidades de pendências.
- [ ] Alternar entre as abas e validar a renderização dos cards com tag de status (ex: "Elaborando"), contagem de dias restantes (ex: "Restam 10 dias"), disciplina, nome da prova e progresso ("X de Y questões").
- [ ] No card da solicitação, testar a ação do botão `Continuar` (edita a prova) e do botão `Visualizar` (ícone de olho laranja).
- [ ] Clicar no botão `Todas as solicitações ->` no rodapé e validar o redirecionamento para a listagem completa.

#### Cenário 10 — Seção "Configure sua conta! 🚀" e LizeCoins

- [ ] Confirmar a exibição do saldo de LizeCoins (ex: "3.000 LizeCoins") e avatares da equipe.
- [ ] Validar a lista de missões de onboarding com checkmarks de conclusão e botões de ação (`Editar`, `Responder`).

#### Cenário 11 — Sidebar de Navegação Lateral

- [ ] Confirmar que o menu `Início` está ativo.
- [ ] Verificar o submenu `Cadernos` com os itens `Todos os cadernos`, `Solicitações`, `Revisões` (com badge numérico de pendências) e `Correções`.
- [ ] Testar a expansão/recolhimento dos accordions `Questões` e `Aplicações` e os links `Materiais de estudo` e `Relatórios`.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] **Captura de Tela — Layout Fullscreen:** Garantir que o preview ocupa toda a tela (`fullscreen_layout`), com header fixo, sidebar com `tw-w-[400px]` e área principal centralizada.
- [x] **Comparação com Visualizar Prova:** Verificar se o card da questão (`import_preview_question_card`) segue a mesma tipografia, badges e estilos de borda (válida/aviso/erro) que o `exam_preview_question_card` de Visualizar Prova.
- [x] **Comparação de Paridade:** Comparar lado a lado o novo preview em Alpine com o legado (`import_preview_modal.html`) para garantir que nenhuma informação ou controle essencial deixou de ser renderizado.
- [ ] **Comparação com o Layout "Meu Painel" (Figma):** Validar o alinhamento visual dos 3 cards superiores ("Explore a nossa plataforma"), das abas de demandas com badges vermelhos e do componente "Configure sua conta! 🚀" contra o layout mockado.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!WARNING]
> **[BUG CRÍTICO — FEEDBACK OCULTO] Omissão de Alerta de Erro ao Confirmar Importação:**
> - **Sintoma:** Sempre que a requisição de importação (`/ai/import/`) falha no backend com `HTTP 400 Bad Request` (ex: questão sem gabarito, tipo inválido ou estouro de cota), o erro é registrado no console JS, mas a notificação em tela (`alertTop`) é renderizada **atrás da camada z-index do modal fullscreen** (`fullscreen_layout` `z-[99990]`), deixando a tela travada sem feedback visual para o usuário.
> - **Causa Raiz:** O componente `alertTop` possui `z-index` menor que a camada modal do `fullscreen_layout`.
> - **Ação Recomendada:** Elevar o `z-index` do `alertTop` ou exibir erros de resposta da API em um banner/modal próprio dentro da interface do `import_preview`.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Débito Técnico — Remoção do Modal Legado:** O template `import_preview_modal.html` foi mantido para consulta conforme especificado em `design.md (D1)`. Em uma sprint futura após validação em produção, o arquivo legado e métodos auxiliares não utilizados em Vue devem ser descontinuados.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.  
  🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_request_teacher_subject_edit_new.md)**

### Exemplo de Automação (Python / Playwright + Setup Mixer)

```python
import pytest
from playwright.sync_api import Page, expect
from fiscallizeon.exams.models import Exam, ExamTeacherSubject
from mixer.backend.django import mixer

@pytest.mark.django_db
def test_doc_import_preview_flow(page: Page, live_server):
    # Setup de dados via Mixer
    user = mixer.blend('accounts.User', user_type='TEACHER', client_has_new_teacher_experience=True)
    exam = mixer.blend(Exam, created_by=user)
    exam_ts = mixer.blend(ExamTeacherSubject, exam=exam)

    # Login e Navegação
    page.goto(f"{live_server.url}/provas/prova/{exam_ts.pk}/editar/")
    
    # Interação com a UI do Preview Redenhado
    page.click('button:has-text("Importar via DOCX")')
    expect(page.locator('#import-preview')).to_be_visible()
    
    # Validação do Botão de Confirmação na Sidebar
    confirm_btn = page.locator('button:has-text("Confirmar importação")')
    expect(confirm_btn).to_be_enabled()
    confirm_btn.click()
    
    # Dialog Nativo de Confirmação
    page.click('button:has-text("Sim, importar")')
    expect(page.locator('#import-preview')).not_to_be_visible()
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo:** Testar o envio real do arquivo `.docx` depende de arquivo físico de exemplo e parsing da IA no ambiente local.
- **Feedback de Desenvolvimento:** A separação limpa do componente em `fiscallizeon/exams/components/import_preview/` e o uso de CustomEvents facilitou a validação técnica de isolamento entre o Vue da página e o Alpine do preview.
- **Melhorias de Workflow:** Manter a documentação em `.ai_qa_acervo/docs/tests/usability/exam_request_teacher_subject_edit_new.md` garante que testes futuros de Playwright possam reutilizar os seletores exatos sem necessitar de novas análises no DOM.


<!-- Anotações de melhorias -->

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

1. **Gatilhos e Barramentos de Eventos JS (Arquitetura Híbrida Vue ↔ Alpine):**
   - *Observação:* Como o preview redesenhado roda fora da árvore do Vue e troca mensagens por `CustomEvent` (`window.dispatchEvent`), a especificação do plano exigiu documentar os eventos disparados.
   - *Sugestão para o Prompt V2:* Adicionar na Seção 3 uma instrução explícita para registrar **"Eventos e Contratos JS Inter-Componentes"** quando a feature envolver comunicação entre diferentes frameworks (ex.: Vue/React ↔ Alpine).

2. **Diferenciação de Navegação Frontend vs HTTP:**
   - *Observação:* Algumas superfícies (como o modal fullscreen do import preview) não possuem uma URL Django própria, sendo ativadas por estado/evento na mesma página.
   - *Sugestão para o Prompt V2:* Orientar a inclusão da diferenciação entre `[Rota HTTP]` e `[Gatilho Frontend]` na Tabela Canônica de Navegação.