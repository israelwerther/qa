# Plano de Testes de QA: Redesign Fluxo de Visualização do Caderno

> Branch: `feat/redesign-fluxo-caderno-CU-86af0r0fx`  
> Tarefa ClickUp: `CU-86af0r0fx`  
> Referências OpenSpec: `openspec/changes/redesign-fluxo-visualizacao-caderno/`

---

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-08-03 |
| **Natureza da Tarefa:** | `[Business Feature]` (Redesign do preview fullscreen de cadernos) |
| **Área da Feature:** | Exams (Visualização de Provas/Cadernos) |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐ (4/5 estrelas) |

---

## 1. Resumo das Alterações
- Criação de componente shell genérico `fullscreen_layout` reutilizável, alinhado com o Figma.
- Nova superfície de Visualizar Prova ("Visualizar caderno"), preservando o preview legado como fonte da verdade funcional.
- Mudança do destino das listagens (Instrumentos avaliativos, Todos os cadernos, Listas de exercícios) para a nova URL de preview.
- Funcionalidades mantidas: revisão, seleção em lote, cópia, PDF, filtros por perfil, trilho de ações condicional.
- Adição de novos componentes específicos `exam_preview_*` utilizando Alpine.js e Tailwind.

## 2. Diferenças de Escopo (Scope Boundaries)
**IN SCOPE:**
- Modal fullscreen para visualização do caderno via `/provas/<uuid>/visualizar/v2`.
- Validação das ações da tela (Selecionar, Editar, Copiar, Revisar, Lize IA) via Alpine.js.
- Listagem scrollável de cards de questões com tabs (Enunciado, Dados Pedagógicos, Histórico, Utilizações).
- Paridade de permissões de Coordenador e Professor.

**OUT OF SCOPE:**
- Alteração no comportamento de negócio, permissões do backend, e APIs.
- Migração dos fluxos "Revisar Caderno" e "Editar Caderno" (continuam no modal legado).
- Redesign do preview de fiscal ou preview simples.

## 3. Navegação e Camada Técnica
| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Lista de provas | Instrumentos Avaliativos | `/provas/?category=exam` | `exams_list` |
| Visualizar Prova (Novo) | (link na listagem) | `/provas/<uuid>/visualizar/v2` | `exams_preview_redesign` |

## 4. Testes Automatizados e Setup de Dados
**Comando pytest:**
```bash
pytest fiscallizeon/exams/tests/components/test_exam_preview.py
```

**Setup Mixer / Fixtures (Camada Técnica):**
Para gerar dados locais equivalentes e acessar como Coordenador:
```python
# Setup para acessar como coordenador com permissões para ações da prova
from fiscallizeon.exams.models import Exam
from fiscallizeon.accounts.models import CustomUser

# Assumindo uso do mixer:
# exam = mixer.blend('exams.Exam', ...)
# user = mixer.blend(CustomUser, is_superuser=True)
# self.client.force_login(user)
```
*Persona de teste:* Coordenador (com permissão total) e Professor (apenas leitura ou edição da sua matéria).

## 5. Roteiro de Testes (Execution Test Script)

### 5.1. Acesso à Nova Superfície
- [x] **Ação humana (Coordenador):** Acessar "Instrumentos Avaliativos", buscar uma prova, e clicar no ícone/link de "Visualizar". [Automatizável ✅]
  - *Camada Técnica:* 
    - URL inicial: `/provas/?category=exam`
    - URL destino: `/provas/<uuid>/visualizar/v2`
- [x] **Ação humana (Professor):** Acessar "Listas de exercícios" ou "Todos os cadernos" e clicar em "Visualizar lista/prova". [Automatizável ✅]
- [ ] **Ação humana (Professor - Extra ClickUp):** Acessar "Cadernos > Listas de exercícios > Editar lista > Adicionar questão", e tentar visualizar uma questão por ali (pelo fluxo de editar caderno). Validar se o padrão visual foi mantido. [Automatizável ✅]

### 5.2. Visualização de Cards e Tabs (Read-only vs Ações)
- [ ] **Ação humana:** Verificar o scroll da lista de cards (gap de ~80px) e checar se as tabs "Enunciado, Dados Pedagógicos, Histórico, Utilizações" funcionam por card sem recarregar a página. [Apenas Manual 👁]
  - *Camada Técnica:* Interações via Alpine.js (`x-data`, `x-show` nas tabs).
- [ ] **Ação humana:** Testar a visualização com uma conta de Coordenador (que deve ver o trilho de ações: Selecionar, Editar, Copiar, Revisar). [Automatizável ✅]
- [ ] **Ação humana:** Testar a visualização com uma conta que não possui permissão de edição (apenas leitura). O trilho de ações **não** deve aparecer. [Automatizável ✅]

### 5.3. Interatividade: Bulk Selection
- [ ] **Ação humana:** Clicar em "Selecionar" no trilho de ações de múltiplas questões e verificar se o estado de seleção múltipla funciona (bulk selection). [Automatizável ✅]
  - *Camada Técnica:* Verificar estado dos componentes Alpine e disparos para `exams_status_question_api_create` ou APIs similares.

### 5.4. Sidebar e Botão Salvar
- [ ] **Ação humana:** Verificar se a Sidebar direita (400px) apresenta corretamente o resumo da prova. [Apenas Manual 👁]
- [ ] **Ação humana:** Verificar se o CTA "Salvar" só aparece/fica habilitado quando há uma ação de persistência pendente. [Apenas Manual 👁]

## 6. Validação Visual e de Layout
- [ ] Tirar screenshot da tela `/visualizar/v2` inteira (Fullscreen layout) e colocar lado a lado com o Figma (`13827:8748`).
- [ ] Tirar screenshot da variante sem permissão (sem trilho de ações) e comparar com o Figma (`13827:51029`).
- [ ] Checar espaçamentos (gap de 80px entre cards) e uso da font/cores do Tailwind (`tw-*`).

## 7. Problemas Encontrados (Bugs)

> [!BUG]
> **Título:** [UX/UI] Ícone de Nível de Dificuldade não reflete a cor correta (Figma)
> **Causa Raiz:** O componente que renderiza o nível de dificuldade (ex: "Nível Difícil") está aplicando a cor verde padrão para o ícone de gráfico de barras, independentemente do nível de dificuldade real.
> **Comportamento Esperado:** (conforme Figma de referência) A cor do ícone deve mudar dinamicamente conforme a dificuldade. Para "Nível Difícil", o ícone deve ser vermelho, assim como estipulado no layout.
> **Workaround:** Nenhum workaround necessário para os testes. Bug apenas visual.

> [!WARNING]
> **Título:** [Tech Debt / Frontend] Erro de Alpine no Console ao renderizar badge ETS (Filtro)
> **Causa Raiz:** O Django renderiza `@click="$store.examPreview.toggleEtsGroup(["uuid"...])"`. O Alpine acusa `Unexpected token '}'` no console devido ao escape de aspas na diretiva `:class` ou `@click`.
> **Comportamento Observado:** Apesar do erro ruidoso no console, o usuário (QA) reportou que a funcionalidade de clicar no filtro e selecionar o grupo **funciona perfeitamente** na prática.
> **Comportamento Esperado:** O console deve estar limpo de erros de *parse* do Alpine. Recomenda-se corrigir o escape (ex: inverter aspas para simples no atributo) para evitar sujeira no log ou comportamentos inesperados em navegadores mais rígidos.
> **Workaround:** Nenhum workaround funcional é necessário para testes, mas a correção técnica é recomendada (usar aspas simples no atributo HTML).

## 8. Melhorias Futuras
> [!NOTE]
> - O OpenSpec sugere que no futuro o redesign abra sobre a própria listagem sem navegar para uma rota fullscreen separada (Open Question #1 do design.md). 

## 8.1. Knowledge Base Notes
- [ ] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.
🔗 **[Ver Mapeamento de Tela](../../../docs/tests/usability/exam_preview_redesign.md)**

---

## 9. Retrospectiva de QA
*(A preencher após a bateria de testes)*
- Gargalos principais: 
- Melhorias no fluxo: 
