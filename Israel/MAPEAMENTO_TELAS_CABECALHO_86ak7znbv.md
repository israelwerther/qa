# Mapeamento de Telas: Cabeçalhos e Páginas Personalizadas (Task 86ak7znbv)

Este documento lista todas as telas onde **Cabeçalhos de Prova** (`ExamHeader`) e **Páginas Customizadas** (`ClientCustomPage`) estão presentes no Lize Edu, servindo como roteiro de testes para validação das variáveis e formatos.

---

## 1. Telas de Edição e Criação (Entrada das Variáveis)

Aqui é onde o usuário insere as variáveis no editor de texto.

### 1.1 Cadastro / Edição de Cabeçalho de Prova
* **URL:** `http://127.0.0.1:8000/provas/cadastrar/cabecalhos/` ou `http://127.0.0.1:8000/provas/cabecalhos/<uuid:pk>/editar`
* **Caminho no Menu:** `Configurações` > `Provas` > `Padrões de cabeçalhos` > *Cadastrar novo* ou ícone de lápis em um existente.
* **Arquivo:** `fiscallizeon/exams/templates/dashboard/exams/exam_header_create_update.html`
* **O que testar:**
  - [ ] Verificar a lista lateral de variáveis.
  - [ ] Inserir variáveis de data (`#DiaDaAplicacao`, `#MesDaAplicacao`, `#AnoDaAplicacao`) e texto (`#NomeDoAluno`, `#NomeDaProva`).
  - [ ] Verificar comportamento atual: hoje são badges estáticos de texto simples (sem escolha de formato ou caixa).

### 1.2 Cadastro / Edição de Páginas Customizadas (Capas, Orientações, Contracapas)
* **URL:** `http://127.0.0.1:8000/provas/pagina/customizada/criar/` ou `http://127.0.0.1:8000/provas/pagina/customizada/<uuid:pk>/update/`
* **Caminho no Menu:** `Configurações` > `Provas` > `Padrões de páginas customizadas` > *Cadastrar nova* ou clicar em uma existente.
* **Arquivo:** `fiscallizeon/exams/templates/dashboard/exams/custom_pages_create_update.html`
* **O que testar:**
  - [ ] Verificar a lista lateral de variáveis.
  - [ ] Verificar comportamento atual: **não possui nenhuma variável de data ou horário** na lista.
  - [ ] Botão *"Salvar e visualizar impressão"* (testa o preview do PDF em modal).

---

## 2. Telas de Configuração e Diagramação (Vínculo com a Prova)

Onde o usuário escolhe qual cabeçalho ou página personalizada será usado.

### 2.1 Padrões de Impressão da Instituição
* **URL:** `http://127.0.0.1:8000/membros/padrao/configuracao/cadastrar/` ou `/membros/padrao/configuracao/atualizar/<uuid:pk>/`
* **Caminho no Menu:** `Configurações` > `Provas` > `Padrões de impressão`
* **Arquivo:** `fiscallizeon/clients/templates/clients/print_defaults_create_update.html`
* **O que testar:**
  - [ ] Seleção do cabeçalho padrão da escola.
  - [ ] Seleção das páginas customizadas padrão.

### 2.2 Diagramação de Caderno de Prova (V2)
* **URL:** Na tela de diagramação de um caderno (ex.: `http://127.0.0.1:8000/provas/<uuid:pk>/v2/diagramacao/`)
* **Arquivo:** `fiscallizeon/exams/templates/dashboard/exams/v2/exam_configs_form.html`
* **O que testar:**
  - [ ] Campo *"Selecione o cabeçalho"*.
  - [ ] Campo *"Páginas customizadas"*.
  - [ ] Opção de cabeçalho *"Completo"* vs *"Apenas nome do aluno"*.

---

## 3. Telas e Saídas de Impressão (Resolução das Variáveis em PDF/HTML)

Onde o sistema processa e substitui as tags pelos valores reais.

### 3.1 Visualização e Impressão Direta do Caderno de Provas
* **URL:** `http://127.0.0.1:8000/provas/<uuid:pk>/imprimir?header=<uuid_cabecalho>` ou `/provas/<uuid:pk>/v2/imprimir/`
* **Arquivo:** `fiscallizeon/exams/templates/dashboard/exams/v2/exam_print.html`
* **Método Python:** `Exam.get_personalized_header()` em `fiscallizeon/exams/models.py`
* **O que testar:**
  - [ ] Se as variáveis do cabeçalho foram substituídas no HTML renderizado.
  - [ ] Comportamento atual de data: mês sai como número (ex.: `08`), sem opção de extenso.

### 3.2 Impressão de Página Customizada (Preview / Documento Isolado)
* **URL:** `http://127.0.0.1:8000/provas/imprimir/paginas/customizada/?custom_page=<uuid>`
* **Arquivo:** `fiscallizeon/exams/templates/dashboard/exams/custom_pages_print.html`
* **Método Python:** `ClientCustomPage.get_content()` em `fiscallizeon/exams/models.py`
* **O que testar:**
  - [ ] Se os dados de turma, disciplina e aluno são substituídos.
  - [ ] Comportamento atual: tags de data não são substituídas (ficam em branco ou literais).

### 3.3 Geração de Malote a partir de Aplicações
* **URL:** `http://127.0.0.1:8000/aplicacoes/`
* **Ação:** No menu de opções da aplicação, clicar em *"Imprimir malote"* / *"Gerar malote"*.
* **Arquivo:** `fiscallizeon/applications/templates/dashboard/applications/application_list_new.html`
* **Tasks Celery:** `fiscallizeon/applications/tasks/export_exam_application_student.py` e `fiscallizeon/distribution/tasks/export_exams_bag.py`
* **O que testar:**
  - [ ] Download do PDF final do malote com cadernos nominais.
  - [ ] Verificar se `#NomeDoAluno`, `#Turma`, etc. saem formatados com a caixa configurada (ex.: Capitalizado vs Maiúsculo).
  - [ ] Verificar se as páginas customizadas anexadas contêm as variáveis de data resolvidas.

### 3.4 Geração de Malote a partir de Ensalamentos (Distribuição de Salas)
* **URL:** `http://127.0.0.1:8000/distribuicao/`
* **Ação:** Na lista de distribuições/ensalamentos, clicar em *"Imprimir malote"* (abre o modal de configuração de impressão do malote).
* **Arquivo:** `fiscallizeon/distribution/templates/distribution/distribution_list.html`
* **Tasks Celery:** `fiscallizeon/distribution/tasks/export_exams_bag.py` (orquestra `export_exam_application_student` e `export_custom_page_application_student`)
* **O que testar:**
  - [ ] Seleção de páginas customizadas no modal do malote.
  - [ ] Geração do arquivo unificado do malote dividido por salas/turmas.
  - [ ] Verificar formatação de texto e datas nos cadernos e capas dos alunos ensalados.

### 3.5 Geração de Malote Individual / Por Sala no Ensalamento
* **URL:** `http://127.0.0.1:8000/distribuicao/salas/<uuid:pk>/`
* **Ação:** Clicar em *"Imprimir Malote"* ou no menu do aluno *"Imprimir malote individual"*.
* **Arquivo:** `fiscallizeon/distribution/templates/distribution/rooms/room_distribution_detail.html`
* **O que testar:**
  - [ ] Download do malote por sala específica ou de um único aluno.
  - [ ] Validar resolução das variáveis de cabeçalho e página personalizada no arquivo gerado.
