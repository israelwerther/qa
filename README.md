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
│   ├── create-exam.sh            # Wrapper executável com detecção de venv
│   ├── create_application.py     # Criação de aplicações, turmas/alunos e respostas
│   └── create-application.sh     # Wrapper executável com detecção de venv
├── maintenance/                  # Utilitários de banco e autenticação
│   ├── reset_passwords.py        # Reset de senhas (123456), desativação de 2FA e limpeza de sessões
│   └── reset-passwords.sh       # Wrapper executável com detecção de venv
├── setup-tasks.sh                # Script de bootstrap do ambiente e slash commands
├── start-pdf-service.sh          # Serviço local de PDF
└── export-plan-pdf.sh            # Exportação de plano de testes Markdown para PDF autocontido (em exports/)
```

---

## ⚡ Comandos Disponíveis na IDE

### 1. Criar Plano de Testes (`/qa-create-plan`)
Núcleo operacional do acervo. Analisa a branch ativa contra a `master`, consulta a OpenSpec e gera o plano estruturado com roteiro de testes e camada técnica para automação:
- Tabela de navegação canônica baseada no `KI_Navegacao.md` (sem alucinações de UI)
- Sugestão e amarração de comandos geradores do acervo para setup rápido
- Roteiro humano focado em confirmações visuais e rótulos literais
- Camada técnica desacoplada e atualização de mapeamentos em `docs/tests/usability/`
- **Suporte Multi-Repo (`lize-student`):** Analisa tarefas conjuntas entre o backend (`lizeedu`) e o app do aluno (`lize-student`), gerando roteiros End-to-End completos.

**Como usar:**
- **Slash Command na IDE:** `/qa-create-plan [opções]` *(ou pelo atalho rápido `/qa`)*
  - *Exemplo (simples):* `/qa-create-plan` (analisa a branch atual)
  - *Exemplo (branch específica):* `/qa-create-plan feat/minha-feature`
  - *Exemplo (Multi-Repo via flag):* `/qa-create-plan --student feat/minha-feature-student`
  - *Exemplo (Multi-Repo em texto livre):* `/qa-create-plan com student na branch feat/cartao-resposta`

---

### 2. Criar Aplicação de Teste (`/qa-create-application`)
Gera aplicações (`Application`) prontas para realização imediata por alunos e fiscais:
- Vincula caderno existente ou encadeia a criação de um novo caderno sob medida
- Matricula alunos com senha padrão `123456`
- Suporte a aplicações 100% respondidas (`--answered`) para testes de correção e histórico de respostas
- Suporte a modelo PAS (`--pas`) e diferentes modalidades (online, presencial, homework)

**Como usar:**
- **Slash Command na IDE:** `/qa-create-application <descrição em texto livre>`
  - *Exemplo:* `/qa-create-application com 5 alunos respondida`
  - *Exemplo:* `/qa-create-application criando caderno com 5 objetivas e 1 discursiva`
- **Linha de comando:**
  ```bash
  ./.ai_qa_acervo/scripts/generators/create-application.sh --create-exam -obj 5 --answered -sc 3
  ```

---

### 3. Criar Caderno de Prova (`/qa-create-exam`)
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

### 4. Resetar Senhas e Acessos (`/qa-reset-passwords`)
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

---

### 5. Exportar Plano com Evidências para PDF (`/qa-export-pdf`)
Compila o plano de testes `.md` em um **relatório PDF consolidado** de alta qualidade, pronto para envio ao ClickUp:
- **Colagem automática de prints:** Ao tirar um print da tela e pressionar `Ctrl + V` dentro de qualquer Markdown do acervo, a imagem é salva automaticamente dentro da pasta `evidencias/` e a tag Markdown é inserida na linha do cursor.
- **Git limpo e imune a inchaço:** As pastas `evidencias/` e `exports/`, bem como arquivos binários (`*.png`, `*.jpg`, `*.pdf`), estão no `.gitignore` do acervo. O repositório Git versiona apenas texto leve.
- **Imagens embutidas em Base64:** O script converte todas as capturas locais em dados Base64 autocontidos dentro do PDF. Quem abrir o PDF no ClickUp ou navegador vê todos os prints nítidos sem depender de links externos.
- **Saída organizada em `exports/`:** O arquivo PDF final é gerado em `.ai_qa_acervo/exports/`, pronto para ser arrastado para a tarefa do ClickUp.

**Como usar:**
- **Slash Command na IDE:** `/qa-export-pdf [caminho-do-plano.md]` *(ou atalho rápido `/qa-export`)*
  - *Exemplo:* `/qa-export-pdf` (detecta o plano aberto na IDE ou o mais recente)
  - *Exemplo:* `/qa-export-pdf QA_TEST_PLAN_feat_minha-feature.md`
- **Linha de comando:**
  ```bash
  ./.ai_qa_acervo/scripts/export-plan-pdf.sh QA_TEST_PLAN_feat_minha-feature.md
  ```

