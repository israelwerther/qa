# QA Test Plan — Sincronização Perseus: Situação dos alunos (Ensino Superior)

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-29 |
| **Branch:** | `feat/perseus-status-alunos` (lizeedu) |
| **Task ClickUp:** | [Sincronização Perseus — Ensino Superior](https://app.clickup.com/t/17tu7rp2x7q) |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Integrações / Perseus Ensino Superior / Gestão de alunos |
| **Nível de Risco:** | **Alto** (altera `User.is_active`, controla acesso à plataforma e reativa usuários automaticamente) |
| **Qualidade da OpenSpec:** | ⭐⭐ (não há change em `openspec/changes/`; a descrição da task funciona como spec funcional detalhada) |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend
- Novo campo `Integration.perseus_student_status_mapping` (`JSONField`, default `{}`) + migração `integrations/0059_integration_perseus_student_status_mapping.py`. Guarda o DE-PARA `código de situação → ativo/inativo` por cliente.
- Novo serviço `fiscallizeon/integrations/services/perseus/student_status_service.py`:
  - `ENROLLMENT_STATUS_GROUPS`: catálogo de grupos/sugestões (Cursando, Contrato e pagamento, Pré-matrícula, Resultado do período, Movimentação interna, Curso encerrado, Saída da instituição).
  - `normalize_status_mapping` / `normalize_person_statuses`: validação do payload.
  - `person_should_be_active`: mantém ativo se **qualquer** matrícula estiver em situação ativa.
  - `build_students_status_rows`: devolve `id_erp`, `name`, `enrollment_number`, `is_active` dos alunos da Lize.
  - `apply_students_status`: inativa/reativa `User.is_active` via `bulk_update_with_history` (motivo `Situação de matrícula no Perseus`).
- Novos endpoints DRF:
  - `POST /integracoes/api/perseus/alunos/situacao/previa/` (`perseus-student-status-preview`).
  - `POST /integracoes/api/perseus/alunos/situacao/aplicar/` (`perseus-student-status-apply`) — salva o mapping e aplica as mudanças.
- `IntegrationsSynconizationsTemplateView` injeta `studentStatusGroups` e `studentStatusMapping` no `perseus_vue_initial_data`.

### Frontend (template Django + Vue)
- Wizard passa de 5 para **6 etapas**: `Unidades → Cursos → Disciplinas → Ofertas → Situação dos alunos → Alunos`.
- Nova aba `#student-status` com:
  - Bloco recolhível "Quais alunos continuam ativos na Lize?".
  - Carregamento em 3 fases (catálogo, matrículas por curso, comparação com a Lize).
  - Cards "Situações do Perseus" (barra verde/vermelha) e "Mudanças na Lize ao aplicar".
  - Agrupamento de situações, filtros Todas/Ativo/Inativo, busca com normalização de acentos, switch "Mostrar situações sem matrículas".
  - Botões "Restaurar sugestão", "Salvar e aplicar" e "Avançar para Alunos".
  - Prévia "O que muda ao aplicar" com abas Serão inativados / Serão reativados / Sem mudança e busca por aluno.
- Aba Alunos ganha a coluna **"Situação no Perseus"** com badge e "Fica ativo/inativo na Lize".
- "Sincronizar Enturmações" passa a aplicar o mapping salvo ao final e reportar inativados/reativados no Swal.
- Bloqueios de avanço: sem turmas sincronizadas, com alterações não salvas e antes de abrir a etapa.

---

## 2. Scope Boundaries (Diferenças de Escopo)

**IN SCOPE**
- Etapa 5 "Situação dos alunos": acesso, carregamento, sugestão, edição, filtros, prévia, salvar/aplicar e avanço.
- Coluna "Situação no Perseus" na etapa de Alunos.
- Aplicação automática da regra ao final da "Sincronizar Enturmações".
- Persistência do mapping por cliente e efeito em `User.is_active` (login de aluno inativado/reativado).
- Situações novas no Perseus (código fora do mapping salvo).

**OUT OF SCOPE**
- Sincronização de Unidades, Cursos, Disciplinas e Ofertas (etapas 1–4), exceto o necessário para destravar a etapa 5.
- Integrações Perseus Escolar, TOTVS, Sophia, LaPlace e demais ERPs.
- Envio de notas (`notes_send`) e demais fluxos de integração.
- Redesign visual das etapas 1–4 e da aba Alunos além da nova coluna.
- Alteração do cadastro do aluno em si (dados pessoais, matrícula, turmas) — validar apenas o `is_active`.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Tela de sincronização | `Chaves` → `Sincronizar Perseus` | `/integracoes/sincronizacoes/` | `integrations:integration_synconizations` |
| Etapa 5 — Situação dos alunos | `5. Situação dos alunos` (wizard no topo) | mesma URL (aba Vue `#student-status`) | — |
| Etapa 6 — Alunos | `6. Alunos` (wizard no topo) | mesma URL (aba Vue `#interships`) | — |
| Editar integração/credenciais | `Chaves` (formulário de integração) | `/integracoes/` [verificar] | `integrations:integration_create_update` |

**APIs críticas**

| Ação | URL | View name |
|---|---|---|
| Prévia dos alunos | `POST /integracoes/api/perseus/alunos/situacao/previa/` | `integrations:perseus-student-status-preview` |
| Salvar + aplicar | `POST /integracoes/api/perseus/alunos/situacao/aplicar/` | `integrations:perseus-student-status-apply` |
| Status já existente na Lize | `POST /integracoes/api/perseus/alunos/sync-status/` | `integrations:perseus-students-sync-status` |
| Sincronizar enturmações | `POST /integracoes/api/sincronizar/enturmacoes` | `integrations:sync_interships` |

> APIs externas chamadas **pelo navegador** no Perseus: `/v1/statusmatricula`, `/v1/pessoas/alunos/matriculas?codigoCurso=<codigo>` e `/v1/pessoas/alunos/matriculas/obter-por-codigo`.

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Persona

- **Coordenação** do cliente, com `user_type = coordination`, vínculo via `CoordinationMember` e permissão `integrations.view_integration`.
- Integração do cliente com `erp = Integration.PERSEUS_COLLEGE`, credenciais válidas e apontando para o **ambiente de teste** do Perseus.

### Comandos

```bash
source venv/bin/activate
pytest fiscallizeon/integrations/tests/test_perseus_sync.py fiscallizeon/integrations/tests/test_perseus_basic_service.py --reuse-db
# Regressão ampla de Perseus:
pytest fiscallizeon/integrations/tests/ -k perseus --reuse-db
```

> **Lacuna identificada:** a branch **não adicionou testes** para `student_status_service` nem para os endpoints `perseus-student-status-preview/apply` (o diff contra `origin/master` só toca APIs, model, migração, service, view, template e URLs). Antes do merge, é recomendável criar `fiscallizeon/integrations/tests/test_perseus_student_status.py` cobrindo: normalização, `person_should_be_active` (múltiplas matrículas), aplicação/reativação e isolamento por cliente.

### Setup Mixer

```python
from django.contrib.auth.models import Permission
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.clients.models import (
    Client,
    CoordinationMember,
    SchoolCoordination,
    Unity,
)
from fiscallizeon.integrations.models import Integration
from fiscallizeon.students.models import Student

client = mixer.blend(Client, has_exam_elaboration=True)
# user_type é derivado de CoordinationMember (property), não é campo do User.
coordinator = mixer.blend(User)
integration = mixer.blend(
    Integration,
    client=client,
    erp=Integration.PERSEUS_COLLEGE,
    username='usuario_perseus',
    password='senha_criptografada',
    base_url='https://perseus-teste.example/PerseusPublicApi',
)
unity = mixer.blend(Unity, client=client)
coordination = mixer.blend(SchoolCoordination, unity=unity)
mixer.blend(CoordinationMember, user=coordinator, coordination=coordination)
coordinator.user_permissions.set(
    Permission.objects.filter(
        codename__in=[
            'view_integration',
            'add_integration',
            'change_integration',
            'delete_integration',
        ]
    )
)

school_class = mixer.blend(
    SchoolClass, coordination=coordination, id_erp='TURMA-1'
)
student = mixer.blend(
    Student,
    client=client,
    id_erp='PESSOA-1',
    enrollment_number='2026001',
    user__is_active=True,
)
school_class.students.add(student)

# Primeira configuração (sem mapping salvo)
integration.perseus_student_status_mapping = {}
integration.save(update_fields=['perseus_student_status_mapping'])
```

Para simular configuração salva: `integration.perseus_student_status_mapping = {'MAT': True, 'CAN': False, ...}` e salvar.

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona global:** Coordenação do cliente com integração Perseus Ensino Superior configurada.
**Pré-condição global:** branch `feat/perseus-status-alunos`, migração `integrations 0059` aplicada, período letivo com turmas sincronizadas e alunos.

### 5.1 Acesso e etapas [Automatizável ✅]

#### Cenário 1 — Wizard com 6 etapas e bloqueio da etapa 5

**Ação humana:**
- [x] Acesse `Chaves` → `Sincronizar Perseus` (`/integracoes/sincronizacoes/`).
- [x] Confira no topo as etapas: `1. Unidades`, `2. Cursos`, `3. Disciplinas`, `4. Ofertas`, `5. Situação dos alunos`, `6. Alunos`.
- [x] Sem concluir Ofertas, clique em `5. Situação dos alunos`.
- [x] Confirme o aviso "**Etapa bloqueada**" com o texto "Conclua a etapa de Ofertas e turmas antes de abrir Situação dos alunos."
- [x] Vá até Ofertas, selecione o período, clique em "**Buscar Turmas**" e sincronize ao menos uma turma.
- [x] Clique em "**Avançar para Situação dos alunos**".
- [x] Antes de salvar qualquer configuração, confira a meta da etapa 5: "**Defina as situações**".
- [x] Após salvar (cenário 7), confira a meta no formato "**N ativas · M inativas**".

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/`
- Seletor: `.perseus-wizard-step:has-text("5. Situação dos alunos")`; meta em `.step-meta`
- Estado esperado: etapa bloqueada com `:disabled` + classe `.perseus-wizard-step--locked`; após destravar, `#student-status` visível
- Fixture: `setup_perseus_status_ui()` (Seção 4)

#### Cenário 2 — Avanço sem turma sincronizada

**Ação humana:**
- [x] Em Ofertas, sem nenhuma turma sincronizada, clique em "**Avançar para Situação dos alunos**".
- [x] Confirme o aviso "**Atenção**": "Sincronize ao menos uma turma antes de definir a situação dos alunos."

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/`
- Seletor: `#classes button:has-text("Avançar para Situação dos alunos")` → `.swal2-popup`
- Estado esperado: `.swal2-title` = `Atenção`; `#student-status` continua oculto
- Fixture: cliente com `SchoolClass` **sem** `id_erp` ou lista `syncedClasses` vazia

### 5.2 Carregamento das situações [Apenas Manual 👁]

> Classificado como manual por depender do tempo de resposta da API externa do Perseus (30–60 s com ~3 mil matrículas) e de mensagens transitórias.

#### Cenário 3 — Sequência de carregamento e cards

**Ação humana:**
- [x] Avance para a etapa 5 e acompanhe a mensagem de carregamento.
- [x] Confirme a passagem por "Buscando situações de matrícula no Perseus...", "Buscando matrículas por curso: X de Y" e "Comparando com os alunos da Lize...".
- [x] Ao terminar, confirme os cards "**Situações do Perseus**" e "**Mudanças na Lize ao aplicar**". ![](../evidencias/cards.png)
- [x] Confirme os grupos: Cursando, Contrato e pagamento, Pré-matrícula, Resultado do período, Movimentação interna, Curso encerrado, Saída da instituição.
- [x] Confira que, por padrão, aparecem só situações com matrículas nas turmas sincronizadas.
- [x] Ative "**Mostrar situações sem matrículas (N)**" e confirme que as demais aparecem.
- [x] Valide que a contagem de matrículas de cada situação considera apenas alunos das turmas sincronizadas do período.

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/` (aba `#student-status`)
- Seletor: `#student-status .text-center.text-muted` (loading); `#student-status .card:has-text("Situações do Perseus")`; `#statusShowEmpty`
- Estado esperado: `statusLoaded = true`; `.progress` com barras `bg-success`/`bg-danger`; linhas vazias com `.status-row--empty`
- Fixture: interceptar `/v1/statusmatricula` e `/v1/pessoas/alunos/matriculas*`; `integration.perseus_student_status_mapping = {}`

### 5.3 Explicação recolhível [Apenas Manual 👁]

#### Cenário 4 — Estado inicial e alternância do bloco explicativo

**Ação humana:**
- [x] Na primeira visita (sem mapping salvo), confirme que "**Quais alunos continuam ativos na Lize?**" começa **aberto**.
- [x] Clique no título e confirme que o bloco recolhe; clique de novo e confirme que expande.
- [x] Observe o chevron à direita mudando de sentido conforme o estado.
- [x] Leia o texto e confirme que explica: o que é ficar inativo, a regra de mais de uma matrícula e a reativação.

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/` (aba `#student-status`)
- Seletor: `#student-status details.status-legend`; `summary h6`; `.status-legend-chevron`
- Estado esperado: atributo `open` presente quando mapping vazio; ausente quando `studentStatusMapping` tem chaves; chevron com `transform: rotate(180deg)` quando aberto
- Fixture: duas execuções — mapping `{}` e mapping preenchido

### 5.4 Sugestão inicial [Automatizável ✅]

#### Cenário 5 — DE-PARA sugerido pela Lize

**Ação humana:**
- [x] Sem configuração salva, abra a etapa 5.
- [x] Confirme como **Ativo**: Cursando, Contrato e pagamento, Pré-matrícula; em Resultado do período: Aprovado e Apto.
- [x] Confirme como **Inativo**: Movimentação interna, Curso encerrado, Saída da instituição; em Resultado do período: Reprovado e Não Apto.
- [x] Confirme que "**Alterações não salvas**" aparece desde o início (nada foi salvo).

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/` (aba `#student-status`)
- Seletor: `tr:has-text("MAT") .status-choice button:has-text("Ativo")[aria-pressed="true"]`; `tr:has-text("CAN") .status-choice button:has-text("Inativo")[aria-pressed="true"]`
- Estado esperado: `mapping[code] === suggestedActive`; indicador `Alterações não salvas` visível
- Fixture: `integration.perseus_student_status_mapping = {}` + catálogo Perseus com `MAT`, `CAN`, `APR`, `REP`

### 5.5 Alteração das situações [Automatizável ✅]

#### Cenário 6 — Troca individual, ações de grupo, filtros e busca

**Ação humana:**
- [x] Em uma situação, clique em "**Inativo**" e depois em "**Ativo**"; confirme que a troca é imediata.
- [x] No grupo "Cursando", use "Marcar todas como **ativo**" e depois "**inativo**".
- [x] Use os filtros "**Todas (N)**", "**Ativo (N)**" e "**Inativo (N)**" e confirme que a lista respeita o filtro.
- [x] Busque por nome e por código, com e sem acento (ex.: "pré-matrícula" e "pre-matricula"); confirme que a busca ignora acentos.
- [x] Clique em "**Restaurar sugestão**" e confirme que as escolhas voltam à sugestão inicial.
- [x] Confirme que "**Restaurar sugestão**" fica desabilitado quando nada difere da sugestão.
- [x] Confirme a etiqueta "**alterado**" em situações diferentes da sugestão e o fundo avermelhado nas linhas inativas.

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/` (aba `#student-status`)
- Seletor: `tr:has-text("<CODIGO>") .status-choice button:has-text("Inativo")`; header do grupo `button:has-text("ativo")`; `input[type="search"][placeholder="Buscar situação ou código"]`; `button:has-text("Restaurar sugestão")`
- Estado esperado: `aria-pressed` refletido; `.status-row--inactive` (fundo `#fdf6f6`); `.badge-light` com texto `alterado`; botão de restaurar com atributo `disabled`
- Fixture: catálogo com acentos (`Pré-matrícula`) e código (`PMA`)

#### Cenário 7 — Barra e legenda do card atualizam

**Ação humana:**
- [x] Com o card "**Situações do Perseus**" visível, alterne situações entre Ativo/Inativo.
- [x] Confirme que a barra verde/vermelha muda de proporção imediatamente.
- [x] Confirme que a legenda atualiza a quantidade de situações e de matrículas de cada lado.
- [x] Confirme que o card "**Mudanças na Lize ao aplicar**" atualiza os números de inativados e reativados.

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/` (aba `#student-status`)
- Seletor: `.card:has-text("Situações do Perseus") .progress-bar.bg-success` (width inline); `.card:has-text("Mudanças na Lize ao aplicar")`
- Estado esperado: `width` das barras recalculado; contadores em `studentsToDeactivate.length` / `studentsToReactivate.length`
- Fixture: alunos com `is_active` variados e matrículas em `MAT`/`CAN`

### 5.6 Prévia do que muda [Automatizável ✅]

#### Cenário 8 — Abas da prévia, busca e múltiplas matrículas

**Ação humana:**
- [x] Clique em "**Ver quem muda**" e confirme que a tela rola até "**O que muda ao aplicar**".
- [x] Alterne entre "**Serão inativados (N)**", "**Serão reativados (N)**" e "**Sem mudança (N)**".
- [x] Confirme que as contagens do card e das abas mudam na hora conforme as situações escolhidas.
- [x] Busque um aluno por nome e por matrícula.
- [x] Confirme que cada aluno mostra as situações das matrículas em verde/vermelho e o resultado na Lize.
- [x] Em uma lista grande, confirme o limite de 100 alunos e o aviso para usar a busca.

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/` (aba `#student-status`)
- Seletor: `a:has-text("Ver quem muda")`; `#student-status-preview button:has-text("Serão inativados")`; `#student-status-preview tbody tr`; `input[placeholder="Buscar aluno por nome ou matrícula"]`
- Estado esperado: no máximo 100 `tbody tr`; `.card-footer` com `Mostrando X de Y`; badge verde/vermelho por código de matrícula
- Fixture: alunos da Lize com `id_erp`; `persons` contendo um aluno com `["MAT", "CAN"]` e `is_active=True`

### 5.7 Salvar e aplicar [Automatizável ✅]

#### Cenário 9 — Cancelar, confirmar, recarregar e login do aluno

**Ação humana:**
- [x] Com mudanças previstas, clique em "**Salvar e aplicar**".
- [x] No diálogo "**Aplicar situações?**", confirme que ele informa quantos alunos serão inativados e reativados.
- [x] Clique em "**Cancelar**" e confirme que nada mudou.
- [x] Repita e confirme com "**Salvar e aplicar**".
- [x] Confirme o diálogo "**Situações salvas**" com a quantidade de inativados e reativados.
- [x] Recarregue a página e volte à etapa: as escolhas devem voltar como salvas, sem "Alterações não salvas", e a prévia não deve mostrar novas mudanças.
- [x] Tente entrar na Lize com um aluno inativado: o login deve ser bloqueado.
- [x] Confirme que um aluno reativado volta a conseguir entrar.
- [x] Confirme que provas e notas dos inativados continuam existindo.
- [x] Sem nenhuma mudança prevista, clique em "Salvar e aplicar" e confirme que **não** há pedido de confirmação.

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/` (aba `#student-status`)
- Seletor: `button:has-text("Salvar e aplicar")`; `.swal2-confirm` / `.swal2-cancel`; `.swal2-title`
- Estado esperado: POST em `integrations:perseus-student-status-apply` retorna `{"deactivated": N, "reactivated": M}`; `Integration.perseus_student_status_mapping` persistido; `User.is_active` alterado com histórico
- Fixture: `Student.user.is_active=True` + matrícula `CAN`; verificar `student.user.refresh_from_db().is_active is False`

### 5.8 Avanço para Alunos [Automatizável ✅]

#### Cenário 10 — Bloqueio por alterações não salvas e coluna de situação

**Ação humana:**
- [x] Altere uma situação **sem salvar** e clique em "**Avançar para Alunos**".
- [x] Confirme o aviso "**Salve as situações**": "Salve e aplique as situações dos alunos antes de seguir para a etapa de Alunos." e que a etapa não muda.
- [x] Salve e clique novamente em "**Avançar para Alunos**"; a etapa 6 deve abrir.
- [x] Na tabela de alunos, confirme a coluna "**Situação no Perseus**" com a situação da matrícula em verde/vermelho e o texto "Fica ativo na Lize" ou "Fica inativo na Lize".

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/` (abas `#student-status` e `#interships`)
- Seletor: `button:has-text("Avançar para Alunos")`; `#interships th:has-text("Situação no Perseus")`; `#interships td .badge-success` / `.badge-danger`
- Estado esperado: `activeMainTab === 'interships'`; `.swal2-title` = `Salve as situações` quando `statusDirty`
- Fixture: `statusLoaded = true` + `perseusInterships` com `codigoMatricula` mapeado

### 5.9 Sincronização de alunos aplica a regra [Apenas Manual 👁]

> Classificado como manual porque depende do fluxo real de "Sincronizar Enturmações" contra a API do Perseus (criação de alunos e turmas reais).

#### Cenário 11 — Enturmação aplica situação e reporta inativados/reativados

**Ação humana:**
- [x] Com o mapping salvo, abra a etapa 6 e clique em "**Sincronizar Enturmações**".
- [x] Aguarde o término e confirme o diálogo "**Concluído!**" com "N de M alunos sincronizados.".
- [x] Confirme, logo abaixo, a quantidade de alunos inativados e reativados (ou "Nenhum aluno mudou de situação na Lize.").
- [x] Verifique um aluno **novo** criado nessa sincronização cuja matrícula esteja em situação inativa: ele deve ficar inativo.
- [x] Verifique um aluno existente que voltou a ficar ativo no Perseus: ele deve ser reativado.

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/` (aba `#interships`)
- Seletor: `#interships button:has-text("Sincronizar Enturmações")`; `.swal2-popup` (título `Concluído!`)
- Estado esperado: chamada final a `POST /integracoes/api/perseus/alunos/situacao/aplicar/` com `persons` do roster; `User.is_active` atualizado
- Fixture: `perseusInterships` com aluno em `CAN`; `statusLoaded=True`; mapping salvo com `CAN: false`

### 5.10 Situação nova no Perseus [Apenas Manual 👁]

#### Cenário 12 — Situação criada depois da configuração

**Ação humana:**
- [x] Remova uma situação da configuração salva (`perseus_student_status_mapping` da integração), simulando uma situação criada depois no Perseus.
- [x] Volte à etapa 5 e recarregue as situações.
- [x] Confirme o aviso "**O Perseus tem N situação(ões) que você ainda não definiu: <código>**". ![](../evidencias/cod_novo.png)
- [x] Confirme que a situação recebeu a etiqueta "**nova**". 

  ![](../evidencias/nova.png)
- [x] Confirme que, até salvar, alunos nessa situação continuam ativos.
- [x] Salve e confirme que o aviso desaparece.

**Referência técnica (para automação):**
- URL: `/integracoes/sincronizacoes/` (aba `#student-status`)
- Seletor: `#student-status .alert-warning`; `tr:has-text("<CODIGO>") .badge-warning`
- Estado esperado: `newStatusCodes` contém o código; `mapping[code] = true`; após salvar, `savedMapping[code]` definido e aviso oculto
- Fixture: mapping salvo sem um código presente no catálogo Perseus (`{"MAT": true}` + catálogo com `MAT` e `NOVA`)

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] Tirar screenshot da tela completa com as **6 etapas** e confirmar que a etapa 5 fica entre `Ofertas` e `Alunos`. 
- [x] Tirar screenshot do card "**Situações do Perseus**" com a barra verde/vermelha e a legenda.
- [x] Tirar screenshot das linhas inativas (fundo `#fdf6f6`) e das etiquetas `alterado`/`nova`. ![](../evidencias/tela_badges.png)
- [x] Tirar screenshot da prévia "**O que muda ao aplicar**" nas três abas.

  #### inativos
  ![](../evidencias/inativos.png) 
  #### reativados
  ![](../evidencias/reativos.png)
  #### Sem mudança
  ![](../evidencias/sem_mudancas.png) 

- [x] Tirar screenshot da coluna "**Situação no Perseus**" na etapa de Alunos. ![](../evidencias/situacao.png)
- [x] Validar em resolução intermediária (1333×1080) e em tela menor: filtros, botões e tabela não devem quebrar/estourar.
- [x] Comparar com a descrição da task no ClickUp (não há mockup/Figma anexado; usar a descrição como referência).

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!WARNING]
> **Instruções de registro:** use `> [!BUG]` para falhas e `> [!WARNING]` para riscos. Categorize com `[UX/UI]`, `[Backend Logic]`, `[Database]` ou `[Spec Gap]`. Cite a origem da expectativa (task do ClickUp ou inferência de UX).

### Riscos levantados na análise estática (validar em execução)

> [!WARNING]
> **[Backend Logic] Aplicação ao final da sincronização depende do estado carregado na etapa 5**
> **Contexto:** `applyStudentStatusAfterSync()` só roda se `statusLoaded && statusMappingIsSaved`. Se o usuário entrar na etapa de Alunos por outro caminho (ex.: recarregar a página direto na etapa 6) sem recarregar a etapa 5, a regra pode não ser aplicada ao final da sincronização.
> **Comportamento esperado:** a regra deve ser aplicada sempre que houver mapping salvo, mesmo que a etapa 5 não tenha sido carregada nesta sessão.
> **Workaround:** antes de sincronizar enturmações, abra a etapa 5 para forçar o carregamento e depois avance para Alunos.

> [!WARNING]
> **[Backend Logic] Situação não encontrada na API mantém o aluno como está**
> **Contexto:** `personStatuses` omite matrículas cujo status não foi retornado pelo Perseus; esses alunos não entram no payload e não são alterados.
> **Comportamento esperado:** deve ser claro para o usuário que alunos sem situação retornada não são avaliados.
> **Workaround:** usar "**Atualizar do Perseus**" e conferir se todas as matrículas foram resolvidas antes de salvar.

> [!WARNING]
> **[Spec Gap] Ausência de testes automatizados para a nova regra**
> **Contexto:** não há `test_perseus_student_status.py` na branch; a cobertura atual não exercita `apply_students_status` nem os endpoints novos.
> **Comportamento esperado:** cobertura automatizada mínima antes do merge.
> **Workaround:** executar o roteiro manual completo desta seção.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **[Backend] Extrair o catálogo `ENROLLMENT_STATUS_GROUPS` para configuração/seed** — hoje os grupos e sugestões estão hardcoded em `student_status_service.py`; clientes com particularidades precisam de deploy para ajustar.

> [!NOTE]
> **[Frontend] Persistir `selectedPeriod` na URL/estado** — ao recarregar a página a etapa 5 perde o recorte de período e exige refazer a busca de turmas.

> [!NOTE]
> **[UX] Indicar explicitamente quais alunos não tiveram situação resolvida** na prévia, em vez de apenas omiti-los.

> [!NOTE]
> **[Performance] Cachear o catálogo de situações por cliente** para reduzir o tempo de 30–60 s em clientes grandes.

---

## 8.1 Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.

🔗 **[Ver Mapeamento de Tela](../docs/tests/usability/perseus_ensino_superior_syncronizations.md)**

**Snippet de automação (setup + UI)** — cobre mixer e interceptação das APIs externas:

```python
def test_fluxo_situacao_alunos(page, live_server):
    # 1) Setup de banco via mixer (persona coordenação + integração Perseus College)
    data = setup_perseus_status_ui()

    # 2) Interceptar a API externa chamada pelo navegador
    page.route("**/v1/statusmatricula*", lambda r: r.fulfill(json=[
        {"codigo": "MAT", "nome": "Matriculado"},
        {"codigo": "CAN", "nome": "Cancelado"},
    ]))
    page.route("**/v1/pessoas/alunos/matriculas*", lambda r: r.fulfill(json=[
        {"codigo": "MATRICULA-1", "status": {"codigo": "MAT", "nome": "Matriculado"}},
    ]))

    # 3) Abrir a etapa 5 e validar sugestão inicial
    page.locator('.perseus-wizard-step:has-text("5. Situação dos alunos")').click()
    page.wait_for_selector('#student-status')
    assert page.locator('#student-status').get_by_text('Situações do Perseus').is_visible()

    # 4) Inativar uma situação e salvar
    page.locator('tr:has-text("MAT") .status-choice button:has-text("Inativo")').click()
    page.locator('button:has-text("Salvar e aplicar")').click()
    page.locator('.swal2-confirm').click()

    # 5) Validar persistência no banco
    data['integration'].refresh_from_db()
    assert 'MAT' in data['integration'].perseus_student_status_mapping
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Bottleneck:** dependência da API externa do Perseus (30–60 s) e da criação de cenários de matrícula (múltiplas matrículas, situações de saída) para validar a prévia.
- **Back-and-forth com desenvolvimento:** [preencher — houve dúvida sobre o recorte de período, situação nova ou reativação automática?]
- **Como melhorar o fluxo:** [preencher — ex.: seed de cliente Perseus com catálogo e matrículas determinísticas no Cloud Lab.]

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
- A task já traz um roteiro de testes muito detalhado; o plano deve reutilizar os critérios de aceite literais para evitar divergência de expectativa.
- Para features que dependem de API externa chamada pelo navegador, vale padronizar no workflow a recomendação de `page.route(...)` como estratégia de automação.
