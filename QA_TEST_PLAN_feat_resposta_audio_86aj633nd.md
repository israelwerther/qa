## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-01 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Questions / Exams / Student Test Execution / Corrections |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ |
| **Branch Backend (lizeedu):** | `feat/resposta-audio-86aj633nd` |
| **Branch Student (lize-student):** | `feat/resposta-audio-86aj633nd` |
| **Card ClickUp:** | [86aj633nd](https://app.clickup.com/t/86aj633nd) |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend (`lizeedu`)
- **Modelos e Migrações:**
  - Adicionado campo booleano `accepts_audio_response` (default `False`) em `Question` e refletido em `HistoricalQuestion` via migration `fiscallizeon/questions/migrations/0055_question_accepts_audio_response_and_more.py`.
- **Validação de Uploads (`answers`):**
  - Implementado serviço `validate_student_file_answer` em [file_answer_upload.py](file:///home/israel/Workspace/lizeedu/fiscallizeon/answers/services/file_answer_upload.py):
    - Se `accepts_audio_response=True`: aceita estritamente arquivos de áudio (`audio/webm`, `audio/mp3`, `audio/mpeg`, `audio/mp4`, `audio/m4a`, `audio/ogg`, `audio/wav`, `audio/aac`) de até 20 MB. Rejeita imagens.
    - Se `accepts_audio_response=False`: mantém comportamento legado de aceitar apenas imagens (`image/png`, `image/jpeg`, `image/pjpeg`, `image/gif`, `image/webp`) de até 20 MB. Rejeita áudios.
- **API v3 do Aluno (`app/students`):**
  - Exposição de `accepts_audio_response` no serializer `SimpleQuestionSerializer` (utilizado pelo endpoint `take_test`).
  - Integração do validador no endpoint `POST /app/applications/{id}/create_answer/` com `category=file`.
- **Caderno Redesign (`questions`):**
  - Inclusão do toggle `accepts_audio_response` em [question_edit_tab_questao.html](file:///home/israel/Workspace/lizeedu/fiscallizeon/questions/components/question_edit_tab_questao/question_edit_tab_questao.html), visível condicionalmente quando a categoria selecionada for "Arquivo anexado" (`category === 2`).
  - Sincronização do estado reativo no Alpine.js em [question_edit_form_question_tab.js](file:///home/israel/Workspace/lizeedu/fiscallizeon/questions/components/question_edit_shell/question_edit_form_question_tab.js) (desativa e oculta a flag se a categoria for alterada para objetiva/discursiva).
- **Correção de Redações/Arquivos (`exams`):**
  - No template [exam_essay_correction.html](file:///home/israel/Workspace/lizeedu/fiscallizeon/exams/templates/dashboard/exams/exam_essay_correction.html), identificação automática de extensões de áudio (`.webm`, `.mp3`, `.ogg`, `.wav`, etc.).
  - Quando a resposta for um áudio, o visualizador OpenSeadragon/Annotorious e o painel de OCR/Lize AI são suprimidos e substituídos por um player nativo HTML5 `<audio controls>`, mantendo o fluxo de atribuição de notas e feedbacks.

### Frontend Aluno (`lize-student`)
- **Estratégia de Questão com Áudio:**
  - Novo componente `AudioAnswerQuestion` em `src/components/test-execution/question-strategies/audio-answer-question.tsx`, renderizado na tela de prova online quando `acceptsAudioResponse=True`.
  - Suporte à gravação in-browser via `MediaRecorder` com tempo limite automático de 5 minutos (`MAX_RECORDING_MS = 300000`).
  - Fluxo de gravação com preview (ouvir antes de enviar), ação de regravar (descarte seguro de blob) e envio ao backend.
  - Alternativa de upload direto de arquivo de áudio (`input[type="file"][accept="audio/*"]`).
- **Tela de Resultados e Revisão:**
  - Em `src/components/exam-result/question-review-sheet.tsx`, adicionado player `<audio controls>` para reprodução da resposta gravada pelo estudante na aba **"Sua resposta"**.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- **Dentro do Escopo:**
  - Criação e edição de questões do tipo "Arquivo anexado" com o switch "Resposta em áudio (prova online)".
  - Realização de prova online no app do aluno (`lize-student`), permitindo gravação via microfone ou anexo de arquivo de áudio.
  - Validação rigorosa de tipo MIME e tamanho máximo (20 MB) no backend.
  - Correção da resposta pelo professor na interface web (`lizeedu`), permitindo ouvir o áudio inline, lançar nota e feedback.
  - Visualização da resposta em áudio no espelho/revisão de prova do aluno após a liberação do resultado.
  - Não regressão em questões do tipo "Arquivo anexado" sem a flag de áudio (devem continuar aceitando somente imagens).

- **Fora do Escopo:**
  - Transcrição automática de áudio para texto via IA (Speech-to-Text).
  - Marcação de anotações com comentários vinculados a timestamps específicos do áudio.
  - Suporte a áudio em provas presenciais via gabarito OMR ou folhas de resposta impressas (o recurso é exclusivo de provas/listas digitais).
  - Criação de nova categoria de questão (`QuestionCategory`), mantendo a categoria unificada `Question.FILE`.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django / Rota SPA | View name / Componente |
|---|---|---|---|
| Cadastro de Questão (Redesign) | Questões ➔ Cadastrar Questão | `/questoes/cadastrar/?v=redesign` | `questions:questions_create` |
| Edição de Questão (Caderno) | Ações ➔ Editar (versão nova) | `/questoes/<uuid>/editar/?v=redesign` | `questions:questions_update` |
| Cadastrar Aplicação | Aplicações ➔ Cadastrar | `/aplicacoes/cadastrar/?category=online` | `applications:applications_create` |
| Prova Online (Aluno) | Minhas Provas ➔ Iniciar Prova | `/provas/<application_id>` | `lize-student: src/routes/provas.$id.tsx` |
| Correção de Redações/Arquivos | Instrumentos ➔ Visualizar ➔ Redações/Arquivos | `/provas/<exam_id>/correcao/?application_student=<id>` | `exams:exam_essay_correction` |
| Revisão de Prova (Aluno) | Minhas Provas ➔ Ver Resultados | `/painel/minhas-provas/<application_id>` | `lize-student: src/routes/_app/painel/minhas-provas.$id.tsx` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Testes Automatizados no Backend (`lizeedu`)
Execute a suíte focada na funcionalidade:
```bash
./venv/bin/pytest fiscallizeon/questions/tests/test_question_edit_redesign.py \
  fiscallizeon/answers/tests/test_file_answer_upload_validation.py \
  fiscallizeon/app/students/tests/test_create_answer_file_audio.py \
  fiscallizeon/app/students/tests/test_take_test_exam_question_serializer.py --reuse-db
```

### Testes Automatizados no Frontend (`lize-student`)
Execute os testes unitários da biblioteca de validação de mídia:
```bash
cd ../lize-student && bun test src/lib/file-answer-media.test.ts
```

### Setup de Dados via Mixer (Python Shell)
Para simular rapidamente o ecossistema completo de teste com uma questão de resposta em áudio:
```python
from mixer.backend.django import mixer
from fiscallizeon.clients.models import Client, Unity, SchoolCoordination
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.subjects.models import Subject
from fiscallizeon.questions.models import Question
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.students.models import Student
from fiscallizeon.users.models import User

# 1. Configuração do Cliente e Coordenação
client = Client.objects.filter(name__icontains="Rede Decisão").first() or Client.objects.first()
unity = client.unities.first()
coordination = unity.coordinations.first()
grade = Grade.objects.first()
subject = Subject.objects.first()

# 2. Criar Questão de Arquivo com Flag de Áudio
q_audio = mixer.blend(
    Question,
    client=client,
    category=Question.FILE,
    accepts_audio_response=True,
    enunciation="<p><strong>Avaliação de Leitura Oral:</strong> Grave um áudio de até 5 minutos lendo o texto proposto com clareza e entonação.</p>"
)

# 3. Criar Questão de Arquivo sem Flag (Para Teste de Regressão de Imagem)
q_image = mixer.blend(
    Question,
    client=client,
    category=Question.FILE,
    accepts_audio_response=False,
    enunciation="<p><strong>Envio de Resolução:</strong> Anexe uma foto legível da sua folha de cálculos.</p>"
)

# 4. Criar Caderno e Associar Questões
exam = mixer.blend(Exam, client=client, name="[QA] Simulado com Resposta em Áudio")
mixer.blend(ExamQuestion, exam=exam, question=q_audio, order=1)
mixer.blend(ExamQuestion, exam=exam, question=q_image, order=2)

# 5. Criar Aplicação Online
application = mixer.blend(
    Application,
    exam=exam,
    client=client,
    category=Application.ONLINE,
    name="[QA] Aplicação Online - Áudio"
)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Configuração de Caderno e Questão (Portal LizeEdu) [Automatizável ✅]

#### Cenário 1 — Criação de Questão com Resposta em Áudio no Redesign
**Ação humana:**
- [x] Acessar o sistema com a **Persona Coordenação / Professor**.
- [x] Navegar para a tela de cadastro de questão: `http://localhost:8000/questoes/cadastrar/?v=redesign`.
- [x] No seletor de tipo de questão, selecionar a opção `"**Arquivo anexado**"` (ícone de anexo/clipe).
- [x] Observar que aparece o container de configuração com o switch `"**Resposta em áudio (prova online)**"`.
- [x] Verificar o texto descritivo: `"Quando ativo, o aluno grava ou anexa áudio no app. Com a opção desligada, permanece o envio de imagem."`.
- [x] Ativar o switch `"**Resposta em áudio (prova online)**"`.
- [ ] Preencher o enunciado `"Grave a leitura do texto em áudio"`, selecionar disciplina/série e clicar no botão `"**Salvar questão**"` (botão laranja no rodapé).
- [ ] Confirmar que a questão foi salva com sucesso e que a flag `accepts_audio_response` permaneceu `True`.

**Referência técnica (para automação):**
- URL: `/questoes/cadastrar/?v=redesign`
- Seletor da categoria Arquivo: `input[name="category"][value="2"]` ou opção correspondente no card
- Seletor do switch: `#accepts_audio_response`
- Estado esperado: `acceptsAudioResponse === true` no Alpine.js e campo oculto `<input name="accepts_audio_response" value="true">`
- Fixture: `mixer.blend(Question, category=Question.FILE, accepts_audio_response=True)`

#### Cenário 2 — Comportamento Reativo ao Alterar Categoria
**Ação humana:**
- [ ] Na mesma tela de cadastro ou edição de questão, com `"**Arquivo anexado**"` selecionado e o switch `"**Resposta em áudio (prova online)**"` ativado.
- [ ] Mudar a categoria da questão para `"**Múltipla escolha**"` ou `"**Discursiva**"`.
- [ ] Verificar que o bloco do switch de áudio desaparece imediatamente da interface.
- [ ] Voltar a categoria para `"**Arquivo anexado**"`.
- [ ] Confirmar que o switch foi resetado para o estado desligado (evitando que a flag permaneça ativa acidentalmente).

**Referência técnica (para automação):**
- URL: `/questoes/cadastrar/?v=redesign`
- Seletor: `div[x-show="category === 2"]`
- Estado esperado: `x-show` falso, `acceptsAudioResponse` redefinido para `false` no state do Alpine.

---

### 5.2 Execução da Prova no App do Aluno (`lize-student`) [Apenas Manual 👁]

#### Cenário 3 — Gravação de Áudio In-Browser com Preview e Regravação
**Ação humana:**
- [ ] Efetuar login no app do aluno (`http://localhost:5173` ou porta de desenvolvimento) com a **Persona Aluno** (ex: `cloud.student@lize.local`, senha `123456`).
- [ ] Iniciar a prova online contendo a questão de resposta em áudio.
- [ ] Navegar até a questão de áudio.
- [ ] Confirmar que a interface exibe o ícone de microfone e o texto explicativo: `"Grave sua resposta em áudio (até 5 min) ou anexe um arquivo."`.
- [ ] Confirmar que são exibidos os botões `"**Gravar**"` (com ícone de microfone) e `"**Anexar áudio**"` (com ícone de upload).
- [ ] Clicar no botão `"**Gravar**"`. O navegador solicitará permissão de microfone (conceda a permissão).
- [ ] Observar que o botão muda para `"**Encerrar gravação**"` com destaque em vermelho.
- [ ] Falar durante alguns segundos (ex: 5 a 10 segundos) e clicar em `"**Encerrar gravação**"`.
- [ ] Confirmar que um player `<audio controls>` surge na tela para preview antes do envio, acompanhado dos botões `"**Regravar**"` e `"**Enviar áudio**"`.
- [ ] Reproduzir o áudio no player para validar que a voz foi capturada com clareza.
- [ ] Clicar no botão `"**Regravar**"`.
- [ ] Confirmar que o preview é descartado e a tela retorna ao estado inicial com o botão `"**Gravar**"`.
- [ ] Iniciar uma nova gravação de teste e clicar em `"**Enviar áudio**"`.
- [ ] Confirmar que é exibido o indicador `"Enviando..."` e em seguida a mensagem de confirmação `"**Áudio enviado com sucesso!**"` em verde.

**Referência técnica (para automação):**
- URL: `/provas/<application_id>`
- Seletor Gravar: `button:has-text("Gravar")`
- Seletor Parar: `button:has-text("Encerrar gravação")`
- Seletor Preview: `audio[src^="blob:"]`
- Seletor Botão Enviar: `button:has-text("Enviar áudio")`
- Estado esperado: Mensagem `p:has-text("Áudio enviado com sucesso!")` visível

#### Cenário 4 — Envio de Arquivo Externo de Áudio e Rejeição de Imagem
**Ação humana:**
- [ ] Na mesma questão de áudio, clicar no botão `"**Anexar áudio**"`.
- [ ] Na janela de seleção de arquivos, escolher um arquivo de áudio válido (ex: `.mp3`, `.wav` ou `.m4a` com menos de 20 MB).
- [ ] Verificar que o player de preview é carregado com o arquivo selecionado.
- [ ] Clicar em `"**Enviar áudio**"` e confirmar a mensagem `"**Áudio enviado com sucesso!**"`.
- [ ] **Teste de Validação Negativa:** Tentar forçar o upload de um arquivo de imagem (ex: `.png` ou `.jpg`) via API ou seletor de arquivos.
- [ ] Confirmar que o sistema bloqueia o envio com erro indicando que apenas arquivos de áudio são permitidos para esta questão.

**Referência técnica (para automação):**
- URL: `/provas/<application_id>`
- Seletor Anexar: `button:has-text("Anexar áudio")`
- Input oculto: `input[type="file"][accept="audio/*"]`
- API Intercept: `POST /api/v3/applications/<id>/create_answer/`
- Resposta esperada para imagem com áudio ativo: HTTP 400 com payload `{"file": ["..."]}`

---

### 5.3 Correção pelo Professor no Portal LizeEdu [Automatizável ✅]

#### Cenário 5 — Reprodução de Áudio Inline na Tela de Correção
**Ação humana:**
- [ ] Finalizar a realização da prova com o aluno.
- [ ] Acessar o portal LizeEdu com a **Persona Professor / Corretor** (`http://localhost:8000`).
- [ ] Navegar até a tela de correção de redações/arquivos da prova: `/provas/<exam_id>/correcao/?application_student=<id>`.
- [ ] Selecionar a questão de resposta em áudio respondida pelo aluno.
- [ ] Verificar que a área central (onde normalmente ficaria a folha de redação/imagem) renderiza um player HTML5 nativo `<audio controls>`.
- [ ] Confirmar que o painel de anotação de imagem (OpenSeadragon / Annotorious) e o painel OCR / Lize AI **não** são exibidos.
- [ ] Dar play no áudio e ouvir a gravação enviada pelo aluno.
- [ ] No painel lateral direito de avaliação, preencher a nota (ex: `8.5`) e digitar um comentário de feedback pedagógico.
- [ ] Clicar no botão `"**Salvar correção**"` (ou equivalente da tela).
- [ ] Confirmar que a nota e o comentário foram persistidos com sucesso.

**Referência técnica (para automação):**
- URL: `/provas/<exam_id>/correcao/?application_student=<app_student_id>`
- Seletor do Player: `.essay-viewer-body .overlay-content audio[controls]`
- Seletor do Campo de Nota: `input[name="grade"]` ou input correspondente da grade
- Estado esperado: `audioAnswerUrl` populado no Vue.js, `controls.loadingSeadragon === false`, player visível.

---

### 5.4 Visualização do Resultado pelo Aluno (`lize-student`) [Apenas Manual 👁]

#### Cenário 6 — Player de Áudio no Espelho de Resposta do Aluno
**Ação humana:**
- [ ] Acessar o sistema com a **Persona Aluno** após a liberação do resultado da aplicação.
- [ ] Navegar para a tela de detalhes da prova: `/painel/minhas-provas/<application_id>`.
- [ ] Clicar na questão de resposta em áudio para abrir o drawer/sheet de revisão (`QuestionReviewSheet`).
- [ ] Clicar na aba `"**Sua resposta**"`.
- [ ] Confirmar que a interface exibe o player `<audio controls>` permitindo que o aluno escute novamente o áudio que enviou.
- [ ] Clicar na aba `"**Questão**"` e conferir se o feedback e nota atribuídos pelo professor estão visíveis.

**Referência técnica (para automação):**
- URL: `/painel/minhas-provas/<application_id>`
- Seletor da Tab: `[role="tab"]:has-text("Sua resposta")`
- Seletor do Player: `.flex.items-center.justify-center.rounded-md audio[controls]`
- Estado esperado: Atributo `src` do elemento `audio` apontando para a URL do arquivo de áudio (`.webm`, `.mp3`, etc.).

---

### 5.5 Teste de Não-Regressão: Questão de Arquivo Tradicional (Imagem) [Automatizável ✅]

#### Cenário 7 — Questão FILE sem Flag de Áudio Mantém Envio Exclusivo de Imagem
**Ação humana:**
- [ ] Iniciar uma prova online contendo uma questão FILE com a flag `"**Resposta em áudio (prova online)**"` **desligada**.
- [ ] Na tela de realização da prova, verificar que o componente renderizado é o seletor tradicional de anexo de imagem (sem opções de microfone ou gravação).
- [ ] Anexar uma imagem válida (PNG/JPEG) e confirmar que o envio é realizado com sucesso.
- [ ] Tentar enviar um arquivo de áudio (`.mp3` ou `.webm`) para esta questão.
- [ ] Confirmar que a validação bloqueia o arquivo com mensagem de erro informando que o formato não é aceito.
- [ ] Na tela de correção do professor, confirmar que a imagem é exibida normalmente no visualizador OpenSeadragon com ferramentas de anotação ativas.

**Referência técnica (para automação):**
- URL: `/provas/<application_id>`
- Seletor: Input tradicional `input[type="file"][accept*="image"]`
- Teste backend: `fiscallizeon/answers/tests/test_file_answer_upload_validation.py`
- Teste API: `fiscallizeon/app/students/tests/test_create_answer_file_audio.py::TestCreateAnswerFileAudioValidation::test_upload_audio_to_non_audio_file_question_fails`

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] Comparar o switch `"**Resposta em áudio (prova online)**"` na aba "Questão" do redesign com o padrão de switches do Design System (`components/switch_toggle/`).
- [ ] Verificar se o estado de gravação no app do aluno destaca claramente o botão de encerramento (`variant="destructive"`, cor avermelhada) para evitar gravações acidentais contínuas.
- [ ] Validar a responsividade do componente `AudioAnswerQuestion` em resoluções mobile (375px) e desktop (1280px).
- [ ] Verificar se o player `<audio>` na tela de correção `exam_essay_correction.html` fica centralizado com largura máxima adequada (`max-width: 640px`) sem quebrar a proporção do painel.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Nenhum bug bloqueante identificado na execução inicial dos testes automatizados (`67 passed`). Registre aqui quaisquer divergências encontradas durante a validação manual.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Transcrição de Áudio (STT):** Para versões futuras, avaliar a integração de transcrição automática via Whisper/IA para que o professor possa ler o texto enquanto ouve o áudio, agilizando correções em larga escala.

> [!NOTE]
> **Feedback com Timestamp:** Permitir que o professor insira anotações pontuais vinculadas a segundos específicos do áudio (ex: "Pronúncia incorreta no minuto 01:23").

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
- 🔗 **[Ver Mapeamento de Tela: question_create_update_redesign.md](docs/tests/usability/question_create_update_redesign.md)** (Toggle de áudio)
- 🔗 **[Ver Mapeamento de Tela: exam_essay_correction.md](docs/tests/usability/exam_essay_correction.md)** (Player de áudio na correção)
- 🔗 **[Ver Mapeamento de Tela: audio_answer_question.md](docs/tests/usability/audio_answer_question.md)** (Componente React de gravação no SPA Aluno)

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Gargalos identificados:** Necessidade de sincronizar as duas branches (`feat/resposta-audio-86aj633nd`) simultaneamente nos repositórios `lizeedu` e `lize-student` para testes de ponta a ponta.
- **Pontos positivos:** A arquitetura manteve o isolamento de regras de upload dentro de `file_answer_upload.py` sem poluir views legadas, com 100% de cobertura nos testes unitários e de integração.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
<!-- Registrar aqui observações surgidas durante a validação desta feature -->
