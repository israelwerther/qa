## ADDED Requirements

### Requirement: Geração sob demanda de cadernos e questões para QA
O utilitário de QA MUST permitir a criação programática ou interativa de instâncias de `Exam`, populadas com `Question`, `QuestionOption`, `ExamTeacherSubject` e `ExamQuestion`, atendendo às combinações requeridas para validação dos cenários de teste com paridade completa em relação aos cadernos de produção.

O utilitário MUST garantir:
1. **Configuração de Impressão Integrada:** Clonagem e vinculação automática da `ExamPrintConfig` padrão do cliente ao `Exam.exam_print_config`.
2. **Estrutura Pedagógica de Disciplina:** Criação de `ExamTeacherSubject` associando a disciplina (`Subject`) e a série (`Grade`) do tenant ao caderno, associando cada `ExamQuestion.exam_teacher_subject`.
3. **Atributos de Questão:** Preenchimento de `category`, `subject`, `grade`, `level` (`Question.MEDIUM`) e `is_essay` em conformidade com o tipo gerado.
4. **Opções de Resposta:** Para questões objetivas (`Question.CHOICE`), criação de 5 instâncias de `QuestionOption` (A a E) indexadas de 0 a 4 com gabarito definido.
5. **Redação e Discursivas:** Para questões discursivas, `is_essay=False` com linhas configuradas; para redação, `is_essay=True` com 30 linhas.
6. **Embaralhamento:** Suporte a flags de randomização no caderno (`random_questions` e `random_alternatives`).
7. **Associação de Tenant:** Vinculação automática do caderno e das questões às coordenações (`coordinations`) do cliente do usuário de teste.

#### Scenario: Geração de caderno misto com paridade de produção
- **WHEN** o QA executa o script solicitando 4 objetivas, 2 discursivas, 1 redação com flags de randomização ativadas
- **THEN** o sistema cria o `Exam` com `is_randomized=True` e `exam_print_config` vinculado
- **AND** cria `ExamTeacherSubject` associando a disciplina e série
- **AND** cria 7 instâncias de `Question` com `subject` e `grade` preenchidos
- **AND** cada `ExamQuestion` está vinculado ao `ExamTeacherSubject` correspondente
- **AND** a rota `/provas/<exam_id>/v2/imprimir/` abre com sucesso (`HTTP 200`) sem violar integridade de banco
- **AND** o caderno fica visível e pesquisável no autocomplete de criação de aplicação em `/aplicacoes/cadastrar/`

#### Scenario: Geração via modo interativo no terminal
- **WHEN** o QA executa o script sem argumentos em um terminal TTY
- **THEN** o script solicita nome, quantidade por tipo de questão e confirmação de randomização via prompt
- **AND** cria o caderno no banco de dados retornando o ID e o resumo de utilização
