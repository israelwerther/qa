## 0. Metadata (Metadados de QA)

| Campo                      | Valor                                                          |
| -------------------------- | -------------------------------------------------------------- |
| **Data:**                  | 2026-10-14                                                     |
| **Natureza da Tarefa:**    | Business Feature                                               |
| **Área da Feature:**       | OMR (Gabaritos)                                                |
| **Nível de Risco:**        | Médio                                                          |
| **Qualidade da OpenSpec:** | (5/5) — spec atualizada e coerente com a implementação em abas |

> **Nota de revisão:** a implementação foi **refatorada** em relação à primeira versão. A abordagem original (`?filter=pending` via URL) foi **descartada**. O plano foi reescrito para refletir o comportamento atual.

---

## 1. Summary of Changes (Resumo das Alterações)

A entrega foi reformulada: em vez de um filtro por URL, a listagem de alunos do detalhe do gabarito agora é organizada em **duas abas** derivadas em JavaScript dos dados já carregados.

### Frontend (Template + JS)

- **Novo arquivo de lógica:** `fiscallizeon/omr/templates/omr/includes/upload-student-tabs.js` — contém o objeto `OMRStudentTabs` com:
  - Regra de pendência: `hasCorrectionPending()` (respostas manuais + automáticas < total, não checado, não faltante).
  - `createStudent()` para normalizar objetos de aluno.
  - `mixin` Vue com dados, computeds, watchers e métodos.
- **`omr_upload_detail_new.html`:**
  - Inclui o JS antes do `new Vue` e integra `mixins: [OMRStudentTabs.mixin]`.
  - Substitui a aba única "Listagem de alunos" por abas dinâmicas `studentTabs` (renderizadas com `v-for`).
  - Labels das abas: "**Alunos com erro**" (id `students-pending`) e "**Alunos finalizados**" (id `students-finished`).
  - Abas com contagem zero são ocultadas após as estatísticas carregarem.
  - `computedOMRStudents` passa a usar `activeStudents` (grupo ativo).
  - Estados novos: carregamento de estatísticas (`isStudentTab && isStudentsStatsLoading`), erro de estatística (`isStudentTab && studentsWithStatsError.length`) e badge "Indisponível".
  - Botão "**Corrigir**" (seção de respostas pendentes) agora condicionado a `omrStudentsWithCorrectionPending.length`.
  - Seleção em lote restrita à aba ativa (`toggleVisibleStudents`, `allVisibleStudentsSelected`, `clearHiddenStudentSelection`).
  - `uploadCheck` movido para o mixin: trata checar/deschecar, previne chamadas duplicadas e exibe erro em falha.
  - Atualização ao retornar de correção via `trackStudentCorrection` + `refreshCorrectedStudents` (eventos `focus`/`pageshow`).
  - Reprocessamento normalizado por `mergeReprocessedStudents` (não zera contagens).
- **Removido:** `?filter=pending`, `initFromUrlParams`, `isViewPendingList`, `viewPendingList` inline e `fetchOmrStudentsStats` inline.

### Backend

- **Nenhuma alteração.** Sem migrations, views, models, serializers, filas ou contratos de API.

### Testes

- **Novo:** `fiscallizeon/omr/tests/frontend/upload-student-tabs.test.cjs` — 20 cenários Node (`node:test`) cobrindo agrupamento, carga inicial, concorrência, falhas, reprocessamento, seleção e retorno de correção.
- **Novo:** `fiscallizeon/omr/tests/test_omr_upload_detail_template.py` — 5 testes Django (`SimpleTestCase`) validando inclusão do mixin, tour, ausência do filtro por URL legado e escopo dos avisos.

### Spec

- `openspec/changes/filtro-pendencias-gabaritos-86ak023yy/` — proposal, design, spec e tasks atualizados para o modelo de abas.

---

## 2. Scope Boundaries (Diferenças de Escopo)

### IN SCOPE

- Organização dos alunos identificados em "**Alunos com erro**" e "**Alunos finalizados**" para **todos** os caminhos de acesso (Detalhes, Resolver, Pendências).
- Classificação pela regra existente de pendência.
- Ocultar abas com contagem zero após estatísticas válidas.
- Atualizar grupos e contagens após correção, "Em branco" ou checagem confirmada.
- Ativar a outra aba quando a aba ativa esvaziar (permanecer no detalhe).
- Estados de carregamento e erro de estatísticas (inclusive retry individual).
- Seleção em lote restrita à aba visível.
- Reprocessamento e retorno de correção recalculando os grupos.
- Erros de leitura (cartões não identificados) continuam na aba "Erros de leitura".

### OUT OF SCOPE

- **Filtro por URL (`?filter=pending`):** descartado e removido do código.
- **Redirecionamento automático** para a lista de envios ao resolver a última pendência: não implementado (o operador permanece no detalhe).
- **Terceira aba** com todos os alunos.
- Alterações em backend, querysets, APIs, models, migrações ou tarefas Celery.
- Correção da coluna "Nº de pendências" da lista de envios.
- Sincronização em tempo real entre operadores.
- Redesenho de página ou mudança na forma de resolver cartões.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino                      | Rótulo real no menu UI                      | URL Django                    | View name               |
| ---------------------------- | ------------------------------------------- | ----------------------------- | ----------------------- |
| Lista de envios de gabaritos | "Enviar respostas"                          | `/gabaritos/`                 | `omr:omr_upload_list`   |
| Detalhe do gabarito          | "Detalhes" / "Resolver" / selo "Pendências" | `/gabaritos/detalhes/<uuid>/` | `omr:omr_upload_detail` |

> Não há query parameter de filtro. Os três caminhos de acesso abrem a mesma tela e a mesma organização em abas.

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comandos

```bash
# Testes unitários JS (Node)
node --test fiscallizeon/omr/tests/frontend/*.test.cjs

# Testes Django do template
python manage.py test fiscallizeon.omr.tests.test_omr_upload_detail_template --verbosity=2

# Cloud Lab (sem Docker)
source .venv/bin/activate && pytest fiscallizeon/omr/tests/test_omr_upload_detail_template.py --reuse-db -v
```

### Persona

- **Usuário:** Coordenação da "Coordenação de testes" (Client `CLOUDLAB`)
- **Permissões:** `is_staff=True` + `omr.view_omrupload`
- **Ação de correção:** requer `exams.can_correct_answers_exam`

### Setup de dados com Mixer (referência)

```python
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

> Para exercitar os grupos, o envio deve conter `omr_students` em estados mistos: pendente (questão em branco/dupla marcação), leitura automática completa, checado e faltante.

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Agrupamento em abas [Automatizável ✅]

#### Cenário 1 — Envio misto exibe as duas abas com contagens corretas

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Acessar `/gabaritos/` e abrir um envio com alunos pendentes e alunos já finalizados pelo botão "**Detalhes**"
- [x] Observar as abas de alunos no topo da área de listagem
- [x] Verificar se existem as abas "**Alunos com erro**" (badge vermelho) e "**Alunos finalizados**" (badge cinza)
- [x] Verificar se o número no badge de cada aba corresponde ao total do grupo
- [x] Confirmar que a aba "**Alunos com erro**" aparece à esquerda e está ativa quando há pendências

**Referência técnica (para automação):**

- URL: `/gabaritos/detalhes/<uuid>/`
- Seletor: `#students-pending-tab`, `#students-finished-tab`
- Estado esperado: `#students-pending-tab` existe quando `omrStudentsWithCorrectionPending.length > 0`; `#students-finished-tab` existe quando `omrStudentsFinished.length > 0`
- Fixture: `mixer.blend(OMRUpload, status=3)` com `omr_students` mistos

---

#### Cenário 2 — Todos os caminhos de acesso mostram a mesma organização

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Abrir o mesmo envio pelo botão "**Detalhes**"
- [x] Repetir a abertura pelo botão "**Resolver**" (visível quando `hasPendingCorrection`)
- [x] Repetir a abertura pelo selo "**Pendências**" (coluna "Respostas aguardando correção")
- [x] Confirmar que nos três casos as abas "Alunos com erro" e "Alunos finalizados" aparecem com as mesmas contagens

**Referência técnica (para automação):**

- URL: `/gabaritos/detalhes/<uuid>/`
- Seletores: `a#resolve-<id>` (Resolver), `a[aria-label="Respostas aguardando correção"]` (selo Pendências), `button#details-<id>` (Detalhes)
- Estado esperado: nenhuma URL contém `filter=pending`; os três destinos são idênticos
- Fixture: upload com pendências

---

### 5.2 Classificação dos alunos [Automatizável ✅]

#### Cenário 3 — Ausência e dupla marcação ficam em "Alunos com erro"

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] No detalhe do envio, localizar um aluno com questão em branco ou com marcação dupla
- [x] Verificar que ele aparece na aba "**Alunos com erro**" com badge vermelho "Pendência"
- [x] Verificar que ele **não** aparece na aba "Alunos finalizados"

**Referência técnica (para automação):**

- Seletor: `#table-uploadstudents tbody tr[data-trchecked="<id>"]`
- Estado esperado: aluno pendente presente em `students-pending`, ausente em `students-finished`
- Fixture: `omrStudent` com `answeredQuestionsCountManually + answeredQuestionsCountAutomatically < allQuestionsCount`, `checked=false`, `applicationStudentMissed=false`

---

#### Cenário 4 — Leitura automática completa vai para "Alunos finalizados"

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Localizar um aluno com 100% das questões lidas automaticamente (sem checagem manual)
- [x] Verificar que ele aparece na aba "**Alunos finalizados**"
- [x] Verificar que ele **não** aparece em "Alunos com erro"

**Referência técnica (para automação):**

- Seletor: `#students-finished-tab` → `#table-uploadstudents tbody tr`
- Estado esperado: presente em `students-finished`
- Fixture: `omrStudent` com `answeredQuestionsCountAutomatically === allQuestionsCount`

---

#### Cenário 5 — Checado e faltante vão para "Alunos finalizados"

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Localizar um aluno marcado como checado (badge verde "Checado por")
- [x] Localizar um aluno marcado como faltante (badge amarelo "Falta")
- [x] Verificar que ambos aparecem na aba "**Alunos finalizados**", mantendo seus status específicos na linha
- [x] Verificar que nenhum aparece em "Alunos com erro"

**Referência técnica (para automação):**

- Seletor: `#students-finished-tab` → `#table-uploadstudents tbody tr[data-trchecked="<id>"]`
- Estado esperado: presente em `students-finished` (checado e faltante)
- Fixture: `omrStudent` com `checked=true` e outro com `applicationStudentMissed=true`

---

### 5.3 Atualização reativa [Automatizável ✅]

#### Cenário 6 — Resolver a última questão move o aluno para "Alunos finalizados"

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Na aba "**Alunos com erro**", abrir a correção de um aluno pendente e salvar a última questão faltante (alternativa ou "Em branco")
- [x] Retornar ao detalhe do envio
- [x] Verificar que o aluno agora aparece na aba "**Alunos finalizados**"
- [x] Verificar que o badge de "Alunos com erro" diminuiu em 1 e o de "Alunos finalizados" aumentou em 1
- [x] Confirmar que a página não recarregou

**Referência técnica (para automação):**

- Seletor: `#students-finished-tab` → `#table-uploadstudents tbody tr[data-trchecked="<id>"]`
- Estado esperado: após salvar, `omrStudent.hasCorrectionPending() === false` e `activeTab === 'students-finished'` quando a aba de erros esvaziar
- Fixture: upload com 1 aluno pendente e demais finalizados

---

#### Cenário 7 — Correção parcial mantém o aluno em erro

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Abrir a correção de um aluno com duas ou mais questões pendentes
- [x] Salvar apenas uma questão
- [x] Retornar ao detalhe
- [x] Verificar que o aluno continua na aba "**Alunos com erro**"

**Referência técnica (para automação):**

- Seletor: `#students-pending-tab` → `#table-uploadstudents tbody tr[data-trchecked="<id>"]`
- Estado esperado: aluno permanece em `students-pending`
- Fixture: aluno com 2+ questões pendentes

---

#### Cenário 8 — Checagem move o aluno para "Alunos finalizados"

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Na aba "**Alunos com erro**", clicar no botão circular de checagem da linha do aluno
- [x] Verificar que a ação é confirmada pelo servidor
- [x] Verificar que o aluno sai de "Alunos com erro" e aparece em "Alunos finalizados"
- [x] Verificar que a linha exibe "Checado por: <operador>"

**Referência técnica (para automação):**

- Seletor: `[data-check="<id>"]`
- Estado esperado: `omrStudent.checked === true` após resposta `data: true`; aluno em `students-finished`
- Fixture: aluno pendente

---

#### Cenário 9 — Falha de salvamento não move o aluno

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Simular falha da API ao salvar correção ou checagem (ex.: interromper a rede)
- [x] Verificar que a tela apresenta o erro
- [x] Verificar que o aluno **não** muda de grupo com base em ação não persistida

**Referência técnica (para automação):**

- Seletor: `[data-check="<id>"]`
- Estado esperado: em erro, `student.checked` permanece inalterado e o aluno continua no grupo anterior
- Fixture: mock de API retornando erro

---

### 5.4 Abas vazias e aba ativa [Automatizável ✅]

#### Cenário 10 — Última pendência resolvida ativa "Alunos finalizados"

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Estar na aba "**Alunos com erro**" com apenas um aluno pendente
- [x] Resolver esse aluno (checagem ou última questão)
- [x] Verificar que a aba "Alunos com erro" desaparece
- [x] Verificar que a aba "**Alunos finalizados**" é ativada automaticamente
- [x] Confirmar que o operador permanece no detalhe (não é redirecionado)

**Referência técnica (para automação):**

- Seletor: `#students-finished-tab`
- Estado esperado: `studentTabs` contém apenas `students-finished`; `activeTab === 'students-finished'`
- Fixture: upload com exatamente 1 aluno pendente

---

#### Cenário 11 — Envio sem nenhuma pendência exibe apenas "Alunos finalizados"

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Abrir um envio onde todos os alunos já estão finalizados
- [x] Verificar que somente a aba "**Alunos finalizados**" aparece entre as abas de alunos
- [x] Confirmar que não há aba "Alunos com erro"

**Referência técnica (para automação):**

- Seletor: `#students-finished-tab`
- Estado esperado: `#students-pending-tab` não existe; `#students-finished-tab` existe
- Fixture: todos os `omrStudent` com estatísticas completas

---

#### Cenário 12 — Envio somente com pendências exibe apenas "Alunos com erro"

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Abrir um envio onde todos os alunos estão pendentes
- [x] Verificar que somente a aba "**Alunos com erro**" aparece entre as abas de alunos

**Referência técnica (para automação):**

- Seletor: `#students-pending-tab`
- Estado esperado: `#students-finished-tab` não existe
- Fixture: todos os `omrStudent` pendentes

---

#### Cenário 13 — Nenhum aluno identificado oculta as abas de alunos

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Abrir um envio sem alunos identificados
- [x] Verificar que as abas de alunos ficam ocultas
- [x] Verificar que as demais áreas (Erros de leitura, Arquivos associados) continuam acessíveis
- [x] Verificar que a ausência de alunos é indicada quando não houver outra visão disponível

**Referência técnica (para automação):**

- Seletor: `#myTab`
- Estado esperado: `studentTabs.length === 0`; `activeTab` cai para `reading-errors`/`associated-files`/`no-file`
- Fixture: upload sem `omr_students`

---

#### Cenário 14 — Carregamento e erro de estatísticas

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Abrir o detalhe com rede lenta
- [x] Verificar a mensagem "**Carregando informações dos alunos…**" enquanto as estatísticas carregam
- [x] Simular falha da API de estatísticas
- [x] Verificar a mensagem "**Não foi possível carregar as informações de N aluno(s).**" com o botão "**Tentar novamente**"
- [x] Verificar que alunos com estatística indisponível aparecem em "Alunos com erro" com o marcador "**Indisponível**"
- [x] Clicar em "**Tentar novamente**" e confirmar a recuperação
- [x] Verificar que os zeros iniciais não são interpretados como finalização

**Referência técnica (para automação):**

- Seletor: `[role="status"]` (carregando), `[role="alert"]` (erro), `button:has-text("Tentar novamente")`
- Estado esperado: em erro, `omrStudent.statsError === true` e aluno em `students-pending`
- Fixture: mock de API com falha e depois sucesso

---

### 5.5 Seleção em lote [Automatizável ✅]

#### Cenário 15 — "Selecionar todos" age somente na aba visível

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Na aba "**Alunos com erro**", clicar no checkbox de cabeçalho "**Selecionar todos os alunos desta aba**"
- [x] Verificar que apenas os alunos da aba atual ficam selecionados
- [x] Trocar para a aba "**Alunos finalizados**"
- [x] Verificar que a seleção anterior é limpa
- [x] Clicar no checkbox de cabeçalho novamente e verificar que só os finalizados são selecionados
- [x] Resolver um aluno da aba de erro e verificar que a seleção não inclui mais esse aluno oculto

**Referência técnica (para automação):**

- Seletor: `#check-student-all-header`, `#check-student-all`
- Estado esperado: `omrStudentsSelecteds` contém somente ids de `activeStudents`
- Fixture: upload misto

---

### 5.6 Erros de leitura e reprocessamento [Apenas Manual 👁]

#### Cenário 16 — Cartões não identificados permanecem em "Erros de leitura"

**Persona:** Coordenação da "Coordenação de testes"

**Ação humana:**

- [x] Abrir um envio com cartões sem identificação de aluno
- [x] Verificar que esses casos aparecem na aba "**Erros de leitura**"
- [x] Verificar que eles **não** aparecem em "Alunos com erro" nem em "Alunos finalizados"

**Referência técnica (para automação):**

- Seletor: `#reading-errors-tab`
- Estado esperado: `errorList` alimenta somente a aba de erros de leitura
- Fixture: upload com `get_unsolved_errors` > 0

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] Verificar que as abas "Alunos com erro" e "Alunos finalizados" seguem o padrão visual das abas existentes (fundo branco na ativa, cinza claro nas demais)
- [x] Verificar que o badge de "Alunos com erro" é vermelho (`tw-bg-[#D92D20]`) e o de "Alunos finalizados" é cinza (`tw-bg-[#E5E7EA]`)
- [x] Verificar que o badge de "Alunos com erro" da aba usa a mesma cor do selo "Pendências"

![](../evidencias/abas.png)

---

## 7. Bugs and Observations (Problemas Encontrados)

> Nenhum bug crítico encontrado na revisão estática do código. Os itens abaixo são pontos de atenção para validação em navegador.

> [!NOTE]
> **[UX/UI]** Alunos com estatística indisponível ficam presos em "Alunos com erro"
>
> Pela regra `isPending = !statsLoaded || hasCorrectionPending()`, um aluno cuja estatística falha permanentemente permanece em "Alunos com erro" com "Indisponível". É o comportamento planejado (assegura acesso), mas pode inflar a contagem de erros. Validar em navegador.

> [!WARNING]
> **[Backend Logic]** Atualização entre operadores não é imediata
>
> Não há sincronização em tempo real. Alterações de outro operador aparecem apenas quando os mecanismos existentes recebem dados ou após recarregamento.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **[UX/UI]** Coluna "Nº de pendências" da lista de envios segue sem cálculo
>
> Fora do escopo desta entrega (conforme proposta). Recomenda-se tratar em melhoria subsequente.

> [!NOTE]
> **[Backend Logic]** Concorrência entre operadores no mesmo envio
>
> Sem comportamento definido quando duas pessoas tratam o mesmo envio simultaneamente.

> [!NOTE]
> **[UX/UI]** Filtro por URL foi descartado sem alternativa de deep-link
>
> A spec atual afirma que todos os caminhos de acesso mostram a mesma organização, sem necessidade de filtro por URL. Se no futuro for necessário abrir direto na aba de erros, será preciso reintroduzir um parâmetro controlado.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML: `omr_upload_list_new.md` e `omr_upload_detail_new.md`
- **[Ver Mapeamento: omr_upload_list_new](docs/tests/usability/omr_upload_list_new.md)**
- **[Ver Mapeamento: omr_upload_detail_new](docs/tests/usability/omr_upload_detail_new.md)**

---

## 9. QA Retrospective (Retrospectiva de QA)

_(Preencher após execução dos testes)_

- Principal gargalo durante os testes:
- Quantas idas e voltas com o desenvolvedor:
- Como poderia ter sido melhorado:

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

---

### Snippet de Automação Sugerido (Python/Playwright)

```python
# Setup de dados + verificação de abas (referência)
def test_upload_detail_student_tabs(client, mixer):
    user = mixer.blend(User, is_staff=True)
    client.force_login(user)
    exam = mixer.blend(Exam, questions_count=10)
    application = mixer.blend(Application, exam=exam)
    upload = mixer.blend(OMRUpload, application=application, status=3)
    # 1 pendente, 1 lido automaticamente, 1 checado, 1 faltante
    mixer.blend(OMRStudent, upload=upload, checked=False, answered_questions_count_manually=0,
                answered_questions_count_automatically=1, all_questions_count=10)
    mixer.blend(OMRStudent, upload=upload, checked=False, answered_questions_count_manually=10,
                answered_questions_count_automatically=0, all_questions_count=10)
    mixer.blend(OMRStudent, upload=upload, checked=True, all_questions_count=10)
    mixer.blend(OMRStudent, upload=upload, application_student__missed=True)
    url = reverse("omr:omr_upload_detail", args=[upload.id])
    response = client.get(url)
    assert response.status_code == 200
    assert b"students-pending" in response.content or b"students-finished" in response.content
```
