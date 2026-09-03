# QA Test Plan — Aplicação Híbrida (Caderno Impresso + Registro de Respostas Digital)

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-09-03 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Applications, Exams, Distribution, OMR, Student App (API v3) |
| **Nível de Risco:** | Alto |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5/5) |

---

## 1. Summary of Changes (Resumo das Alterações)

Esta branch implementa o tipo de aplicação **Híbrida** (`Application.HYBRID = 5`), atendendo a escolas que aplicam avaliações com cadernos de prova impressos (com ou sem randomização de questões/alternativas), mas onde os alunos realizam o registro de suas respostas no ambiente digital (aplicativo do aluno), dispensando o uso de cartões-resposta físicos e leitura por OMR.

### Backend & Modelos
- **Novo Enum de Categoria:** Adicionado `Application.HYBRID = 5` em `CATEGORY_CHOICES` com rótulo "Híbrida" (`fiscallizeon/applications/models.py`).
- **Camada de Serviço Centralizada:** Criada a classe `ApplicationCategoryRoles` (`fiscallizeon/applications/services/application_service.py`) com os métodos `prints_presential_bag()` (Presencial e Híbrida) e `uses_digital_answers()` (Online, Lista e Híbrida) para evitar dispersão de `if category == HYBRID`.
- **Status e Ausências:** Atualizados `ApplicationStudent.get_status`, `missing_students_count` e `finish_students_count` para que aplicações Híbridas usem o critério digital (`start_time`/`end_time`) e não `is_omr`.
- **Formulário de Aplicação:** `ApplicationForm` aceita Híbrida tanto para cadernos randomizados quanto para não randomizados, e não restringe cadernos contendo questões discursivas, arquivos ou redações.
- **Bloqueio de Malote Após Início:** Em `ExportApplicationExamsBagAPIView`, a geração de malote de Híbrida é recusada com `HTTP 401 UNAUTHORIZED` se o horário atual for maior ou igual ao início da aplicação (`timezone.localtime(timezone.now()) >= application.date_time_start_tz`).

### Malote da Aplicação e de Ensalamento (Tarefas Celery / OMR / Distribution)
- **Malote sem Cartão-Resposta:** Em `omr/tasks/export_answer_sheet.py` e `distribution/tasks/export_exams_bag.py`, aplicações Híbridas não enfileiram cartões-resposta objetivos, discursivos ou folhas de redação. O cartão OMR é exclusivo para `Application.PRESENTIAL`.
- **Exclusão de Páginas Customizadas de Folhas:** Como não há cartão-resposta gerado, qualquer página customizada do cliente posicionada antes ou depois da folha de respostas (`ClientCustomPage.OBJECTIVE_ANSWER_SHEET` e `ClientCustomPage.DISCURSIVE_ANSWER_SHEET`) é suprimida do malote. Páginas customizadas do caderno (`STUDENT_EXAM` e `AFTER_STUDENT_EXAM`) continuam sendo impressas normalmente.
- **Caderno Obrigatório:** O backend força `include_exams = True` para aplicações Híbridas, garantindo a exportação do caderno e o disparo de `randomize_application()` quando o caderno for randomizado.
- **Blindagem contra `PdfError` em Agrupamento:** Em `omr/tasks/group_answer_sheet_files.py` (`process_unity_separated_files` no modo BAG_SEPARATED_FILES) e `distribution/tasks/group_files.py`, o merge de `answer_full_urls` só é executado se houver paths de cartão-resposta e a aplicação for Presencial. Isso evita que listas vazias produzam arquivos corrompidos sem trailer.

### Interface de Coordenação
- **Sidebar:** Adicionado o item **Híbridas** no submenu "Aplicações" de `components/sidebar/sidebar_coordination.html`, com filtro `?category=hibrid`, ícone dedicado (`lucide-book-open-check`), ativo via `application_hybrid_active` no `context_processors.py`.
- **Criação/Edição de Aplicação:** Inserido o 4º card **Híbrida** na seleção de categoria em `application_create_update.html`, adaptando o grid para 4 colunas em telas médias/grandes (`lg:tw-grid-cols-4`).
- **Modal de Impressão de Malote:** Em `application_list_new.html` e `distribution_list.html`, o modal `#configurePrintModal` oculta campos de folhas de resposta objetivas/discursivas e o checkbox de incluir caderno (já que o caderno é mandatório). As opções de diagramação e versões de randomização permanecem acessíveis.

### API v3 do Aluno (`fiscallizeon/app/students/`)
- **Listagem e Acesso:** Aplicações Híbridas entram na listagem de `availables_today` e no queryset `is_online()` (que exclui apenas `PRESENTIAL`).
- **Ordenação em `take_test` e `result`:** Se houver `RandomizationVersion` vinculada ao aluno, as questões e alternativas são ordenadas rigorosamente pelo `exam_json` persistido no malote. Se não houver versão e o caderno não for randomizado, segue a ordem padrão do caderno. O `shuffle_code` de prova online é ignorado em Híbridas.
- **Higienização do Payload:** Em Híbridas, `enunciation`, `base_texts` e `alternatives[].text` são retornados vazios, permitindo que a interface do aluno funcione como folha de preenchimento de gabarito avulso sem expor os enunciados já impressos (o mesmo modelo visual de um gabarito avulso no `app.lizeedu`).
- **Gravação e Correção:** O endpoint `create_answer` associa as respostas (`OptionAnswer`/`SumAnswer`) às questões reais do banco, e a finalização preenche `start_time`/`end_time`.

---

## 2. Scope Boundaries (Diferenças de Escopo)

### In Scope
- Criação e edição de aplicações com categoria Híbrida por usuários do perfil Coordenação.
- Exibição universal do item "Híbridas" na sidebar e dos cards na tela de cadastro para todos os clientes, sem necessidade de ativação de flag.
- Filtro funcional de aplicações híbridas na listagem (`/aplicacoes/?category=hibrid`).
- Geração de malote de prova impresso contendo apenas o caderno dos alunos, suprimindo qualquer folha de cartão-resposta (objetivo, discursivo e redação) e suas respectivas páginas customizadas.
- Atribuição determinística de versão de randomização (`RandomizationVersion`) para cada aluno durante a geração do malote quando o caderno possuir parâmetros de randomização ativados.
- Geração de malote em ensalamentos mistos (`RoomDistribution`), aplicando o comportamento híbrido apenas às aplicações híbridas e mantendo cartões OMR para as presenciais.
- Bloqueio estrito da geração de malote de aplicação híbrida após o horário de início agendado (`date_time_start_tz`), pois a partir desse instante o aluno já pode realizar a prova no app.
- Entrega do contrato de dados via API v3 (`take_test`, `availables_today`, `create_answer`, `finish`, `result`) com numeração e alternativas alinhadas ao caderno impresso.
- Cálculo de correção objetiva existente para respostas digitais enviadas pelo aluno.
- Apuração correta de status (Em aberto, Realizando, Realizado, Ausente) baseando-se exclusivamente em eventos de tempo e respostas digitais, sem interferência de leitura por OMR.
- Cards e listagens de finalizados/ausentes (detalhes da aplicação, analytics de presença) tratando Híbrida como online. Quem finalizou o registro digital conta como presente (mesmo com `is_omr=False`); quem só tivesse leitura OMR não contaria como presente.

### Out of Scope
- Implementação de telas dentro do SPA do aluno (o frontend do app do aluno reside em repositório externo separado; este PR entrega apenas o contrato da API v3).
- Exibição de textos de enunciados, imagens ou textos de apoio no aplicativo do aluno durante a realização da prova.
- Processamento, leitura óptica ou upload de cartões-resposta via OMR para aplicações Híbridas.
- Alteração no motor ou nos algoritmos centrais de geração de permutações de prova (`randomize_exam_json`).
- Criação de novas filas no Celery (são reaproveitadas as filas existentes `omr-export` e rotas de `distribution`).
- Criação de campos de flag de ativação por cliente (`Client`) ou permissões customizadas de grupo (`CustomGroup`).
- Refatoração da tela legada de criação de aplicação para o design system novo (`redesign/base_component.html`).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Listagem de Aplicações Híbridas | Aplicações > Híbridas | `/aplicacoes/?category=hibrid` | `applications:applications_list` |
| Agendar Aplicação Híbrida | Botão "Agendar aplicação" (na listagem com filtro) | `/aplicacoes/cadastrar/?category=hibrid` | `applications:applications_create` |
| Agendar Várias Híbridas | Botão "Agendar várias aplicações" | `/aplicacoes/cadastrar-multiplas/?category=hibrid` | `applications:applications_create_multiple` |
| Editar Aplicação | Ação "Editar" na linha da aplicação | `/aplicacoes/<uuid:pk>/editar/` | `applications:applications_update` |
| Imprimir Malote da Aplicação | Linha da tabela > Ações > Impressão > "Todos os alunos" | `POST /aplicacoes/api/aplicacao/<uuid:pk>/imprimir-malote/` | `applications:applications_export_exams_bag` (API) |
| Listagem de Ensalamento | Aplicações > Ensalamento | `/ensalamento/` | `distribution:distribution_list` |
| Imprimir Malote de Ensalamento | Linha do ensalamento > Ações > "Imprimir malote" | `POST /ensalamento/api/ensalamentos/<uuid:pk>/gerar-malote/` | `distribution:export_distribution_exams_bag` (API) |
| App Aluno: Aplicações Disponíveis | Home / Minhas Avaliações | `GET /api/v3/applications/availables_today/` | `app:applications-availables-today` |
| App Aluno: Iniciar Prova / Registro | Card da Prova > "Iniciar Prova" | `GET /api/v3/applications/<uuid:pk>/take_test/` | `app:applications-take-test` |
| App Aluno: Salvar Resposta | Marcar alternativa A–E | `POST /api/v3/applications/<uuid:pk>/create_answer/` | `app:applications-create-answer` |
| App Aluno: Finalizar Prova | Botão "Finalizar Avaliação" | `POST /api/v3/applications/<uuid:pk>/finish/` | `app:applications-finish` |
| App Aluno: Ver Resultado | Prova Concluída > "Ver resultado" | `GET /api/v3/applications/<uuid:pk>/result/` | `app:applications-result` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comandos de Testes Automatizados (CLI)

```bash
# Execução no ambiente local (venv)
./venv/bin/pytest fiscallizeon/applications/tests/forms/test_application_form_hybrid.py --reuse-db
./venv/bin/pytest fiscallizeon/applications/tests/models/test_application_hybrid_status.py fiscallizeon/applications/tests/models/test_application_prints_presential_bag.py --reuse-db
./venv/bin/pytest fiscallizeon/applications/tests/services/test_application_category_roles.py fiscallizeon/applications/tests/test_exams_bag_api.py fiscallizeon/applications/tests/test_views.py --reuse-db
./venv/bin/pytest fiscallizeon/omr/tests/test_export_answer_sheet.py fiscallizeon/omr/tests/test_group_answer_sheet_files.py --reuse-db
./venv/bin/pytest fiscallizeon/distribution/tests/test_export_exams_bag.py fiscallizeon/distribution/tests/test_group_files.py --reuse-db
./venv/bin/pytest fiscallizeon/app/students/tests/test_take_test_and_result_views.py fiscallizeon/app/students/tests/test_availables_today.py fiscallizeon/app/students/tests/test_take_test_shuffle_service.py --reuse-db
```

### Personas Envolvidas
- **Persona Coordenador:** Usuário membro de `SchoolCoordination` com permissões completas de gerenciar aplicações e gerar malotes (`applications.view_application`, `applications.add_application`, `applications.can_print_exams_bag`).
- **Persona Aluno:** Usuário com perfil `Student` ativo, matriculado na `SchoolClass` vinculada à aplicação.

### Fixtures e Setup de Dados para Testes Manuais (Python / Mixer)

```python
from datetime import timedelta
from django.utils import timezone
from mixer.backend.django import mixer

from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.classes.models import Grade, SchoolClass
from fiscallizeon.clients.models import (
    Client,
    CoordinationMember,
    SchoolCoordination,
    Unity,
)
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject
from fiscallizeon.questions.models import Alternative, Question, TeacherSubject
from fiscallizeon.students.models import Student
from fiscallizeon.subjects.models import Subject

# 1. Tenant e Coordenação
client = mixer.blend(
    Client,
    name="Colégio Demo Híbrida",
    has_exam_elaboration=True,
    has_distribution=True,
    require_2fa=False,
)
unity = mixer.blend(Unity, client=client, name="Unidade Central")
coordination = mixer.blend(
    SchoolCoordination, unity=unity, name="Coordenação Ensino Médio"
)

# 2. Coordenador
coord_user = mixer.blend(
    User,
    username="coordenador_qa",
    email="coord.qa@lize.local",
    is_staff=True,
    is_superuser=True,
)
coord_user.set_password("lize123456")
coord_user.save()
mixer.blend(CoordinationMember, user=coord_user, coordination=coordination)

# 3. Turma e Alunos (2 alunos para comparar randomização)
grade = mixer.blend(Grade, name="3ª Série EM")
school_class = mixer.blend(
    SchoolClass,
    coordination=coordination,
    grade=grade,
    name="Turma A",
    school_year=timezone.now().year,
)

student_user_1 = mixer.blend(
    User, username="aluno_qa_1", email="aluno1@lize.local", is_active=True
)
student_user_1.set_password("lize123456")
student_user_1.save()
student_1 = mixer.blend(Student, client=client, user=student_user_1)
school_class.students.add(student_1)

student_user_2 = mixer.blend(
    User, username="aluno_qa_2", email="aluno2@lize.local", is_active=True
)
student_user_2.set_password("lize123456")
student_user_2.save()
student_2 = mixer.blend(Student, client=client, user=student_user_2)
school_class.students.add(student_2)

# 4. Caderno de Prova com Randomização
subject = mixer.blend(Subject, name="Matemática")
teacher_subject = mixer.blend(
    TeacherSubject, subject=subject, coordination=coordination
)

exam = mixer.blend(
    Exam,
    client=client,
    name="Simulado Híbrido Randomizado 2026",
    random_questions=True,
    random_alternatives=True,
    is_abstract=False,
)
exam.coordinations.add(coordination)

ets = mixer.blend(
    ExamTeacherSubject, exam=exam, teacher_subject=teacher_subject, order=1
)

for i in range(1, 6):
    q = mixer.blend(
        Question,
        client=client,
        subject=subject,
        category=Question.CHOICE,
        enunciation=f"Enunciado completo da questão {i} com texto e fórmulas.",
    )
    mixer.blend(
        Alternative, question=q, text=f"Alternativa Correta Q{i}", is_correct=True
    )
    for letter in ["B", "C", "D", "E"]:
        mixer.blend(
            Alternative,
            question=q,
            text=f"Distrator {letter} Q{i}",
            is_correct=False,
        )
    mixer.blend(
        ExamQuestion,
        exam=exam,
        question=q,
        exam_teacher_subject=ets,
        order=i,
    )

# 5. Aplicação Híbrida agendada
app_hybrid = mixer.blend(
    Application,
    exam=exam,
    category=Application.HYBRID,
    date=timezone.localdate(),
    start="07:00",
    end="23:00",
    school_class=school_class,
)
mixer.blend(ApplicationStudent, application=app_hybrid, student=student_1)
mixer.blend(ApplicationStudent, application=app_hybrid, student=student_2)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

> **Persona Ativa Padrão (Cenários 5.1 a 5.4):** Coordenador de Unidade com login realizado na plataforma web.  
> **Persona Ativa Aluno (Cenários 5.5 e 5.6):** Aluno matriculado na turma com login realizado no App do Aluno.

### 5.1 Sidebar e Listagem de Aplicações [Automatizável ✅]

#### Cenário 1 — Visibilidade do item Híbridas na barra lateral de navegação
- [x] Acessar o menu lateral esquerdo como Coordenador.
- [x] Clicar sobre a opção "Aplicações" para expandir os submódulos.
- [x] Verificar se o item "Híbridas" está visível entre as opções (abaixo de "Presencial").
- [x] Confirmar que o ícone correspondente de livro com check é exibido ao lado do texto.
- [x] Clicar no item "Híbridas" e verificar se a URL é atualizada para `/aplicacoes/?category=hibrid`.
- [x] Verificar se o item "Híbridas" permanece com estilo destacado de ativo no menu.

#### Cenário 2 — Filtragem da listagem principal de aplicações
- [x] Estando na listagem de Híbridas, verificar as aplicações listadas na tabela.
- [x] Confirmar que apenas aplicações da categoria Híbrida são exibidas na tela.
- [x] Verificar se aplicações puramente presenciais ou online NÃO aparecem nesta listagem.
- [x] Limpar os filtros ou alternar para o submenu "Atividade Online" e confirmar a troca imediata das aplicações listadas.

---

### 5.2 Criação e Edição de Aplicação Híbrida [Automatizável ✅]

#### Cenário 3 — Criação de aplicação com seleção do card Híbrida
- [x] Na tela de listagem de Híbridas, clicar no botão azul "Agendar aplicação".
- [x] Verificar se a página de cadastro abre com o quarto card "Híbrida" selecionado por padrão.
- [x] Observar os textos do card: título "Híbrida" e subtítulo informativo "Geração de malote + Respostas cadastradas online."
- [x] Selecionar um caderno com parâmetros de randomização ativados (`is_randomized = True`).
- [x] Preencher as datas, horários (início e término) e vincular uma turma com alunos.
- [x] Clicar no botão para salvar a aplicação.
- [ ] Confirmar o redirecionamento com mensagem de sucesso e verificar a aplicação recém-criada na listagem de Híbridas.


#### Cenário 4 — Criação com caderno de prova não randomizado
- [x] Iniciar um novo agendamento de aplicação selecionando a categoria Híbrida.
- [x] Selecionar um caderno tradicional que NÃO possui randomização de questões nem de alternativas.
- [x] Preencher as informações obrigatórias da aplicação e submeter o formulário.
- [x] Confirmar que o sistema grava a aplicação com sucesso sem disparar validações impeditivas de randomização.

#### Cenário 5 — Criação com caderno contendo questões discursivas ou redação
- [x] Iniciar um novo agendamento de aplicação selecionando a categoria Híbrida.
- [x] Selecionar um caderno que contenha questões discursivas e proposta de redação.
- [x] Concluir o preenchimento dos campos e salvar.
- [x] Confirmar que a aplicação é salva com sucesso sem rejeição por conter questões não-objetivas.

#### Cenário 6 — Bloqueio de alteração de categoria após malote pronto
- [x] Abrir uma aplicação Híbrida já existente que já teve malote gerado ou está marcada como pronta para impressão.
- [x] Acessar a tela de edição da aplicação.
- [x] Observar a seção de escolha de categoria.
- [x] Confirmar que as opções de categoria encontram-se desabilitadas para clique.
- [x] Verificar a presença da mensagem de alerta informando a impossibilidade de alteração da categoria por haver malote gerado.

---

### 5.3 Modal de Impressão e Geração de Malote da Aplicação [Automatizável ✅]

#### Cenário 7 — Abertura do modal de impressão com controles adaptados
- [x] Na listagem de aplicações, localizar uma aplicação Híbrida.
- [x] Na última coluna da linha da aplicação, clicar no botão "**Opções**" (botão branco com borda cinza).
- [x] No menu que se abre, localizar a seção com cabeçalho cinza "**IMPRESSÃO**" e clicar na opção "**Todos os alunos**" (ícone de usuários).
- [ ] Verificar que o modal de configuração de impressão é aberto na tela.
- [ ] Confirmar que a seção "Modelo da folhas de resposta objetivas" NÃO está visível no modal.
- [ ] Confirmar que a opção "Foto oficial" NÃO está visível no modal.
- [ ] Confirmar que a opção "Incluir folhas de respostas discursivas" NÃO está visível no modal.
- [ ] Confirmar que a opção "Incluir cadernos de prova" NÃO está visível (o caderno é obrigatório).
- [ ] Confirmar que as opções de diagramação e o checkbox de incluir folha com versões de randomização permanecem acessíveis.

#### Cenário 8 — Geração do malote antes do início da prova
- [ ] No modal de impressão de uma aplicação Híbrida cujo horário de início ainda não ocorreu, clicar em "Imprimir malote".
- [ ] Confirmar o fechamento do modal e o disparo da geração.
- [ ] Aguardar a conclusão da exportação do arquivo e efetuar o download do arquivo ZIP gerado.
- [ ] Descompactar o arquivo ZIP e inspecionar os PDFs contidos:
  - Verificar a presença dos cadernos de prova de cada aluno da turma.
  - Verificar a ausência total de arquivos de cartões-resposta (folhas OMR).
  - Verificar se a folha de presença está incluída (se configurada).

#### Cenário 9 — Bloqueio de geração de malote após o início da prova
- [ ] Localizar uma aplicação Híbrida cujo horário de início agendado já foi ultrapassado (data/hora atual superior à data e horário de início).
- [ ] Abrir o menu de ações da aplicação e clicar para imprimir o malote.
- [ ] Submeter a solicitação de impressão.
- [ ] Verificar que o sistema recusa a solicitação, retornando mensagem informativa indicando que o malote não pode mais ser impresso após o início da aplicação.

#### Cenário 10 — Vínculo de versão de randomização no malote
- [ ] Gerar o malote de uma aplicação Híbrida cujo caderno é randomizado.
- [ ] Abrir os cadernos impressos de dois alunos diferentes do mesmo pacote.
- [ ] Comparar o caderno do Aluno 1 com o caderno do Aluno 2 e confirmar que a ordem das questões e alternativas é distinta entre eles.
- [ ] Verificar no banco de dados se cada aluno recebeu uma versão registrada correspondente exatamente ao caderno impresso.

#### Cenário 10.1 — Páginas customizadas associadas a cartão-resposta vs caderno
- [ ] Configurar no caderno da aplicação páginas customizadas do cliente (`ClientCustomPage`) em diferentes posições: antes/depois da folha de resposta (`OBJECTIVE_ANSWER_SHEET` ou `DISCURSIVE_ANSWER_SHEET`) e páginas do caderno (`STUDENT_EXAM` ou `AFTER_STUDENT_EXAM`).
- [ ] Gerar o malote da aplicação Híbrida e inspecionar o PDF resultante.
- [ ] Confirmar que páginas customizadas de folhas de respostas NÃO são geradas nem incluídas no pacote (já que a folha OMR foi suprimida).
- [ ] Confirmar que as páginas customizadas vinculadas ao caderno de prova continuam sendo geradas e anexadas perfeitamente ao caderno do aluno.

---

### 5.4 Malote no Ensalamento (Room Distribution) [Automatizável ✅]

#### Cenário 11 — Ensalamento contendo apenas aplicações Híbridas
- [ ] Acessar o módulo de Ensalamento (`/ensalamento/`).
- [ ] Criar ou localizar um ensalamento que possua apenas aplicações da categoria Híbrida.
- [ ] Clicar na ação de imprimir malote do ensalamento.
- [ ] Verificar que o modal não exibe controles de modelos de cartão OMR nem folhas discursivas.
- [ ] Gerar o malote e baixar o arquivo final.
- [ ] Confirmar que o pacote final do ensalamento contém apenas os cadernos dos alunos, sem gerar erros de arquivo corrompido ou merge de PDFs vazios.

#### Cenário 12 — Ensalamento misto (Presencial + Híbrida)
- [ ] Montar um ensalamento que contenha na mesma sala uma aplicação Presencial e uma aplicação Híbrida.
- [ ] Disparar a geração do malote completo do ensalamento.
- [ ] Baixar o pacote gerado e inspecionar os arquivos:
  - Confirmar que para os alunos da aplicação Presencial foram gerados cadernos E cartões-resposta OMR.
  - Confirmar que para os alunos da aplicação Híbrida foram gerados apenas os cadernos de prova, sem cartões OMR.
  - Confirmar que o processo finaliza com sucesso sem inconsistências de contagem de páginas.

#### Cenário 12.1 — Restrição de seleção de tipos de aplicação no Ensalamento
- [ ] Acessar a tela de criação de ensalamento (`/ensalamento/cadastrar/`).
- [ ] Inspecionar a listagem de aplicações disponíveis para seleção no filtro de data/turma.
- [ ] Verificar se o sistema impede a seleção conjunta de aplicações de categorias incompatíveis ou se isola aplicações Híbridas de Presenciais, conforme regra de negócio reforçada na especificação.

---

### 5.5 Experiência e Registro de Respostas do Aluno (API v3 / App Aluno) [Apenas Manual 👁]

> [!TIP]
> **Dica de Teste / Referência Visual (`app.lizeedu`):**  
> Caso deseje comparar com o comportamento esperado de uma prova sem exibição de enunciado e alternativas, acesse ou crie um caderno com gabarito avulso (`Exam.is_abstract = True`) no ambiente web antigo de alunos (`app.lizeedu`). O fluxo da aplicação Híbrida é análogo: o aluno visualiza apenas os identificadores numéricos das questões e as bolhas A–E para marcação rápida, acompanhando o caderno impresso físico em mãos.

#### Cenário 13 — Visualização da avaliação na área do aluno
- [ ] Autenticar-se no App do Aluno com as credenciais do Aluno 1.
- [ ] Verificar se a aplicação Híbrida aparece listada no painel de avaliações disponíveis no dia.
- [ ] Confirmar que o card da avaliação exibe o nome do caderno e o período de realização.

#### Cenário 14 — Abertura da tela de preenchimento (Caderno Randomizado)
- [ ] Com o Aluno 1, clicar no botão para iniciar a avaliação dentro da janela de tempo.
- [ ] Observar o layout da tela:
  - Verificar a presença de aviso instruindo o aluno a acompanhar a numeração de acordo com seu caderno impresso.
  - Confirmar que os enunciados, imagens e textos de apoio das questões NÃO são exibidos na tela (campos em branco).
  - Confirmar que cada questão exibe apenas as bolhas de seleção de alternativas (A, B, C, D, E).
- [ ] Verificar a numeração da questão 1:
  - Comparar a numeração e alternativas com o caderno impresso físico do Aluno 1.
  - Confirmar que a ordem das alternativas (A até E) corresponde rigorosamente à ordem impressa no caderno dele.

#### Cenário 15 — Comparação de ordem entre alunos distintos
- [ ] Abrir simultaneamente a tela de realização no login do Aluno 2 (ou inspecionar o payload de `take_test`).
- [ ] Comparar a tela do Aluno 1 com a tela do Aluno 2.
- [ ] Confirmar que o ID interno e a correspondência das alternativas refletem a versão exclusiva de cada aluno, sem uso de embaralhamento dinâmico volátil.

#### Cenário 16 — Envio e confirmação de respostas
- [ ] Com o Aluno 1, selecionar as alternativas correspondentes no gabarito digital para todas as questões.
- [ ] Confirmar o envio de cada questão e verificar o feedback visual de resposta registrada.
- [ ] Clicar no botão para finalizar a avaliação.
- [ ] Confirmar o diálogo de entrega e verificar a mensagem de conclusão com sucesso.

---

### 5.6 Correção Objetiva, Presença e Status da Aplicação [Automatizável ✅]

#### Cenário 17 — Associação da resposta à questão correta e acerto
- [ ] Acessar os dados da resposta gravada pelo Aluno 1.
- [ ] Verificar se a resposta marcada na posição visual "Alternativa A" do caderno dele ficou associada à entidade `Question` correta no banco de dados.
- [ ] Verificar se a rotina de correção atribuiu pontuação correta comparando a alternativa selecionada com o gabarito oficial daquela questão.

#### Cenário 18 — Status do aluno na aplicação (Realizado e Realizando)
- [ ] Criar um cenário onde o Aluno 1 concluiu o registro no app e o Aluno 3 iniciou a prova (`start_time` preenchido) mas ainda não finalizou (`end_time` nulo).
- [ ] Acessar o painel da aplicação como Coordenador:
  - Verificar se o Aluno 1 consta com status "Realizado".
  - Verificar se o Aluno 3 consta com status "Realizando".
  - Confirmar que para ambos o campo `is_omr` permanece `False`.
  - Confirmar que a contagem de presentes nos cards da coordenação e no analytics de presença computa o Aluno 1 como concluído.

#### Cenário 19 — Aluno ausente na aplicação Híbrida
- [ ] Deixar o Aluno 2 sem preencher respostas até que o horário de término da aplicação expire.
- [ ] Consultar o relatório e a listagem da aplicação na coordenação após o término.
- [ ] Confirmar que o Aluno 2 figura com o status "Ausente", sem depender de ausência de leitura óptica de cartão OMR.

#### Cenário 20 — Imunidade à leitura OMR para cálculo de presença
- [ ] Em ambiente de teste/banco, forçar o atributo `is_omr = True` em um aluno de aplicação Híbrida que NÃO tenha registros de `start_time`/`end_time`.
- [ ] Acessar o detalhe da aplicação e o analytics de presença.
- [ ] Confirmar que o sistema NÃO considera o aluno como presente com base exclusivamente no `is_omr`. A presença em Híbridas deve depender estritamente do fluxo digital (`start_time`/`end_time`).

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

> **MANDATÓRIO:** O testador de QA deve capturar screenshots das telas mencionadas abaixo e efetuar comparação lado a lado com os mockups fornecidos em `openspec/changes/aplicacao-presencial-registro-online/references/`.

### Checklist de Telas e Mockups

- [ ] **Seleção de Categoria na Criação (`criacao-aplicacao.html`):**
  - Tirar print dos 4 cards de categoria em tela cheia (desktop) e em tela reduzida (mobile).
  - Validar se o card "Híbrida" respeita as cores de borda laranja/primary quando selecionado (`tw-border-primary-600 tw-bg-primary-200`).
  - Validar se o ícone e textos estão alinhados aos demais três cards (Online, Presencial, Lista).
- [ ] **Modal de Impressão de Malote (`application_list_new.html`):**
  - Tirar print do modal `#configurePrintModal` aberto para uma aplicação Híbrida.
  - Validar a limpeza visual do modal, garantindo que não restaram espaços em branco ou divisores orfãos dos campos ocultados (folha objetiva e discursiva).
- [ ] **Contrato Visual do Registro de Respostas (`registro-respostas-aluno.html`):**
  - Tirar print da tela de preenchimento de respostas do aluno no SPA.
  - Validar se o aviso textual sobre o acompanhamento pelo caderno impresso está visível no topo.
  - Validar o espaçamento e alinhamento das bolhas A–E para preenchimento.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!BUG]
> **Bug 1: Redirecionamento pós-cadastro de Aplicação Híbrida não preserva o filtro da categoria**  
> **Categoria:** `[Backend Logic]` / `[UX/UI]`  
> **Contexto / Root Cause:** Em `fiscallizeon/applications/views.py`, os métodos `get_success_url` das views `ApplicationCreateView` (linhas 716–726) e `ApplicationCreateMultipleView` (linhas 872–882) verificam apenas:
> ```python
> if self.object.category == Application.PRESENTIAL:
>     url += '?category=presential'
> elif self.object.category == Application.HOMEWORK:
>     url += '?category=homework'
> return url
> ```
> Para aplicações da categoria `Application.HYBRID` (`category = 5`), a condição cai no fallback padrão sem query parameters (`reverse('applications:applications_list')`). Como resultado, o usuário é redirecionado para a listagem geral (`/aplicacoes/`) em vez da listagem filtrada de Híbridas (`/aplicacoes/?category=hibrid`), desmarcando o item "Híbridas" ativo na sidebar.  
> **Comportamento Esperado:** `(inferência de UX — Spec Gap)`: Ao cadastrar uma aplicação Híbrida (ou múltiplas), o sistema deve redirecionar para `/aplicacoes/?category=hibrid`, espelhando o comportamento das aplicações presenciais (`?category=presential`) e listas de exercício (`?category=homework`).  
> **Workaround:** Clicar manualmente no menu lateral "Aplicações > Híbridas" após salvar o formulário para visualizar a aplicação recém-criada.

> [!WARNING]
> **Status de Implementação: Tratamento de Retorno HTTP 409 sem Malote Gerado**  
> **Categoria:** `[Backend Logic]` / `[Spec Gap]`  
> **Contexto:** A tarefa 4.3 da OpenSpec (`tasks.md L.51`) prevê que a rota `take_test` retorne `HTTP 409 CONFLICT` caso a aplicação Híbrida possua caderno randomizado mas o malote ainda não tenha sido gerado (ausência de `RandomizationVersion`). Atualmente, se o aluno tentar acessar sem versão prévia, a API não lança 409 explícito.  
> **Comportamento Esperado:** `(conforme OpenSpec: spec.md L.85)`: Se o caderno for randomizado e não houver `RandomizationVersion` (malote ainda não gerado), o GET de `take_test` MUST retornar 409 com mensagem de que o caderno ainda não foi impresso. Caderno não randomizado MUST NOT retornar 409.  
> **Workaround temporário:** Certificar-se de sempre gerar o malote da aplicação Híbrida antes de testar o login do aluno no `take_test`.

> [!WARNING]
> **Atenção Técnica: Listagem de Aplicações na Criação de Ensalamento**  
> **Categoria:** `[Backend Logic]` / `[Spec Gap]`  
> **Contexto:** O endpoint `ApplicationListView` (`/aplicacoes/api/`), consumido pela tela de criação de ensalamento (`/ensalamento/cadastrar/`), filtra internamente por `category=Application.PRESENTIAL`. Por conta disso, aplicações Híbridas não são retornadas pelo filtro assíncrono padrão do modal de ensalamento a menos que sejam explicitamente incluídas ou que o ensalamento seja gerado via botão de atalho direto da aplicação (`?application_id=...`).  
> **Comportamento Esperado:** `(conforme alinhamento ClickUp)`: Verificar se o ensalamento deve bloquear ou não a combinação de aplicações de tipos distintos. Validar na prática se a coordenação consegue ensalar aplicações híbridas e se a regra de restrição de tipos diferentes está sendo respeitada.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Janela de Extensão para Digitação de Gabarito em Casa**  
> Atualmente, a janela de digitação das respostas no app do aluno encerra-se rigidamente no horário final da aplicação (`application.end`). Para escolas onde os alunos fazem a prova presencialmente mas digitam o gabarito no contraturno em casa, pode ser oportuno adicionar no futuro um campo independente de prazo de digitação de respostas.

> [!NOTE]
> **Cache do Payload de Questões de Híbridas no App**  
> Na consulta de `result` do aluno em Híbridas, a chave de cache desconsidera o `shuffle_code` online e usa `rv_number`. Garantir monitoramento do volume de invalidações desse cache em simulados de grande porte.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do template HTML, e não a View.  
🔗 **[Ver Mapeamento de Tela — Cadastro de Aplicações](docs/tests/usability/application_create_update.md)**  
🔗 **[Ver Mapeamento de Tela — Listagem e Malote](docs/tests/usability/application_list_new.md)**  
🔗 **[Ver Mapeamento de Tela — Impressão de Ensalamento](docs/tests/usability/modal_print.md)**

### Snippet de Automação (Playwright + Fixtures de Banco com Mixer)

O script abaixo demonstra a automação completa ponta a ponta: prepara os dados no banco via `mixer`, abre o navegador como Coordenador, valida o modal de impressão de malote híbrido e executa o fluxo de envio da API v3 do aluno.

```python
import pytest
from django.utils import timezone
from mixer.backend.django import mixer
from playwright.sync_api import Page, expect

from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.clients.models import (
    Client,
    CoordinationMember,
    SchoolCoordination,
    Unity,
)
from fiscallizeon.exams.models import Exam, ExamQuestion, ExamTeacherSubject
from fiscallizeon.questions.models import Alternative, Question, TeacherSubject
from fiscallizeon.students.models import Student
from fiscallizeon.subjects.models import Subject


@pytest.mark.django_db
def test_hybrid_application_print_modal_and_api(page: Page, live_server):
    # 1. Setup Backend com Mixer
    client = mixer.blend(
        Client, has_exam_elaboration=True, has_distribution=True, require_2fa=False
    )
    unity = mixer.blend(Unity, client=client)
    coordination = mixer.blend(SchoolCoordination, unity=unity)

    coord_user = mixer.blend(
        User, username="coord_playwright", is_staff=True, is_superuser=True
    )
    coord_user.set_password("senha123")
    coord_user.save()
    mixer.blend(CoordinationMember, user=coord_user, coordination=coordination)

    exam = mixer.blend(
        Exam,
        client=client,
        name="Exame Híbrido Automação",
        random_questions=True,
        random_alternatives=True,
        is_abstract=False,
    )
    exam.coordinations.add(coordination)

    school_class = mixer.blend(SchoolClass, coordination=coordination)
    student_user = mixer.blend(User, username="student_pw", is_active=True)
    student = mixer.blend(Student, client=client, user=student_user)
    school_class.students.add(student)

    app_hybrid = mixer.blend(
        Application,
        exam=exam,
        category=Application.HYBRID,
        date=timezone.localdate(),
        start="08:00",
        end="18:00",
        school_class=school_class,
    )
    app_student = mixer.blend(
        ApplicationStudent, application=app_hybrid, student=student
    )

    # 2. Login de Coordenador no Live Server
    page.goto(f"{live_server.url}/conta/login/")
    page.fill('input[name="username"]', "coord_playwright")
    page.fill('input[name="password"]', "senha123")
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    # 3. Navegação para Listagem de Híbridas
    page.goto(f"{live_server.url}/aplicacoes/?category=hibrid")
    expect(page.locator("#createSimpleApplication")).to_be_visible()

    # 4. Validar Ausência de Cartões OMR no Modal de Impressão
    # Dispara a abertura do modal de impressão do aplicativo híbrido
    page.evaluate(f"window.app.showPrintModal({{id: '{app_hybrid.id}', category: 5}})")
    modal = page.locator("#configurePrintModal")
    expect(modal).to_be_visible()

    # Validação dos campos que DEVEM estar ocultos para Híbrida:
    expect(modal.locator("#print-exam")).not_to_be_visible()
    expect(modal.locator("#print-discursives")).not_to_be_visible()
    expect(modal.locator("#show-official-picture")).not_to_be_visible()

    # Validação do botão de submissão
    btn_imprimir = modal.locator('button:has-text("Imprimir malote")')
    expect(btn_imprimir).to_be_visible()
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante os testes:**  
  *Aguardando execução do QA manual pelo time.*
- **Volume de idas e vindas com os desenvolvedores:**  
  *Aguardando execução do QA manual pelo time.*
- **Oportunidades de melhoria no processo de desenvolvimento/QA:**  
  *Aguardando execução do QA manual pelo time.*

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
- **Feedback sobre o mapeamento incremental:** A estrutura de arquivos de tela centralizados (`.ai_qa_acervo/docs/tests/usability/<template>.md`) provou-se altamente eficaz para desacoplar seletores DOM detalhados do roteiro de testes humano, mantendo a Seção 5 limpa e intuitiva para o testador manual.
- **Detecção de Dependência SPA:** Adicionar no Prompt V2 uma diretriz explícita para casos em que o backend entrega contratos de API (como `/api/v3/`) para SPAs em repositórios separados, orientando a inclusão de chamadas diretas de validação de payload/JSON caso o frontend ainda esteja em homologação separada.
