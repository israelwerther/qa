# QA Test Plan: Formatação de Variáveis em Cabeçalho e Página Personalizada

## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-10-01 |
| **Natureza da Tarefa:** | `[Business Feature]` |
| **Área da Feature:** | Exams (Cabeçalhos e Páginas Personalizadas) |
| **Nível de Risco:** | Médio |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ |
| **Branch:** | `feat/formatacao-variaveis-cabecalho-pagina-CU-86ak7znbv` |
| **Task ClickUp:** | [86ak7znbv](https://app.clickup.com/t/86ak7znbv) |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend
- **Novo serviço centralizado** `render_template_variables()` em `fiscallizeon/exams/services/exam_service.py` — fonte única de verdade para substituição de variáveis em cabeçalhos, páginas personalizadas e exports
- **5 formatos de data da aplicação** implementados:
  - `#DataDaAplicacao` → `DD/MM/AAAA` (ex.: `28/08/2026`)
  - `#DataCompletaDaAplicacao` → data por extenso (ex.: `28 de agosto de 2026`)
  - `#MesDaAplicacao:extenso` → mês por extenso (ex.: `agosto`)
  - `#DiaDaAplicacao` → dia com zero (ex.: `08`)
  - `#DiaDaAplicacao:sem_zero` → dia sem zero (ex.: `8`)
- **Modificadores de caixa** (`:maiusculo`, `:minusculo`, `:capitalizado`) para todas as variáveis textuais
- **Variável de horário** `#HorarioDaAplicacao` → formato `HH:MM`
- **Formatação gramatical** de múltiplas disciplinas em `#NomeDasDisciplinas` (ex.: "Português, Matemática e Geografia")
- **Fallback seguro** para string vazia quando aplicação não tem data/horário

### Frontend
- **Novo partial compartilhado** `_variables_sidebar.html` com badges interativos, popovers e preview ao vivo
- **TinyMCE integrado** — inserção direta da tag escolhida no cursor do editor
- **Duas telas atualizadas**: `exam_header_create_update.html` e `custom_pages_create_update.html`
- **Compatibilidade Alpine.js + Vue 2** via diretiva `v-pre`

### Testes Automatizados
- **64 testes** adicionados/atualizados em `test_variable_formatting.py`, `test_exam.py`, `test_clientcustompage.py`
- Cobertura de retrocompatibilidade, novos formatos, fallbacks e formatação gramatical

---

## 2. Scope Boundaries (Diferenças de Escopo)

### IN SCOPE
- Inserção de variáveis de data em cabeçalhos e páginas personalizadas
- Inserção de variável de horário de início da aplicação
- Modificadores de caixa (maiúsculo, minúsculo, capitalizado) em variáveis textuais
- Formatação gramatical de múltiplas disciplinas
- Retrocompatibilidade total com cabeçalhos/páginas existentes
- Fallback para string vazia quando dados não estão disponíveis

### OUT OF SCOPE
- Novas permissões ou papéis de banco (permissões existentes mantidas)
- Migrações de banco (não há novas colunas)
- Alterações no shell/base das telas (apenas na coluna lateral)
- Validações sintáticas bloqueantes (tags malformadas não quebram a renderização)
- Suporte a outros idiomas além do português

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Lista de cabeçalhos | "Cabeçalhos" [verificar] | `/exams/headers/` | `exam_header_list` |
| Criar/Editar cabeçalho | "Novo Cabeçalho" / "Editar" [verificar] | `/exams/headers/create/`, `/exams/headers/<id>/edit/` | `exam_header_create_update` |
| Lista de páginas personalizadas | "Páginas Personalizadas" [verificar] | `/exams/custom-pages/` | `client_custom_page_list` |
| Criar/Editar página personalizada | "Nova Página" / "Editar" [verificar] | `/exams/custom-pages/create/`, `/exams/custom-pages/<id>/edit/` | `client_custom_page_create_update` |
| Provas (para testar impressão) | "Instrumentos Avaliativos" [verificar] | `/exams/` | `exams_list` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Comando para executar testes automatizados
```bash
# Todos os testes da feature
pytest fiscallizeon/exams/tests/test_variable_formatting.py -v

# Testes de modelo (retrocompatibilidade e novos formatos)
pytest fiscallizeon/exams/tests/models/test_exam.py -v
pytest fiscallizeon/exams/tests/models/test_clientcustompage.py -v

# Testes de views
pytest fiscallizeon/exams/tests/views/test_views.py -v
```

### Persona dos Testes
- **Usuário:** Coordenador/Diagramador com permissões `exams.add_examheader`, `exams.change_examheader`, `exams.add_clientcustompage`, `exams.change_clientcustompage`
- **Cliente:** Cliente de teste (ex.: "CLOUDLAB")

### Fixtures/Mixer para Setup Manual
```python
from mixer.backend.django import mixer
from fiscallizeon.exams.models import Exam, ExamHeader, ClientCustomPage
from fiscallizeon.applications.models import Application
from fiscallizeon.students.models import Student
from fiscallizeon.classes.models import Class

# Criar aplicação com data e horário
application = mixer.blend(
    Application,
    date='2026-08-28',
    start='08:00',
    client=client
)

# Criar prova vinculada à aplicação
exam = mixer.blend(
    Exam,
    application=application,
    client=client
)

# Criar aluno
student = mixer.blend(
    Student,
    name='JOAO DA SILVA E SOUZA',
    client=client
)

# Criar cabeçalho com variáveis
header = mixer.blend(
    ExamHeader,
    content='Prova de: #NomeDaProva - #DataDaAplicacao',
    client=client
)

# Criar página personalizada
custom_page = mixer.blend(
    ClientCustomPage,
    content='Data: #DataCompletaDaAplicacao',
    client=client
)
```

---

## 5. Roteiro de Testes com Checkboxes (Human-Centric Test Script)

### 5.1 Inserção de Variáveis de Data no Cabeçalho [Automatizável ✅]

#### Cenário 1.1 — Inserir variável de data padrão (DD/MM/AAAA)

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar na variável `"**Data da Aplicação**"` na barra lateral (badge com ícone de calendário)
- [x] Selecionar a opção `"**Formato: DD/MM/AAAA**"` no popover
- [x] Verificar que a tag `#DataDaAplicacao` foi inserida no editor TinyMCE na posição do cursor
- [x] Salvar o cabeçalho
- [x] Gerar um caderno de prova para uma aplicação com data `28/08/2026`
- [x] Verificar que o PDF exibe `28/08/2026`

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Data da Aplicação")`, `.variable-badge[data-variable="DataDaAplicacao"]`
- Estado esperado: `#DataDaAplicacao` presente no conteúdo do editor
- Fixture: `mixer.blend(ExamHeader, content='...', client=client)`

#### Cenário 1.2 — Inserir variável de data completa por extenso

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar na variável `"**Data da Aplicação**"` na barra lateral
- [x] Selecionar a opção `"**Formato: Data Completa (por extenso)**"` no popover
- [x] Verificar que a tag `#DataCompletaDaAplicacao` foi inserida no editor
- [x] Salvar e gerar caderno para aplicação com data `28/08/2026`
- [x] Verificar que o PDF exibe `28 de agosto de 2026`

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Data Completa")`, `.variable-badge[data-variable="DataCompletaDaAplicacao"]`
- Estado esperado: `#DataCompletaDaAplicacao` no conteúdo
- Fixture: `mixer.blend(Application, date='2026-08-28')`

#### Cenário 1.3 — Inserir variável de mês por extenso

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar na variável `"**Mês da Aplicação**"` na barra lateral
- [x] Selecionar a opção `"**Formato: Por Extenso**"` no popover
- [x] Verificar que a tag `#MesDaAplicacao:extenso` foi inserida no editor
- [x] Salvar e gerar caderno para aplicação com data `28/08/2026`
- [x] Verificar que o PDF exibe `agosto`

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Mês da Aplicação")`, `.variable-badge[data-variable="MesDaAplicacao"]`
- Estado esperado: `#MesDaAplicacao:extenso` no conteúdo
- Fixture: `mixer.blend(Application, date='2026-08-28')`

#### Cenário 1.4 — Inserir variável de dia sem zero à esquerda

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar na variável `"**Dia da Aplicação**"` na barra lateral
- [x] Selecionar a opção `"**Formato: Sem Zero à Esquerda**"` no popover
- [x] Verificar que a tag `#DiaDaAplicacao:sem_zero` foi inserida no editor
- [x] Salvar e gerar caderno para aplicação com data `08/08/2026`
- [x] Verificar que o PDF exibe `8` (sem zero)

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Dia da Aplicação")`, `.variable-badge[data-variable="DiaDaAplicacao"]`
- Estado esperado: `#DiaDaAplicacao:sem_zero` no conteúdo
- Fixture: `mixer.blend(Application, date='2026-08-08')`

---

### 5.2 Modificadores de Caixa (Case) [Automatizável ✅]

#### Cenário 2.1 — Aplicar caixa maiúscula em nome do aluno

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar na variável `"**Nome do Aluno**"` na barra lateral
- [x] Selecionar a opção `"**Caixa: Maiúsculo**"` no popover
- [x] Verificar que a tag `#NomeDoAluno:maiusculo` foi inserida no editor
- [x] Salvar e gerar caderno nominal para aluno cadastrado como `João da Silva`
- [x] Verificar que o PDF exibe `JOÃO DA SILVA`

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Nome do Aluno")`, `.variable-badge[data-variable="NomeDoAluno"]`
- Estado esperado: `#NomeDoAluno:maiusculo` no conteúdo
- Fixture: `mixer.blend(Student, name='João da Silva')`

#### Cenário 2.2 — Aplicar caixa minúscula em nome do aluno

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar na variável `"**Nome do Aluno**"` na barra lateral
- [x] Selecionar a opção `"**Caixa: Minúsculo**"` no popover
- [x] Verificar que a tag `#NomeDoAluno:minusculo` foi inserida no editor
- [x] Salvar e gerar caderno nominal para aluno cadastrado como `JOÃO DA SILVA`
- [x] Verificar que o PDF exibe `joão da silva`

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Nome do Aluno")`, `.variable-badge[data-variable="NomeDoAluno"]`
- Estado esperado: `#NomeDoAluno:minusculo` no conteúdo
- Fixture: `mixer.blend(Student, name='JOÃO DA SILVA')`

#### Cenário 2.3 — Aplicar caixa capitalizada em nome do aluno

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar na variável `"**Nome do Aluno**"` na barra lateral
- [x] Selecionar a opção `"**Caixa: Capitalizado**"` no popover
- [x] Verificar que a tag `#NomeDoAluno:capitalizado` foi inserida no editor
- [x] Salvar e gerar caderno nominal para aluno cadastrado como `JOAO DA SILVA E SOUZA`
- [x] Verificar que o PDF exibe `Joao da Silva e Souza` (preposições em minúsculo)

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Nome do Aluno")`, `.variable-badge[data-variable="NomeDoAluno"]`
- Estado esperado: `#NomeDoAluno:capitalizado` no conteúdo
- Fixture: `mixer.blend(Student, name='JOAO DA SILVA E SOUZA')`

#### Cenário 2.4 — Aplicar caixa em mês por extenso

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar na variável `"**Mês da Aplicação**"` na barra lateral
- [x] Selecionar `"**Formato: Por Extenso**"` e depois `"**Caixa: Maiúsculo**"` no popover
- [x] Verificar que a tag `#MesDaAplicacao:extenso:maiusculo` foi inserida no editor
- [x] Salvar e gerar caderno para aplicação com data `28/08/2026`
- [x] Verificar que o PDF exibe `AGOSTO`

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Mês da Aplicação")`, `.variable-badge[data-variable="MesDaAplicacao"]`
- Estado esperado: `#MesDaAplicacao:extenso:maiusculo` no conteúdo
- Fixture: `mixer.blend(Application, date='2026-08-28')`

---

### 5.3 Variável de Horário de Início [Automatizável ✅]

#### Cenário 3.1 — Inserir variável de horário de início

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar na variável `"**Horário da Aplicação**"` na barra lateral
- [x] Verificar que a tag `#HorarioDaAplicacao` foi inserida no editor
- [x] Salvar e gerar caderno para aplicação com horário `08:00`
- [x] Verificar que o PDF exibe `08:00`

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Horário da Aplicação")`, `.variable-badge[data-variable="HorarioDaAplicacao"]`
- Estado esperado: `#HorarioDaAplicacao` no conteúdo
- Fixture: `mixer.blend(Application, start='08:00')`

#### Cenário 3.2 — Aplicação sem horário de início (fallback)

**Ação humana:**
- [x] Criar uma aplicação sem horário de início (campo `start` vazio)
- [x] Acessar a tela de edição de cabeçalho
- [x] Inserir a variável `"**Horário da Aplicação**"`
- [x] Salvar e gerar caderno para essa aplicação
- [x] Verificar que a variável sai em branco no PDF, sem quebrar o layout nem exibir mensagem de erro

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Horário da Aplicação")`
- Estado esperado: string vazia no PDF
- Fixture: `mixer.blend(Application, start=None)`

---

### 5.4 Páginas Personalizadas (ClientCustomPage) [Automatizável ✅]

#### Cenário 4.1 — Inserir variável de data em página personalizada

**Ação humana:**
- [x] Acessar a tela de edição de página personalizada
- [x] Clicar na variável `"**Data da Aplicação**"` na barra lateral
- [x] Selecionar a opção `"**Formato: Data Completa (por extenso)**"` no popover
- [x] Verificar que a tag `#DataCompletaDaAplicacao` foi inserida no editor
- [x] Salvar e gerar caderno para aplicação com data `28/08/2026`
- [x] Verificar que a capa da prova exibe `28 de agosto de 2026`

**Referência técnica (para automação):**
- URL: `/exams/custom-pages/<id>/edit/`
- Seletor: `button:has-text("Data da Aplicação")`, `.variable-badge[data-variable="DataCompletaDaAplicacao"]`
- Estado esperado: `#DataCompletaDaAplicacao` no conteúdo
- Fixture: `mixer.blend(ClientCustomPage, content='...', client=client)`

#### Cenário 4.2 — Inserir variável de horário em página personalizada

**Ação humana:**
- [x] Acessar a tela de edição de página personalizada
- [x] Clicar na variável `"**Horário da Aplicação**"` na barra lateral
- [x] Verificar que a tag `#HorarioDaAplicacao` foi inserida no editor
- [x] Salvar e gerar caderno para aplicação com horário `14:30`
- [ ] Verificar que a capa exibe `14:30`

**Referência técnica (para automação):**
- URL: `/exams/custom-pages/<id>/edit/`
- Seletor: `button:has-text("Horário da Aplicação")`
- Estado esperado: `#HorarioDaAplicacao` no conteúdo
- Fixture: `mixer.blend(Application, start='14:30')`

---

### 5.5 Formatação Gramatical de Múltiplas Disciplinas [Automatizável ✅]

#### Cenário 5.1 — Uma única disciplina

**Ação humana:**
- [x] Criar uma prova com apenas uma disciplina vinculada (ex.: "Matemática")
- [x] Acessar a tela de edição de cabeçalho
- [x] Inserir a variável `"**Nome das Disciplinas**"`
- [x] Salvar e gerar caderno
- [x] Verificar que o PDF exibe `Matemática` (sem vírgula nem conjunção)

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Nome das Disciplinas")`
- Estado esperado: `Matemática` no PDF
- Fixture: `mixer.blend(Exam, subjects=[subject1])`

#### Cenário 5.2 — Duas disciplinas

**Ação humana:**
- [x] Criar uma prova com duas disciplinas vinculadas (ex.: "Português" e "Matemática")
- [x] Acessar a tela de edição de cabeçalho
- [x] Inserir a variável `"**Nome das Disciplinas**"`
- [x] Salvar e gerar caderno
- [x] Verificar que o PDF exibe `Português e Matemática`

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Nome das Disciplinas")`
- Estado esperado: `Português e Matemática` no PDF
- Fixture: `mixer.blend(Exam, subjects=[subject1, subject2])`

#### Cenário 5.3 — Três ou mais disciplinas

**Ação humana:**
- [x] Criar uma prova com três disciplinas vinculadas (ex.: "Português", "Matemática" e "Geografia")
- [x] Acessar a tela de edição de cabeçalho
- [x] Inserir a variável `"**Nome das Disciplinas**"`
- [x] Salvar e gerar caderno
- [x] Verificar que o PDF exibe `Português, Matemática e Geografia`

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `button:has-text("Nome das Disciplinas")`
- Estado esperado: `Português, Matemática e Geografia` no PDF
- Fixture: `mixer.blend(Exam, subjects=[subject1, subject2, subject3])`

---

### 5.6 Retrocompatibilidade [Automatizável ✅]

#### Cenário 6.1 — Cabeçalho existente sem modificadores

**Ação humana:**
- [x] Criar um cabeçalho com o conteúdo `Prova de: #NomeDaProva - #DiaDaAplicacao/#MesDaAplicacao/#AnoDaAplicacao` (formato antigo, sem modificadores)
- [x] Salvar o cabeçalho
- [x] Gerar caderno para aplicação com data `28/08/2026`
- [x] Verificar que o PDF exibe exatamente `Prova de: Matemática - 28/08/2026` (comportamento idêntico ao anterior)

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: N/A (apenas verificação de saída)
- Estado esperado: `28/08/2026` no PDF
- Fixture: `mixer.blend(ExamHeader, content='Prova de: #NomeDaProva - #DiaDaAplicacao/#MesDaAplicacao/#AnoDaAplicacao')`

#### Cenário 6.2 — Cabeçalho existente não é alterado ao abrir a tela de edição

**Ação humana:**
- [x] Criar um cabeçalho com variáveis antigas (sem modificadores)
- [x] Abrir a tela de edição desse cabeçalho
- [x] Verificar que o conteúdo no editor permanece inalterado (nenhuma tag nova é adicionada automaticamente)
- [x] Salvar sem fazer alterações
- [x] Gerar caderno e verificar que a saída é idêntica ao comportamento anterior

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: N/A (apenas verificação de que o conteúdo não muda)
- Estado esperado: conteúdo inalterado
- Fixture: `mixer.blend(ExamHeader, content='...')`

---

### 5.7 Interface e Popovers [Apenas Manual 👁]

#### Cenário 7.1 — Popover de variáveis abre corretamente

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar em qualquer variável na barra lateral
- [x] Verificar que o popover abre com as opções de formato/caixa
- [x] Verificar que o preview ao vivo mostra um exemplo formatado
- [x] Clicar fora do popover e verificar que ele fecha

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `.variable-badge`, `.variable-popover`
- Estado esperado: popover visível com opções

#### Cenário 7.2 — Preview ao vivo no popover

**Ação humana:**
- [x] Acessar a tela de edição de cabeçalho
- [x] Clicar na variável `"**Nome do Aluno**"`
- [x] Alternar entre as opções de caixa (maiúsculo, minúsculo, capitalizado)
- [x] Verificar que o preview no popover atualiza em tempo real mostrando o texto formatado

**Referência técnica (para automação):**
- URL: `/exams/headers/<id>/edit/`
- Seletor: `.variable-popover .preview`
- Estado esperado: texto do preview muda conforme a seleção

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] Validar que a barra lateral de variáveis está visualmente consistente entre as telas de cabeçalho e página personalizada
- [ ] Validar que os badges de variáveis têm ícones e cores distintas por categoria (data, horário, texto)
- [ ] Validar que os popovers estão bem posicionados e não sobrepõem o editor
- [ ] Validar que o preview ao vivo está legível e com fonte adequada
- [ ] Validar que a inserção no TinyMCE posiciona a tag corretamente no cursor
- [ ] Tirar screenshots da tela de edição de cabeçalho e página personalizada para comparação com o mockup `references/header-variables-editor.html`

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Esta seção deve ser preenchida durante a execução dos testes.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> Nenhum item identificado no momento.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi nomeado refletindo exatamente o template HTML (Django) ou rota/componente (SPA Aluno), e não a View.
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/exam_header_create_update.md)**
- 🔗 **[Ver Mapeamento de Tela](docs/tests/usability/custom_pages_create_update.md)**

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Principal gargalo durante os testes:** (preencher após execução)
- **Muitos vai-e-vem com o desenvolvedor?** (preencher após execução)
- **Como o fluxo de desenvolvimento ou QA poderia ser melhorado?** (preencher após execução)

---

## 10. Sugestões de Melhorias para o Prompt V2 (Anotações para Discussão Futura)

<!-- Anotações de melhorias -->
