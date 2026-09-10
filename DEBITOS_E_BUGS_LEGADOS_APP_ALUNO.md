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

## ➕ Como Registrar Novos Bugs Futuros (Template Padrão)

Este documento é um **registro contínuo e cumulativo**. Sempre que você ou outro membro da equipe identificar qualquer bug ou comportamento estranho fora de escopo durante os testes no App do Aluno:
1. Adicione uma nova linha no **Índice de Ocorrências** no topo (incrementando o ID: `#004`, `#005`, etc.);
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

