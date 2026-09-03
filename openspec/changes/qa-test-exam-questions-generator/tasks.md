# Tasks: Gerador de Cadernos e Questões para Testes de QA

## 1. Implementação do Script Python Principal
- [x] 1.1 Criar `.ai_qa_acervo/scripts/create_test_exam.py` com bootstrapping autônomo do Django (`django.setup()`) e parsing de argumentos CLI com `argparse`.
- [x] 1.2 Implementar resolução dinâmica de usuário ativo (`fiscallize_geral`, `cloud.coord`) e recuperação das coordenações autorizadas do cliente.
- [x] 1.3 Implementar recuperação de metadados pedagógicos reais do tenant (`Subject`, `Grade`, `TeacherSubject`).
- [x] 1.4 Implementar clonagem da configuração de diagramação padrão do cliente (`client.get_exam_print_config()`) e vínculo em `Exam.exam_print_config`.
- [x] 1.5 Implementar criação de `ExamTeacherSubject` vinculando a disciplina e série ao caderno.
- [x] 1.6 Implementar instanciação do `Exam` parametrizando título, flags de randomização de questões e alternativas.
- [x] 1.7 Implementar geração em lote de questões objetivas (`Question.CHOICE`), criando 5 alternativas (`QuestionOption`) indexadas de 0 a 4 (letras A a E) com gabarito definido.
- [x] 1.8 Implementar geração de questões discursivas padrão (`category=Question.TEXTUAL`, `is_essay=False`) e propostas de redação (`is_essay=True`, 30 linhas) com `subject`, `grade` e `level` atribuídos.
- [x] 1.9 Implementar vínculo de todas as questões ao caderno via `ExamQuestion` com ordenação sequencial `1..N`, vínculo ao `ExamTeacherSubject` e coordenações.

## 2. Shell Wrapper e Modo Interativo
- [x] 2.1 Criar wrapper executável `.ai_qa_acervo/scripts/create-exam.sh` com permissão de execução (`chmod +x`).
- [x] 2.2 Adicionar detecção automática do interpretador Python do ambiente virtual (`./venv/bin/python`).
- [x] 2.3 Implementar modo interativo via terminal (prompt TTY) quando o script for chamado sem parâmetros.

## 3. Validação de Integração e Compatibilidade
- [x] 3.1 Executar o gerador para criar caderno com 3 objetivas, 2 discursivas e 1 redação (`bff04123-c48c-4ba3-ab90-147c63549eaf`).
- [x] 3.2 Diagnosticar e flexibilizar colunas residuais `NOT NULL` em `clients_examprintconfig` herdadas de migrações de branches paralelas, garantindo que `ExamPrintV2View` retorne `HTTP 200 OK`.
- [x] 3.3 Executar o gerador completo com paridade de produção gerando caderno com disciplina, série, `ExamTeacherSubject` e `exam_print_config` (`537f3a50-0a89-4fb1-b12a-16af6348cdf6`).
- [x] 3.4 Validar que o caderno gerado aparece perfeitamente no autocomplete assíncrono de agendamento de aplicação (`/aplicacoes/cadastrar/?category=hibrid`).
