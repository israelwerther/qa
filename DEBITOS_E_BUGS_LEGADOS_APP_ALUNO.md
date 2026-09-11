# 📌 Débitos Técnicos e Achados Fora de Escopo — App do Aluno (`lize-student`)

> **Objetivo deste documento:**  
> Centralizar todos os bugs legados, inconsistências de UX, quebras de layout e débitos técnicos identificados durante as sessões de QA no **App do Aluno** (`LizeEdu/lize-student`), mas que estão **fora do escopo das tarefas em andamento**.  
> 
> Utilize este arquivo como pauta em reuniões de planejamento de sprint, refinamento técnico ou alinhamentos com a coordenação de engenharia para evitar que esses problemas caiam no esquecimento.

---

## 📋 Índice de Ocorrências

| ID | Data | Funcionalidade / Tela | Problema | Severidade | Status |
| :-: | :-: | :--- | :--- | :-: | :-: |
| **#001** | 10/09/2026 | Materiais de Estudo (`/painel/materiais-de-estudo/$id`) | Pré-visualização de PDFs inoperante (falha com URLs assinadas S3/Spaces) | **Alta** | ⏳ Aguardando Pauta |
| **#002** | 10/09/2026 | Materiais de Estudo (`/painel/materiais-de-estudo/$id`) | Metadados e ícones esmagados/sobrepostos no card lateral direito | **Média** | ⏳ Aguardando Pauta |
| **#003** | 10/09/2026 | Materiais de Estudo (`/painel/materiais-de-estudo/$id`) | Ausência de visualização inline para arquivos de imagem (JPEG/PNG) | **Baixa** | ⏳ Aguardando Pauta |
| **#004** | 10/09/2026 | Execução de Provas/Listas (`/provas/$id`) | Redirecionamento e toast incorretos ao finalizar Lista de Exercícios (manda para `/painel/minhas-provas`) | **Média** | ⏳ Aguardando Pauta |
| **#005** | 10/09/2026 | Navegação Mobile (`AppSidebar`) | Menu lateral mobile não fecha automaticamente ao selecionar um item | **Média** | ⏳ Aguardando Pauta |
| **#006** | 10/09/2026 | Listagens (`ExamTabs` / `minhas-provas` / `listas-de-exercicio`) | Alternar abas de status reseta o scroll para o topo da página (scroll jump forçado) | **Média** | ⏳ Aguardando Pauta |
| **#007** | 11/09/2026 | Resultado da Prova (`/painel/minhas-provas/$id`) | Redundância visual: Legenda inferior de status torna-se desnecessária com o mapa de cores e labels nos cards | **Baixa** | ⏳ Aguardando Pauta |
| **#008** | 11/09/2026 | Modal de Disciplina (`SubjectPerformanceModal` / API `/result/subject/`) | Divergência no percentual por tópico para questões de Somatório (`SumAnswer`) vs alinhamento PO | **Média** | ⏳ Aguardando Alinhamento com PO |

---

## 🔍 Detalhamento das Ocorrências

### [APP-ALUNO #001] — Pré-visualização de PDFs Inoperante (URLs Assinadas com Querystring)

* **Data de Identificação:** 10 de setembro de 2026
* **Identificado durante:** QA da branch `feat/header-cor-da-escola` / `feat/materiais-empty-states`
* **Tipo:** Bug Legado (presente desde o commit inicial `297fb45` em 30/03/2026)
* **Severidade:** **Alta** (Afeta 100% dos alunos que tentam ler PDFs na plataforma)
* **Arquivo:** [`src/components/study-materials/material-viewer.tsx`](file:///home/israel/Workspace/lize-student/src/components/study-materials/material-viewer.tsx) (linha 59)

#### 📝 Descrição
Ao clicar em qualquer material de estudo do tipo PDF, o aluno é direcionado para a tela de visualização, mas a tela sempre exibe:
> *"Visualização não disponível. Este tipo de arquivo não pode ser visualizado diretamente no navegador."*  
> Botão: `[Baixar Arquivo]`

O leitor embutido (`<iframe>`) nunca é exibido, forçando o aluno a fazer o download para conseguir ler o conteúdo.

#### 🛠️ Causa Técnica
O backend do Lize armazena arquivos no DigitalOcean Spaces / AWS S3 via `PrivateMediaStorage`. Por segurança, a API entrega URLs pré-assinadas com querystring:
`https://.../arquivo.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Signature=...`

O componente `material-viewer.tsx` faz uma verificação ingênua no final da string:
```tsx
const isPdf = url.toLowerCase().endsWith(".pdf");
```
Como a URL termina com os parâmetros de assinatura e não com `.pdf`, o retorno é sempre `false`. O próprio desenvolvedor já havia tratado isso no arquivo novo de filtros (`file-type-utils.ts`), mas a tela de visualização permaneceu com o código legado.

#### 💡 Sugestão de Correção
No arquivo `src/components/study-materials/material-viewer.tsx`, alterar a checagem para ignorar querystrings:
```tsx
// Substituir:
const isPdf = url.toLowerCase().endsWith(".pdf");

// Por:
const isPdf = url.split("?")[0].toLowerCase().endsWith(".pdf");
```

---

### [APP-ALUNO #002] — Metadados e Ícones Esmagados no Card Lateral de Detalhes

* **Data de Identificação:** 10 de setembro de 2026
* **Identificado durante:** QA da branch `feat/materiais-empty-states`
* **Tipo:** Bug Legado de Layout / CSS (presente desde 30/03/2026)
* **Severidade:** **Média** (Defeito visual nítido em telas grandes/desktop)
* **Arquivo:** [`src/components/study-materials/material-info.tsx`](file:///home/israel/Workspace/lize-student/src/components/study-materials/material-info.tsx) (linha 50)

#### 📝 Descrição
Na tela de detalhes do material de estudo, os metadados do card lateral direito (*"Enviado por"*, *"Data de Upload"* e *"Etapa"*) ficam espremidos horizontalmente. Em telas desktop, os textos mais longos colidem diretamente com os ícones vizinhos (ex.: o nome da escola atropela o ícone do calendário).

#### 🛠️ Causa Técnica
O componente `MaterialInfo` fica confinado em uma coluna lateral estreita (`lg:col-span-1`, com ~320px de largura). No entanto, o container dos metadados foi programado com a classe Tailwind `md:grid-cols-3`.  
Em monitores desktop (`>= 768px`), o layout força a divisão desses 3 blocos em 3 colunas de ~90px cada, provocando a sobreposição visual.

#### 💡 Sugestão de Correção
Como o card lateral é sempre estreito independente da resolução do monitor, os blocos devem ser empilhados verticalmente:
```tsx
// Em material-info.tsx, substituir:
<div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t border-slate-50">

// Por:
<div className="flex flex-col gap-4 pt-6 border-t border-slate-50">
```

---

### [APP-ALUNO #003] — Ausência de Visualização Inline para Arquivos de Imagem (JPEG/PNG)

* **Data de Identificação:** 10 de setembro de 2026
* **Identificado durante:** QA da branch `feat/materiais-empty-states`
* **Tipo:** Omissão de Feature / Oportunidade de UX
* **Severidade:** **Baixa**
* **Arquivo:** [`src/components/study-materials/material-viewer.tsx`](file:///home/israel/Workspace/lize-student/src/components/study-materials/material-viewer.tsx)

#### 📝 Descrição
Quando um professor anexa um material de estudo que é uma imagem (ex.: infográfico, mapa mental, foto de quadro nos formatos `.jpg`, `.jpeg`, `.png`), o visualizador exibe a mensagem de que o arquivo não pode ser visualizado diretamente no navegador.

#### 🛠️ Causa Técnica
O componente `MaterialViewer` apenas prevê suporte para vídeos e PDFs. Qualquer outra extensão cai no bloco de fallback para download, mesmo que navegadores suportem nativamente renderizar imagens com uma simples tag `<img src={url} />`.

#### 💡 Sugestão de Correção
Adicionar suporte a imagens no `MaterialViewer`:
```tsx
const cleanUrl = url.split("?")[0].toLowerCase();
const isImage = /\.(jpg|jpeg|png|webp|gif)$/.test(cleanUrl);

// Se for imagem, renderizar <img src={url} alt={title} className="max-h-[70vh] mx-auto object-contain" />
```

---

### [APP-ALUNO #004] — Redirecionamento e Feedback Incorretos ao Finalizar Lista de Exercícios

* **Data de Identificação:** 10 de setembro de 2026
* **Identificado durante:** QA da branch `feat/header-cor-da-escola` / `feat/materiais-empty-states` (Validação de Copy "Exercício" vs "Avaliação")
* **Tipo:** Defeito de Navegação / Inconsistência de UX
* **Severidade:** **Média**
* **Arquivos Afetados:**
  - [`src/hooks/use-finish-exam.ts`](file:///home/israel/Workspace/lize-student/src/hooks/use-finish-exam.ts) (linhas 21 e 33)
  - [`src/components/test-execution/exam-finished-redirect.tsx`](file:///home/israel/Workspace/lize-student/src/components/test-execution/exam-finished-redirect.tsx) (linhas 12 e 19)

#### 📝 Descrição
Ao realizar uma **Lista de Exercícios** (iniciada a partir de `/painel/listas-de-exercicio`) e clicar em **"Finalizar"**:
1. O aluno recebe uma notificação toast genérica: `toast.success("Prova finalizada com sucesso")` (usando o termo *"Prova"* em vez de *"Exercício"*).
2. O sistema força o redirecionamento via `window.location.href = "/painel/minhas-provas"` (tela de Provas Oficiais).
3. Como a tela `/painel/minhas-provas` filtra apenas avaliações com categorias 2 e 3 (`category__in: [2, 3]`), a lista recém-concluída **não aparece nessa tela**.
4. Se o aluno tentar acessar a URL da lista já concluída, o componente `ExamFinishedRedirect` também exibe a mensagem `Prova já finalizada. Redirecionando...` e direciona para `/painel/minhas-provas/${applicationId}`.

**Impacto:** O aluno tem a sensação de que suas respostas sumiram ou fica desorientado por ser levado para a tela de avaliações em vez de retornar para a listagem de onde veio (`/painel/listas-de-exercicio`).

#### 🛠️ Causa Técnica
O hook `useFinishExam` e o componente `ExamFinishedRedirect` possuem a URL `/painel/minhas-provas` e a mensagem de toast gravadas de forma rígida (*hardcoded*), sem consultar a categoria da aplicação (`category === 4` ou helper `isExerciseListCategory(category)`):

```typescript
// use-finish-exam.ts (linhas 20-22 e 32-34)
await lifecycle.finishAttempt();
toast.success("Prova finalizada com sucesso");
window.location.href = "/painel/minhas-provas"; // ❌ Hardcoded
```

#### 💡 Sugestão de Correção
No hook `useFinishExam` e no componente `ExamFinishedRedirect`, verificar a categoria da aplicação atual (já disponível no store de execução ou via helper `isExerciseListCategory` / `getApplicationCopy`):

```typescript
// Redirecionamento e mensagem dinâmicos conforme a categoria:
const isExercise = isExerciseListCategory(category);
const redirectUrl = isExercise ? "/painel/listas-de-exercicio" : "/painel/minhas-provas";
const successMessage = isExercise ? "Exercício finalizado com sucesso" : "Prova finalizada com sucesso";

toast.success(successMessage);
window.location.href = redirectUrl;
```

---

### [APP-ALUNO #005] — Menu Lateral Mobile Não Fecha Automaticamente ao Selecionar Item

* **Data de Identificação:** 10 de setembro de 2026
* **Identificado durante:** QA da branch `feat/header-cor-da-escola` (Validação de Usabilidade Mobile - Cenário 8)
* **Tipo:** Inconsistência de UX / Defeito de Interação Mobile
* **Severidade:** **Média** (Fricção de usabilidade repetitiva para 100% dos usuários mobile)
* **Arquivo Afetado:** [`src/components/layout/app-sidebar.tsx`](file:///home/israel/Workspace/lize-student/src/components/layout/app-sidebar.tsx)

#### 📝 Descrição
Ao navegar no App do Aluno em dispositivos móveis (ou simulador DevTools com largura mobile):
1. O aluno toca no botão hambúrguer para abrir o menu lateral (`AppSidebar`).
2. O aluno seleciona qualquer destino da lista (por exemplo, *"Materiais de estudo"*).
3. A rota da página ao fundo é alterada com sucesso, **porém o menu lateral permanece 100% aberto na frente da tela**, cobrindo todo o conteúdo.
4. O aluno é obrigado a realizar um toque extra no fundo escuro ou no botão de fechar para finalmente visualizar a tela que acabou de selecionar.

**Impacto:** Quebra a expectativa básica de fluidez mobile (onde a gaveta de navegação deve recolher assim que um item é escolhido), gerando esforço cognitivo e toques repetitivos desnecessários.

#### 🛠️ Causa Técnica
O componente `AppSidebar` renderiza os itens usando o `<Link>` do TanStack Router sem invocar o fechamento do menu móvel:
```typescript
// app-sidebar.tsx
const { state, toggleSidebar } = useSidebar();
// ❌ Não consome 'isMobile' nem 'setOpenMobile' do contexto de useSidebar()
```
Como a navegação SPA ocorre no lado do cliente sem recarregar a página, o estado booleano `openMobile` no `SidebarProvider` (`src/components/ui/sidebar.tsx`) permanece `true`, mantendo o `Sheet` aberto sobre a tela.

#### 💡 Sugestão de Correção
Desestruturar `isMobile` e `setOpenMobile` do hook `useSidebar()` e fechar a gaveta ao navegar:

```typescript
// src/components/layout/app-sidebar.tsx
const { state, toggleSidebar, isMobile, setOpenMobile } = useSidebar();

// Opção recomendada: Fechar automaticamente sempre que a rota mudar
useEffect(() => {
    if (isMobile) {
        setOpenMobile(false);
    }
}, [location.pathname, isMobile, setOpenMobile]);

// Ou no próprio handler de clique dos Links de navegação:
<Link
    to={path}
    onClick={() => {
        if (isMobile) setOpenMobile(false);
    }}
>
```

#### 📸 Evidência Visual
![Menu lateral cobrindo a tela após seleção de item no mobile](./evidencias/sidebar-mobile-not-closing.png)

---

### [APP-ALUNO #006] — Alternar Abas de Provas/Exercícios Reseta o Scroll para o Topo

* **Data de Identificação:** 10 de setembro de 2026
* **Identificado durante:** QA da branch `feat/header-cor-da-escola` (Cenário 8)
* **Tipo:** Defeito de Usabilidade / Scroll
* **Severidade:** **Média**
* **Vídeo do Problema (Jam):** [https://jam.dev/c/2a39a37a-58d3-4386-94bb-f789b2640bf0](https://jam.dev/c/2a39a37a-58d3-4386-94bb-f789b2640bf0)
* **Arquivos:** [`src/routes/_app/painel/listas-de-exercicio.tsx`](file:///home/israel/Workspace/lize-student/src/routes/_app/painel/listas-de-exercicio.tsx), [`src/routes/_app/painel/minhas-provas.index.tsx`](file:///home/israel/Workspace/lize-student/src/routes/_app/painel/minhas-provas.index.tsx)

#### 📝 Descrição
Ao clicar em qualquer aba (*"Disponíveis"*, *"Realizados"*, *"Agendados"*), a página reseta o scroll e salta imediatamente para o topo `(y: 0)`, obrigando o aluno a rolar tudo para baixo novamente para enxergar os cards.

#### 💡 Sugestão de Correção
Passar `resetScroll: false` na navegação de parâmetros de busca do TanStack Router:
```typescript
navigate({ search: updater, resetScroll: false })
```

#### 📸 Evidências
* 🎬 **Gravação Jam:** [Assistir reprodução completa](https://jam.dev/c/2a39a37a-58d3-4386-94bb-f789b2640bf0)

| Momento 1: Clicando na aba | Momento 2: Salto forçado para o topo |
| :---: | :---: |
| ![Momento 1: Clicando na aba](./evidencias/tab-scroll-reset-moment-1.png) | ![Momento 2: Salto forçado para o topo](./evidencias/tab-scroll-reset-moment-2.png) |

---

### [APP-ALUNO #007] — Redundância Visual entre Legenda Inferior e Mapa de Cores / Labels nos Cards de Questões

* **Data de Identificação:** 11 de setembro de 2026
* **Identificado durante:** QA da branch `feat/resultado-area-do-conhecimento`
* **Tipo:** Oportunidade de UX / Limpeza de Layout (*Declutter*)
* **Severidade:** **Baixa**
* **Tela / Rota:** `/painel/minhas-provas/$id` (Seção *"Todas as questões"*)
* **Arquivo Afetado:** [`src/components/exam-result/questions-overview.tsx`](file:///home/israel/Workspace/lize-student/src/components/exam-result/questions-overview.tsx) (linhas 215 a 235)

#### 📝 Descrição
Na seção de listagem de questões da tela de resultado (`QuestionsOverview`):
1. Cada card retangular já possui um duplo indicador claro de status:
   - **Mapa de cores contextual**: Círculo com o número da questão em verde esmeralda para acertos (`1, 3, 4, 6`) e rosa/vermelho para erros (`2, 5`).
   - **Label textual direto**: Texto explícito `"Acertou"` ou `"Errou"` logo acima do enunciado.
2. Logo abaixo da grade de cards, a interface exibe uma barra de legenda horizontal estática repetindo:
   `● Acertos   ● Erros   ● Parciais   ● Aguardando correção`.

**Impacto:**  
A legenda inferior torna-se redundante e desnecessária, uma vez que o próprio mapa de cores e o texto de cada card já comunicam o status imediatamente ao estudante. Isso gera ruído visual (*clutter*) e ocupa espaço vertical desnecessário na tela.

#### 🛠️ Causa Técnica
No componente `questions-overview.tsx`, o bloco de legenda foi mantido estático no rodapé do componente mesmo após a introdução dos novos cards estruturados com chips e labels textuais internos.

#### 💡 Sugestão de Encaminhamento / Correção
- **Opção A (Recomendada - *Declutter*):** Remover o container da legenda inferior (`<div className="flex flex-wrap gap-x-6 gap-y-2 items-center ...">`), deixando a interface mais limpa e focada no conteúdo.
- **Opção B (Filtros interativos):** Caso a equipe de produto queira manter esses itens, transformá-los em chips clicáveis de filtro rápido por status (ex.: clicar em "Erros" para filtrar apenas as questões erradas na grade), conferindo utilidade prática ao elemento em vez de mera legenda estática redundante.

---

### [APP-ALUNO #008] — Divergência no Cálculo de Desempenho por Tópico para Questões de Somatório (`SumAnswer`)

* **Data de Identificação:** 11 de setembro de 2026
* **Identificado durante:** QA da branch `feat/resultado-area-do-conhecimento` (Cenário 3 - Validação de Modal de Desempenho por Disciplina)
* **Tipo:** Inconsistência de Regra de Negócio / Omissão de Modelo no Backend (`lizeedu`)
* **Severidade:** **Média**
* **Tela / Rota:** `/painel/minhas-provas/$id` (Modal `SubjectPerformanceModal` consumindo `/api/v3/applications/<id>/result/subject/<subject_id>/`)
* **Arquivo Afetado:** [`fiscallizeon/app/students/serializers.py`](file:///home/israel/Workspace/lizeedu/fiscallizeon/app/students/serializers.py) (linhas 420 a 503)

#### 📝 Descrição e Contexto
Ao abrir o modal de desempenho detalhado de uma disciplina (`SubjectPerformanceModal`), o valor do percentual exibido no cabeçalho (**"DESEMPENHO: 79,17%"**) diverge expressivamente do percentual exibido nas seções analíticas inferiores (**"Desempenho por assunto: 58%"**, **"por habilidade: 58%"** e **"por competência: 58%"**).

* **Contexto de Negócio / Alinhamento com PO:**
  * O PO pontuou recentemente que **não existe aplicação de prova online com questões de somatório** no modelo operacional da plataforma.
  * Todavia, se um caderno contiver questões de somatório (por exemplo, simulados híbridos ou provas impressas com cartões-resposta OMR cujos resultados sejam liberados para consulta no App do Aluno), essa divergência matemática se manifesta diretamente no modal da disciplina.

#### 🛠️ Causa Técnica (Backend)
No método `SubjectPerformanceDetailSerializer._aggregate_performance_by`, a agregação calcula a pontuação (`score`) do aluno com subqueries que contemplam apenas `OptionAnswer` (objetiva), `TextualAnswer` (discursiva) e `FileAnswer` (anexo):
```python
score=Coalesce(
    Sum(
        'weight',
        filter=Q(
            Q(is_correct=True)
            | Q(is_correct_textual=True)
            | Q(is_correct_file=True)
            # ❌ Ausência de verificação para SumAnswer (Question.SUM_QUESTION)
        ),
    ),
    Decimal('0'),
)
```
Como `SumAnswer` foi omitido:
1. O peso da questão de somatório (ex: Q9, peso 1.25) é somado normalmente no denominador (`weight = Sum('weight')` = 6.00).
2. O acerto do aluno não é computado no numerador, gerando nota 0.00 para a questão no agregador (totalizando 3.50 / 6.00 = 58.33% -> 58%).
3. O cabeçalho do modal, por sua vez, consome `get_performance_v2()`, que calcula a nota real completa (4.75 / 6.00 = 79.17%), gerando a discrepância visual.

#### 💡 Ponto de Pauta para Reunião com o PO
1. **Dúvida para o PO:** O App do Aluno exibirá resultados de avaliações que tenham questões de somatório (ex.: simulados tradicionais estilo UFSC/UEM importados via OMR)?
2. **Se SIM:** Devemos abrir uma tarefa técnica no backend `lizeedu` para adicionar a subquery de `SumAnswer` em `_aggregate_performance_by`.
3. **Se NÃO (Não suportado por definição de produto):** O produto deve definir se cadernos com questões de somatório devem ter o modal bloqueado ou se é uma restrição de negócio que não requer suporte online.

---

## ➕ Como Registrar Novos Bugs Futuros (Template Padrão)

Este documento é um **registro contínuo e cumulativo**. Sempre que você ou outro membro da equipe identificar qualquer bug ou comportamento estranho fora de escopo durante os testes no App do Aluno:
1. Adicione uma nova linha no **Índice de Ocorrências** no topo (incrementando o ID: `#007`, `#008`, etc.);
2. Cole e preencha o modelo abaixo na seção de **Detalhamento**:

```markdown
### [APP-ALUNO #00X] — [Título Resumido do Problema]

* **Data de Identificação:** [DD/MM/AAAA]
* **Identificado durante:** QA da branch [nome-da-branch]
* **Tipo:** [Bug Legado / Quebra de Layout / Defeito de API / Inconsistência de UX]
* **Severidade:** [Crítica / Alta / Média / Baixa]
* **Tela / Rota:** [ex.: `/painel/minhas-provas`]
* **Arquivo (se conhecido):** `caminho/do/arquivo.tsx`

#### 📝 Descrição
[O que acontece na prática, passos para reproduzir e o impacto no aluno]

#### 🛠️ Causa Técnica (se identificada)
[Detalhe técnico, classe CSS incorreta ou função com erro]

#### 💡 Sugestão de Correção / Encaminhamento
[Sugestão de código ou ação recomendada para a engenharia]
```

---

## 📌 Histórico de Discussões e Decisões de Reunião

*Espaço reservado para anotar o desfecho dos itens após alinhamentos com o time (ex.: "Aprovado para sprint X", "Criada task CU-86xxxx no ClickUp", etc.)*

