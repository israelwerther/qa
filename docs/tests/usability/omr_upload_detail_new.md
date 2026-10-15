# Mapeamento de Usabilidade: omr_upload_detail_new

## 1. URLs e Navegação

| Destino | URL Django | View name | Como navegar |
|---------|-----------|-----------|--------------|
| Detalhe do gabarito | `/gabaritos/detalhes/<uuid>/` | `omr:omr_upload_detail` | Clique em "Detalhes" / "Resolver" / selo "Pendências" na lista |

> **Nota:** não há filtro por URL. Os três caminhos de acesso abrem a mesma tela e a mesma organização em abas.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

- **Permissão:** `omr.view_omrupload` (perfis: Coordenação, Professor, Staff)
- **Correção:** requer `exams.can_correct_answers_exam`
- **Usuário:** `mixer.blend(User, is_staff=True)` ou coordenador com client `CLOUDLAB`
- **Dados mínimos:**
  - `OMRUpload` com `status=3` (processado)
  - `omr_students` em estados mistos: pendente (questão em branco/dupla marcação), leitura automática completa, checado, faltante

```python
# Snippet de setup com Mixer
from mixer.backend.django import mixer
from fiscallizeon.omr.models import OMRUpload
from fiscallizeon.exams.models import Exam
from fiscallizeon.applications.models import Application
from fiscallizeon.core.models import Client
from django.contrib.auth import get_user_model

User = get_user_model()
client = mixer.blend(Client)
user = mixer.blend(User, client=client, is_staff=True)
exam = mixer.blend(Exam, client=client, questions_count=10)
application = mixer.blend(Application, exam=exam, client=client)
upload = mixer.blend(OMRUpload, application=application, client=client, status=3)
```

## 3. Seletores DOM e Ações

### Abas (tabs)

| Aba | Seletor | Condição de exibição |
|-----|---------|----------------------|
| "Erros de leitura" | `#reading-errors-tab` | `object.get_unsolved_discursive_errors` ou `object.get_unsolved_errors` e `status != 5` |
| "Alunos com erro" | `#students-pending-tab` | `omrStudentsWithCorrectionPending.length > 0` |
| "Alunos finalizados" | `#students-finished-tab` | `omrStudentsFinished.length > 0` |
| "Listagem de alunos" (provisória) | `#list-of-students-tab` | Apenas durante o carregamento inicial (`isInitialStatsLoading`) |
| "Arquivos associados" | `#associated-files-tab` | `associatedFiles.length > 0` |

### Controles da área de alunos

| Elemento | Seletor / Descrição | Ação |
|----------|---------------------|------|
| Botão "Corrigir" | `<button @click="viewPendingList()">` com texto "Corrigir" | Vai para a aba `students-pending` |
| Card "Respostas pendentes de checagem" | Spinner durante `isStudentsStatsLoading`, `—` em erro, contador ao final | Exibe total de pendências |
| Carregando estatísticas | `[role="status"]` com texto "Carregando informações dos alunos…" | Estado de carregamento |
| Erro de estatísticas | `[role="alert"]` com texto "Não foi possível carregar as informações de N aluno(s)." | Estado de erro |
| Botão "Tentar novamente" (global) | `<button @click="retryStudentStats()">` | Refaz consultas com falha |
| Badge "Indisponível" | Texto "Indisponível" na coluna Status | Aluno com `statsError && !statsLoaded` |
| Link "Tentar novamente" (individual) | `<button @click="fetchOmrStudentsStats([omrStudent])">` na célula do nome | Refaz a estatística do aluno |

### Tabela de alunos (`#table-uploadstudents`)

| Coluna | Seletor / Descrição |
|--------|---------------------|
| Checkbox "selecionar todos" (cabeçalho) | `#check-student-all-header` |
| Checkbox "selecionar todos" (barra superior) | `#check-student-all` |
| Checkbox de linha | `#check-student-${id}` |
| Nome | Coluna com `#{omrStudent.name}` e `(#{omrStudent.enrollmentNumber})` |
| Status | Badge colorido: vermelho `#DC2626` = pendente, amarelo `#FEFCE8` = falta, verde = checado |
| Linha | `tr[data-trchecked="<id>"]` |
| Botão de checagem | `[data-check="<id>"]` |

### Estados de aluno relevantes

| Estado | Grupo | Badge visual |
|--------|-------|-------------|
| Pendente (sem resposta / dupla marcação) | `students-pending` | Vermelho "Pendência" |
| Checado | `students-finished` | Verde "Checado por: X" |
| 100% lidas automaticamente | `students-finished` | (sem badge especial) |
| Faltante | `students-finished` | Amarelo "Falta" |
| Erro de leitura (QR não identificado) | Aba "Erros de leitura" | N/A |
| Estatística indisponível | `students-pending` | "Indisponível" |

### Lógica (arquivo `omr/includes/upload-student-tabs.js`)

- `hasCorrectionPending()` — respostas manuais + automáticas < total, não checado, não faltante.
- `isPending(student)` — `!statsLoaded || hasCorrectionPending()`.
- `studentTabs` — abas com contagens; oculta grupos zerados após estatísticas válidas.
- `activeStudents` — grupo da aba ativa (`students-pending`, `students-finished` ou `list-of-students`).
- `ensureStudentTab()` — ativa outra aba quando a atual zera.
- `fetchOmrStudentsStats()` — concorrência máxima 4; marca `statsError`/`statsLoaded`.
- `retryStudentStats()` — refaz consultas com falha.
- `uploadCheck(id)` — checar/deschecar; previne duplicadas; trata erro.
- `mergeReprocessedStudents()` — normaliza e recalcula após reprocessamento.
- `trackStudentCorrection(id)` + `refreshCorrectedStudents()` — atualiza ao retornar de correção (`focus`/`pageshow`).
- `toggleVisibleStudents()` / `allVisibleStudentsSelected` / `clearHiddenStudentSelection` — seleção restrita à aba ativa.

### Testes automatizados

- JS: `node --test fiscallizeon/omr/tests/frontend/*.test.cjs`
- Django: `python manage.py test fiscallizeon.omr.tests.test_omr_upload_detail_template`
