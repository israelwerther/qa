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
2. **Atalhos de Slash Command na IDE:** Cria links simbólicos apontando para os workflows em:
   - `.agent/workflows/` (Antigravity IDE)
   - `.cursor/commands/` (Cursor IDE)
3. **Isolamento de Git:** Registra automaticamente `.ai_qa_acervo/`, `.agent/workflows/qa*.md` e `.cursor/commands/qa*.md` no arquivo local `.git/info/exclude` do `lizeedu`, mantendo o `git status` do repositório principal 100% limpo.

---

## 🤖 Instruções para Agentes de IA (Antigravity / Cursor)

Se o usuário relatar que algum comando `/qa-*` não está aparecendo ou que está em uma máquina nova:
1. **NUNCA altere ou commite nada no repositório `lizeedu`**.
2. Execute o script `./.ai_qa_acervo/scripts/setup-tasks.sh`.
3. Verifique se os links simbólicos foram criados em `.agent/workflows/` e `.cursor/commands/`.
4. Confirme que `.git/info/exclude` está ignorando esses arquivos para manter o `git status` do `lizeedu` intacto.

---

## 📁 Estrutura de Scripts (`scripts/`)

A pasta `scripts/` está organizada por domínios de responsabilidade:

```
.ai_qa_acervo/scripts/
├── generators/                   # Geradores de massa de dados
│   ├── create_exam.py            # Criação autônoma de cadernos, questões e amarrações
│   └── create-exam.sh            # Wrapper executável com detecção de venv
├── maintenance/                  # Utilitários de banco e autenticação
│   ├── reset_passwords.py        # Reset de senhas (123456), desativação de 2FA e limpeza de sessões
│   └── reset-passwords.sh       # Wrapper executável com detecção de venv
├── setup-tasks.sh                # Script de bootstrap do ambiente e slash commands
└── start-pdf-service.sh          # Serviço local de PDF
```

---

## ⚡ Comandos Disponíveis na IDE

### 1. Criar Caderno de Prova (`/qa-create-exam`)
Gera instantaneamente cadernos de prova (`Exam`) com paridade completa de produção:
- Questões objetivas (múltipla escolha A-E) com gabarito definido
- Questões discursivas e propostas de redação
- Randomização de questões e alternativas
- Vinculação com disciplina (`Subject`), série (`Grade`), professor (`TeacherSubject`), `ExamTeacherSubject` e diagramação V2 (`ExamPrintConfig`)
- Associação automática às coordenações do tenant

**Como usar:**
- **Slash Command na IDE:** `/qa-create-exam <descrição em texto livre>`
  - *Exemplo:* `/qa-create-exam 5 objetivas e 1 redação com alternativas embaralhadas`
- **Linha de comando:**
  ```bash
  ./.ai_qa_acervo/scripts/generators/create-exam.sh -obj 5 -disc 2 -ess 1 -rq -ra
  ```

---

### 2. Resetar Senhas e Acessos (`/qa-reset-passwords`)
Reseta senhas de usuários para acesso em ambientes locais de teste:
- Define senha padrão (`123456`) para todos os usuários ou usuário filtrado
- Desativa flag de troca de senha obrigatória (`must_change_password=False`)
- Garante permissão de acesso ao app do aluno (`can_access_app=True`)
- Desativa 2FA e login obrigatório Google nos clientes
- Limpa sessões ativas existentes

**Como usar:**
- **Slash Command na IDE:** `/qa-reset-passwords [opções]`
  - *Exemplo:* `/qa-reset-passwords`
  - *Exemplo:* `/qa-reset-passwords -u cloud.admin@lize.local -p minhasenha`
- **Linha de comando:**
  ```bash
  ./.ai_qa_acervo/scripts/maintenance/reset-passwords.sh
  ```
