---
description: Gera a descrição de Pull Request preenchida no padrão oficial da empresa (.github/PULL_REQUEST_TEMPLATE.md) com checklist pre-deploy marcado e link de compare
---

# Workflow: Criar Descrição de Pull Request (`/qa-criar-pr`)

Este comando gera automaticamente o **Título**, o **Link de Compare** e o **Corpo formatado do Pull Request (PR)** seguindo à risca o template oficial da empresa (`.github/PULL_REQUEST_TEMPLATE.md`).

Evita retrabalho e inconsistências ao garantir que todos os itens do checklist do pre-deploy venham devidamente checados e preenchidos, com tratamento condicional correto para o tipo de entrega (bug fix vs feature/chore).

---

## 🚀 Como Usar na IDE

Basta invocar o comando na IDE:

```bash
/qa-criar-pr
```

Ou passar detalhes adicionais, link do ClickUp ou link de evidências/vídeo:

```bash
/qa-criar-pr https://jam.dev/c/...
```

---

## 📋 Regras Mandatórias de Formatação e Checklist

1. **Template Base Obrigatório**:
   - A estrutura Markdown gerada DEVE ser **idêntica** à do arquivo `.github/PULL_REQUEST_TEMPLATE.md` do repositório principal.

2. **Regras do Checklist Pre-Deploy**:
   - Os seguintes 5 itens DEVEM vir **SEMPRE marcados como concluídos (`- [x]`)**:
     - `- [x] Verifiquei se há migrações pendentes com \`./manage.py makemigrations --check --dry-run\``
     - `- [x] Rodei todos os testes unitários e de usabilidade`
     - `- [x] Testei localmente o comportamento alterado`
     - `- [x] Verifiquei se não há arquivos \`.env, media\`, etc., no commit`
     - `- [x] A branch segue o padrão [\`Conventional Commits\`](https://www.conventionalcommits.org/pt-br/v1.0.0/)`
   - O item **`Esse PR corrige um bug?`**:
     - **MARCADO (`- [x] Esse PR corrige um bug?`)**: se a branch iniciar com `fix/` ou `hotfix/`, ou se os commits forem do tipo `fix:`, ou se for uma tarefa de correção de defeito/bug.
     - **DESMARCADO (`- [ ] Esse PR corrige um bug?`)**: se a branch for `feat/`, `chore/`, `refactor/` ou melhoria sem correção de bug.

3. **Seção "🚀 Descrição do PR"**:
   - NUNCA entregar a descrição vazia ou com o placeholder `> Descreva de forma clara...`.
   - DEVE conter o link da tarefa do ClickUp: `[CU-<ID>](https://app.clickup.com/t/<ID>)`.
   - DEVE conter um resumo objetivo em tópicos (bullet points) destacando as alterações técnicas e funcionais implementadas.

4. **Seção "📸 Prints / GIFs (se aplicável)"**:
   - Incluir links de vídeos (ex.: Jam Dev), capturas salvas na pasta `.ai_qa_acervo/evidencias/` ou fornecidas pelo usuário na conversa.
   - Se não houver mídias no momento, colocar `N/A` ou link do Jam / plano de testes correspondente.

---

## 🤖 Passos de Execução para a IA

### 1. Inspecionar o Contexto do Repositório
A IA deve rodar comandos pontuais para coletar os metadados da branch atual:
- **Nome da branch atual**: `git branch --show-current`
- **ID da Task ClickUp**: extraído do nome da branch (ex: `fix/exams-...-CU-17tu7rpaqj8` -> `17tu7rpaqj8`), de `tasks.md` da OpenSpec ou dos commits.
- **Commits da branch contra a master**: `git log master..HEAD --oneline` (ou `git log -n 5 --oneline`).
- **Verificar se é bugfix**: analisar o prefixo da branch (`fix/`, `hotfix/`) e mensagens de commit (`fix(...)`).

### 2. Validar Pre-Deploy Rapidamente
- Checar se makemigrations está limpo: `python manage.py makemigrations --check --dry-run` (ou constatar que a tarefa não alterou modelos).

### 3. Montar a Saída
A IA executa o gerador automatizado:
```bash
python3 .ai_qa_acervo/scripts/generate_pr_link.py
```

O script gera a URL perfeita utilizando:
- `quick_pull=1` (força a abertura do formulário do PR diretamente).
- Cabeçalhos Setext (`-------------------`) para evitar o bug `%23%23` causado pelo `decodeURI` do GitHub.
- Parâmetro `safe='?'` para evitar o bug `%3F` no checklist.
- Checkboxes pré-marcados (`[x]`), com tratamento inteligente de bug fix.

A IA apresenta ao usuário:
1. **Link direto preenchido para abrir no navegador**:
   O link gerado pelo script que já carrega o título e a descrição 100% preenchidos no GitHub.
2. **Título do PR** e **Bloco de Código Markdown** para referência e cópia rápida se necessário.

