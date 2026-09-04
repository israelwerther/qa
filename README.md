# AI QA Acervo

Repositório de planos de testes, automações, scripts e ferramentas para suporte a QA no ecossistema Lize Edu.

---

## 🛠️ Setup em Qualquer Máquina (Sem commitar em `lizeedu`)

> [!IMPORTANT]
> **REGRA DE ISOLAMENTO:** Nunca commitar arquivos ou atalhos do acervo no repositório principal `lizeedu`. Toda integração com IDEs (VS Code, Antigravity, Cursor) deve ser feita exclusivamente via links simbólicos locais e isolada em `.git/info/exclude`.

Ao clonar ou abrir o projeto em um novo computador (Desktop ou Notebook), basta executar:

```bash
./.ai_qa_acervo/scripts/setup-tasks.sh
```

Esse script realiza automaticamente:
1. **Configuração de Tasks do VS Code:** Copia `tasks.json` para `.vscode/tasks.json` (permite rodar `Ctrl+Shift+B` para ligar Django, Celery e PDF Service).
2. **Atalhos de Slash Command (`/qa-create-test-exam`):** Cria links simbólicos apontando para os workflows em:
   - `.agent/workflows/qa-create-test-exam.md` (Antigravity IDE)
   - `.cursor/commands/qa-create-test-exam.md` (Cursor IDE)
3. **Isolamento de Git:** Registra automaticamente `.ai_qa_acervo/`, `.agent/workflows/qa*.md` e `.cursor/commands/qa*.md` no arquivo local `.git/info/exclude` do `lizeedu`, mantendo o `git status` do repositório principal 100% limpo.

---

## 🤖 Instruções para Agentes de IA (Antigravity / Cursor)

Se o usuário perguntar por que o comando `/qa-create-test-exam` não está aparecendo ou relatar que mudou de máquina:
1. **NÃO altere ou commite nada no repositório `lizeedu`**.
2. Execute o script `./.ai_qa_acervo/scripts/setup-tasks.sh`.
3. Verifique se os links simbólicos foram criados em `.agent/workflows/qa-create-test-exam.md` e `.cursor/commands/qa-create-test-exam.md`.
4. Confirme que `.git/info/exclude` está ignorando esses arquivos para manter o `git status` do `lizeedu` intacto.

---

## Ferramentas Disponíveis

### 1. Gerador de Cadernos e Questões de Teste
Localização: `scripts/create_test_exam.py` e `scripts/create-exam.sh`

Gera instantaneamente cadernos de prova (`Exam`) com paridade completa de produção:
- Questões objetivas (múltipla escolha A-E) com gabarito definido
- Questões discursivas e propostas de redação
- Randomização de questões e alternativas
- Vinculação com disciplina (`Subject`), série (`Grade`), professor (`TeacherSubject`), `ExamTeacherSubject` e diagramação V2 (`ExamPrintConfig`)
- Associação automática às coordenações do tenant

#### Formas de Execução:
- **Slash Command na IDE:** `/qa-create-test-exam <descrição em texto livre>`
  - *Exemplo:* `/qa-create-test-exam 5 objetivas com alternativas embaralhadas`
- **Linha de comando direta:**
  ```bash
  ./.ai_qa_acervo/scripts/create-exam.sh -obj 5 -disc 2 -ess 1 -rq -ra
  ```
- **Modo interativo no terminal:**
  ```bash
  ./.ai_qa_acervo/scripts/create-exam.sh
  ```
