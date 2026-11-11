# Mapeamento de Tela: teacher_tabs.html (Painel do Professor - /painel/professor/)

> **Nota de Acervo:** Este arquivo é alimentado de forma incremental e colaborativa. Sempre que uma nova funcionalidade for testada nesta tela/componente, o mapeamento de IDs e seletores estáveis deve ser atualizado aqui. O objetivo é criar um repositório centralizado para facilitar a automação via Playwright, sem depender de classes CSS frágeis.

## 1. URLs e Navegação
- **URL Base:** `/painel/professor/` ou `/` (quando autenticado com `user.user_type == TEACHER`)
- **View Django:** `fiscallizeon.core.views.DashboardTeacherView` (template `dashboard/teacher_v3.html`)
- **Componentes Centrais:** `teacher_panel` (`teacher_panel.html` / `teacher_panel.js`) e `teacher_tabs` (`teacher_tabs.html`)
- **Navegação UI:** Ao logar como professor, a Home da plataforma abre diretamente no Painel do Professor (`/painel/professor/`).

## 2. Abas do Painel Principal
O painel exibe um conjunto de 3 abas principais:
1. **"Elaborar"** (Aba padrão / ativa):
   - Exibe os cadernos que a Coordenação solicitou para este professor elaborar questões.
   - Badge vermelha com contador de cadernos a elaborar (ex: `1`).
2. **"Revisar"** (Aba central):
   - Visível **apenas** quando `user.inspector.is_discipline_coordinator = True`.
   - Exibe os cadernos que **outros professores** elaboraram e que estão aguardando aprovação/revisão deste professor coordenador de disciplina.
   - É alimentada assincronamente pela API `GET /exams/api/prova/get_exams_to_review/?page_size=6` (que consome o método `Inspector.get_exams_to_review`).
3. **"Corrigir"** (Aba à direita):
   - Visível quando o cliente possui a flag de correções/followup.

## 3. Seletores DOM e Ações

### 3.1. Abas de Navegação (Tabs)
- **Container das Abas:** `div[x-data="teacherTabsAlpine()"]`
- **Aba "Elaborar":**
  - Seletor: `button#opened` ou elemento com texto `"Elaborar"`
  - Badge de contagem: `span` com número de solicitações (ex: `1`)
- **Aba "Revisar":**
  - Seletor: `div:has(span:has-text("Revisar"))` (com `@click="active = 'review'"`)
  - Badge de contagem: `span[x-text="count_exams_to_review"]`
  - Link/Botão inferior para ver todas: `button:has-text("Todas as revisões")` (redireciona para `/provas/professor/revisar/?v=2`)
- **Aba "Corrigir":**
  - Seletor: `div:has(span:has-text("Corrigir"))` (com `@click="active = 'corrections'"`)

### 3.2. Cards de Cadernos no Painel de Revisão (Aba "Revisar")
- **Container do Card:** `div.tw-border.tw-rounded-lg:has(h2)`
- **Badge de Prazo:** `span` com status de prazo (ex: `"Dentro do prazo"`, `"Atrasado"`)
- **Disciplina:** `p.tw-text-gray-500` (ex: `"Álgebra"`)
- **Título do Caderno:** `h2.tw-font-semibold` (ex: `"Caderno Rayssa Teste"`)
- **Série do Caderno:** `p.tw-text-sm.tw-text-[#9BA3AF]` (ex: `"Anos iniciais - 1º Ano"`)
- **Contador de Questões:** `p:has-text("questões")` (ex: `"0 de 5 questões"`)
- **Botão Continuar:** `a:has(button:has-text("Continuar"))` (redireciona para a tela de revisão: `/provas/<exam_id>/revisar/?exam_teacher_subject=<ets_id>`)

### 3.3. Estado Vazio (Aba "Revisar" sem pendências)
- `div[x-show="examsToReviewLoaded && count_exams_to_review <= 0"]`
- Título: `"Não há questões para revisão"`
- Descrição: `"Parabéns! Você não possui questões para serem revisadas."`

## 4. API Interception & Endpoints
- `GET /exams/api/prova/get_exams_to_review/?page_size=6` — Endpoint DRF que alimenta os cards da aba **"Revisar"** com base em `Inspector.get_exams_to_review`.
- `GET /provas/professor/revisar/` — Tela completa de listagem de todas as revisões.
