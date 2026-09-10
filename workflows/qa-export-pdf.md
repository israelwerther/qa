---
description: Exporta o plano de testes de QA ativo para um arquivo PDF consolidado com imagens embutidas (Base64), pronto para anexar no ClickUp.
---

# Workflow: Exportar Plano de Testes para PDF (`/qa-export-pdf`)

Este comando compila um Plano de Testes de QA (arquivo `.md`) em um relatório **PDF consolidado de alta qualidade**, com todas as formatações, tabelas, checkboxes (`[x]`) e capturas de tela locais devidamente embutidas em Base64. O arquivo gerado é salvo na pasta dedicada `exports/`, pronto para ser anexado diretamente na tarefa do ClickUp.

---

**Input**: O texto passado após `/qa-export-pdf` pode especificar o plano ou ser executado sem argumentos para detectar o plano aberto na IDE.  
*Exemplos:*
- `/qa-export-pdf` (detecta o plano de testes atualmente aberto ou mais recente)
- `/qa-export-pdf QA_TEST_PLAN_feat_client-brand-color_header-cor-da-escola.md`
- `/qa-export-pdf "QA Plans/QA_TEST_PLAN_feat_minha-feature.md"`

---

## Passos de Execução para a IA

### 1. Identificar o Plano de Testes Alvo
1. Se o usuário forneceu um caminho de arquivo, utilize-o.
2. Se nenhum caminho foi informado:
   - Verifique se há algum documento `.md` com prefixo `QA_TEST_PLAN_` aberto na IDE ou no contexto recente.
   - Caso não haja, localize o plano de testes mais recentemente modificado no acervo:
     ```bash
     find .ai_qa_acervo -name "QA_TEST_PLAN_*.md" -type f -printf "%T@ %p\n" | sort -n | tail -n 1 | awk '{print $2}'
     ```

### 2. Executar o Script de Exportação
Execute o wrapper shell oficial de exportação:

```bash
./.ai_qa_acervo/scripts/export-plan-pdf.sh "<CAMINHO_DO_PLANO.md>"
```

O script realizará automaticamente:
1. Conversão de todas as imagens locais (`./evidencias/...` ou relativas) em dados Base64 (`data:image/...;base64,...`) para embutir no documento;
2. Formatação visual com tipografia profissional, quebras de página controladas e suporte a tags `<details open>`;
3. Geração do PDF via Google Chrome Headless;
4. Salvamento automático do arquivo compilado na pasta `.ai_qa_acervo/exports/`.

### 3. Apresentar o Resumo ao Usuário
Informe ao usuário:
1. ✅ **Sucesso da Exportação**: caminho completo clicável para o arquivo PDF gerado dentro de `exports/`.
2. 📊 **Estatísticas**: tamanho do arquivo e número de páginas.
3. 📋 **Ação Recomendada**: instrua o usuário a arrastar o arquivo PDF diretamente para os anexos da tarefa correspondente no ClickUp.
4. 🧹 **Lembrete de Limpeza**: lembre que o arquivo `.pdf` e as imagens da pasta `evidencias/` estão no `.gitignore` e não inflam o repositório Git, podendo ser mantidos ou excluídos após o envio ao ClickUp.
