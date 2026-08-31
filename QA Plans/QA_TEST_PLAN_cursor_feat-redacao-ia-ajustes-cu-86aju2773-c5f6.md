# QA Test Plan: Ajustes no Modo Correção de Redação IA (ClickUp 86aju2773)

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-08-31 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Exams / Answers (Redação ENEM AI / Lize AI) |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5 estrelas) |

---

## 1. Summary of Changes (Resumo das Alterações)

- **Modo Correção de IA no Canvas:**
  - Novo botão flutuante com ícone de estrela à direita do canvas (`#ia`). Ao ser clicado, recolhe a coluna esquerda de navegação de alunos, ativa o modo de visualização *Texto digitalizado* e expande o painel *Lize AI* na sidebar direita para foco total na correção assistida.
  - Ao desativar, restaura a visualização do *Texto original* (imagem da folha), fecha popovers/seleções ativas e reexibe a barra de zoom/pan do OpenSeadragon.

- **Agrupamento de Sugestões por Competência (C1–C5):**
  - O painel Lize AI e a serialização backend (`_serialize_correction`) deixaram de agrupar por tipos de ação ("Desvios sugeridos", "Feedbacks", "Notas", "Rúbricas") e agora agrupam estritamente por competência ENEM (**C1, C2, C3, C4, C5** e opcionalmente "Outras").
  - Cada item filho dentro de uma competência exibe um chip identificador de tipo (`.lize-ai-kind-chip`), indicando se é *Desvio*, *Feedback*, *Nota* ou *Rúbrica*.
  - Cada cabeçalho de seção de competência possui badge com a contagem de itens pendentes daquela competência específica.

- **Layout e Refluxo de Linhas do OCR:**
  - Criação do serviço `enem_ai_ocr_layout.py` (`layout_transcription_lines`) que divide a transcrição em linhas numeradas estilo folha de redação.
  - Quebras de parágrafo (`\n`) viram linhas distintas e linhas longas refluem com largura máxima (72 caracteres) respeitando quebras de palavras, garantindo que o texto não ultrapasse a largura da folha sem gerar barras de rolagem horizontais.
  - Os marcadores de desvios (`.lize-ai-mark`) que cruzam quebras de linha refluídas são renderizados perfeitamente em múltiplos segmentos contínuos.

- **Revisão e Edição de OCR Diretamente no Canvas:**
  - Ao clicar em qualquer trecho grifado (`.lize-ai-mark`), um card de revisão flutuante (`.lize-ai-canvas-review`) se posiciona sobre o texto digitalizado.
  - O título do popover/card é interpolado corretamente com a sintaxe do Vue pai (`${getLizeAISuggestionTitle(...)}`), corrigindo a exibição de tags literais cruas `#{...}`.
  - Ações no canvas: **Aceitar** (marca como aceita e decrementa badge), **Recusar** (marca como recusada e remove o grifo), **Desfazer** (restaura status para pendente e reexibe o grifo) e **Editar OCR**.
  - Fluxo de **Editar OCR**: permite ao professor alterar o texto processado pela IA em um `textarea`. Ao salvar, o novo endpoint `PATCH /respostas/arquivos/<uuid:pk>/enem-ai-correction/transcription/` (`replace_transcription_span`) substitui o intervalo na transcrição e recalcula/desloca os *offsets* de todas as demais sugestões daquela correção, mantendo a consistência dos grifos.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- **IN SCOPE:**
  - Ativação e desativação do Modo Correção de IA via ícone de estrela flutuante no canvas da redação.
  - Agrupamento de sugestões da Lize AI por competência (C1 a C5) com chips de identificação de tipo.
  - Renderização da transcrição OCR em formato de folha de redação com linhas numeradas e refluxo de texto longo.
  - Interação de clique nos grifos do canvas para abrir o card de revisão contextual.
  - Decisões de Aceitar, Recusar e Desfazer realizadas diretamente pelo canvas ou pelo painel lateral.
  - Edição de trecho de OCR com persistência via PATCH e realinhamento de offsets de spans.
  - Interpolação correta do título do popover de revisão (`${...}`).
  - Cobertura de testes unitários para a API e serviços de layout e edição de transcrição.

- **OUT OF SCOPE:**
  - Disparo do job de IA a partir do zero ou integração com provedores externos reais (mock/stubs ou dados persistidos).
  - Correção de redações de modelos que não sejam ENEM (ex: Fuvest, Unicamp, modelos discursivos livres).
  - Aplicação automática de sugestões sem revisão e decisão do professor.
  - Mapeamento de spans do texto digitalizado para coordenadas de imagem no Annotorious (OpenSeadragon).
  - Modificações na API externa `corretor-redacao-api` ou alteração no app SPA do aluno (`/api/v3/`).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Lista de Redações da Turma | Turmas [verificar] -> Redações | `/provas/<exam_id>/redacoes/?school_class=<school_class_id>` | `exams:exam_essay_correction_list` |
| Tela de Correção de Redação | Clicar em um aluno na lista | `/provas/<exam_id>/correcao/?application_student=<uuid>&school_class=<uuid>` | `exams:exam_essay_correction` |
| Endpoint Correção IA | N/A (Chamada AJAX/Axios) | `POST/GET /respostas/arquivos/<pk>/enem-ai-correction/` | `answers:enem_ai_correction` |
| Endpoint Edição OCR | N/A (Chamada AJAX/Axios) | `PATCH /respostas/arquivos/<pk>/enem-ai-correction/transcription/` | `answers:enem_ai_correction_transcription` |
| Endpoint Decisão Sugestão | N/A (Chamada AJAX/Axios) | `POST /respostas/enem-ai-suggestions/<pk>/accept/` ou `/reject/` | `answers:enem_ai_suggestion_decision` |
| Endpoint Desfazer Sugestão | N/A (Chamada AJAX/Axios) | `POST /respostas/enem-ai-suggestions/<pk>/undo/` | `answers:enem_ai_suggestion_undo` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Execução dos Testes Automatizados
```bash
# Execução no ambiente com container de testes (Docker)
./scripts/tests/run-tests.sh fiscallizeon/answers/tests/test_enem_ai_correction_api.py fiscallizeon/answers/tests/test_enem_ai_ocr_layout.py fiscallizeon/answers/tests/test_enem_ai_transcription.py --no-tty

# Execução alternativa no venv local / Cloud Lab
source .venv/bin/activate && pytest fiscallizeon/answers/tests/test_enem_ai_correction_api.py fiscallizeon/answers/tests/test_enem_ai_ocr_layout.py fiscallizeon/answers/tests/test_enem_ai_transcription.py --reuse-db
```

### Persona Ativa
- **Papel:** Professor ou Coordenador (`role='teacher'` ou `role='coordinator'`) pertencente a um Cliente com `has_essay_system=True`.
- **Credenciais Cloud Lab:** `cloud.teacher@lize.local` (senha: `lize-cloud-lab`).

### Setup de Dados Determinísticos (Mixer Fixtures)
```python
from mixer.backend.django import mixer
from fiscallizeon.core.models import Client
from fiscallizeon.users.models import User
from fiscallizeon.exams.models import Exam, Question, ExamQuestion, TextCorrection
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.answers.models import FileAnswer, EssayAICorrection, EssayAISuggestion
from fiscallizeon.students.models import Student

# 1. Configuração do Tenant e Usuário
client = mixer.blend(Client, has_essay_system=True)
teacher = mixer.blend(User, role='teacher', client=client, is_active=True)

# 2. Template ENEM e Questão de Redação
text_correction = mixer.blend(TextCorrection, name="Competências ENEM", client=None)
question = mixer.blend(Question, client=client, is_essay=True, text_correction=text_correction)
exam = mixer.blend(Exam, client=client)
mixer.blend(ExamQuestion, exam=exam, question=question, order=1)

# 3. Aplicação e Aluno com Redação Anexada
school_class = mixer.blend(SchoolClass, client=client)
student = mixer.blend(Student, client=client)
application = mixer.blend(Application, exam=exam, client=client)
app_student = mixer.blend(ApplicationStudent, application=application, student=student, school_class=school_class)
file_answer = mixer.blend(FileAnswer, student_application=app_student, question=question, arquivo="redacoes/folha_exemplo.png")

# 4. Correção IA Pronta com Sugestões e Linhas de OCR
correction = mixer.blend(
    EssayAICorrection,
    file_answer=file_answer,
    status=EssayAICorrection.STATUS_READY,
    transcription="O Brasil enfrenta desafios complexos na educação basica nacional.\nPara superar esse cenario e preciso investir continuamente.",
    total_score=880,
)

# Sugestão de desvio (C1)
mixer.blend(
    EssayAISuggestion,
    correction=correction,
    competency="c1",
    kind="deviation",
    status=EssayAISuggestion.STATUS_PENDING,
    payload={
        "start": 44,
        "end": 50,
        "excerpt": "basica",
        "label": "Acentuação gráfica (básica)",
        "match_status": "corrected"
    }
)

# Sugestão de feedback (C2)
mixer.blend(
    EssayAISuggestion,
    correction=correction,
    competency="c2",
    kind="feedback",
    status=EssayAISuggestion.STATUS_PENDING,
    payload={"feedback": "Excelente repertório sociocultural produtivo."}
)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona Ativa:** Professor Corretor ou Coordenador com acesso ao sistema de redações.

### 5.1 Modo Correção de IA [Automatizável ✅]

#### Cenário 1 — Entrar no Modo Correção de IA
- [x] Acessar a tela de correção de uma redação ENEM que possua status de IA pronto.
- [x] Localizar o ícone de estrela flutuante no canto inferior direito do canvas de correção.
- [x] Clicar no ícone de estrela para ativar o Modo Correção de IA.
- [x] Confirmar que o ícone de estrela fica destacado com fundo alaranjado.
- [x] Confirmar que a visualização central do canvas alterna automaticamente para o Texto Digitalizado.
- [x] Confirmar que a barra lateral esquerda com a lista de alunos encolhe para dar mais espaço à correção.
- [x] Confirmar que o painel Lize AI permanece aberto e acessível na barra lateral direita.
- [x] Confirmar que nenhum erro de JavaScript ou Vue aparece no console do navegador.

#### Cenário 2 — Sair do Modo Correção de IA
- [x] Estando com o Modo Correção de IA ativo, clicar novamente no ícone de estrela flutuante.
- [x] Confirmar que a visualização central retorna para o Texto Original (imagem da folha).
- [x] Confirmar que o card de revisão ou popovers abertos sobre o texto são fechados.
- [x] Confirmar que a barra de ferramentas de zoom e centralização da imagem reaparece no canto direito.
- [x] Confirmar que a barra lateral esquerda retorna à largura padrão.

---

### 5.2 Agrupamento por Competências C1–C5 [Automatizável ✅]

#### Cenário 3 — Estrutura de Seções C1 a C5
- [x] Expandir o painel Lize AI na barra lateral direita (aba Corrigir).
- [x] Inspecionar os cabeçalhos das seções disponíveis no painel.
- [x] Confirmar que as seções principais são nomeadas por competência (C1, C2, C3, C4, C5).
- [x] Confirmar que não existem mais seções principais separadas por tipo como "Desvios sugeridos", "Feedbacks" ou "Rúbricas".
- [x] Confirmar que cada cabeçalho de competência exibe um badge com o número exato de itens pendentes de decisão.
- [x] Confirmar que competências sem itens exibem a mensagem "Nenhum item nesta seção."

#### Cenário 4 — Identificação do Tipo de Sugestão via Chips
- [x] Expandir uma competência que contenha mais de um item sugerido (ex: Desvio e Feedback).
- [x] Confirmar que cada linha de sugestão exibe um chip legível com o tipo correspondente (Desvio, Feedback, Nota ou Rúbrica).
- [x] Confirmar que os botões de Aceitar (ícone de check) e Recusar (ícone de X) na linha da sugestão continuam funcionais.
- [x] Confirmar que o ponto colorido (dot) ao lado de cada item reflete a cor oficial da respectiva competência.

---

### 5.3 Layout da Folha OCR e Refluxo de Linhas [Automatizável ✅]

#### Cenário 5 — Linhas Numeradas e Quebras de Parágrafo
- [x] Ativar o Texto Digitalizado ou entrar no Modo Correção de IA.
- [x] Observar a formatação da folha de texto digitalizado no canvas.
- [x] Confirmar que cada linha de texto possui uma numeração sequencial à esquerda (1, 2, 3...).
- [ ] Confirmar que as quebras de linha da transcrição geram linhas separadas numeradas, preservando o ritmo da folha de redação.
- [ ] Confirmar que nenhum caractere de controle (`\n` literal) é visível no texto.

#### Cenário 6 — Refluxo de Linhas Longas sem Barra Horizontal
- [ ] Inspecionar uma redação com parágrafos longos contínuos.
- [ ] Confirmar que linhas de texto longas refluem naturalmente para a linha seguinte respeitando o limite de largura.
- [ ] Confirmar que o painel de texto digitalizado não apresenta barra de rolagem horizontal indesejada.
- [ ] Confirmar que trechos com grifos de desvio que ultrapassam a quebra de linha visual continuam destacados em ambas as linhas refluídas.

---

### 5.4 Revisão e Ações Diretamente no Canvas [Automatizável ✅]

#### Cenário 7 — Aceitar e Recusar Desvio pelo Canvas
- [x] No texto digitalizado, clicar sobre uma palavra ou trecho grifado em laranja.
- [x] Confirmar que um card de revisão flutuante abre posicionado logo abaixo do trecho selecionado.
- [x] Confirmar que o card exibe as opções Aceitar, Recusar e Editar OCR.
- [x] Clicar em "Aceitar" no card.
- [x] Confirmar que o item é marcado como aceito no painel lateral, o badge de pendências decrementa e o grifo permanece visível no texto.
- [x] Clicar em outro trecho grifado e selecionar "Recusar".
- [x] Confirmar que o item é marcado como recusado e o grifo laranja desaparece imediatamente do texto digitalizado.

#### Cenário 8 — Edição do Texto do OCR e Persistência
- [x] Clicar em um trecho grifado com indicação de texto processado do OCR.
- [x] Clicar no botão "Editar OCR" no card de revisão.
- [x] Confirmar que uma caixa de texto editável surge com o conteúdo atual do trecho selecionado.
- [x] Alterar o texto e clicar em "Salvar".
- [x] Confirmar que o texto da folha digitalizada atualiza imediatamente com a nova grafia.
- [x] Recarregar a página (F5) e alternar novamente para o Texto Digitalizado.
- [x] Confirmar que a edição do texto persiste no banco de dados.
- [x] Confirmar que outros grifos posteriores no texto permanecem nas posições corretas sem deslocamento incorreto.

#### Cenário 9 — Título do Card de Revisão sem Tags Cruas
- [x] Clicar em qualquer trecho grifado no texto digitalizado para abrir o card de revisão.
- [x] Ler atentamente a primeira linha do cabeçalho do card.
- [x] Confirmar que o título exibe o formato limpo `Lize AI — <Nome da Sugestão>` (ex: `Lize AI — Acentuação gráfica`).
- [x] Confirmar que não aparece nenhuma sintaxe crua de template como `#{getLizeAISuggestionTitle(...)}` ou `#{...}`.

#### Cenário 10 — Desfazer Decisão pelo Canvas e pelo Painel
- [x] Clicar em um item previamente aceito ou selecionar a opção no painel lateral.
- [x] Clicar no botão "Desfazer".
- [x] Confirmar que o item retorna ao estado de pendente.
- [x] Se o item havia sido recusado, confirmar que o grifo laranja reaparece no texto digitalizado.
- [x] Confirmar que o badge de itens pendentes no painel lateral é incrementado novamente.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **Comparação de Layout do Painel Lateral:**
  - Tirar screenshot do painel Lize AI aberto na aba *Corrigir*.
  - Validar hierarquia visual das seções C1 a C5, badges circulares de contagem e chips de tipo arredondados.
- [ ] **Comparação do Card de Revisão no Canvas:**
  - Tirar screenshot do card flutuante `.lize-ai-canvas-review` aberto sobre o texto digitalizado.
  - Verificar espaçamento, bordas arredondadas (10px), sombra suave e tipografia dos botões Aceitar (verde `#12B76A`), Recusar e Editar OCR.
- [ ] **Verificação de Responsividade e Refluxo:**
  - Redimensionar a janela do navegador e verificar se o texto digitalizado reflui adequadamente em telas de diferentes larguras sem estourar o container.
- [ ] **Destaque do Ícone de Modo IA:**
  - Confirmar que o botão flutuante `#ia` possui estados visuais distintos: branco com ícone cinza quando inativo, e fundo amarelo-claro com ícone laranja (`#FF8F3D`) e borda ativa quando ligado.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!BUG]
> **[UX/UI / Backend Logic] Numeração e Quebras de Linha do OCR Divergindo da Folha Física**
> - **Contexto/Causa Raiz:** O algoritmo de refluxo em `enem_ai_ocr_layout.py` (`ENEM_PAGE_LINE_WIDTH = 72`) e quebras de parágrafo da API (`\n\n`) dividem linhas da transcrição em múltiplas linhas visuais e inserem linhas em branco extras, fazendo com que a numeração do texto digitalizado não corresponda às linhas reais escritas pelo aluno na folha física.
> - **Comportamento Esperado:** `(conforme escopo acordado com desenvolvimento)` A quebra e a numeração das linhas na folha digitalizada devem obedecer fielmente ao ritmo e às linhas físicas da folha de redação original.
> - **Status / Encaminhamento:** Alinhado com o desenvolvedor responsável e repassado para ajuste no algoritmo de layout da transcrição.

> [!WARNING]
> **[UX/UI] Interpolação de Delimitadores no Vue Monolítico**
> - **Contexto/Causa Raiz:** O template pai utiliza delimitadores customizados `${ ... }` para interpolação de dados no Vue, enquanto componentes filhos usam `#{ ... }`. A chamada no canvas utilizava `#{...}` no HTML pai, exibindo o texto cru da função.
> - **Comportamento Esperado:** `(conforme OpenSpec: spec.md / commits 30dd409e5)` O título deve exibir o nome formatado da sugestão.
> - **Solução Aplicada:** Corrigido no commit `30dd409e5` para `${getLizeAISuggestionTitle(lizeAI.ui.selectedSuggestion)}`.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **[Feature Request] Mapeamento Bidirecional OCR ↔ Imagem Original**
> - Futuramente, ao clicar em um trecho no texto digitalizado, posicionar automaticamente a lente de zoom do OpenSeadragon sobre a região correspondente da imagem manuscrita.

> [!NOTE]
> **[Refactoring] Componentização da Folha Digitalizada**
> - Extrair o renderizador de texto digitalizado e o card de revisão para um componente isolado do `django-components` / Vue SFC para reduzir o tamanho de `exam_essay_correction.html`.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.
🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_essay_correction.md)**

### Automation Snippet (Python / Playwright + Mixer Data Setup)

```python
import pytest
from playwright.sync_api import Page, expect
from mixer.backend.django import mixer
from fiscallizeon.core.models import Client
from fiscallizeon.users.models import User
from fiscallizeon.exams.models import Exam, Question, ExamQuestion, TextCorrection
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.answers.models import FileAnswer, EssayAICorrection, EssayAISuggestion
from fiscallizeon.students.models import Student

@pytest.mark.django_db(databases="__all__")
def test_essay_correction_ai_mode_and_canvas_review(page: Page, live_server):
    # 1. Setup Backend via Mixer
    client = mixer.blend(Client, has_essay_system=True)
    teacher = mixer.blend(User, role='teacher', client=client, is_active=True, is_superuser=True)
    
    text_correction = mixer.blend(TextCorrection, name="Competências ENEM", client=None)
    question = mixer.blend(Question, client=client, is_essay=True, text_correction=text_correction)
    exam = mixer.blend(Exam, client=client)
    mixer.blend(ExamQuestion, exam=exam, question=question, order=1)
    
    school_class = mixer.blend(SchoolClass, client=client)
    student = mixer.blend(Student, client=client, name="Aluno Teste")
    application = mixer.blend(Application, exam=exam, client=client)
    app_student = mixer.blend(ApplicationStudent, application=application, student=student, school_class=school_class)
    file_answer = mixer.blend(FileAnswer, student_application=app_student, question=question, arquivo="redacao.png")
    
    correction = mixer.blend(
        EssayAICorrection,
        file_answer=file_answer,
        status=EssayAICorrection.STATUS_READY,
        transcription="O Brasil precisa valorizar a educacao de base.",
        total_score=920,
    )
    suggestion = mixer.blend(
        EssayAISuggestion,
        correction=correction,
        competency="c1",
        kind="deviation",
        status=EssayAISuggestion.STATUS_PENDING,
        payload={"start": 27, "end": 35, "excerpt": "educacao", "label": "Acentuação (educação)", "match_status": "corrected"}
    )
    
    # 2. Autenticação e Navegação
    page.goto(f"{live_server.url}/conta/login/")
    # ... autenticar usuário professor ...
    
    url = f"{live_server.url}/provas/{exam.id}/correcao/?application_student={app_student.id}&school_class={school_class.id}"
    page.goto(url)
    
    # 3. Interação com o Modo Correção de IA
    star_btn = page.locator("#ia")
    expect(star_btn).to_be_visible()
    star_btn.click()
    expect(star_btn).to_have_class(/activated/)
    
    # 4. Validação do Layout OCR
    expect(page.locator(".ocr-page-line")).to_be_visible()
    expect(page.locator(".ocr-line-num").first).to_have_text("1")
    
    # 5. Clique no Highlight e Ação de Aceite no Canvas
    mark = page.locator(f'.lize-ai-mark[data-suggestion-id="{suggestion.id}"]')
    expect(mark).to_be_visible()
    mark.click()
    
    review_card = page.locator(".lize-ai-canvas-review")
    expect(review_card).to_be_visible()
    expect(review_card.locator(".lize-ai-canvas-review-title")).to_contain_text("Lize AI — Acentuação (educação)")
    
    # Aceitar sugestão pelo canvas
    review_card.locator("button.accept").click()
    expect(mark).to_have_class(/is-accepted/)
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante os testes:**
  - [ ] *(Aguardando execução do QA: registrar se houve demora no tempo de resposta do Celery ou no carregamento inicial das imagens).*
- **Interações e idas-e-vindas com desenvolvimento:**
  - [ ] *(Ajuste de interpolação do título do card no Vue pai realizado e validado com sucesso).*
- **Oportunidades de melhoria no fluxo de desenvolvimento/QA:**
  - [ ] *(Reforçar cobertura automatizada via Playwright para telas que utilizam múltiplos delimitadores de template).*

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias:
1. Incluir seção explícita para validação de endpoints REST auxiliares (PATCH/DELETE) utilizados diretamente por componentes de canvas.
2. Mapear nos metadados se a tela possui dependência de workers assíncronos (Celery/Redis) para alertar o QA na preparação do ambiente de teste.
-->
