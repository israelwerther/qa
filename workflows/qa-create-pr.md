---
description: Gera a descrição de Pull Request preenchida no padrão oficial da empresa (.github/PULL_REQUEST_TEMPLATE.md) a partir da cópia direta do template
---

# Workflow: Criar Descrição de Pull Request (`/qa-criar-pr`)

Este comando gera de forma rápida e direta o **Título**, o **Link do Compare no GitHub** e a **Cópia preenchida do template oficial da empresa (`.github/PULL_REQUEST_TEMPLATE.md`)**, pronto para copiar e colar na criação do PR.

---

## 🚀 Como Usar na IDE

Basta invocar o comando na IDE:

```bash
/qa-criar-pr
```

Ou passar link de evidência / Jam Dev:

```bash
/qa-criar-pr https://jam.dev/c/...
```

---

## 📋 Regras de Formatação e Preenchimento

1. **Cópia Exata do Template Oficial**:
   - Usa rigorosamente o arquivo `.github/PULL_REQUEST_TEMPLATE.md` como base.

2. **Checklist do Pre-Deploy**:
   - Marca automaticamente com `[x]` os 5 itens padrão de pre-deploy verificados.
   - O item `Esse PR corrige um bug?`:
     - Marcado com `[x]` se a branch for `fix/`, `hotfix/` ou commits `fix:`.
     - Mantido desmarcado `[ ]` se for `feat/`, `chore/` ou melhoria.

3. **Seção Descrição**:
   - Inclui o link da tarefa do ClickUp `[CU-<ID>](https://app.clickup.com/t/<ID>)`.
   - Inclui um resumo conciso dos commits e alterações implementadas na branch.

4. **Seção Prints / GIFs**:
   - Adiciona o link de evidência (Jam Dev, vídeo ou print) se informado ou preenche `N/A`.

---

## 🤖 Execução para a IA

Basta rodar o script utilitário:

```bash
python3 .ai_qa_acervo/scripts/generate_pr.py [LINK_EVIDENCIA_OPCIONAL]
```

A IA entrega:
1. **Título do PR**.
2. **Link de compare no GitHub** (`?expand=1`).
3. **Bloco de Markdown com a cópia exata do template preenchida**, pronto para copiar e colar diretamente no GitHub.
