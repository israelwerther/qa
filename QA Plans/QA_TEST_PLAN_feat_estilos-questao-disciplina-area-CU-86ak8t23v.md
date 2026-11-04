## 0. Metadata (Metadados de QA)

| Campo                      | Valor                                                                                                                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data:**                  | 2026-11-03                                                                                                                                                                   |
| **Natureza da Tarefa:**    | `[Business Feature]`                                                                                                                                                         |
| **Área da Feature:**       | Exams / Impressão — Cabeçalho de questão, Disciplina e Área (Padrões de Impressão)                                                                                           |
| **Nível de Risco:**        | Médio                                                                                                                                                                        |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐                                                                                                                                                                   |
| **ClickUp:**               | [86ak8t23v](https://app.clickup.com/t/86ak8t23v) — status **to test staging**; OpenSpec prevalece sobre o pitch. Branch: `feat/estilos-questao-disciplina-area-CU-86ak8t23v` |

**Resumo da task (ClickUp / OpenSpec):** Implementada a personalização visual do cabeçalho das questões nos modelos de impressão, com 6 estilos pré-definidos (Clássico, Centralizado com barra — Estilo ENEM, Em Caixa/Moldura, Pílula/Badge, Minimalista e Barra Lateral) e ajustes granulares (cores primária/secundária, alinhamento, caixa alta, negrito, formato do número, cantos e bordas). O estilo ENEM foi ajustado para seguir o padrão oficial do INEP (linha fina superior de 1px com 50% de opacidade e barra inferior de 3px com terminação escura).

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend

- `fiscallizeon.clients.models.ExamPrintConfig`: campos `question_header_style` (choices, default `0` = Clássico), `question_header_color` (`CharField(7)`, default `'#000000'`), `question_header_secondary_color` (`CharField(7)`, default `''`) e campos granulares `question_header_*` (alinhamento, maiúsculas, negrito, formato de número, zero à esquerda, cantos) + barras `question_header_border_{left,top,bottom,right}`.
- Migração Django aditiva (somente `AddField` com defaults).
  - clients.0217_examprintconfig_question_header_color_and_more
  - clients.0218_examprintconfig_question_header_alignment_and_more
  - clients.0219_remove_examprintconfig_question_header_background_color_and_more
  - clients.0220_examprintconfig_question_header_border_bottom_and_more
- APIs: `SimplePrintConfigSerializer` e `ExamPrintConfigViewSet` (`clients/api/print_configs.py`); `ExamPrintConfigUpdateApi` (`exams/apis.py`) com validação de cor no formato `#RRGGBB`.

### Frontend / UI

- `fiscallizeon/exams/templates/dashboard/exams/v2/exam_configs_form.html`: nova seção de presets, seletor de cores, painel de personalização granular reativo e mini-amostra.
- `fiscallizeon/clients/templates/clients/print_defaults_create_update.html`: integração reativa com o bloco Vue.
- `fiscallizeon/exams/templates/dashboard/exams/includes/exam/question_header.html`: partial modular com os 6 presets.
- Refatoração em `not_separate.html`, `separate_subjects.html` e `separate_category.html`.
- Replicação de parâmetros: `diagram_layout_list.js`, `exam_print.html` (v1 e v2), `modal_print.html`, `exam_list_new.html`, `application_list_new.html`, `distribution_list.html` e `omr/mockup_utils.py`.

### Testes

- `fiscallizeon/clients/tests/test_exam_print_config.py` e `fiscallizeon/clients/tests/test_print_configs_api.py`.
- `fiscallizeon/exams/tests/test_exam_print_question_header_styles.py` e malotes de aplicações/distribuição.

---

## 2. Scope Boundaries (Diferenças de Escopo)

### IN SCOPE (validar neste QA)

- Persistência e API dos novos campos com isolamento multi-tenant por `Client`.
- Mini-amostra dinâmica no formulário respondendo a preset, cor e switches de visibilidade.
- Renderização nos templates de impressão (prova individual, caderno).
- Aplicação do estilo no Diagramador (via **"Usar modelo"**), em PDF e em malotes (Aplicações e Ensalamento).
- Retrocompatibilidade do preset `0` (Clássico) com defaults que reproduzem o layout legado.
- Modo **Preto e Branco / Risógrafo** (`all_black`) convertendo cores do cabeçalho.

### OUT OF SCOPE (não bloquear release por ausência)

- Editor livre de layout, tamanho de fonte independente, customização por questão avulsa, posição de nota/disciplina/área.
- Templates legados obsoletos.
- App do Aluno (`/api/v3/`).

### BLOQUEADO POR INFRA (documentar, não fechar release sem plano)

- Comparação visual de malote PDF legado vs. novo (depende de print service — padrão QA-117 do redesign).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

**CRITICAL:** Create a Canonical Navigation Map table. If you inferred a URL, View, or UI Menu Label from the code and are not 100% certain it matches the visual UI text, you MUST mark it with a `[verificar]` tag.

| Destino                          | Rótulo real no menu UI                              | URL Django                                          | View name                      |
| -------------------------------- | --------------------------------------------------- | --------------------------------------------------- | ------------------------------ |
| Criar/editar padrão de impressão | **Padrões de impressão** `[verificar]`              | `/membros/padrao/configuracao/cadastrar/`           | `clients:print-configs-create` |
| Editar padrão existente          | **Padrões de impressão** `[verificar]`              | `/membros/padrao/configuracao/atualizar/<uuid:pk>/` | `clients:print-configs-update` |
| Visualizar prova                 | Instrumentos Avaliativos → Visualizar `[verificar]` | `/provas/<uuid>/visualizar`                         | `exams:exams_preview`          |
| Diagramar caderno (V2)           | Instrumentos Avaliativos → Diagramar `[verificar]`  | `/provas/<uuid>/v2/diagramacao/`                    | —                              |
| Imprimir prova (V2)              | —                                                   | `/provas/<uuid>/v2/imprimir/`                       | `exam-print-v2`                |
| Imprimir malote                  | —                                                   | `/aplicacoes/`, `/distribuicao/`                    | —                              |

- Menu pai do item pode ser **Configurações** ou **Gerenciamento** — registrar `[verificar]` no QA.
- No Diagramador, o gatilho de aplicação de modelo é o botão **"Usar modelo"** (`diagram_layout_list.js`).

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comandos CLI

```bash
source venv/bin/activate && pytest fiscallizeon/clients/tests/test_exam_print_config.py fiscallizeon/exams/tests/test_exam_print_question_header_styles.py --reuse-db
source venv/bin/activate && pytest fiscallizeon/clients/ fiscallizeon/exams/ --reuse-db
./scripts/dev/predeploy.sh --no-tty
```

### Setup Mixer (padrão com preset customizado — coordenador)

```python
from mixer.backend.django import mixer
from fiscallizeon.clients.models import Client, ExamPrintConfig

client_obj = mixer.blend(Client, has_exam_elaboration=True, two_factor_enabled=False)
config = ExamPrintConfig.objects.create(
    client=client_obj,
    name='Padrão QA',
    is_default=True,
    question_header_style=1,  # 0 Clássico, 1 Centralizado c/ barra (ENEM), 2 Em Caixa/Moldura, 3 Pílula/Badge, 4 Minimalista, 5 Barra Lateral
    question_header_color='#1D4ED8',
    question_header_secondary_color='#000000',
    question_header_alignment=0,
)
```

### Setup Exam + Application (preview/impressão)

```python
from mixer.backend.django import mixer
from fiscallizeon.exams.models import Exam, ExamQuestion

exam = mixer.blend(Exam, created_by=mixer.blend('fiscallizeon.accounts.models.User'), is_printed=False)
exam_question = mixer.blend(ExamQuestion, exam=exam, order=1)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

**Persona padrão:** Coordenador com módulo de elaboração de provas.

### 5.1 Configuração de Padrões de Impressão — Presets e Personalização [Automatizável ✅ / Apenas Manual 👁]

#### Cenário 1 — Cadastro/edição de padrão com preset e cor (fluxo principal)

**Ação humana:**

- [x] Acessar **Configurações → Provas → Padrões de impressão** e criar/editar padrão.
- [x] Selecionar preset **Clássico (Padrão atual)** e confirmar cor primária `#000000`.
- [x] Selecionar preset **Centralizado com barra (Estilo ENEM)** e informar cor institucional (ex.: `#1D4ED8`).
- [x] Salvar o padrão e confirmar que as preferências são mantidas ao reabrir.

**Referência técnica (para automação):**

- URL: `/membros/padrao/configuracao/cadastrar/`
- Seletor: container de presets/mini-amostra `[verificar]`
- Estado esperado: `question_header_style` e `question_header_color` persistidos via API
- Fixture: `ExamPrintConfig` com `question_header_style=1` e `question_header_color='#1D4ED8'`

#### Cenário 2 — Personalização granular, troca de preset e restaurar padrão

**Ação humana:**

- [x] Sobre o preset selecionado, ajustar cores primária/secundária, alinhamento, caixa alta, negrito, formato do número e cantos.
- [x] Trocar de preset e confirmar que os ajustes passam a refletir os defaults do novo preset (fallback: ao selecionar **Estilo ENEM**, alinhamento Centro volta a **Esquerda**).
- [ ] Acionar a restauração de valores do preset (**Restaurar padrão do preset**) e confirmar o reset dos campos granulares ao default do preset `[verificar]`.

**Referência técnica (para automação):**

- Campos: `question_header_alignment`, `question_header_uppercase`, `question_header_bold`, `question_header_number_format`, `question_header_zero_padded`, `question_header_corner`, `question_header_border_left`, `question_header_border_top`, `question_header_border_bottom`, `question_header_border_right`.
- Estado esperado: valores persistidos e refletidos na mini-amostra.

#### Cenário 3 — Desativação visual limpa (alinhamento Centro no ENEM; cantos sem moldura/badge)

**Ação humana:**

- [x] Com preset **Estilo ENEM** selecionado, verificar que a opção de alinhamento ao **Centro** fica desabilitada no seletor e que o fallback automático para **Esquerda** (`0`) é aplicado.
- [x] Verificar que o controle de **Cantos** permanece visível e desabilitado nos presets que não usam moldura/badge (Clássico, ENEM, Minimalista, Barra Lateral).

---

### 5.2 Estilo ENEM — Barras, cor secundária e fechamento [Apenas Manual 👁]

#### Cenário 4 — Estilo ENEM (barra superior/baixa + bloco final)

**Ação humana:**

- [x] Selecionar preset **Estilo ENEM** e definir cor de destaque e cor secundária.
- [x] Verificar se a linha fina superior herda a cor do texto com opacidade suave (≈50%) e se a barra inferior de 3px exibe a cor secundária com o bloco final (20%) na cor do texto.

**Referência técnica (para automação):**

- Campos: `question_header_color`, `question_header_secondary_color`.
- Estado esperado: linha superior/baixa renderizadas conforme preset.

---

### 5.3 Impressão da Prova — Diagramação, PDF e Preto e Branco [Automatizável ✅ / Apenas Manual 👁]

#### Cenário 5 — Aplicar estilo via Diagramar (Usar modelo)

**Ação humana:**

- [x] Abrir uma prova vinculada a um padrão com estilo e ir à tela de diagramação.
- [x] Acionar **"Usar modelo"** e confirmar que a prévia atualiza para o estilo e a cor escolhidos.

**Referência técnica (para automação):**

- URL: `/provas/<uuid>/v2/diagramacao/`
- Ação: aplicar `ExamPrintConfig` do caderno.

### 5.4 Impressão de Malote — Aplicações e Ensalamento [Apenas Manual 👁 + Infra]

#### Cenário 6 — Gerar malote respeitando estilo e cores

**Ação humana:**

- [x] Gerar o malote da prova (tanto via **Aplicações** quanto via **Ensalamento**).
- [x] Confirmar que o caderno no malote respeita o estilo e as cores configuradas.

---

### 5.5 Retrocompatibilidade, granularidade e isolamento multi-tenant [Automatizável ✅]

#### Cenário 7 — Preset Clássico reproduz layout legado; isolamento por Client

**Ação humana:**

- [x] Abrir um padrão/caderno sem estilo novo e confirmar que o visual atual (sem estilo novo) continua igual.
- [x] Confirmar isolamento: padrão criado por um `Client` não aparece/altera dados de outro.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [x] Capturar prints da tela de criação/edição de padrão com mini-amostra (6 presets). ![](../evidencias/presets.png)
- [x] Capturar prints da prévia da diagramação e do PDF individual com preset customizado.![](../evidencias/diagramacao.png)
- [x] Comparar com `openspec/changes/estilos-visuais-questao-disciplina-area-86ak8t23v/references/preview-estilos.html` e `comparativo-antes-depois.html`.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!BUG] **[Título do bug]**
> **Contexto/Causa raiz:** …
> **Comportamento esperado:** … (conforme OpenSpec: `spec.md` L.XX — quando aplicável)
> **Workaround (Gambiarra temporária):** …

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE] **Editor livre de layout** — fora do MVP; candidato a incremento futuro.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML/View, e não a View.

🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_configs_form.md)**

### Snippet Playwright + setup de dados

```python
import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from mixer.backend.django import mixer
from playwright.sync_api import Page, expect

from fiscallizeon.clients.models import Client, ExamPrintConfig
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.classes.models import Grade
from fiscallizeon.subjects.models import Subject
from fiscallizeon.questions.models import Question, QuestionOption


@pytest.mark.django_db(databases="__all__")
def test_print_config_question_header_style(page: Page, live_server):
    client_obj = mixer.blend(Client, has_exam_elaboration=True, two_factor_enabled=False)
    unity = mixer.blend(Unity, client=client_obj)
    coordination = mixer.blend(SchoolCoordination, unity=unity)
    grade = mixer.blend(Grade)
    subject = mixer.blend(Subject)

    perms = Permission.objects.filter(
        codename__in=["coordination", "add_question", "change_question", "view_question"]
    )
    user = mixer.blend(User, two_factor_enabled=False, must_change_password=False)
    mixer.blend(CoordinationMember, user=user, coordination=coordination)
    user.user_permissions.set(perms)

    config = ExamPrintConfig.objects.create(
        client=client_obj,
        name="Padrão QA",
        is_default=True,
        question_header_style=1,
        question_header_color="#1D4ED8",
    )

    page.goto(f"{live_server.url}{reverse('clients:print-configs-list')}")
    expect(page.get_by_text("Padrões de impressão")).to_be_visible()
```

---

## 9. QA Retrospective (Retrospectiva de QA)

_Preencher após execução:_

- **Principal gargalo:** …
- **Back-and-forths com dev:** …
- **Melhoria de workflow:** …

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->

---

## Objetivos da Sessão Atual de Teste (Validação do Prompt V2)

Durante os testes da branch atual (como "prova de fogo" do Prompt V2), nosso foco é validar e garantir os seguintes pontos ao final:

1. **Otimização:** Descobrir formas de otimizar ainda mais o Prompt V2.
2. **Entendimento de Fluxo:** Validar se a forma como o plano é estruturado realmente ajuda a IA a compreender com clareza o fluxo da tela testada.
3. **Mapeamento para Automação Futura:** Confirmar se o mapeamento técnico criado (seletores, URLs reais, fixtures) permitiria à IA testar _novas funcionalidades_ desta tela no futuro, com total autonomia.
4. **Sugestões de Melhorias:** Registrar ativamente minhas sugestões (como IA) de ajustes ou correções na especificação, no teste ou no próprio prompt durante a nossa interação.
