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

## 5. Execution Test Script (Roteiro de Testes com Checkboxes)

### 5.1 Abertura e Carregamento do Preview `[Automatizável ✅]`
- [ ] **Ação humana:** Na página de edição de questões do caderno, clicar em "Importar via DOCX" e selecionar um arquivo `.docx` válido.
  - **Referência técnica (para automação):**
    - URL: `/provas/prova/<uuid:exam_teacher_subject_pk>/editar/`
    - Elemento DOM Trigger: `button:has-text("Importar via DOCX")`
    - Input de Arquivo: `input[type="file"][accept*=".docx"]`
    - Evento Disparado: `window.dispatchEvent(new CustomEvent('import-preview-open', { detail: { data: payload } }))`
    - Estado Esperado: O container `#import-preview` torna-se visível e `$store.importPreview.isOpen` fica `true`.

- [ ] **Ação humana:** Verificar o estado de carregamento enquanto o parser valida o documento.
  - **Referência técnica (para automação):**
    - Estado DOM: `div[x-show="$store.importPreview.isLoading"]` visível com texto "Validando questões...".

### 5.2 Validação da Sidebar e Navegação `[Automatizável ✅]`
- [ ] **Ação humana:** Conferir as estatísticas de questões na sidebar (total de questões, válidas, avisos, erros e barra de progresso).
  - **Referência técnica (para automação):**
    - Elementos DOM: Componente `sidebar_progress` exibindo percentual `$store.importPreview.progressPercent()`.
    - Resumo de contadores: `x-text="$store.importPreview.stats.total + ' Questões'"` e `x-text="$store.importPreview.stats.valid"`.

- [ ] **Ação humana:** Clicar na pill do número da questão na sidebar para navegar até a questão correspondente.
  - **Referência técnica (para automação):**
    - Seletor DOM: `nav button.tw-rounded-full:has-text("02")`
    - Comportamento: Rola suavemente até a questão com ID `#import-preview-question-1` (`$store.importPreview.goToQuestion(1)`).

### 5.3 Edição de Questões e Gabarito `[Automatizável ✅]`
- [ ] **Ação humana:** Em uma questão objetiva, alterar a opção marcada como correta clicando no radio button de outra alternativa.
  - **Referência técnica (para automação):**
    - Seletor DOM: `input[type="radio"][name^="correct_choice_"]`
    - Estado Esperado: `$store.importPreview.setCorrectChoice(question, choiceIndex)` atualiza a propriedade `is_correct` da alternativa e limpa erros de gabarito não preenchido.

- [ ] **Ação humana:** Clicar nos botões "Subir" e "Descer" no action rail da questão para alterar sua posição na lista.
  - **Referência técnica (para automação):**
    - Seletor DOM Subir: `button[title="Mover para cima"]`
    - Seletor DOM Descer: `button[title="Mover para baixo"]`
    - Estado Esperado: `$store.importPreview.moveQuestion(question, 'up')` troca as posições no array de questões e reordena os números visíveis.

### 5.4 Remoção de Questão `[Automatizável ✅]`
- [ ] **Ação humana:** Clicar no botão "Remover" de uma questão, visualizar o modal de confirmação e confirmar a remoção.
  - **Referência técnica (para automação):**
    - Seletor DOM Gatilho: `button[title="Remover questão"]`
    - Modal Nativo: `dialog[x-ref="importPreviewRemoveDialog"]` abre (`showModal()`).
    - Botão Confirmar Remoção: `button:has-text("Remover")` dentro do dialog.
    - Estado Esperado: A questão é removida do array `$store.importPreview.questions`, o total de questões e o número das questões subsequentes são atualizados imediatamente.

### 5.5 Validação de Bloqueio por Questões Inválidas `[Apenas Manual 👁]`
- [ ] **Ação humana:** Tentar importar um arquivo contendo questões com erro (ex.: questão objetiva sem alternativa marcada como correta) e verificar se a importação fica bloqueada.
  - **Referência técnica (para automação):**
    - Mensagem de Alerta: `Importação bloqueada — corrija ou remova as questões com erros.` visível na sidebar.
    - Botão Confirmar Importação: `button:has-text("Confirmar importação")` está no estado `disabled` (`!$store.importPreview.canConfirm()`).
    - Fonte do requisito: `(conforme OpenSpec: spec.md L.27-32)`.

### 5.6 Confirmar Importação e Cutover `[Automatizável ✅]`
- [ ] **Ação humana:** Com todas as questões válidas, clicar em "Confirmar importação", validar a caixa de diálogo e concluir o envio.
  - **Referência técnica (para automação):**
    - Seletor DOM: `button:has-text("Confirmar importação")`
    - Modal Nativo: `dialog[x-ref="importPreviewConfirmDialog"]` exibe "Deseja realmente importar X questões?".
    - Botão Confirmação Final: `button:has-text("Sim, importar")`
    - Evento Disparado: `window.dispatchEvent(new CustomEvent('import-preview-confirm', { detail: { questions, stats } }))`
    - Estado Esperado: O preview fullscreen é fechado e as questões são inseridas na página de elaboração do caderno.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **Captura de Tela — Layout Fullscreen:** Garantir que o preview ocupa toda a tela (`fullscreen_layout`), com header fixo, sidebar com `tw-w-[400px]` e área principal centralizada.
- [ ] **Comparação com Visualizar Prova:** Verificar se o card da questão (`import_preview_question_card`) segue a mesma tipografia, badges e estilos de borda (válida/aviso/erro) que o `exam_preview_question_card` de Visualizar Prova.
- [ ] **Comparação de Paridade:** Comparar lado a lado o novo preview em Alpine com o legado (`import_preview_modal.html`) para garantir que nenhuma informação ou controle essencial deixou de ser renderizado.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Nenhum bug crítico identificado até o momento durante a análise estática e estruturação do componente. Registre abaixo eventuais inconsistências encontradas na execução manual.

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