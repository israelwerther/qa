---
description: Exporta o plano de testes de QA ativo para um arquivo PDF consolidado com imagens embutidas (Base64), pronto para anexar no ClickUp.
---

# Workflow: Exportar Plano de Testes para PDF (`/qa-export-pdf`)

Este comando compila um Plano de Testes de QA (arquivo `.md`) em um relatório **PDF consolidado de alta qualidade**, com todas as formatações, tabelas, checkboxes (`[x]`) e capturas de tela locais devidamente embutidas em Base64. O arquivo gerado é salvo na pasta dedicada `exports/`, pronto para ser anexado diretamente na tarefa do ClickUp.

**Padrão:** plano **100% completo**, sem pular nada salvo `--skip` explícito.

---

**Input**: O texto passado após `/qa-export-pdf` pode especificar o plano ou ser executado sem argumentos para detectar o plano aberto na IDE.  
*Exemplos:*
- `/qa-export-pdf` (detecta o plano aberto/mais recente; exporta 100%)
- `/qa-export-pdf QA_TEST_PLAN_feat_client-brand-color_header-cor-da-escola.md`
- `/qa-export-pdf "QA Plans/QA_TEST_PLAN_feat_minha-feature.md"`
- `/qa-export-pdf --skip 4,3` (sem fixtures nem navegação)
- `/qa-export-pdf --skip 4` (sem fixtures)
- `/qa-export-pdf --skip none` (explícito, sem pulos)

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

### 2. Conciliação Automática de Mapeamento de Usabilidade (Audit & Sync Pré-Exportação)
**REGRA MANDATÓRIA (Acervo Vivo e Auto-Sustentável):**
Antes de gerar o arquivo PDF, a IA DEVE auditar e conciliar os aprendizados da execução do plano com os arquivos de mapeamento de tela em `.ai_qa_acervo/docs/tests/usability/`:

1. **Localizar as Telas Mapeadas:**
   - Leia a **Seção 8.1 (Knowledge Base Notes)** do plano de testes alvo e extraia todos os arquivos de mapeamento referenciados (ex.: `docs/tests/usability/<screen_name>.md`).
2. **Coleta de Seletores e Estados Validados:**
   - Inspecione a **Seção 5 (Roteiro de Testes)** do plano: examine os blocos `**Referência técnica (para automação):**` (URLs, seletores estáveis, estados DOM e fixtures mixer).
   - Inspecione a **Seção 7 (Bugs e Observações)**: se houver bugs relatados ou alertas de seletores que quebraram, mudaram de ID ou mudaram de comportamento na interface.
3. **Auditar e Atualizar o Mapeamento da Tela (`<screen_name>.md`):**
   - Para cada arquivo de mapeamento referenciado:
     - **Seção 3 (Seletores DOM e Ações):** Se a Seção 5 usou novos seletores, botões, modais ou abas que ainda não constavam na Seção 3 do mapeamento, adicione-os na tabela de seletores estáveis. Se algum seletor legado foi corrigido durante o teste, atualize-o.
     - **Seção 4 (API Interception & Fixtures):** Adicione novas rotas de API ou modelos descobertos.
     - **Seção 6 (Armadilhas Conhecidas e Cruzamentos de QA):** Se a Seção 7 do plano registrou um bug real ou armadilha nova (ex.: comportamento de modal, filtros combinados, quebras em resolução específica), registre um resumo preventivo na Seção 6 do arquivo de mapeamento da tela correspondente.
4. **Registrar Status no Resumo:**
   - Armazene quais arquivos foram auditados/atualizados para apresentar no resumo final da exportação.

### 3. Executar o Script de Exportação
Execute o wrapper shell oficial de exportação.

**Padrão (100% — sem pulos):**
```bash
./.ai_qa_acervo/scripts/export-plan-pdf.sh "<CAMINHO_DO_PLANO.md>"
```

**Pular seções extras (lista negativa):**
```bash
./.ai_qa_acervo/scripts/export-plan-pdf.sh "<CAMINHO_DO_PLANO.md>" --skip 4,3
```

**Incluir tudo explicitamente (não pular nada):**
```bash
./.ai_qa_acervo/scripts/export-plan-pdf.sh "<CAMINHO_DO_PLANO.md>" --skip none
```

**Sem fixtures:**
```bash
./.ai_qa_acervo/scripts/export-plan-pdf.sh "<CAMINHO_DO_PLANO.md>" --skip 4
```

O script realizará automaticamente:
1. Remoção das seções em `--skip` (padrão: nenhuma; pular `8` também remove `8.1`);
2. Conversão de imagens locais em Base64;
3. Formatação visual + `<details open>`;
4. PDF via Google Chrome Headless em `.ai_qa_acervo/exports/`.

### 4. Apresentar o Resumo ao Usuário
Informe ao usuário:
1. 🔄 **Auditoria & Sincronização do Acervo (Seção 8.1)**:
   - Lista clara dos arquivos em `docs/tests/usability/<screen_name>.md` auditados e atualizados (seletores novos adicionados, armadilhas aprendidas registradas na Seção 6). Se nenhuma alteração foi necessária, confirme: *"Mapeamentos conferidos e 100% em sincronia com os testes executados"*.
2. ✅ **Sucesso da Exportação**: caminho completo clicável para o arquivo PDF gerado dentro de `exports/`.
3. ✂️ **Escopo**: seções puladas (`--skip`, padrão sem pulos).
4. 📊 **Estatísticas**: tamanho do arquivo e número de páginas.
5. 📋 **Ação Recomendada**: arrastar o PDF para os anexos da tarefa no ClickUp.
6. 🧹 **Lembrete de Limpeza**: `.pdf` e `evidencias/` estão no `.gitignore`.
