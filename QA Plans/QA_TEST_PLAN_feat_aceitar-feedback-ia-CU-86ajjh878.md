# QA Test Plan — Aceitar Apenas Feedback da IA (Discursivas)

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-08 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Exams — Correção de Discursivas com IA |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ |

---

## 1. Summary of Changes (Resumo das Alterações)

- **Nova ação "Aprovar apenas o feedback"** no card de sugestão da IA em três templates de correção:
  - `exam_detail_new.html` (visão por aluno)
  - `exam_detail_enunciation_new.html` (visão por enunciado)
  - `exam_detail_v2.html` (template legado)
- **Função `setOnlyFeedback(suggestion)`** adicionada em dois arquivos JS:
  - `exam-detail-functions.js` (visão por aluno)
  - `exam-detail-enunciation-functions.js` (visão por enunciado)
- **Comportamento:** ao acionar, o texto do feedback da IA é copiado para o campo `teacher_feedback`, a nota permanece vazia e a questão segue pendente de correção.
- **Toast informativo:** exibe mensagem "Feedback inserido! Atribua a nota para concluir a questão."
- **Expansão automática** do colapso de comentário (`collapseTeacherComment`) para facilitar edição.
- **Testes automatizados** adicionados em `test_textual_answers.py`, `test_file_answers.py` e `test_exam_ai_feedback_templates.py`.

---

## 2. Scope Boundaries (Diferenças de Escopo)

**IN SCOPE:**
- Fluxo de correção de discursivas (Texto e Arquivo anexado) onde o professor recebe sugestão da IA e decide sobre ela.
- Ação "Aprovar apenas o feedback" nas visões por aluno e por enunciado.
- Manutenção do estado pendente quando feedback é aceito sem nota.
- Edibilidade do feedback aceito antes da gravação final.
- Preservação das ações existentes ("Aprovar a nota" e "Aprovar nota e feedback").
- Comportamento do aluno ao visualizar feedback após liberação do resultado.

**OUT OF SCOPE:**
- Correção automática em listas de exercício (IA atribui nota sozinha).
- Novos status, badges ou filtros na listagem de questões.
- Migrações ou alterações de banco de dados.
- Telemetria de aceitação parcial da IA.
- Alterações em endpoints de API existentes.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Listagem de provas | Instrumentos Avaliativos [verificar] | /exams/ | exams_list |
| Detalhe da prova (correção) | Prova → Correção [verificar] | /exams/<id>/ | exam_detail |
| Visão por aluno | Aba "Por aluno" [verificar] | /exams/<id>/ (tab) | exam_detail |
| Visão por enunciado | Aba "Por enunciado" [verificar] | /exams/<id>/ (tab) | exam_detail_enunciation |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comandos para rodar os testes automatizados

```bash
source venv/bin/activate
pytest fiscallizeon/answers/tests/test_textual_answers.py fiscallizeon/answers/tests/test_file_answers.py fiscallizeon/exams/tests/views/test_exam_ai_feedback_templates.py --reuse-db -v
```

### Persona

**Professor corretor** com permissão de correção de provas na aplicação.

### Fixture (Mixer)

```python
from mixer.backend.django import mixer
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.students.models import Student
from fiscallizeon.clients.models import Client
from fiscallizeon.answers.models import TextualAnswer, FileAnswer

exam = mixer.blend(Exam, is_abstract=True)
question = mixer.blend(Question, category=Question.TEXTUAL)  # ou Question.FILE
exam_question = mixer.blend(ExamQuestion, question=question, exam=exam, weight=1)
client = mixer.blend(Client)
student = mixer.blend(Student, client=client)
application = mixer.blend(Application, exam=exam)
application_student = mixer.blend(ApplicationStudent, student=student, application=application)

# Resposta textual com sugestão da IA
textual_answer = mixer.blend(
    TextualAnswer,
    student_application=application_student,
    question=question,
    exam_question=exam_question,
    ai_grade=Decimal("0.7"),
    ai_explanation="Explicação detalhada dos pontos atendidos.",
    teacher_grade=None,
    teacher_feedback=None,
)

# Resposta de arquivo com sugestão da IA
file_answer = mixer.blend(
    FileAnswer,
    student_application=application_student,
    question=question,
    exam_question=exam_question,
    ai_grade=Decimal("0.8"),
    ai_teacher_feedback="Excelente fundamentação teórica, mas faltou concluir a argumentação.",
    teacher_grade=None,
    teacher_feedback=None,
)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona ativo:** Professor corretor com permissão de correção de provas.

### 5.1 Visão por Aluno — Card de Sugestão da IA [Automatizável ✅]

#### Cenário 1 — Botão "Aprovar apenas o feedback" está presente

**Ação humana:**
- [x] Acesse a listagem de provas e abra uma prova com questões discursivas corrigidas por IA.
- [x] Navegue até a aba ou seção de correção por aluno.
- [x] Verifique se o card de sugestão da IA exibe o botão "**Aprovar apenas o feedback**" (botão com ícone de balão de mensagem, borda laranja, posicionado acima do botão "Aprovar nota e feedback").

**Referência técnica (para automação):**
- URL: `/exams/<id>/`
- Seletor: `button[title="Aprovar apenas o feedback"]`
- Estado esperado: botão visível com texto "Aprovar apenas o feedback"
- Fixture: prova com questão discursiva e resposta com sugestão da IA

#### Cenário 2 — Ao clicar, feedback é preenchido e nota permanece vazia

**Ação humana:**
- [x] Com a sugestão da IA visível, clique no botão "**Aprovar apenas o feedback**".
- [x] Verifique se o campo de feedback (textarea) é preenchido automaticamente com o texto sugerido pela IA.
- [x] Verifique se o campo de nota permanece vazio.
- [x] Verifique se um toast informativo é exibido: "Feedback inserido! Atribua a nota para concluir a questão."

**Referência técnica (para automação):**
- URL: `/exams/<id>/`
- Seletor: `button[title="Aprovar apenas o feedback"]`
- Estado esperado: textarea preenchido com feedback da IA, input de nota vazio, toast visível
- Fixture: `mixer.blend(TextualAnswer, ai_explanation="...", teacher_feedback=None)`

#### Cenário 3 — Questão permanece pendente após aceitar apenas feedback

**Ação humana:**
- [x] Após clicar em "Aprovar apenas o feedback", observe o status da questão.
- [x] Verifique se a questão continua sinalizada como **pendente de correção**.
- [x] Verifique se o total de questões corrigidas da aplicação do aluno não é incrementado.

**Referência técnica (para automação):**
- URL: `/exams/<id>/`
- Seletor: indicador de pendência (badge ou ícone)
- Estado esperado: questão marcada como pendente, contador de corrigidas inalterado
- Fixture: aplicação com questão sem nota

### 5.2 Visão por Aluno — Atribuição Posterior de Nota [Automatizável ✅]

#### Cenário 4 — Professor atribui nota após aceitar feedback

**Ação humana:**
- [x] Com o feedback já preenchido via "Aprovar apenas o feedback", digite uma nota no campo de nota.
- [x] Salve a correção.
- [x] Verifique se a questão é concluída com a nota atribuída pelo professor.
- [x] Verifique se o feedback preenchido é mantido.

**Referência técnica (para automação):**
- URL: `/exams/<id>/`
- Seletor: input de nota + botão salvar
- Estado esperado: questão corrigida, nota e feedback persistidos
- Fixture: resposta com feedback aceito e sem nota

#### Cenário 5 — Feedback aceito pode ser editado antes de salvar

**Ação humana:**
- [x] Após clicar em "Aprovar apenas o feedback", edite o texto no campo de feedback.
- [x] Atribua uma nota e salve.
- [x] Verifique se o texto editado é persistido (não o original da IA).

**Referência técnica (para automação):**
- URL: `/exams/<id>/`
- Seletor: textarea de feedback
- Estado esperado: texto editado persistido no banco
- Fixture: resposta com feedback da IA aceito

### 5.3 Visão por Enunciado — Card de Sugestão da IA [Automatizável ✅]

#### Cenário 6 — Botão presente na visão por enunciado

**Ação humana:**
- [x] Acesse a prova e navegue até a aba ou seção de correção por enunciado.
- [x] Verifique se o card de sugestão da IA exibe o botão "**Aprovar apenas o feedback**".

**Referência técnica (para automação):**
- URL: `/exams/<id>/` (visão por enunciado)
- Seletor: `button[title="Aprovar apenas o feedback"]`
- Estado esperado: botão visível
- Fixture: prova com questão discursiva e resposta com sugestão da IA

#### Cenário 7 — Feedback preenchido e nota vazia na visão por enunciado

**Ação humana:**
- [x] Clique no botão "**Aprovar apenas o feedback**" na visão por enunciado.
- [x] Verifique se o feedback é preenchido e a nota permanece vazia.
- [x] Verifique se o toast informativo é exibido.

**Referência técnica (para automação):**
- URL: `/exams/<id>/` (visão por enunciado)
- Seletor: `button[title="Aprovar apenas o feedback"]`
- Estado esperado: feedback preenchido, nota vazia, toast visível
- Fixture: resposta com sugestão da IA

### 5.4 Preservação de Comportamentos Existentes [Automatizável ✅]

#### Cenário 8 — Ação "Aprovar a nota" permanece inalterada

**Ação humana:**
- [x] Com a sugestão da IA visível, clique no botão "**Aprovar a nota**".
- [x] Verifique se a nota calculada pela IA é atribuída automaticamente.
- [x] Verifique se a questão é concluída.

**Referência técnica (para automação):**
- URL: `/exams/<id>/`
- Seletor: `button[title="Aprovar a nota"]`
- Estado esperado: nota atribuída, questão concluída
- Fixture: resposta com sugestão da IA

#### Cenário 9 — Ação "Aprovar nota e feedback" permanece inalterada

**Ação humana:**
- [x] Com a sugestão da IA visível, clique no botão "**Aprovar nota e feedback**".
- [x] Verifique se a nota e o feedback são atribuídos automaticamente.
- [x] Verifique se a questão é concluída.

**Referência técnica (para automação):**
- URL: `/exams/<id>/`
- Seletor: `button[title="Aprovar nota e feedback"]`
- Estado esperado: nota e feedback atribuídos, questão concluída
- Fixture: resposta com sugestão da IA

### 5.5 Visão do Aluno — Liberação de Resultado [Automatizável ✅]

#### Cenário 10 — Aluno visualiza feedback após liberação

**Ação humana:**
- [x] Como aluno, acesse a prova após a liberação do resultado.
- [x] Verifique se o feedback aceito da IA é exibido normalmente.
- [x] Verifique se o feedback é idêntico a qualquer outro feedback manual inserido por professores.

**Referência técnica (para automação):**
- URL: `/aplicacoes/<id>/` (visão do aluno)
- Seletor: área de feedback da questão
- Estado esperado: feedback visível e legível
- Fixture: prova com resultado liberado e feedback aceito da IA

### 5.6 Correção Manual — Fluxo Sem IA [Apenas Manual 👁]

#### Cenário 11 — Professor ignora sugestão e preenche manualmente

**Ação humana:**
- [x] Com a sugestão da IA visível, ignore os botões de aceite.
- [x] Digite manualmente a nota e o feedback.
- [x] Salve a correção.
- [x] Verifique se a questão é concluída corretamente.

**Referência técnica (para automação):**
- URL: `/exams/<id>/`
- Seletor: input de nota + textarea de feedback + botão salvar
- Estado esperado: questão corrigida com dados manuais
- Fixture: resposta sem sugestão da IA (ou com sugestão ignorada)

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] Capturar print da tela de correção por aluno com o card da IA e os três botões de ação.
- [ ] Capturar print da tela de correção por enunciado com o card da IA e os três botões de ação.
- [ ] Comparar o layout dos botões com o mockup de referência (`references/ai-suggestion-actions.html`).
- [ ] Verificar se o alinhamento e espaçamento dos botões está consistente.
- [ ] Verificar se o toast informativo é exibido corretamente.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Nenhum bug identificado até o momento. Esta seção será preenchida durante a execução dos testes.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> - Avaliar se a questão com feedback aceito e nota em aberto deveria receber sinalização própria na listagem de correção (hoje aparece como qualquer pendente).
> - Considerar telemetria para acompanhar quanto a sugestão da IA é aproveitada quando a nota é descartada.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django): `exam_detail_new.md`, `exam_detail_enunciation_new.md` e `exam_detail_v2.md`.
- 🔗 **[Ver Mapeamento de Tela — exam_detail_new](docs/tests/usability/exam_detail_new.md)**
- 🔗 **[Ver Mapeamento de Tela — exam_detail_enunciation_new](docs/tests/usability/exam_detail_enunciation_new.md)**
- 🔗 **[Ver Mapeamento de Tela — exam_detail_v2](docs/tests/usability/exam_detail_v2.md)**

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Qual foi o principal gargalo durante os testes?** (preencher após execução)
- **Houve muitos vai-e-vem com o desenvolvedor?** (preencher após execução)
- **Como o fluxo de desenvolvimento ou QA poderia ser melhorado?** (preencher após execução)

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
