## 0. Metadata (Metadados de QA)

| Campo                         | Valor                                                                         |
| ----------------------------- | ----------------------------------------------------------------------------- |
| **Data:**                     | 2026-10-16                                                                    |
| **Natureza da Tarefa:**       | `[Business Feature]`                                                          |
| **Área da Feature:**          | OMR / Gabaritos (leitura de cartões)                                          |
| **Nível de Risco:**           | Alto                                                                          |
| **Qualidade da OpenSpec:**    | ⭐⭐⭐⭐⭐                                                                    |
| **Task ClickUp:**             | [Reprocessar leitura de um único cartão](https://app.clickup.com/t/86ak00150) |
| **Branch Backend (lizeedu):** | `feat/reprocessamento-individual-cartoes-86ak00150`                           |
| **Anexo de teste (ClickUp):** | `alfa-contraste.pdf` (escaneamento Colégio Alfa)                              |

> **Alinhamento shaping × entrega:** a task original pedia ação também na aba "**Erros de leitura**" (página a página). A OpenSpec e o código entregam **ação em massa na listagem de alunos** ("**Reprocessar folhas**" + modal de contraste / contraste inteligente). Validar o que foi implementado; o gap da aba de erros fica em OUT OF SCOPE / Spec Gap.

---

## 1. Summary of Changes (Resumo das Alterações)

### Problema (ClickUp)

Quando um cartão falha na leitura, a única releitura era "**Reprocessar**" o **upload inteiro**, sobrescrevendo respostas e correções manuais de todos os alunos. Na prática a operação digitava o cartão à mão.

### Backend / Celery

- Nova task orquestradora `reprocess_omr_student_sheet` em `fiscallizeon/omr/tasks/reprocessing/reprocess_omr_student_sheet.py`, fila `omr-import`.
- Fluxo: grava `gamma_option` no upload → resolve imagem (`scan_image` ou fallback do mesmo aluno) → QR / `omr_category` → chain `read_sheets_directory_fiscallize` + `handle_answers` (objetiva) ou `handle_answers_pas` (PAS).
- Discursiva / redação → `outcome=skipped`; QR ilegível → erro **sem** criar `OMRError`; **não** chama `finish_processing`.
- Suporte a `smart_read` (contraste inteligente) no POST e na page dict da leitura.
- Migration `0080_omrstudents_omr_category.py`: campo `omr_category` em `OMRStudents` (e histórico) — desvio da OpenSpec que previa “sem migração”.

### API (`/gabaritos/api/`)

- **POST** `/gabaritos/api/omr-students/<uuid>/reprocess-sheet/` → `202` `{ task_id, omr_student_id }`; body `gamma_option` + `smart_read`.
- **GET** `/gabaritos/api/omr-students/reprocess-sheet/status/?task_id=&omr_student_id=` (listas / vírgula) → `results` com status Celery + `outcome`.
- Permissões: `COORDINATION` / `TEACHER` + `IsOMRStudentUploadOwner`. `task_id` **não** persistido.

### Frontend (Vue + Bootstrap, template existente)

- Template `omr_upload_detail_new.html`: botão "**Reprocessar folhas**" (`#menu-item-reprocess-sheets`) na barra de seleção em massa.
- Modal `#reprocess-sheets-modal`: alerta âmbar de sobrescrita, select "**Tipo de marcação**", checkbox "**Aplicar contraste inteligente**", depois lista de status por aluno (poll 2s + 5s).
- Botão de confirmação dinâmico: "**Reprocessar N aluno(s)**"; após envio vira acompanhamento ("**Na fila**" / "**Processando**" / "**Concluído**" / "**Ignorado (não objetiva)**" / "**Erro**").
- Ação "**Reprocessar**" do upload inteiro (`#reprocess-modal`) permanece.

### Testes

- `fiscallizeon/omr/tests/api/test_reprocess_omr_student_sheet.py`
- `fiscallizeon/omr/tests/tasks/reprocessing/test_reprocess_omr_student_sheet.py`
- Cobertura adicional em `test_read_sheets_directory_fiscallize` / `test_handle_answers`

### OpenSpec

- Change: `openspec/changes/reprocessamento-individual-cartoes/` (proposal, design, spec, tasks, references HTML).

---

## 2. Scope Boundaries (Diferenças de Escopo)

### IN SCOPE

- Ação em massa "**Reprocessar folhas**" com alunos selecionados no detalhe do upload.
- Modal de contraste (normal / caneta clara / lápis ou scan claro) e "**Aplicar contraste inteligente**".
- Acompanhamento assíncrono por aluno na mesma modal, sem reload.
- Isolamento: só o(s) aluno(s) selecionado(s) têm respostas objetivas/PAS sobrescritas; demais alunos do envio intactos.
- Aviso explícito de sobrescrita antes de confirmar.
- Fluxo manual pós-falha continua disponível (corrigir pela imagem / checar).
- "**Reprocessar**" (upload inteiro) continua funcionando como antes.
- Permissões coordenação/professor dono do upload; outro tenant bloqueado (API).

### OUT OF SCOPE

- Ação "**Reprocessar leitura**" por página na aba "**Erros de leitura**" (critério de shaping original da task — **não entregue** nesta branch).
- Reprocessar discursivas (`DISCURSIVE_025`) ou redação (`ESSAY_1`) — devem ser **ignoradas**.
- Pipelines ELIT, SESI, Salta, offset/turma.
- Template legado `omr_upload_detail.html` (`?v=old`).
- Redesign / `redesign/base_component.html` / django-components novos.
- Checkbox “ignorar QR codes” na modal de folhas (existe só na modal de upload inteiro).
- Persistência de `task_id` (reload perde o acompanhamento — aceito).
- App do aluno / `lize-student` / `/api/v3/`.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino                 | Rótulo real no menu UI                                                           | URL Django                                            | View name                                |
| ----------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------- |
| Lista de envios         | Sidebar "**Gabaritos**" → "**Enviar respostas**"                                 | `/gabaritos/`                                         | `omr:omr_upload_list`                    |
| Detalhe do upload       | "**Detalhes**" / "**Resolver**" / selo "**Pendências**"                          | `/gabaritos/detalhes/<uuid>/`                         | `omr:omr_upload_detail`                  |
| Reprocessar folhas (UI) | Barra de seleção → "**Reprocessar folhas**"                                      | (modal `#reprocess-sheets-modal`)                     | —                                        |
| POST reprocessar folha  | —                                                                                | `/gabaritos/api/omr-students/<uuid>/reprocess-sheet/` | `omr:reprocess_omr_student_sheet`        |
| GET status lote         | —                                                                                | `/gabaritos/api/omr-students/reprocess-sheet/status/` | `omr:reprocess_omr_student_sheet_status` |
| Reprocessar upload      | Botão header "**Reprocessar**" [verificar se rótulo completo é só "Reprocessar"] | `/gabaritos/api/reprocess_omr/<uuid>/`                | `omr:reprocess_omr`                      |

Template canônico: `fiscallizeon/omr/templates/omr/omr_upload_detail_new.html`.

🔗 **[Ver Mapeamento de Tela](docs/tests/usability/omr_upload_detail_new.md)**

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Persona

- **Primária:** Coordenação com `omr.view_omrupload`, módulo OMR ativo, dona do upload (mesmas coordenações do `OMRUpload.user`).
- **Secundária (API):** Professor com coordenação em comum — autorizado; usuário de outro `Client` — `403`.
- **Cloud Lab (se disponível):** `cloud.coord@lize.local` / cliente `CLOUDLAB`.

### Comandos (Docker — agent usa `--no-tty`)

```bash
./scripts/tests/run-tests.sh --no-tty \
  fiscallizeon/omr/tests/api/test_reprocess_omr_student_sheet.py \
  fiscallizeon/omr/tests/tasks/reprocessing/test_reprocess_omr_student_sheet.py
```

### Setup Mixer (espelho dos testes da API)

```python
from django.conf import settings
from django.core.cache import cache
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.omr.models import OMRStudents, OMRUpload
from fiscallizeon.students.models import Student

cache.clear()
client_obj = mixer.blend(Client, has_omr=True, two_factor_enabled=False)
unity = mixer.blend(Unity, client=client_obj)
coordination = mixer.blend(SchoolCoordination, unity=unity)
user = mixer.blend(User, must_change_password=False, two_factor_enabled=False)
mixer.blend(CoordinationMember, user=user, coordination=coordination)
cache.set(f'USER_TYPE_{user.pk}', settings.COORDINATION)

upload = mixer.blend(OMRUpload, user=user, filename='scan.pdf')
student = mixer.blend(Student, client=client_obj)
application = mixer.blend(Application)
application_student = mixer.blend(
    ApplicationStudent, application=application, student=student
)
omr_student = mixer.blend(
    OMRStudents,
    upload=upload,
    application_student=application_student,
    scan_image='omr/scans/folha.jpg',
)
```

### Setup manual recomendado (ClickUp)

1. Usar o anexo **`alfa-contraste.pdf`** (ou folhas claras reais).
2. Importar em "**Enviar respostas**" até o detalhe ter alunos com pendências (marcação fraca / lápis).
3. Garantir worker Celery na fila `omr-import` e Redis (result backend) ativos.

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona padrão:** Coordenação dona do upload, logada no portal (`http://localhost:8000`).

### 5.1 Ação em massa e modal [Automatizável ✅]

#### Cenário 1 — Botão aparece só com seleção

**Ação humana:**

- [x] Ir em "**Gabaritos**" → "**Enviar respostas**" e abrir um envio pelo botão "**Detalhes**" (ou "**Resolver**")
- [x] Na listagem de alunos (aba "**Alunos com erro**" ou "**Alunos finalizados**"), **não** selecionar ninguém
- [x] Confirmar que a barra de ações em massa **não** mostra "**Reprocessar folhas**" (nem "**Zerar prova**" / faltas)
- [x] Marcar o checkbox de **um** aluno na tabela
- [x] Confirmar que a barra exibe "**N Selecionados**" e o botão "**Reprocessar folhas**" (ícone de setas circulares, à direita de "**Remover falta**")

**Referência técnica (para automação):**

- URL: `/gabaritos/detalhes/<uuid>/`
- Seletor: `#menu-item-reprocess-sheets` (visível sob `v-if="omrStudentsSelecteds.length > 0"`)
- Estado esperado: botão ausente no DOM visível sem seleção; presente após `#check-student-<id>` marcado
- Fixture: `OMRUpload` processado com ≥1 `OMRStudents`

---

#### Cenário 2 — Abertura da modal e formulário inicial

**Ação humana:**

- [x] Com alunos selecionados, clicar em "**Reprocessar folhas**"
- [x] Verificar o título da modal "**Reprocessar folhas**"
- [x] Ler o alerta âmbar: começa com "**Atenção!**" e avisa que o reprocessamento irá "**sobrescrever**" respostas objetivas ou PAS; páginas discursivas e de redação serão ignoradas
- [x] Confirmar o label "**Tipo de marcação**" com select default "**Marcação normal**", opções "**Marcação em caneta clara**" e "**Marcação a lapis ou escaneamento claro**"
- [x] Confirmar checkbox "**Aplicar contraste inteligente**" desmarcado, com texto auxiliar "**O sistema aplica padrões de contraste e retorna a melhor leitura.**"
- [x] Confirmar que **não** existe opção de ignorar QR codes nesta modal
- [x] Confirmar botões "**Cancelar**" e "**Reprocessar N aluno(s)**" (N = quantidade selecionada)
- [x] Confirmar que a página **não** recarregou

**Referência técnica (para automação):**

- URL: modal `#reprocess-sheets-modal`
- Seletor: `#reprocessSheetsModalLabel`, `#reprocess-sheets-gamma`, `#reprocess-sheets-smart-read`
- Estado esperado: `reprocessSheets.submitted === false`; `gammaOption === '1'`; `smartRead === false`; sem `#ignore-qr` nesta modal
- Fixture: seleção de 1–3 alunos com `scan_image`

---

#### Cenário 3 — Contraste inteligente desabilita o select

**Ação humana:**

- [x] Na modal, marcar "**Aplicar contraste inteligente**"
- [x] Verificar que o select "**Tipo de marcação**" fica desabilitado (visual cinza / não editável)
- [x] Desmarcar o checkbox e confirmar que o select volta a ficar habilitado

**Referência técnica (para automação):**

- Seletor: `#reprocess-sheets-smart-read`, `#reprocess-sheets-gamma[disabled]`
- Estado esperado: com smart read, select `disabled`; POST enviará `smart_read: true`
- Fixture: mesma modal aberta

---

### 5.2 Reprocessamento com contraste fixo [Automatizável ✅]

#### Cenário 4 — Reprocessar um aluno com contraste escolhido (ClickUp)

**Ação humana:**

- [x] Preferencialmente com upload do anexo `alfa-contraste.pdf` (ou folhas claras) onde haja aluno com pendência de leitura
- [x] Selecionar **um** aluno pendente e abrir "**Reprocessar folhas**"
- [x] Escolher "**Marcação a lapis ou escaneamento claro**" (ou "**Marcação em caneta clara**")
- [x] Clicar em "**Reprocessar 1 aluno**"
- [x] Verificar que o botão de confirmação some e aparece a lista com o nome do aluno e status ("**Na fila**" → "**Processando**" → "**Concluído**" ou "**Erro**")
- [x] Verificar o texto "**Não é necessário atualizar a página.**"
- [x] Aguardar conclusão; se "**Concluído**", fechar a modal com "**Fechar**" e conferir se as pendências/status do aluno na tabela melhoraram ou mudaram
- [x] Confirmar que o status do **upload** (header) **não** voltou para "processando" do ciclo completo

**Referência técnica (para automação):**

- URL POST: `/gabaritos/api/omr-students/<uuid>/reprocess-sheet/` body `{ "gamma_option": "3.5", "smart_read": false }` → `202`
- URL GET: `/gabaritos/api/omr-students/reprocess-sheet/status/?task_id=...&omr_student_id=...`
- Seletor: lista em `#reprocess-sheets-modal ul li` com badge de status
- Estado esperado: labels `Na fila` | `Processando` | `Concluído` | `Erro`; poll após 2s e a cada 5s
- Fixture: `OMRStudents` com `scan_image` + worker `omr-import`

---

#### Cenário 5 — Contraste inteligente (ClickUp)

**Ação humana:**

- [x] Selecionar **outro** aluno (ou o mesmo se ainda pendente) com marcação fraca
- [x] Abrir "**Reprocessar folhas**", marcar "**Aplicar contraste inteligente**"
- [x] Confirmar e acompanhar até "**Concluído**" ou "**Erro**"
- [x] Se "**Concluído**", validar na listagem se a pendência foi reduzida/resolvida em relação à leitura anterior

**Referência técnica (para automação):**

- POST body: `{ "gamma_option": "1", "smart_read": true }` (gamma ainda enviado; select desabilitado na UI)
- Estado esperado: task usa `smart_read=True` na page; outcome `success` ou `error`
- Fixture: aluno com `scan_image` e marcação clara/fraca

---

### 5.3 Isolamento e sobrescrita [Automatizável ✅]

#### Cenário 6 — Demais alunos permanecem intactos

**Ação humana:**

- [x] Em um envio com vários alunos já lidos, anotar (print ou nota) respostas/status de um aluno **não** selecionado (ex.: checado ou finalizado)
- [x] Reprocessar **apenas** outro aluno até "**Concluído**"
- [x] Verificar que o aluno não selecionado manteve o mesmo status/respostas/checagem
- [x] Verificar que só o aluno reprocessado teve leitura atualizada

**Referência técnica (para automação):**

- Comparar `OptionAnswer` / stats do `ApplicationStudent` não selecionado antes e depois
- Fixture: 2+ `OMRStudents` no mesmo `OMRUpload`; reprocessar só um `pk`

---

#### Cenário 7 — Aviso e sobrescrita de correção manual

**Ação humana:**

- [x] Em um aluno, corrigir manualmente ao menos uma questão objetiva (fluxo de correção existente)
- [x] Voltar ao detalhe, selecionar esse aluno, abrir "**Reprocessar folhas**"
- [x] Confirmar que o alerta âmbar deixa claro que respostas serão sobrescritas
- [x] Confirmar o reprocessamento e, após "**Concluído**", abrir de novo a correção/imagem e verificar que as respostas refletem a **nova** leitura (não necessariamente a correção manual anterior)

**Referência técnica (para automação):**

- `handle_answers` / `handle_answers_pas` apagam e recriam `OptionAnswer` do aluno
- Estado esperado: respostas pós-task = nova leitura
- Fixture: aluno com `OptionAnswer` manuais + `scan_image`

---

### 5.4 Bordas e regressão [Automatizável ✅ / parcial Manual]

#### Cenário 8 — Leitura continua falhando → fluxo manual disponível [Automatizável ✅]

**Ação humana:**

- [x] Reprocessar um cartão que continue ilegível (ou forçar cenário de erro)
- [x] Na modal, ver badge "**Erro**" (vermelho)
- [x] Fechar a modal e confirmar que ainda é possível abrir a correção pela imagem e/ou marcar o aluno como checado (fluxos manuais atuais)

**Referência técnica (para automação):**

- Estado esperado: `outcome=error` ou `status=FAILURE`; aba de "**Erros de leitura**" **não** ganha novo `OMRError` por falha de QR nesta task
- Fixture: scan sem QR válido / mock de falha

---

#### Cenário 9 — Reprocessar upload inteiro preservado [Automatizável ✅]

**Ação humana:**

- [x] No header do detalhe (quando o upload `can_be_reprocessed` e não está processando), clicar no botão "**Reprocessar**"
- [x] Confirmar que abre a modal "**Reprocessar upload**" (título distinto de "**Reprocessar folhas**")
- [x] Verificar alerta de sobrescrita do **upload**, select de contraste e checkbox de ignorar QR (fluxo antigo)
- [x] Cancelar sem confirmar (ou confirmar em ambiente de teste consciente do impacto)
- [x] Garantir que a modal de folhas e a de upload são diálogos **separados**

**Referência técnica (para automação):**

- Seletores: `#reprocess-modal` vs `#reprocess-sheets-modal`
- URL upload: POST `/gabaritos/api/reprocess_omr/<uuid>/`
- Fixture: upload com `can_be_reprocessed`

---

#### Cenário 10 — Múltiplos alunos no mesmo lote [Automatizável ✅]

**Ação humana:**

- [x] Selecionar 2 ou 3 alunos e clicar "**Reprocessar folhas**"
- [x] Confirmar botão "**Reprocessar 2 alunos**" (ou 3)
- [x] Após confirmar, ver uma linha de status por aluno na lista
- [x] Aguardar todos terminarem; fechar a modal e ver a listagem atualizar estatísticas dos reprocessados

**Referência técnica (para automação):**

- N POSTs independentes; GET em lote com `task_id` e `omr_student_id` separados por vírgula
- Ao fechar: `hidden.bs.modal` → `refreshReprocessSheetsStudents()` / `fetchOmrStudentsStats`
- Fixture: 2–3 `OMRStudents` com imagem

---

#### Cenário 11 — Reload perde acompanhamento (comportamento aceito) [Apenas Manual 👁]

**Ação humana:**

- [x] Iniciar um reprocessamento e, ainda em "**Processando**", recarregar a página (F5)
- [x] Confirmar que a modal volta ao estado inicial / fechada e não há barra de progresso persistida
- [x] Após alguns segundos, atualizar a listagem/status do aluno para ver se a task no worker concluiu mesmo assim (efeito nas respostas)
- JAM com teste gravado: [Vídeo do teste](https://jam.dev/c/a742742e-96fe-4e53-90f0-b73da1c1cdc6)

**Referência técnica (para automação):**

- `task_id` só em memória Vue (`reprocessSheets.students[].taskId`)
- Spec: reload perde acompanhamento; tasks seguem no worker

---

### 5.5 Permissões [Automatizável ✅]

#### Cenário 12 — Outro tenant não reprocessa

**Ação humana:**

- [x] (API ou segundo usuário) Tentar POST no `omr_student` de outro cliente
- [x] Esperar bloqueio (`403`/`404`); nenhuma task enfileirada

**Referência técnica (para automação):**

- Cobertura em `test_reprocess_omr_student_sheet.py` (tenant isolado)
- Fixture: segundo `Client` + user sem coordenação em comum

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

Comparar com mockups OpenSpec (não há Figma no campo da task):

| Referência                | Arquivo                                                                                          |
| ------------------------- | ------------------------------------------------------------------------------------------------ |
| Barra de ações            | `openspec/changes/reprocessamento-individual-cartoes/references/detalhe-upload-acoes-massa.html` |
| Modal formulário + status | `openspec/changes/reprocessamento-individual-cartoes/references/modal-reprocessar-folhas.html`   |

Checklist:

- [x] Tirar print da barra com "**Reprocessar folhas**" ao lado de zerar/faltas ![](../evidencias/reprocessar.png)
- [x] Tirar print da modal no estado formulário (alerta âmbar + select + contraste inteligente) ![](../evidencias/modal.png)
- [x] Tirar print da modal no estado acompanhamento (badges de status)

| fila                        | processando                        | resultado                        |
| --------------------------- | ---------------------------------- | -------------------------------- |
| ![](../evidencias/fila.png) | ![](../evidencias/processando.png) | ![](../evidencias/resultado.png) |

---

## 7. Bugs and Observations (Problemas Encontrados)

Instruir o QA a registrar issues com:

> [!BUG]
> **Title:** …
> **Tags:** `[UX/UI]` | `[Backend Logic]` | `[Database]` | `[Spec Gap]`
> **Context/Root Cause:** …
> **Expected Behavior:** … (conforme OpenSpec: `spec.md` L.XX) ou (inferência de UX — Spec Gap)
> **Workaround:** …

### Gaps já conhecidos (pré-QA)

> [!WARNING]
> **Title:** Shaping pedia reprocessar página em "Erros de leitura"; entrega não inclui.
> **Tags:** `[Spec Gap]`
> **Context:** Critérios de aceite da task ClickUp vs OpenSpec/implementação (só listagem + ação em massa).
> **Expected Behavior:** (conforme shaping ClickUp) ação por página na aba de erros.
> **Workaround:** Associar/corrigir manualmente na aba de erros; usar "**Reprocessar folhas**" quando o aluno já estiver na listagem com `scan_image`.

> [!NOTE]
> **Title:** OpenSpec dizia “sem migração”; há `0080_omrstudents_omr_category`.
> **Tags:** `[Database]`
> **Context:** Campo `omr_category` em `OMRStudents` para evitar reler QR.
> **Expected Behavior:** Rodar migrate no ambiente de QA antes dos testes E2E.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> Avaliar ação pontual na aba "**Erros de leitura**" (página sem `OMRStudents` associado) — pedida no shaping e fora desta entrega.

> [!NOTE]
> Comportamento se a releitura identificar aluno diferente do associado (open question do ClickUp) — documentar se aparecer em QA.

> [!NOTE]
> Persistência opcional de `task_id` / toast pós-reload para não “perder” o acompanhamento (hoje aceito como trade-off).

> [!NOTE]
> `gamma_option` no upload é compartilhado pelo lote; corrida com outro reprocessamento do mesmo upload é rara, mas possível.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.

🔗 **[Ver Mapeamento de Tela](docs/tests/usability/omr_upload_detail_new.md)**

### Snippet Playwright + Mixer (sugestão)

```python
# Persona: coordenação dona do upload (is_staff / COORDINATION + CoordinationMember)
# Pré: self.client.force_login(self.user); upload processado; omr_student com scan_image

def test_reprocessar_folhas_abre_modal_e_enfileira(page, live_server, omr_upload, omr_student):
    page.goto(f"{live_server.url}/gabaritos/detalhes/{omr_upload.pk}/")
    page.locator(f"#check-student-{omr_student.pk}").check()
    page.locator("#menu-item-reprocess-sheets").click()
    assert page.locator("#reprocessSheetsModalLabel").inner_text() == "Reprocessar folhas"
    page.locator("#reprocess-sheets-gamma").select_option("3.5")
    page.get_by_role("button", name="Reprocessar 1 aluno").click()
    page.get_by_text("Não é necessário atualizar a página.").wait_for()
    # Aguardar badge Concluído / Erro conforme worker
```

**Permissões no setup:** `cache.set(f'USER_TYPE_{user.pk}', settings.COORDINATION)` + `CoordinationMember`; cliente `has_omr=True`. Elevação `is_superuser` não é obrigatória se as permissões OMR estiverem corretas.

**APIs críticas:**

| Método         | Rota                                                  |
| -------------- | ----------------------------------------------------- |
| POST           | `/gabaritos/api/omr-students/<uuid>/reprocess-sheet/` |
| GET            | `/gabaritos/api/omr-students/reprocess-sheet/status/` |
| GET (listagem) | `/gabaritos/api/omr_upload/<uuid>/students/`          |

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Gargalo principal durante o teste:** _[preencher]_
- **Ida e volta com o desenvolvedor:** _[preencher]_
- **Como melhorar o fluxo de desenvolvimento/QA desta task:** _[preencher]_

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

- Quando a task ClickUp (shaping) e a OpenSpec divergirem (ex.: aba Erros vs ação em massa), o prompt deveria exigir uma subseção explícita "**Shaping vs Entrega**" no Metadata — evita o QA validar critério antigo como bug.
- Anexos ClickUp (PDF de scan) deveriam ser linkados no plano com instrução de download via MCP `clickup_download_task_attachment` quando o ambiente local não tiver o arquivo.
- Features OMR que dependem de worker `omr-import` + Redis result backend precisam de um pré-check obrigatório no Section 4 (senão o QA marca "Erro" falso-positivo).
