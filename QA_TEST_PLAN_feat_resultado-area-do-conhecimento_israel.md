## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-09-11 |
| **Branch Backend (lizeedu):** | `feat/resultado-questoes-excerpt-disciplina` |
| **Branch Frontend (lize-student):** | `feat/resultado-area-do-conhecimento` |
| **Natureza da Tarefa:** | `[Business Feature]` / `[UI/UX & Results]` |
| **Área da Feature:** | App do Aluno (Tela de Resultados, Desempenho por Área de Conhecimento, Revisão por Disciplina e Navegação em Cards) |
| **Nível de Risco:** | Médio (Altera os principais pontos de contato do estudante com o resultado pedagógico das avaliações) |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐ (4 estrelas - Contrato de API documentado em `backend_docs/api-application-student.md`, tipagem TypeScript estrita e cobertura de testes automatizados nos dois repositórios) |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend (`LizeEdu/lizeedu` — branch `feat/resultado-questoes-excerpt-disciplina`)
- **Enriquecimento do Payload de Resultado (`GET /api/v3/applications/{pk}/result/`):**
  - Cada item da lista `questions_data` passa a entregar os novos campos `excerpt`, `subject` e `knowledge_area`, permitindo ao frontend renderizar os cards de questão e cabeçalhos de revisão sem consultas adicionais.
  - A disciplina e área são resolvidas a partir do `select_related` já existente no queryset (`question.subject` e `question.subject.knowledge_area`), mantendo zero queries adicionais ao banco.
- **Enriquecimento do Detalhe da Questão (`GET /api/v3/applications/{pk}/question_detail_with_answer/?question_id={id}`):**
  - O serializer `ExamQuestionResultSerializer` passa a expor os campos `subject` (`{"id": "...", "name": "Biologia"}`) e `knowledge_area` no topo do cabeçalho da revisão.
- **Serviço de Extração e Limpeza de Enunciado (`build_question_excerpt`):**
  - Implementada função especializada em `fiscallizeon/questions/services/questions.py` que converte o HTML do enunciado em texto puro (máx. 160 caracteres com elipse `…`), removendo tags, resolvendo entidades HTML (`&nbsp;`, `&eacute;`), retirando delimitadores de LaTeX (`$`, `$$`, `\(`, `\)`, `\[`, `\]`) e colapsando múltiplos espaços em branco.
- **Tratamento Resiliente de Questões sem Disciplina:**
  - Caso uma questão avulsa não possua disciplina vinculada, a API retorna `null` para `subject` e `knowledge_area` sem interromper a montagem do resultado.
- **Cobertura de Testes Automatizados:**
  - Testes unitários e de integração adicionados em `fiscallizeon/app/students/tests/test_result_performance.py` cobrindo o `build_question_excerpt`, presença de `excerpt`/`subject`/`knowledge_area` no resultado e no detalhe, e casos com disciplina ausente.

### Frontend (`LizeEdu/lize-student` — branch `feat/resultado-area-do-conhecimento`)
- **Alternador de Visão: Disciplinas vs Área do Conhecimento (`disciplines-breakdown.tsx`):**
  - Novo seletor de abas (`Tabs` do design system — pílula compacta no mobile e abas em caixa no desktop) para alternar entre a tabela clássica de disciplinas e a visão consolidada por Área do Conhecimento.
  - O alternador só é exibido se a avaliação possuir **mais de uma área do conhecimento**. Provas de área única exibem diretamente o título fixo "Disciplinas".
- **Cálculo de Desempenho Ponderado da Área:**
  - As disciplinas são agrupadas por área somando questões, acertos, parciais, erros e pesos (`totalWeight`).
  - O percentual de desempenho da área é calculado como a média ponderada pelo peso (`totalWeight`), garantindo exatidão inclusive em simulados no modelo ENEM (onde o campo `score` é enviado zerado no payload).
- **Acesso Direto às Questões da Área ("Visualizar"):**
  - Na visão por área do conhecimento, cada linha da tabela exibe o botão `"**Visualizar**"` (com ícone `Eye`), que abre a gaveta de revisão (`QuestionReviewSheet`) com o escopo de navegação (`navScope`) restrito unicamente às questões daquela área.
- **Aba de Primeiro Nível "Questões para revisar" (`minhas-provas.$id.tsx` e `questions-to-review.tsx`):**
  - Alternador de nível superior entre as abas `"**Informações Gerais**"` e `"**Questões para revisar**"`.
- **Painel de Revisão Analítica por Disciplina (`questions-to-review.tsx`):**
  - Seção dedicada para cada matéria da prova com indicadores de desempenho, acertos, erros, barra de progresso com emoji 🚀 e nota/peso.
  - Componente de Grau de Domínio (`SubjectMastery`): seletor para visualizar o domínio do aluno em "Assuntos", "Habilidades" e "Competências" com barras segmentadas de 4 blocos.
  - Tabela "Questões que você pode revisar": lista apenas as questões em que o aluno cometeu erro ou acerto parcial (`reviewableQuestions`), com trecho do enunciado (`excerpt`), badge com percentual de acerto da turma e botão `"**Revisar**"` com escopo restrito à disciplina.
- **Reformulação da Listagem de Questões em Cards (`questions-overview.tsx`):**
  - A grade legada de números foi substituída por cards paginados (15 por página), exibindo número, badge de status (Acertou, Errou, Parcial, Aguardando correção), trecho do enunciado e percentual de acertos da turma.
  - Filtros rápidos por categoria (Todas, Objetivas, Discursivas, Somatório, Arquivo anexado) e seletor de ordenação (crescente/decrescente por número ou por percentual de acerto da turma).
- **Gaveta Lateral de Revisão de Questões (`question-review-sheet.tsx`):**
  - Substituição do antigo modal por um painel lateral (`Sheet`) contínuo, com cabeçalho fixo, navegação por setas (‹ ›) e atalhos de teclado (setas esquerda/direita), badge de status, subtítulo da matéria/área, re-renderização de fórmulas matemáticas (MathJax) e abas internas ("Questão", "Sua resposta", "Resposta comentada", "Assuntos abordados", "Competências" e "Habilidades").

---

## 2. Scope Boundaries (Diferenças de Escopo)

### Dentro do Escopo (IN SCOPE)
- Entrega dos campos `excerpt`, `subject` e `knowledge_area` pela API v3 no backend `lizeedu`.
- Exibição de `subject` e `knowledge_area` no cabeçalho do detalhe da questão no backend `lizeedu`.
- Exibição do alternador "Disciplinas" vs "Área do conhecimento" no bloco de disciplinas do app do aluno para provas com 2 ou mais áreas.
- Ocultação do alternador e fixação do título "Disciplinas" quando a prova tem apenas 1 área de conhecimento.
- Agregação correta de questões, acertos, parciais, erros, nota e cálculo ponderado de desempenho por área de conhecimento.
- Ação do botão "Visualizar" na tabela de Área do Conhecimento abrindo o painel lateral com navegação restrita às questões daquela área.
- Clique na linha de disciplina (aba Disciplinas) abrindo o modal detalhado de disciplina (`SubjectPerformanceModal`).
- Alternância entre as abas de primeiro nível "Informações Gerais" e "Questões para revisar".
- Renderização dos cards de desempenho por matéria, seletor de domínio (Assuntos/Habilidades/Competências) e tabela de questões a revisar.
- Filtragem estrita da tabela de revisão: somente questões com erro (`is_incorrect=True`) ou acerto parcial (`is_partial=True`) são listadas (questões aguardando correção ou 100% corretas não aparecem).
- Listagem geral em cards paginados de 15 em 15 com trecho do enunciado, filtros por tipo e ordenação por acerto da turma.
- Navegação fluida no painel lateral de revisão via setas de cabeçalho e teclas do teclado (`ArrowLeft` / `ArrowRight`).
- Validação responsiva no desktop e mobile.

### Fora do Escopo (OUT OF SCOPE)
- **Recálculo do algoritmo TRI ou reclassificação de acertos:** A branch apenas consome e apresenta os dados de pontuação e estatísticas calculados pelo backend.
- **Permitir alteração de respostas após encerramento da prova:** A tela de resultados é estritamente de leitura pedagógica e revisão.
- **Revisão de cadernos em andamento:** Provas que ainda não foram finalizadas ou cujo resultado não foi liberado não devem renderizar a tela de resultados.
- **Geração de arquivos PDF de gabarito para download:** Funcionalidade tratada em outros módulos do sistema.

---

## 3. Navegação e Camada Técnica

| Destino | Rótulo real no menu UI | URL / Rota | Repositório / Camada |
|---|---|---|---|
| **App do Aluno: Minhas Provas** | Minhas provas | `http://localhost:5173/painel/minhas-provas` | `lize-student` (SPA Aluno) |
| **App do Aluno: Resultado da Prova** | (Card da prova na listagem) ➔ Ver resultado [verificar] | `http://localhost:5173/painel/minhas-provas/<application_student_id>` | `lize-student` (SPA Aluno) |
| **API: Resultado Detalhado** | Payload `/result/` | `GET /api/v3/applications/<pk>/result/` | `lizeedu` (Backend DRF) |
| **API: Detalhe da Questão** | Payload `/question_detail_with_answer/` | `GET /api/v3/applications/<pk>/question_detail_with_answer/?question_id=<id>` | `lizeedu` (Backend DRF) |
| **Portal Coordenação: Aplicações** | Aplicações | `http://localhost:8000/aplicacoes/` | `lizeedu` (Django Web) |
| **Portal Coordenação: Ver Resultados** | Ver resultados [verificar] | `http://localhost:8000/aplicacoes/<uuid>/resultados/` | `lizeedu` (Django Web) |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Personas Ativas para Teste
1. **Aluno de Teste Multi-Área (`aluno.multi@lize.local`):** Aluno que realizou uma avaliação contendo questões de pelo menos 2 Áreas do Conhecimento distintas (ex.: *Ciências da Natureza* e *Ciências Humanas*), com acertos, erros e acertos parciais.
2. **Aluno de Teste Mono-Área (`aluno.mono@lize.local`):** Aluno que realizou avaliação contendo apenas 1 Área do Conhecimento (ex.: apenas *Matemática e suas Tecnologias*), usada para validar a supressão do alternador de abas.
3. **Coordenador da Unidade (`coord.teste@lize.local`):** Acessa o portal Django para conferência do gabarito e notas consolidadas.

### Comandos de Testes Automatizados Locais

#### Backend (`lizeedu`):
```bash
# Ativar venv e executar os testes do endpoint de resultado
source venv/bin/activate
pytest fiscallizeon/app/students/tests/test_result_performance.py -v --reuse-db
```

#### Frontend (`lize-student`):
```bash
# Executar a suite de testes dos componentes de resultado
cd /home/israel/Workspace/lize-student
npm test -- src/components/exam-result/ --run
```

### Setup de Dados para Testes Manuais via Django Shell

Execute no terminal do backend para criar uma avaliação multi-área com respostas e notas preparadas:

```python
# python manage.py shell
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.students.models import Student
from fiscallizeon.clients.models import Client
from fiscallizeon.subjects.models import KnowledgeArea, Subject
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question, Alternative
from fiscallizeon.applications.models import Application, ApplicationStudent, ApplicationStudentAnswer

# 1. Recuperar ou criar cliente e aluno de testes
client = Client.objects.filter(can_access_app=True).first()
if not client:
    client = mixer.blend(Client, name="Colégio Exemplo", can_access_app=True)

user, _ = User.objects.get_or_create(
    email="aluno.resultado@lize.local",
    defaults={"username": "aluno.resultado", "can_access_app": True, "must_change_password": False}
)
user.set_password("123456")
user.save()
student, _ = Student.objects.get_or_create(user=user, defaults={"client": client, "name": "Aluno Resultado Multi-Área"})

# 2. Áreas do Conhecimento e Disciplinas
area_natureza, _ = KnowledgeArea.objects.get_or_create(name="Ciências da Natureza e suas Tecnologias")
area_humanas, _ = KnowledgeArea.objects.get_or_create(name="Ciências Humanas e suas Tecnologias")

sub_bio, _ = Subject.objects.get_or_create(name="Biologia", defaults={"knowledge_area": area_natureza, "client": client})
sub_his, _ = Subject.objects.get_or_create(name="História", defaults={"knowledge_area": area_humanas, "client": client})

# 3. Caderno de Prova com 4 questões (2 de Biologia, 2 de História)
exam = mixer.blend(Exam, name="Simulado Integrado Multi-Áreas", is_abstract=True, client=client)

# Q1 (Biologia) - Acerto
q1 = mixer.blend(Question, subject=sub_bio, enunciation="<p>Em uma população de borboletas da espécie <i>Heliconius</i>, a seleção natural atua na coloração das asas.</p>", client=client)
alt1_correta = mixer.blend(Alternative, question=q1, is_correct=True, text="Seleção disruptiva")
alt1_errada = mixer.blend(Alternative, question=q1, is_correct=False, text="Deriva genética")
mixer.blend(ExamQuestion, exam=exam, question=q1, weight=2.5)

# Q2 (Biologia) - Erro (para aparecer em questões para revisar)
q2 = mixer.blend(Question, subject=sub_bio, enunciation="<p>Durante a fotossíntese, a fase clara ocorre nos tilacoides e depende de luz solar direta.</p>", client=client)
alt2_correta = mixer.blend(Alternative, question=q2, is_correct=True, text="Fotólise da água")
alt2_errada = mixer.blend(Alternative, question=q2, is_correct=False, text="Ciclo de Calvin")
mixer.blend(ExamQuestion, exam=exam, question=q2, weight=2.5)

# Q3 (História) - Acerto
q3 = mixer.blend(Question, subject=sub_his, enunciation="<p>A Declaração dos Direitos do Homem e do Cidadão sintetizou os ideais da Revolução Francesa.</p>", client=client)
alt3_correta = mixer.blend(Alternative, question=q3, is_correct=True, text="Liberdade e Igualdade")
mixer.blend(ExamQuestion, exam=exam, question=q3, weight=2.5)

# Q4 (História) - Erro (para aparecer em questões para revisar)
q4 = mixer.blend(Question, subject=sub_his, enunciation="<p>O período da Guerra Fria caracterizou-se pela bipolarização ideológica entre EUA e URSS.</p>", client=client)
alt4_correta = mixer.blend(Alternative, question=q4, is_correct=True, text="Doutrina Truman e Pacto de Varsóvia")
alt4_errada = mixer.blend(Alternative, question=q4, is_correct=False, text="Tratado de Versalhes")
mixer.blend(ExamQuestion, exam=exam, question=q4, weight=2.5)

# 4. Aplicação Finalizada com Respostas Registradas
from django.utils import timezone
app = mixer.blend(Application, exam=exam, release_result_at_end=True)
app_student = mixer.blend(
    ApplicationStudent,
    application=app,
    student=student,
    start_time=timezone.now() - timezone.timedelta(hours=2),
    end_time=timezone.now() - timezone.timedelta(hours=1),
)

# Respostas: Q1 Acerto, Q2 Erro, Q3 Acerto, Q4 Erro
mixer.blend(ApplicationStudentAnswer, application_student=app_student, question=q1, alternative=alt1_correta, is_correct=True, teacher_grade=2.5)
mixer.blend(ApplicationStudentAnswer, application_student=app_student, question=q2, alternative=alt2_errada, is_correct=False, teacher_grade=0.0)
mixer.blend(ApplicationStudentAnswer, application_student=app_student, question=q3, alternative=alt3_correta, is_correct=True, teacher_grade=2.5)
mixer.blend(ApplicationStudentAnswer, application_student=app_student, question=q4, alternative=alt4_errada, is_correct=False, teacher_grade=0.0)

print(f"Aplicação Student ID para teste: {app_student.id}")
print(f"URL de Acesso: http://localhost:5173/painel/minhas-provas/{app_student.id}")
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

> **Ambiente Backend**: `lizeedu` (branch `feat/resultado-questoes-excerpt-disciplina`) rodando via `./manage.py runserver` (porta 8000).  
> **Ambiente Frontend**: `lize-student` (branch `feat/resultado-area-do-conhecimento`) rodando via `npm run dev` ou `bun dev` (porta 5173).  
> **Persona Ativa Principal**: `enrico.a53143@aluno.decisaovirtual.com.br` (senha `123456` / Turma `F4MA`).  
> **Aplicação de Teste Ativa**: `b47ce1b3-4883-40b3-bf68-025ca3f2835e` (`Simulado Multi-Áreas (Natureza e Humanas) - QA`).

---

### 5.1 Visão Geral e Listagem de Questões em Cards (`QuestionsOverview`) [Automatizável ✅]
> **Persona**: Aluno logado na SPA do estudante.  
> **Objetivo**: Garantir que as questões da avaliação são exibidas na nova interface de cards paginados com metadados corretos.

#### Cenário 1 — Exibição dos Cards e Trechos de Enunciado
- [x] 1. Fazer login no app do aluno (`http://localhost:5173`) com o usuário de teste (`enrico.a53143@aluno.decisaovirtual.com.br` / senha `123456`).
- [x] 2. Na barra lateral, clicar em `"**Minhas provas**"` e acessar a tela de resultado da aplicação multi-área recém-concluída (`Simulado Multi-Áreas (Natureza e Humanas) - QA`) ou abrir diretamente `http://localhost:5173/painel/minhas-provas/b47ce1b3-4883-40b3-bf68-025ca3f2835e`.
- [x] 3. Rolar a página até a seção de listagem de questões.
- [x] 4. Confirmar que as antigas células circulares/quadradas numeradas foram substituídas por **cards retangulares estruturados**.
- [ ] 5. Verificar se cada card exibe:
  - [x] O número da questão em destaque (ex.: `"**Q1**"`, `"**Q2**"`).
  - [x] A pílula de status visual com texto e cor corretos: `"**Acertou**"` (verde esmeralda) nas questões 1, 3, 4 e 6; `"**Errou**"` (rosa suave com texto vinho) nas questões 2 e 5.
  - [ ] O trecho do enunciado em texto limpo (`excerpt`), sem tags HTML aparentes (`<p>`, `<i>`) e sem caracteres crus de LaTeX (`$x^2$`).
  - [ ] O percentual médio de acertos da turma formatado (ex.: `"**75% de acertos**"`).

#### Cenário 2 — Filtros por Categoria e Ordenação dos Cards
- [ ] 1. Na barra de filtros acima dos cards de questão, observar as opções de categoria: `"**Todas**"`, `"**Objetivas**"`, `"**Discursivas**"`, `"**Somatório**"` e `"**Arquivo anexado**"`.
- [ ] 2. Clicar no chip `"**Objetivas**"` e validar que a lista filtra apenas questões de múltipla escolha.
- [ ] 3. Clicar no campo seletor de ordenação `(dropdown no canto direito com texto padrão "Número (crescente)")`.
- [ ] 4. Selecionar a opção `"**Número (decrescente)**"` e validar que os cards invertem a ordem imediatamente (da Q6 para a Q1).
- [ ] 5. Selecionar `"**Acerto da turma (menor → maior)**"` e validar que as questões com menor índice de acerto aparecem no início da grade.
- [ ] 6. Em provas com mais de 15 questões, validar que a paginação exibe no máximo 15 cards por página e os botões de seta `(‹ e ›)` transitam de página sem recarregar a tela.

---

### 5.2 Alternador de Visão: Disciplinas vs Área do Conhecimento (`DisciplinesBreakdown`) [Automatizável ✅]
> **Persona**: Aluno na tela de resultado da prova.  
> **Objetivo**: Validar a alternância entre a visão analítica por matéria e a visão agregada por Área do Conhecimento.

#### Cenário 3 — Presença e Funcionamento das Abas de Área
- [ ] 1. Na tela de resultados, rolar até o bloco analítico de desempenho (abaixo dos cards de questão).
- [ ] 2. Observar a presença das abas de alternância de visão: `"**Disciplinas**"` e `"**Área do conhecimento**"`.
- [ ] 3. Estando na aba ativa `"**Disciplinas**"`, validar as linhas da tabela:
  - [ ] Linha `"**Biologia**"` com 3 questões, 2 acertos, 0 parciais, 1 erro, desempenho 66.67% e nota 3.33/5.0.
  - [ ] Linha `"**História**"` com 3 questões, 2 acertos, 0 parciais, 1 erro, desempenho 66.67% e nota 3.33/5.0.
  - [ ] Confirmar que o cursor do mouse vira ponteiro (`cursor: pointer`) ao passar sobre a linha e o hover destaca a linha suavemente.
- [ ] 4. Clicar sobre a linha `"**Biologia**"` e validar que o modal detalhado de desempenho da matéria (`SubjectPerformanceModal`) abre na tela com nota, histórico e tópicos. Fechar o modal no botão `(X)`.
- [ ] 5. Clicar na aba `"**Área do conhecimento**"`.
- [ ] 6. Validar a nova renderização da tabela:
  - [ ] A primeira coluna agora se chama `"**Área do conhecimento**"`.
  - [ ] Exibe a linha `"**Ciências da Natureza e suas Tecnologias**"` com 3 questões, 2 acertos, 1 erro e desempenho 66.67%.
  - [ ] Exibe a linha `"**Ciências Humanas e suas Tecnologias**"` com 3 questões, 2 acertos, 1 erro e desempenho 66.67%.
  - [ ] Na extrema direita de cada linha de área, validar a presença da coluna com o botão `"**Visualizar**"` `(botão branco com contorno cinza e ícone de olho)`.

---

### 5.3 Navegação Restrita por Área de Conhecimento ("Visualizar") [Manual 👁]
> **Persona**: Aluno navegando na visão por Área do Conhecimento.  
> **Objetivo**: Confirmar que o botão "Visualizar" abre o painel lateral com navegação restrita unicamente às questões daquela área.

#### Cenário 4 — Escopo de Navegação na Área do Conhecimento
- [ ] 1. Na tabela da aba `"**Área do conhecimento**"`, localizar a linha `"**Ciências da Natureza e suas Tecnologias**"`.
- [ ] 2. Clicar no botão `"**Visualizar**"` `(botão com ícone de olho)` correspondente a essa linha.
- [ ] 3. Confirmar que a gaveta lateral de revisão (`QuestionReviewSheet`) abre deslizando da direita para a esquerda.
- [ ] 4. Validar o cabeçalho da gaveta:
  - [ ] Deve exibir `"**Q1**"` (primeira questão de Biologia/Natureza).
  - [ ] O subtítulo deve exibir claramente `"**Biologia · Ciências da Natureza e suas Tecnologias**"`.
- [ ] 5. Clicar no botão de próxima questão `(botão circular com ícone de seta ChevronRight)` ou pressionar a tecla `ArrowRight` no teclado.
- [ ] 6. Confirmar que a gaveta transita para a `"**Q2**"` e depois para a `"**Q3**"` (todas de Biologia/Natureza).
- [ ] 7. Observar o botão de próxima questão na Q3:
  - [ ] Validar que o botão de próxima questão fica **desabilitado** (opacidade reduzida e não clicável).
  - [ ] Confirmar que **NÃO transita** para a Q4 de História (o escopo respeita estritamente as 3 questões da área selecionada!).
- [ ] 8. Fechar a gaveta lateral no botão de fechar `(X no canto superior direito)` ou clicando fora no backdrop escuro.

---

### 5.4 Aba de Primeiro Nível: "Questões para revisar" (`QuestionsToReview`) [Manual 👁]
> **Persona**: Aluno revisando seus pontos de melhoria na avaliação.  
> **Objetivo**: Validar a apresentação segmentada por disciplina, domínios de competência e listagem exclusiva de erros/parciais.

#### Cenário 5 — Painel de Disciplinas e Grau de Domínio
- [ ] 1. No topo da tela de resultados (abaixo do cabeçalho da prova), localizar as abas principais: `"**Informações Gerais**"` e `"**Questões para revisar**"`.
- [ ] 2. Clicar na aba `"**Questões para revisar**"`.
- [ ] 3. Validar a renderização da seção de `"**Biologia**"`:
  - [ ] Título `"**Biologia**"` com subtítulo `"**Ciências da Natureza e suas Tecnologias**"`.
  - [ ] Indicador numérico correspondente a 2 acertos em 3 questões (`"**67%**"` ou similar) acompanhado da legenda `"Desempenho na prova"`.
  - [ ] Lista com marcadores: `"3 questões"`, `"2 acertos"`, `"1 erros"`.
  - [ ] Card lateral de acertos com barra de progresso e o emoji `"🚀"`.
  - [ ] Resumo no rodapé: `"2/3 questões"`.
- [ ] 4. No bloco `"**Grau de domínio**"`, testar o seletor `(dropdown com opção inicial "Assuntos")`:
  - [ ] Alternar para `"**Habilidades**"` e validar que a lista recarrega exibindo as habilidades avaliadas e suas barras segmentadas de 4 blocos.
  - [ ] Alternar para `"**Competências**"` e verificar a exibição correspondente.

#### Cenário 6 — Tabela de Questões a Revisar e Botão "Revisar"
- [ ] 1. Rolar até a tabela `"**Questões que você pode revisar**"` dentro do bloco de Biologia.
- [ ] 2. Observar as questões listadas:
  - [ ] Validar que apenas a `"**Q2**"` (questão que o aluno errou) está presente.
  - [ ] Confirmar que a `"**Q1**"` (que o aluno acertou) **NÃO é exibida** na tabela de revisão.
- [ ] 3. Validar os elementos da linha da Q2:
  - [ ] Círculo cinza com o número `"**2**"`.
  - [ ] Trecho do enunciado: `"Durante a fotossíntese, a fase clara ocorre nos tilacoides e depende de luz solar direta..."`.
  - [ ] Selo colorido com o índice da turma: `"[X]% da turma acertou essa questão"`.
  - [ ] Botão `"**Revisar**"` `(botão branco com ícone de olho)`.
- [ ] 4. Clicar no botão `"**Revisar**"` da Q2 de Biologia.
- [ ] 5. Confirmar que a gaveta lateral abre exibindo a Q2.
- [ ] 6. Verificar que como só havia 1 questão errada de Biologia, os botões de avançar e voltar ficam desabilitados (escopo restrito à lista de revisão da matéria).
- [ ] 7. Fechar a gaveta lateral.

---

### 5.5 Navegação Completa no Painel Lateral (`QuestionReviewSheet`) [Manual 👁]
> **Persona**: Aluno revisando itens e gabaritos na gaveta lateral.  
> **Objetivo**: Assegurar a integridade das abas de conteúdo da questão e suporte a fórmulas/gráficos.

#### Cenário 7 — Abas Internas da Revisão e Resposta Comentada
- [ ] 1. Na listagem de cards da aba "Informações Gerais", clicar na `"**Q1**"` para abrir a gaveta lateral com todas as questões.
- [ ] 2. No cabeçalho da gaveta, validar a presença das abas internas: `"**Questão**"`, `"**Sua resposta**"`, `"**Resposta comentada**"`, `"**Assuntos abordados**"`, `"**Competências**"` e `"**Habilidades**"`.
- [ ] 3. Na aba `"**Questão**"`:
  - [ ] Validar a leitura do enunciado completo e a lista de alternativas com as letras (a, b, c...).
  - [ ] A alternativa correta deve estar contornada em verde esmeralda com fundo verde claro.
- [ ] 4. Clicar na aba `"**Sua resposta**"`:
  - [ ] Validar que exibe a alternativa que o aluno assinalou. Se correta, verde; se incorreta, vermelha.
- [ ] 5. Clicar na aba `"**Resposta comentada**"`:
  - [ ] Validar a exibição do gabarito oficial com o comentário explicativo do professor/autor da questão.
  - [ ] Caso haja feedback individual inserido pelo professor, verificar se aparece o card `"**Feedback do professor**"`.
- [ ] 6. Clicar nas abas `"**Assuntos abordados**"`, `"**Competências**"` e `"**Habilidades**"` e validar se os respectivos tópicos pedagógicos são listados com badges e barras de progresso.

---

### 5.6 Usabilidade Mobile e Interações Touch [Manual 👁]
> **Persona**: Aluno acessando o portal pelo smartphone.  
> **Objetivo**: Garantir que as abas, tabelas e gaveta lateral não quebram em telas pequenas (<400px).

#### Cenário 8 — Comportamento Responsivo e Toque no Mobile
- [ ] 1. No navegador, abrir as Ferramentas de Desenvolvedor (`F12`) e ativar a emulação móvel (ex.: iPhone 14, largura 390px).
- [ ] 2. Acessar a tela de resultado da avaliação.
- [ ] 3. Observar o alternador de nível superior:
  - [ ] Validar que as abas `"Informações Gerais"` e `"Questões para revisar"` assumem o formato de **pílula compacta** ajustada à largura total da tela (`TabsList size="sm"`), sem estourar a viewport horizontal.
- [ ] 4. Rolar até a tabela de Disciplinas / Área do Conhecimento:
  - [ ] Validar que o alternador "Disciplinas" / "Área do conhecimento" também renderiza em pílula compacta.
  - [ ] Verificar se a tabela possui rolagem horizontal suave nos dados numéricos sem quebrar a estrutura da página.
- [ ] 5. Tocar no botão `"**Visualizar**"` da área de conhecimento:
  - [ ] Validar que a gaveta lateral abre ocupando 100% da largura da tela mobile.
  - [ ] Confirmar que as 6 abas internas da revisão quebram harmoniosamente em 2 linhas em vez de esconder abas ou gerar barra de rolagem horizontal defeituosa.
- [ ] 6. Deslizar verticalmente e validar que o botão de fechar `(X)` e a navegação por toques funcionam perfeitamente sem estados de hover presos.

---

### 5.7 Casos de Borda e Resiliência [Manual 👁]
> **Persona**: Alunos em cenários atípicos (prova mono-área e aluno que gabaritou).  
> **Objetivo**: Prevenir falhas visuais ou exceções em casos extremos.

#### Cenário 9 — Prova com Apenas 1 Área do Conhecimento (Mono-Área)
- [ ] 1. No backend, criar ou acessar uma avaliação composta unicamente por questões de Matemática (Área: *Matemática e suas Tecnologias*).
- [ ] 2. Abrir o resultado dessa prova no app do aluno.
- [ ] 3. Rolar até a tabela de desempenho das matérias.
- [ ] 4. Validar que o alternador de abas ("Disciplinas" / "Área do conhecimento") **NÃO é exibido**.
- [ ] 5. Confirmar que a tela renderiza diretamente o título estático `"**Disciplinas**"`, evitando redundância desnecessária.

#### Cenário 10 — Aluno que Gabaritou a Disciplina (Zero Erros)
- [ ] 1. Acessar uma prova onde o estudante obteve 100% de acertos em uma matéria específica.
- [ ] 2. Entrar na aba `"**Questões para revisar**"` e rolar até a matéria gabaritada.
- [ ] 3. Validar a exibição do empty state elegante com borda pontilhada:
  - [ ] `"Nada a revisar aqui — você não errou nenhuma questão desta disciplina."`
- [ ] 4. Confirmar que nenhuma linha quebrada ou tabela vazia sem cabeçalho é desenhada.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **Alinhamento dos Cards de Questão:** Validar que todos os cards de questão na listagem mantêm altura uniforme, sem deformações quando o trecho do enunciado (`excerpt`) tiver tamanho variado.
- [ ] **Tipografia e Cores de Status:** Assegurar que as cores dos badges de tom (Acertou, Errou, Parcial, Aguardando correção) seguem a paleta exata do Tailwind do design system (verde `emerald`, vinho `rose`, amarelo `amber`, cinza `slate`).
- [ ] **Quebra das Abas na Gaveta Lateral:** Confirmar que as abas do cabeçalho da gaveta lateral (`QuestionReviewSheet`) não geram overflow horizontal com barra de rolagem sob os títulos.
- [ ] **Captura de Evidências Obrigatórias:** Anexar capturas de tela demonstrando:
  1. Tela de Informações Gerais com os novos cards paginados de questões.
  2. Alternador de abas "Disciplinas" vs "Área do conhecimento" no desktop e mobile.
  3. Gaveta lateral aberta com subtítulo da área e setas de navegação.
  4. Aba "Questões para revisar" com barra de domínio e tabela de questões erradas.

---

## 7. Bugs and Observations (Problemas Encontrados)

*(Espaço reservado para o QA registrar falhas durante a execução dos testes)*

> [!WARNING]
> **[Exemplo / Template de Bug]**
> - **Título:** Falha na navegação restrita de questões por área.
> - **Contexto / Causa Raiz:** O array `navScope` no componente `minhas-provas.$id.tsx` não filtrou as questões pelo campo `knowledgeArea`.
> - **Comportamento Esperado:** *(conforme design system e PR #19)* A navegação deve conter exclusivamente questões da área selecionada.
> - **Workaround:** Atualizar a página e utilizar a navegação geral de cards.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **[Filtragem de Áreas sem Questões no Caderno]:** Em cadernos onde uma disciplina estiver associada a uma área diferente da questão avulsa, documentar a padronização no cadastro pedagógico para que a árvore curricular seja 100% coerente entre o cadastro da questão e o caderno da prova.

> [!NOTE]
> **[Paginação Assíncrona no Backend]:** Para provas com grande volume de questões (>90 itens, como ENEM), planejar paginação server-side dos dados de questões em futuras releases para reduzir o peso inicial do payload `/result/`.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o nome do componente/tela (`minhas-provas.$id.tsx`), e não a View.
🔗 **[Ver Mapeamento de Tela (App Aluno - Resultado da Prova e Revisão)](docs/tests/usability/minhas_provas_id.md)**

### Identificadores Estáveis e Seletores do Frontend (`lize-student`):
- Alternador de Áreas: `button[role="tab"]:has-text("Área do conhecimento")`
- Botão Visualizar Área: `button:has-text("Visualizar")`
- Aba Superior Revisão: `button[role="tab"]:has-text("Questões para revisar")`
- Cards de Questão: `div[role="button"]:has(span:has-text("Q"))`
- Gaveta Lateral: `div[role="dialog"][data-state="open"]`
- Setas de Navegação no Sheet: `button[aria-label="Questão anterior"]` e `button[aria-label="Próxima questão"]`

### Snippet de Automação (Backend Setup + Playwright):
```python
import pytest
from playwright.sync_api import Page, expect
from mixer.backend.django import mixer
from fiscallizeon.clients.models import Client
from fiscallizeon.accounts.models import User
from fiscallizeon.students.models import Student
from fiscallizeon.subjects.models import KnowledgeArea, Subject
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Question, Alternative
from fiscallizeon.applications.models import Application, ApplicationStudent, ApplicationStudentAnswer

def test_student_result_area_knowledge_navigation(page: Page, live_server):
    # 1. Setup determinístico de dados via Mixer
    client = mixer.blend(Client, can_access_app=True)
    user = mixer.blend(User, can_access_app=True, must_change_password=False)
    user.set_password("123456")
    user.save()
    student = mixer.blend(Student, user=user, client=client)

    area_bio = mixer.blend(KnowledgeArea, name="Ciências da Natureza")
    area_mat = mixer.blend(KnowledgeArea, name="Matemática")
    sub_bio = mixer.blend(Subject, name="Biologia", knowledge_area=area_bio, client=client)
    sub_mat = mixer.blend(Subject, name="Matemática", knowledge_area=area_mat, client=client)

    exam = mixer.blend(Exam, name="Simulado Automatizado", is_abstract=True, client=client)
    q1 = mixer.blend(Question, subject=sub_bio, enunciation="<p>Citologia</p>", client=client)
    q2 = mixer.blend(Question, subject=sub_mat, enunciation="<p>Geometria</p>", client=client)
    mixer.blend(ExamQuestion, exam=exam, question=q1, weight=1.0)
    mixer.blend(ExamQuestion, exam=exam, question=q2, weight=1.0)

    app = mixer.blend(Application, exam=exam, release_result_at_end=True)
    app_student = mixer.blend(ApplicationStudent, application=app, student=student)

    # 2. Navegação no frontend
    page.goto(f"http://localhost:5173/painel/minhas-provas/{app_student.id}")
    
    # Valida presença das abas Disciplinas e Área do conhecimento
    expect(page.locator('button[role="tab"]:has-text("Área do conhecimento")')).to_be_visible()
    page.click('button[role="tab"]:has-text("Área do conhecimento")')

    # Clica no botão Visualizar da área de Biologia
    page.click('tr:has-text("Ciências da Natureza") button:has-text("Visualizar")')

    # Valida abertura da gaveta lateral
    sheet = page.locator('div[role="dialog"][data-state="open"]')
    expect(sheet).to_be_visible()
    expect(sheet.locator('text=Ciências da Natureza')).to_be_visible()
```

---

## 9. QA Retrospective (Retrospectiva de QA)
- **Coordenação Multi-Repositório:** A dependência direta dos novos campos (`excerpt`, `subject`, `knowledge_area`) no backend `lizeedu` foi antecipada com elegância pelo frontend através de renderização condicional graciosa (`canViewQuestionsByArea`). O teste unificado garante que a feature opere com riqueza máxima de detalhes quando as duas branches forem implantadas simultaneamente.
- **Eficiência de Navegação:** A substituição da grade numérica estática por cards paginados e a criação da gaveta lateral reduzem expressivamente a fricção do estudante, que antes precisava abrir e fechar modais individuais para ler o comentário de cada questão.

---

## 10. Sugestões de Melhorias para o Processo de QA
<!-- Anotações de melhorias no prompt ou no acervo coletadas durante o teste -->
- Avaliar a inclusão de um comando de seed automático para gerar respostas aleatórias de alunos em aplicações de teste, acelerando a preparação de dados para QA de telas de resultado.
