## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-13 |
| **Branch:** | `fix/ensalamento-tipos-diferentes-prova-86ak8wuvc` |
| **ClickUp:** | [Ensalamento misto com cartão por caderno (86ak8wuvc)](https://app.clickup.com/t/86ak8wuvc) |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Ensalamento / Malote de Provas / Impressão OMR / Geração de Malote ZIP |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (completa: proposal, design, spec, tasks e referências em `openspec/changes/ensalamento-cadernos-mistos-86ak8wuvc/`) |

---

## 1. Summary of Changes (Resumo das Alterações)

- **Backend & Formulário de Ensalamento (`fiscallizeon/distribution/forms.py`):**
  - Remoção da `ValidationError` em `RoomDistributionForm.clean()` que impedia cadastrar ou editar ensalamentos contendo simultaneamente cadernos com questões de somatório (`has_sum_questions`) e cadernos sem somatório.
  - Manutenção estrita da regra que proíbe misturar cadernos do formato PAS com outros formatos de prova.
- **Resolução de Cartão por Caderno (`fiscallizeon/distribution/utils.py`):**
  - Criação da função helper centralizada `resolve_exam_sheet_model(requested_sheet_model, exam)`:
    - Caderno PAS (`Exam.PAS`) ➔ devolve invariavelmente `'pas'`.
    - Caderno com somatório (`exam.has_sum_questions`) ➔ resolve deterministicamente via `resolve_sheet_model('sum', exam)` para `'sum'` (até 15 questões) ou `'sum_only'` (mais de 15 questões).
    - Caderno só de objetivas ➔ devolve o `requested_sheet_model` selecionado pelo usuário no modal (`'fiscallize'`, `'enem'` ou `'large_bubbles'`).
- **Geração de Malote & Mockups (`fiscallizeon/distribution/tasks/export_exams_bag.py`):**
  - Em `print_mockups`, o modelo é resolvido por exame via `resolve_exam_sheet_model(sheet_model, application.exam)`.
  - No loop de aplicações e alunos em `export_exams_bag`, a resolução é feita por caderno e aluno em variáveis de escopo local (`application_sheet_model` e `current_sheet_model`), eliminando o bug de vazamento onde um caderno PAS sobrescrevia a variável global da task e contaminava os cadernos subsequentes.
- **Empacotamento de Arquivos no ZIP (`fiscallizeon/distribution/tasks/group_files.py`):**
  - Em `collect_student_paths`, aplicação do helper `resolve_exam_sheet_model` para cada aluno/caderno.
  - Caderno `sum_only` com questões objetivas recebe a folha Lize adicional (`_lize.pdf`) exclusivamente para seus alunos; cadernos de objetivas puras do mesmo ensalamento recebem unicamente o modelo escolhido no modal, sem anexos indevidos.
- **Interface Web de Cadastro (`distribution_create_update.html`):**
  - Remoção da trava em Vue.js na função `canSelectApplicationWith` que exibia alerta SweetAlert (*"Você não pode ensalar cadernos com questões de somatório e outros modelos de uma única vez."*).
  - Manutenção dos bloqueios de horário divergente e de cadernos PAS misturados.
- **Interface Web do Modal de Impressão (`distribution_list.html`):**
  - Criação da propriedade computada `distributionHasMixedSum` (`exams.some(hasSum) && exams.some(!hasSum)`).
  - Em ensalamento misto:
    - O modal exibe apenas os seletores de cartão para cadernos de objetivas: **Folha de respostas Lize** (`fiscallize`), **Bolhas ampliadas** (`large_bubbles`) e **Folha de respostas ENEM** (`enem`).
    - Modelos de Somatório, PAS, Híbrido, Reduzido e EFAI ficam estritamente ocultos.
    - Exibição de banner informativo azul (`alert alert-info`): *"Cadernos com somatório saem no cartão de somatório automaticamente (até 15 questões: uma folha; mais de 15: somatório expandido). A escolha acima vale só para cadernos de objetivas."*
    - Pré-seleção padrão definida como `fiscallize`.
- **Testes Automatizados:**
  - `fiscallizeon/distribution/tests/test_resolve_exam_sheet_model.py`: Testes unitários cobrindo PAS, somatório ≤15 (`sum`), somatório >15 (`sum_only`) e modelos de objetivas.
  - `fiscallizeon/distribution/tests/test_room_distribution_form.py`: Testes cobrindo validação de ensalamento misto, rejeição de PAS misturado e ensalamentos homogêneos.
  - `fiscallizeon/distribution/tests/test_export_exams_bag.py` e `test_group_files.py`: Testes cobrindo resolução por caderno no malote misto e empacotamento ZIP.

---

## 2. Scope Boundaries (Diferenças de Escopo)

- IN SCOPE: Permitir cadastrar e editar ensalamentos que agrupem cadernos com somatório e cadernos só de objetivas para as mesmas salas e no mesmo horário.
- IN SCOPE: Seleção no modal de malote de ensalamento restrita a Folha Lize, ENEM e bolhas ampliadas quando o ensalamento for misto, com aviso explícito de que os cadernos com somatório saem no cartão próprio automaticamente.
- IN SCOPE: Resolução do cartão-resposta no backend no momento da geração do malote por caderno/aluno, gerando os PDFs corretos na mesma pasta de sala no arquivo ZIP.
- IN SCOPE: Manter bloqueio inegociável de mistura de cadernos do formato PAS com quaisquer outros formatos (tanto no formulário quanto na interface).
- IN SCOPE: Manter inalterado o comportamento de ensalamentos homogêneos (100% somatório, 100% objetivas e 100% PAS).
- OUT OF SCOPE: Permitir ensalar cadernos PAS junto com outros formatos de prova.
- OUT OF SCOPE: Alteração no malote em massa da listagem geral de aplicações (`application_list_new.html`), que segue com sua regra própria.
- OUT OF SCOPE: Disponibilização de modelos Híbrido, Reduzido ou EFAI no ensalamento misto (estes seguem exclusivos para ensalamentos sem somatório).
- OUT OF SCOPE: Redesign visual das páginas de ensalamento ou migração para `redesign/base_component.html`.
- OUT OF SCOPE: Modificações nos templates OMR, no leitor de gabaritos ou nas rotas de API do aplicativo do aluno (`/api/v3/`).

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---|---|---|---|
| Lista de Ensalamentos | Menu lateral ➔ **Aplicações** ➔ **Ensalamento** | `/ensalamento/` | `distribution:distribution_list` (`RoomDistributionList`) |
| Cadastrar Ensalamento | Tela de Ensalamentos ➔ botão **"Cadastrar ensalamento"** (superior direito) | `/ensalamento/criar/` | `distribution:distribution_create` (`RoomDistributionCreateView`) |
| Editar Ensalamento | Tabela de ensalamentos ➔ botão **"Opções"** ➔ item **"Editar"** | `/ensalamento/<uuid:pk>/atualizar/` | `distribution:distribution_update` (`RoomDistributionUpdateView`) |
| Modal de Impressão do Malote | Tabela de ensalamentos ➔ botão **"Opções"** ➔ item **"Imprimir malote"** (ou **"Imprimir malote novamente"**) | Aciona modal `#configurePrintModal` em `/ensalamento/` | Dispara POST para `distribution:export_exams_bag` |
| Download do Arquivo Malote (ZIP) | Tabela de ensalamentos ➔ botão/pill **"Baixar malote"** | Link direto para o arquivo ZIP gerado em S3/Spaces | `exams_bag` URL do `RoomDistribution` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Persona Executora:
- **Coordenação Escolar:** Usuário com perfil de coordenação vinculado a `SchoolCoordination` e cliente com `client.has_distribution = True`, `client.client_has_sum_questions = True` e `client.has_exam_elaboration = True`.

### Execução de Testes Automatizados Locais:

```bash
# Ativação do ambiente e execução dos testes da feature:
source venv/bin/activate && pytest fiscallizeon/distribution/tests/test_resolve_exam_sheet_model.py fiscallizeon/distribution/tests/test_room_distribution_form.py fiscallizeon/distribution/tests/test_export_exams_bag.py fiscallizeon/distribution/tests/test_group_files.py --reuse-db -q

# Verificação de lint e formatação:
source venv/bin/activate && ruff check fiscallizeon/distribution/
```

### Como Funciona a Regra de Ensalamento no Lize (Pré-requisitos Mandatórios):
Para que as aplicações apareçam disponíveis e possam ser selecionadas juntas na tela de ensalamento (`/ensalamento/criar/`), elas **precisam cumprir 4 regras fundamentais**:
1. **Mesma Data de Aplicação:** O campo `"Data do Ensalamento"` faz um filtro automático via API (`/aplicacoes/api/list/?date=AAAA-MM-DD`). Apenas aplicações cadastradas para aquela data específica aparecem listadas.
2. **Mesmo Horário de Início e Término:** O Lize não permite ensalar provas em horários distintos. Todas as aplicações a serem reunidas na mesma sala devem ter rigorosamente o mesmo horário (ex: `14:00 às 18:00`). Se os horários divergirem, o sistema impede a seleção conjunta com alerta de horário!
3. **Mesma Coordenação e Salas com Vagas:** As aplicações precisam pertencer à mesma coordenação de ensino para que as salas dessa coordenação apareçam. A soma da capacidade das salas selecionadas deve ser maior ou igual ao número total de alunos somados de todas as aplicações.
4. **Cadernos de Prova Diversificados (Escopo do Teste):** Para validar a feature ponta a ponta, é necessário dispor de 5 aplicações criadas com cadernos de formatos distintos:
   - **Caderno 1 (Somatório ≤15Q):** Prova com até 15 questões de somatório (ex: 10 questões).
   - **Caderno 2 (Somatório Amplo >15Q + Objetivas):** Prova com 18 questões de somatório e 5 questões de múltipla escolha.
   - **Caderno 3 (Apenas Objetivas):** Prova com 10 questões de múltipla escolha puras.
   - **Caderno 4 (Redação / Discursiva):** Prova com proposta de redação / questão textual.
   - **Caderno 5 (Formato PAS):** Prova no formato PAS (usada no teste negativo para provar que PAS misturado continua bloqueado).

---

### Dados Prontos no seu Ambiente Local (Gerados Automaticamente):
Para que você não precise criar 5 cadernos e 5 aplicações manualmente, os dados de teste já foram gerados e sincronizados no seu banco local:

- **📅 Data configurada:** `2026-10-20`
- **⏰ Horário sincronizado:** `14:00` às `18:00`
- **🏢 Coordenação:** `Ensino Médio` (Cliente ativo: `Rede Decisão`)
- **📚 Aplicações disponíveis para seleção imediata na tela:**
  1. `[QA] Caderno 1 - Somatório 10Q` *(Somatório puro ≤ 15 questões)*
  2. `[QA] Caderno 2 - Somatório Amplo 18Q + 5 Obj` *(Somatório amplo + objetivas)*
  3. `[QA] Caderno 3 - Objetivas 10Q` *(Apenas objetivas)*
  4. `[QA] Caderno 4 - Redação e Discursiva` *(Discursiva / Redação)*
  5. `[QA] Caderno 5 - Formato PAS (Bloqueio)` *(Formato PAS para validação da trava de segurança)*

> [!TIP]
> **Como regerar os dados para outra data (se necessário):**
> Caso deseje criar novas aplicações de teste para qualquer outra data futura, basta executar no terminal:
> ```bash
> source venv/bin/activate && python .ai_qa_acervo/scripts/generators/create_mixed_distribution_data.py --date AAAA-MM-DD
> ```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Cadastro e Edição de Ensalamento Misto [Automatizável ✅]

#### Cenário 1 — Seleção simultânea de cadernos com somatório e cadernos de objetivas

**Ação humana:**
- [x] Acessar o menu lateral `"**Aplicações**"` e clicar no submenu `"**Ensalamento**"`.
- [x] Clicar no botão azul `"**Cadastrar ensalamento**"` (localizado no canto superior direito da página).
- [x] No campo `"**Data do Ensalamento**"`, preencher ou selecionar a data **`2026-10-20`** (ou a data informada pelo gerador de dados).
- [x] No campo `"**Tipo de Ensalamento**"`, selecionar a opção `"**Por nome e série**"`.
- [x] Observar que a seção `"**Aplicações Envolvidas**"` será carregada automaticamente via API exibindo as aplicações com horário `"De 14:00 até 18:00"`.
- [x] **Passo 1 (Somatório):** Marcar o checkbox da aplicação `"**[QA] Caderno 1 - Somatório 10Q**"`.
- [x] **Passo 2 (Objetivas - Ponto Chave da Feature):** Em seguida, marcar o checkbox da aplicação `"**[QA] Caderno 3 - Objetivas 10Q**"`.
- [x] **Validação Crítica:** Verificar que o sistema aceita a seleção de ambas simultaneamente **SEM exibir nenhum alerta de erro** (no passado, abria o SweetAlert bloqueando *"Você não pode ensalar cadernos com questões de somatório e outros modelos de uma única vez"*).
- [x] **Passo 3 (Adicionar Somatório Amplo e Discursiva):** Marcar também as aplicações `"**[QA] Caderno 2 - Somatório Amplo 18Q + 5 Obj**"` e `"**[QA] Caderno 4 - Redação e Discursiva**"`.
- [x] Verificar que agora existem 4 aplicações selecionadas juntas no painel de resumo lateral.
- [x] Na seção inferior `"**Salas Envolvidas**"`, localizar a coordenação e marcar o checkbox de uma ou mais salas (ex: `"**Sala 01**"` ou outra sala com vagas disponíveis).![alt text](../evidencias/image-16.png)
- [x] No painel lateral direito de resumo (sticky), confirmar que o total de alunos é atendido pela capacidade das salas e que o botão azul `"**Salvar Ensalamento**"` está habilitado.
- [x] Clicar em `"**Salvar Ensalamento**"` e confirmar que o ensalamento é salvo com sucesso e você é redirecionado para a listagem (`/ensalamento/`).![alt text](../evidencias/image-17.png)

**Referência técnica (para automação):**
- URL: `/ensalamento/criar/`
- Seletor: `input#id_date`, `input[type="checkbox"][name="applications"]`, `input[type="checkbox"][name="rooms"]`, `button[type="submit"]:has-text("Salvar Ensalamento")`
- Estado esperado no DOM: ausência de modal SweetAlert impeditivo; redirecionamento HTTP 302 para `/ensalamento/` e persistência do objeto `RoomDistribution` no banco com 4 aplicações vinculadas.
- Fixture: `python .ai_qa_acervo/scripts/generators/create_mixed_distribution_data.py`.

#### Cenário 2 — Bloqueio inegociável de mistura com caderno formato PAS (Teste Negativo)

**Ação humana:**
- [x] Acessar novamente a tela de cadastro de ensalamento (`/ensalamento/criar/`).
- [x] No campo `"**Data do Ensalamento**"`, preencher a data **`2026-10-20`**.
- [x] Na seção `"**Aplicações Envolvidas**"`, marcar o checkbox da aplicação `"**[QA] Caderno 5 - Formato PAS (Bloqueio)**"`.
- [x] Em seguida, tentar marcar qualquer uma das outras aplicações que NÃO sejam PAS (ex: `"**[QA] Caderno 1 - Somatório 10Q**"` ou `"**[QA] Caderno 3 - Objetivas 10Q**"`). ![alt text](../evidencias/image-1.png)
- [x] **Validação Crítica:** Confirmar que a interface visual bloqueia imediatamente a seleção mista e dispara o alerta SweetAlert com o texto exato:
  `"**Não é permitido ensalar cadernos do tipo PAS com outros modelos.**"`.![alt text](../evidencias/image-2.png)
- [x] Clicar no botão `"**Ok, entendi**"` do pop-up e verificar que o checkbox da segunda aplicação permanece desmarcado, garantindo que o isolamento do formato PAS foi preservado.

**Referência técnica (para automação):**
- URL: `/ensalamento/criar/`
- Seletor: `.swal2-popup.swal2-show .swal2-html-container`
- Estado esperado no DOM: elemento SweetAlert visível com texto exato `"Não é permitido ensalar cadernos do tipo PAS com outros modelos."`; checkbox desmarcado no array `selectedApplications`.
- Fixture: `Exam.objects.create(name="...", exam_format=Exam.PAS)`.

---

### 5.2 Modal de Impressão do Malote de Ensalamento Misto [Automatizável ✅]

#### Cenário 3 — Abertura do modal e exibição restrita das opções de objetivas

**Ação humana:**
- [x] Na listagem de ensalamentos (`/ensalamento/`), localizar a linha do ensalamento misto cadastrado no Cenário 1.
- [x] Na coluna de ações à direita, clicar no botão branco `"**Opções**"` (com ícone chevron-down).
- [x] No menu dropdown aberto, clicar na opção `"**Imprimir malote**"` (com ícone de documento).
- [x] Confirmar a abertura do modal intitulado `"**Configure a impressão do malote nesta exportação**"`.
- [x] Verificar visualmente as opções de cartão-resposta exibidas no grupo de botões:
  - Deve estar visível `"**Folha de respostas Lize**"` (selecionada por padrão com classe `active`).
  - Deve estar visível `"**Bolhas ampliadas**"`.
  - Deve estar visível `"**Folha de respostas ENEM**"`.![alt text](../evidencias/image-3.png)
- [x] Verificar que as opções `"**Modelo somatório**"`, `"**Modelo PAS**"`, `"**Modelo Híbrido**"`, `"**Modelo Reduzido**"` e `"**EFAI**"` NÃO aparecem no modal.![alt text](../evidencias/image-4.png)
- [x] Verificar a presença do alerta azul de informação com o texto exato:
  `"**Cadernos com somatório saem no cartão de somatório automaticamente (até 15 questões: uma folha; mais de 15: somatório expandido). A escolha acima vale só para cadernos de objetivas.**"`.![alt text](../evidencias/image-5.png)

**Referência técnica (para automação):**
- URL: `/ensalamento/`
- Seletor: `button:has-text("Opções")`, `a:has-text("Imprimir malote")`, `#configurePrintModal`
- Estado esperado no DOM:
  - `#configurePrintModal .alert-info` visível com texto exato.
  - `input[name="enem"][value="fiscallize"]` marcado (`active`).
  - `input[value="sum"]`, `input[value="pas"]`, `input[value="hybrid"]`, `input[value="reduced"]`, `input[value="subjects"]` inexistentes no DOM do modal misto.
- Fixture: `RoomDistribution` vinculado a aplicações com e sem somatório.

#### Cenário 4 — Configuração e envio da solicitação de impressão do malote

**Ação humana:**
- [x] No modal de impressão aberto, manter selecionada a opção `"**Folha de respostas Lize**"` (ou alternar para `"**Folha de respostas ENEM**"`).
- [x] Marcar o checkbox `"**Incluir folhas de respostas discursivas**"`.
- [x] Marcar o checkbox `"**Incluir cadernos de prova**"`.
- [x] Clicar no botão azul `"**Imprimir malote**"` no rodapé do modal.
- [x] Verificar que o modal se fecha e o status da linha na tabela passa para indicador de processamento/geração do malote.

**Referência técnica (para automação):**
- URL: `POST /ensalamento/api/exportar/malote/<distribution_id>/`
- Seletor: `#configurePrintModal button:has-text("Imprimir malote")`
- Estado esperado no DOM: modal fechado (`#configurePrintModal` com display none); payload enviado com `sheet_model: "fiscallize"`, `include_discursives: true`, `include_exams: true`.
- Fixture: `RoomDistribution` com status atualizado para 2 (em processamento).

---

### 5.3 Validação dos Arquivos e Cartões no Malote ZIP Gerado [Automatizável ✅]

#### Cenário 5 — Conferência detalhada dos cartões gerados por caderno na mesma sala

**Ação humana:**
- [x] Aguardar a conclusão do processamento do malote (o worker Celery processa a fila `omr-export`).
- [x] Recarregar a página `/ensalamento/` e verificar que surgiu o botão/pill `"**Baixar malote**"` na linha do ensalamento.
- [x] Clicar em `"**Baixar malote**"` e descompactar o arquivo `.zip` baixado.
- [x] Acessar a pasta correspondente à sala (ex: `Sala QA 101/`).
- [x] Verificar a presença e o formato dos cartões de resposta de cada aluno:
  - **Caderno 1 (Somatório ≤15Q):** O arquivo de cartão do aluno deve ser no modelo `"**sum**"` em folha única (cartão de somatório padrão de até 15 questões).
  - **Caderno 2 (Somatório >15Q + Objetivas):** O arquivo do aluno deve conter o cartão de somatório expandido (`"**sum_only**"`) E adicionalmente a folha de respostas Lize complementar (`_lize.pdf`) com as 5 questões objetivas.
  - **Caderno 3 (Só Objetivas):** O arquivo do aluno deve conter estritamente o cartão escolhido no modal (`"**fiscallize**"` ou `"**enem**"`), SEM folha de somatório nem anexos indevidos.
  - **Caderno 4 (Discursivas/Redação):** O arquivo do aluno deve conter a folha de redação/discursiva gerada corretamente.
- [x] Verificar que a lista de presença (`lista_presenca.pdf`) contém todos os 4 alunos listados na mesma sala.

**Referência técnica (para automação):**
- URL: arquivo ZIP extraído localmente
- Caminho dos arquivos: `Sala QA 101/gabaritos/<student_id>_*.pdf`
- Estado esperado:
  - Aluno 1: PDF com layout OMR `sum` (1 página).
  - Aluno 2: PDF com layout OMR `sum_only` + anexo `*_lize.pdf`.
  - Aluno 3: PDF com layout OMR `fiscallize` (ou `enem`).
  - Aluno 4: PDF com folha de redação/discursiva.
- Fixture: tarefas `export_exams_bag` e `group_files`.

---

### 5.4 Testes de Regressão em Ensalamentos Homogêneos [Automatizável ✅]

#### Cenário 6 — Ensalamento 100% Somatório (Regressão)

**Ação humana:**
- [ ] Cadastrar um novo ensalamento contendo apenas aplicações com cadernos de somatório.
- [ ] Na listagem `/ensalamento/`, abrir o modal `"**Imprimir malote**"` para este ensalamento.
- [ ] Verificar que o modal exibe unicamente a opção `"**Modelo somatório**"` (comportamento clássico).
- [ ] Verificar que o alerta azul de ensalamento misto NÃO é exibido.
- [ ] Gerar o malote e confirmar que todos os alunos recebem o cartão de somatório correspondente à quantidade de questões.

**Referência técnica (para automação):**
- URL: `/ensalamento/`
- Seletor: `#configurePrintModal input[value="sum"]`
- Estado esperado: `distributionAllSum == true`, rádio `sum` visível e marcado; alerta informativo misto oculto.
- Fixture: `RoomDistribution` contendo apenas aplicações com `has_sum_questions=True`.

#### Cenário 7 — Ensalamento 100% Objetivas (Regressão)

**Ação humana:**
- [ ] Cadastrar um novo ensalamento contendo apenas aplicações com cadernos só de objetivas.
- [ ] Na listagem `/ensalamento/`, abrir o modal `"**Imprimir malote**"` para este ensalamento.
- [ ] Verificar que o modal exibe as opções normais: `"**Folha de respostas Lize**"`, `"**Bolhas ampliadas**"`, `"**Folha de respostas ENEM**"` e os modelos extras do cliente (ex: `"**Modelo Híbrido**"`, `"**Modelo Reduzido**"`, `"**EFAI**"`, caso habilitados no cliente).
- [ ] Verificar que o alerta azul de somatório automático NÃO é exibido.
- [ ] Gerar o malote com `"**Folha de respostas ENEM**"` e confirmar que todos os alunos saem no modelo ENEM.

**Referência técnica (para automação):**
- URL: `/ensalamento/`
- Seletor: `#configurePrintModal input[value="enem"]`
- Estado esperado: `distributionHasMixedSum == false`, `distributionAllSum == false`, modelos extras visíveis conforme flags do cliente.
- Fixture: `RoomDistribution` com aplicações sem somatório.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **Alerta no Modal de Impressão:** O alerta informativo (`.alert.alert-info`) no modal `#configurePrintModal` deve possuir fundo azul claro, borda suave e tipografia legível, posicionado imediatamente abaixo do grupo de botões de cartão-resposta.
- [ ] **Comparação com Mockup da OpenSpec:** Comparar o modal renderizado no navegador com o arquivo de referência:
  `openspec/changes/ensalamento-cadernos-mistos-86ak8wuvc/references/modal-malote-misto.html`
- [ ] **Remoção Limpa do Alerta no Cadastro:** Na tela `/ensalamento/criar/`, confirmar que a marcação alternada entre cadernos somatório e objetivas ocorre de forma fluida, sem "piscar" caixas de diálogo ou mensagens de erro.
- [ ] **Comparação com Mockup de Cadastro da OpenSpec:** Comparar a listagem de aplicações no cadastro com o arquivo de referência:
  `openspec/changes/ensalamento-cadernos-mistos-86ak8wuvc/references/cadastro-ensalamento-misto.html`

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Nenhum bug bloqueante ou regressão foi identificado nos testes automatizados executados (`40 passed`). Esta seção deve ser preenchida caso surja qualquer anomalia durante o teste manual em tela.

Formato padrão para abertura de apontamentos caso necessário:

```markdown
> [!BUG] [Backend Logic / UX/UI] Título claro do problema
> - **Contexto / Causa Raiz:** Detalhar a causa técnica ou comportamento inesperado.
> - **Comportamento Esperado:** Conforme OpenSpec: `openspec/changes/ensalamento-cadernos-mistos-86ak8wuvc/specs/ensalamento-cadernos-mistos/spec.md`.
> - **Workaround:** Solução paliativa para prosseguir o teste, se houver.
```

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **Malote em Massa de Aplicações (`application_list_new.html`):** O malote de aplicações da listagem geral continua bloqueando a seleção simultânea de somatório e objetivas. Isso foi mantido expressamente como não-objetivo desta mudança para evitar impactos na tela de aplicações sem especificação dedicada. No futuro, pode-se alinhar essa experiência criando uma issue própria.

> [!NOTE]
> **Híbrido e Reduzido em Ensalamento Misto:** Atualmente, se um ensalamento tiver cadernos de somatório e a escola desejar usar o modelo reduzido ou híbrido nas objetivas, o sistema restringe a Lize, ENEM e bolhas. Se no futuro houver demanda pedagógica para modelos reduzidos no ensalamento misto, deve ser avaliada a compatibilidade de layout dos malotes.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
  - 🔗 **[Ver Mapeamento de Tela: distribution_list.html](docs/tests/usability/distribution_list.md)**
  - 🔗 **[Ver Mapeamento de Tela: distribution_create_update.html](docs/tests/usability/distribution_create_update.md)**

### Automation Snippet (Python + Playwright / E2E com Mixer Setup)

Abaixo está o exemplo consolidado de teste automatizado ponta a ponta demonstrando o setup via `mixer` e a validação do modal misto com seletores estáveis:

```python
import pytest
from datetime import datetime, timedelta
from mixer.backend.django import mixer
from playwright.sync_api import Page, expect

from fiscallizeon.accounts.models import User
from fiscallizeon.applications.models import Application, ApplicationStudent
from fiscallizeon.classes.models import SchoolClass
from fiscallizeon.clients.models import Client, CoordinationMember, SchoolCoordination, Unity
from fiscallizeon.distribution.models import Room, RoomDistribution, RoomDistributionStudent
from fiscallizeon.exams.models import Exam, ExamQuestion
from fiscallizeon.questions.models import Alternative, Question
from fiscallizeon.students.models import Student


@pytest.mark.django_db(transaction=True)
def test_modal_malote_ensalamento_misto_exibe_apenas_objetivas(page: Page, live_server):
    # 1. Setup de Dados via Mixer
    user = mixer.blend(User, username='coord_e2e_test', is_superuser=True)
    user.set_password('123456')
    user.save()

    client = mixer.blend(
        Client,
        name='Colégio E2E',
        has_distribution=True,
        has_exam_elaboration=True,
        client_has_sum_questions=True,
        require_2fa=False,
    )
    unity = mixer.blend(Unity, client=client)
    coordination = mixer.blend(SchoolCoordination, unity=unity)
    mixer.blend(CoordinationMember, user=user, coordination=coordination)

    room = mixer.blend(Room, coordination=coordination, name='Sala E2E 01', capacity=30)
    school_class = mixer.blend(SchoolClass, coordination=coordination, name='3º A')
    student_1 = mixer.blend(Student, client=client, school_class=school_class, name='Aluno 1')
    student_2 = mixer.blend(Student, client=client, school_class=school_class, name='Aluno 2')

    # Caderno Somatório
    exam_sum = mixer.blend(Exam, client=client, name='Prova Somatório E2E')
    q_sum = mixer.blend(Question, client=client, category=Question.SUM)
    mixer.blend(ExamQuestion, exam=exam_sum, question=q_sum, order=1)

    # Caderno Objetivas
    exam_obj = mixer.blend(Exam, client=client, name='Prova Objetivas E2E')
    q_obj = mixer.blend(Question, client=client, category=Question.CHOICE)
    mixer.blend(Alternative, question=q_obj, text='A', is_correct=True)
    mixer.blend(ExamQuestion, exam=exam_obj, question=q_obj, order=1)

    app_sum = mixer.blend(Application, exam=exam_sum, date=datetime.now().date(), start='08:00', end='12:00', category=Application.PRESENTIAL)
    app_obj = mixer.blend(Application, exam=exam_obj, date=datetime.now().date(), start='08:00', end='12:00', category=Application.PRESENTIAL)

    app_st_1 = mixer.blend(ApplicationStudent, application=app_sum, student=student_1)
    app_st_2 = mixer.blend(ApplicationStudent, application=app_obj, student=student_2)

    distribution = mixer.blend(RoomDistribution, category=RoomDistribution.NAME_GRADE, is_printed=False)
    distribution.applications.add(app_sum, app_obj)
    distribution.rooms.add(room)
    mixer.blend(RoomDistributionStudent, distribution=distribution, room=room, application_student=app_st_1)
    mixer.blend(RoomDistributionStudent, distribution=distribution, room=room, application_student=app_st_2)

    # 2. Login
    page.goto(f'{live_server.url}/conta/entrar/')
    page.fill('input[name="username"]', 'coord_e2e_test')
    page.fill('input[name="password"]', '123456')
    page.click('button[type="submit"]')

    # 3. Navegação para Ensalamento
    page.goto(f'{live_server.url}/ensalamento/')

    # 4. Abertura do Modal de Impressão
    page.click('button:has-text("Opções")')
    page.click('a:has-text("Imprimir malote")')

    # 5. Validações no Modal
    modal = page.locator('#configurePrintModal')
    expect(modal).to_be_visible()

    # Opções válidas visíveis
    expect(modal.locator('label:has-text("Folha de respostas Lize")')).to_be_visible()
    expect(modal.locator('label:has-text("Bolhas ampliadas")')).to_be_visible()
    expect(modal.locator('label:has-text("Folha de respostas ENEM")')).to_be_visible()

    # Opções de outros modelos ocultas
    expect(modal.locator('label:has-text("Modelo somatório")')).not_to_be_visible()
    expect(modal.locator('label:has-text("Modelo PAS")')).not_to_be_visible()

    # Alerta de ensalamento misto visível com o texto esperado
    alert = modal.locator('.alert.alert-info')
    expect(alert).to_be_visible()
    expect(alert).to_contain_text('Cadernos com somatório saem no cartão de somatório automaticamente')
```

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Gargalo principal identificado durante a análise/teste:**
  Necessidade de recriação do banco de dados de testes (`--create-db`) devido a colunas transitórias herdadas de branches anteriores no banco local. Após essa etapa, toda a suíte de testes unitários e de integração (`40 testes`) rodou perfeitamente e passou com 100% de sucesso.
- **Iterações com desenvolvedor:**
  A documentação e os commits estavam extremamente organizados, com especificação OpenSpec completa (`proposal.md`, `design.md`, `spec.md`, `tasks.md` e referências HTML).
- **Oportunidades de melhoria no fluxo:**
  Expandir futuramente a resolução por caderno também para o malote de aplicações da listagem geral (`application_list_new.html`), unificando a experiência da coordenação.

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
- **Aviso sobre recriação de banco de testes (`--reuse-db` vs `--create-db`):** Ao alternar entre branches de features que adicionam colunas em modelos com migrations ainda não mergeadas na master, documentar na instrução de execução para tentar `--create-db` caso surja erro de `NotNullViolation` em campos não presentes na branch atual.
