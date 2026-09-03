# AI QA Acervo

Repositório de planos de testes, automações, scripts e ferramentas para suporte a QA no ecossistema Lize Edu.

## Ferramentas Disponíveis

### 1. Gerador de Cadernos e Questões de Teste
Localização: `scripts/create_test_exam.py` e `scripts/create-exam.sh`

Gera instantaneamente cadernos de prova (`Exam`) com paridade completa de produção:
- Questões objetivas (múltipla escolha A-E) com gabarito definido
- Questões discursivas e propostas de redação
- Randomização de questões e alternativas
- Vinculação com disciplina (`Subject`), série (`Grade`), professor (`TeacherSubject`), `ExamTeacherSubject` e diagramação V2 (`ExamPrintConfig`)
- Associação automática às coordenações do tenant

#### Comandos Disponíveis:
- **Slash Command na IDE:** `/qa-create-exam <descrição em texto livre>`
- **Linha de comando direta:**
  ```bash
  ./.ai_qa_acervo/scripts/create-exam.sh -obj 5 -disc 2 -ess 1 -rq -ra
  ```
- **Modo interativo no terminal:**
  ```bash
  ./.ai_qa_acervo/scripts/create-exam.sh
  ```
