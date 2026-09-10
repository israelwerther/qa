## 0. Metadata (Metadados de QA)

| Campo | Valor |
|---|---|
| **Data:** | 2026-09-10 |
| **Branch Backend (lizeedu):** | `feat/client-brand-color` |
| **Branch Frontend (lize-student):** | `feat/header-cor-da-escola` *(inclui `feat/materiais-empty-states`)* |
| **Natureza da Tarefa:** | `[Business Feature]` / `[UI/UX & Branding]` |
| **Área da Feature:** | App do Aluno (Branding Institucional, Header, Materiais de Estudo, Copy de Exercícios) |
| **Nível de Risco:** | Médio (Impacta 100% dos alunos no acesso ao app, visual mobile em 90% dos acessos e navegação de materiais) |
| **Qualidade da OpenSpec:** | ⭐⭐⭐⭐⭐ (5 estrelas - Proposals detalhadas nos dois repositórios, com especificação completa de degradê, luminância WCAG, empty states e vocabulário) |

---

## 1. Summary of Changes (Resumo das Alterações)

### Backend (`LizeEdu/lizeedu` — branch `feat/client-brand-color`)
- **Novo Campo `Client.primary_color`:** Adicionado campo opcional `CharField(max_length=7, blank=True, default="")` no modelo `Client` e no histórico de auditoria `HistoricalClient`, com validação estrita via regex para hexadecimais no formato `#RRGGBB` (ex.: `#1B4DB2`).
- **Exposição na API do Aluno (`/api/v3/user/`):** Adicionada a chave `primary_color` no dicionário de `AccountSerializer.get_client()`, entregue serializada em camelCase como `client.primaryColor` sem criar endpoints novos.
- **Invalidação Proativa de Cache:** Hook de ciclo de vida (`after_update`) no `Client` que limpa a chave de cache `USER_CLIENTS_OBJ_{user_id}` para todos os usuários vinculados quando `primary_color` é alterada, eliminando a espera pelo TTL de 4 horas.
- **Interface Django Admin:** Configurado widget de texto livre com placeholder `#RRGGBB` no admin de clientes (`ClientAdmin`), permitindo preencher ou limpar a cor (inputs HTML nativos `type="color"` não permitem valor vazio).
- **Cobertura de Testes Automatizados:** Testes unitários para persistência, regex, invalidação de cache e serialização (`test_client_primary_color.py` e `test_account_serializer.py`).

### Frontend (`LizeEdu/lize-student` — branches `feat/header-cor-da-escola` e `feat/materiais-empty-states`)
- **Degradê Dinâmico da Escola no Header:** O componente de cabeçalho (`HeaderBackdrop`, `AppHeader` e `MobileHeader`) passa a renderizar um degradê calculado com `color-mix(in oklab, ...)` a partir da custom property CSS `--brand` quando `client.primaryColor` estiver presente.
- **Cálculo Automático de Contraste (WCAG):** Módulo puro `brand-theme.ts` que calcula a luminância relativa da cor base (limiar `0.1791`). Se a cor da escola for clara (ex.: `#FFDD00`), os textos e ícones assumem tom escuro (`brand-fg-dark`); se for escura (ex.: `#0A2540`), assumem tom claro/branco (`brand-fg-light`).
- **Precedência de Branding sobre Wallpaper do Aluno:** Quando a escola tem cor definida, ela sobrepõe a imagem de papel de parede e **oculta** o seletor de wallpapers do menu de temas. Se a escola remover a cor, o papel de parede previamente escolhido pelo aluno (`user.background`) é restaurado automaticamente.
- **Empty States Unificados em Materiais de Estudo:** Componente compartilhado `StudyMaterialsEmptyState` com 5 variantes especializadas:
  1. *Pasta Vazia (`default`):* Ícone de pasta fechada e ação "Voltar para o início".
  2. *Busca sem Resultado (`search-empty`):* Ícone de lupa tachada e ação "Limpar busca" (ou "Limpar busca e filtros").
  3. *Filtros sem Resultado (`filters-empty`):* Ícone de ajustes e ação "Limpar filtros".
  4. *Sem Favoritos (`favorites-empty`):* Ícone de estrela e ação "Ver todos os materiais".
  5. *Erro de Carregamento (`error`):* Ícone de alerta, aviso de falha de comunicação e botão "Tentar novamente".
- **Filtro "Tipo de arquivo" em Materiais:** Ao navegar para dentro da pasta de uma disciplina, o filtro redundante de "Disciplina" é substituído pelo filtro "Tipo de arquivo" (Vídeo, PDF/Documento, Outro).
- **Acesso Direto ao Arquivo:** O clique sobre o título/nome do material de estudo abre diretamente o arquivo/vídeo sem exigir cliques intermediários.
- **Ajuste de Copy por Categoria de Aplicação:** O vocabulário do app do aluno (`application-copy.ts`) diferencia avaliações e listas de exercício: itens da categoria homework passam a exibir "Iniciar exercício", "Refazer exercício", "Finalize o exercício para baixar o caderno", evitando que o aluno confunda listas com provas valendo nota (fluxo de NPS preservado).
- **Correção de Escala de Acessibilidade:** As alternativas das questões (`alternatives-list.tsx`) agora herdam a classe `fontSizeClass`, escalando a fonte junto com o enunciado.

---

## 2. Scope Boundaries (Diferenças de Escopo)

### Dentro do Escopo (IN SCOPE)
- Configuração da cor `#RRGGBB` no Django Admin (`lizeedu`) e verificação do payload `/api/v3/user/`.
- Renderização do degradê da marca no Header (Desktop e Mobile) do app do aluno (`lize-student`).
- Verificação do cálculo de contraste visual (textos escuros sobre cores claras, textos brancos sobre cores escuras).
- Ocultação do seletor de wallpaper na presença de cor da escola e restauração do wallpaper ao remover a cor.
- Exibição de todas as 5 variantes de Empty States na tela de Materiais de Estudo.
- Funcionamento do filtro de "Tipo de arquivo" dentro das pastas de disciplinas.
- Clique no título do material abrindo o arquivo/vídeo diretamente.
- Adaptação das frases de copy de "avaliação" para "exercício" em aplicações da categoria Lista de Exercícios.
- Validação de usabilidade mobile (toque em cards, visualização sem hover preso e responsividade do header).

### Fora do Escopo (OUT OF SCOPE — Conforme sinalização e verificação estrita do diff)
- **NÃO IMPLEMENTADO NO DIFF:** *KPI de desempenho segmentado por provas e exercícios* (item desmarcado na task original, zero código ou endpoints entregues nesta entrega).
- **NÃO IMPLEMENTADO NO DIFF:** *Considerar apenas atividades feitas quando o aluno estava presente no KPI* (item desmarcado na task original, zero código entregue).
- **NÃO IMPLEMENTADO NO DIFF:** *Download da prova após realização* (depende de pitch separado da equipe de produto).
- **NÃO IMPLEMENTADO NO DIFF:** *Agenda de estudos do estudante* (pitch separado).
- **NÃO IMPLEMENTADO NO DIFF:** *Hierarquia de subpastas aninhadas dentro de disciplina* (fora do escopo da capability).
- **PRESERVADO SEM ALTERAÇÃO:** O tema geral da sidebar e componentes internos (`user.colorModeTheme` / Dark Mode) não é afetado pela cor da escola; a cor da instituição afeta exclusivamente o Header.

---

## 3. Navegação e Camada Técnica

| Destino | Rótulo real no menu UI | URL / Rota | Repositório / Camada |
|---|---|---|---|
| Admin: Edição do Cliente | Clientes ➔ [Nome do Cliente] | `/admin/clients/client/<uuid>/change/` | `lizeedu` (Django Admin) |
| API: Dados do Aluno Logado | Payload `/api/v3/user/` | `http://localhost:8000/api/v3/user/` | `lizeedu` (DRF / Auth) |
| App do Aluno: Home / Início | Início | `http://localhost:3000/painel` | `lize-student` (SPA) |
| App do Aluno: Minhas Provas | Minhas provas | `http://localhost:3000/painel/minhas-provas` | `lize-student` (SPA) |
| App do Aluno: Materiais de Estudo | Materiais de estudo | `http://localhost:3000/painel/materiais-de-estudo` | `lize-student` (SPA) |
| App do Aluno: Pasta da Disciplina | [Nome da Disciplina] | `http://localhost:3000/painel/materiais-de-estudo?disciplineId=<id>` | `lize-student` (SPA) |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

### Personas Ativas para Teste
1. **Superusuário / Administrador (`admin`):** Acessa o Django Admin para configurar ou limpar `Client.primary_color`.
2. **Aluno de Escola com Cor de Marca (`aluno.marca@lize.local`):** Aluno vinculado a um cliente com `primary_color = "#1B4DB2"` (Azul escuro) ou `#FFC700` (Amarelo claro).
3. **Aluno de Escola sem Cor de Marca (`aluno.padrao@lize.local`):** Aluno vinculado a um cliente com `primary_color = ""` (deve visualizar wallpapers normais).

### Comandos de Testes Automatizados Locais

#### Backend (`lizeedu`):
```bash
source .venv/bin/activate
pytest fiscallizeon/clients/tests/test_client_primary_color.py fiscallizeon/app/auth/tests/test_account_serializer.py -v --reuse-db
```

#### Frontend (`lize-student`):
```bash
cd /home/israel/Workspace/lize-student
bun test src/lib/brand-theme.test.ts src/components/layout/header-backdrop.test.tsx src/components/study-materials/empty-state.test.tsx src/components/study-materials/filters.test.tsx src/lib/application-copy.test.ts
bun run typecheck
```

### Setup de Dados para o Teste Manual (via Terminal / Django Shell)

Para configurar cores em clientes locais e preparar os alunos:

```python
# python manage.py shell
from fiscallizeon.clients.models import Client
from fiscallizeon.accounts.models import User

# 1. Configura cliente com cor escura (Azul Institucional)
c1 = Client.objects.first()
c1.primary_color = "#1B4DB2"
c1.save()
print(f"Cliente {c1.name} atualizado com cor {c1.primary_color}")

# 2. Garante que o aluno do cliente está com senha 123456
aluno = User.objects.filter(client=c1, type_profile=User.STUDENT).first()
if aluno:
    aluno.set_password("123456")
    aluno.save()
    print(f"Aluno de teste: {aluno.email} / senha: 123456")
```

---

## 5. Roteiro de Testes com Checkboxes (Dividido por Repositório e Branch)

---

### 🔹 PARTE 1: Backend (`LizeEdu/lizeedu` — Branch: `feat/client-brand-color`)
> **Ambiente**: Backend rodando via `./manage.py runserver` (porta 8000).  
> **Escopo desta branch**: Modelo `Client.primary_color`, validação no Django Admin, hook de invalidação de cache e entrega serializada no payload `/api/v3/user/`.

#### Cenário 1 — Validação e Persistência do Campo no Admin [Automatizável ✅]
- [x] 1. Fazer login no Django Admin (`http://localhost:8000/admin/`) como administrador.
- [x] 2. Acessar a listagem de "**Clientes**" e clicar em um cliente de teste (ex.: **Rede Decisão**).
- [x] 3. Localizar o campo "**Cor primária**" na seção de dados gerais.
- [x] 4. Testar validação com valor inválido: digitar `"azul"` ou `"#12345"` e clicar em "**Salvar**" (botão azul no rodapé).
- [x] 5. Confirmar que o Django exibe mensagem de erro: `"Informe a cor no formato hexadecimal #RRGGBB (ex.: #1B4DB2)."`.
- [x] 6. Digitar uma cor válida com letras minúsculas: `"#1b4db2"` e clicar em "**Salvar**".
- [x] 7. Confirmar que a cor é salva com sucesso e normalizada.
- [x] 8. Apagar o conteúdo do campo (deixando vazio) e clicar em "**Salvar**".
- [x] 9. Confirmar que o cliente salva sem erros com cor vazia (não obrigatória).

---

### 🔹 PARTE 2: Frontend Header (`LizeEdu/lize-student` — Branch: `feat/header-cor-da-escola`)
> **Instrução de Setup**: No terminal de `lize-student`, alterne para esta branch:
> ```bash
> git checkout feat/header-cor-da-escola
> bun dev
> ```
> **Ambiente**: App do Aluno rodando em `http://localhost:3000`.  
> **Escopo desta branch**: Degradê dinâmico da instituição no header desktop e mobile, cálculo de contraste de texto/ícone (WCAG) e ocultação do seletor de wallpaper.

#### Cenário 2 — Escola com Cor Escura (Ex.: Azul Escuro `#1B4DB2` ou Verde `#0A5C36`) [Manual 👁]
- [x] 1. No Admin (`http://localhost:8000/admin/`), definir a cor primária do cliente para `"#1B4DB2"` e clicar em **Salvar**.
- [x] 2. Abrir o app do aluno (`http://localhost:3000`) e fazer login com o aluno desse cliente (`enrico.a53143@aluno.decisaovirtual.com.br`).
- [x] 3. Observar a barra superior (Header) na tela de Início (Desktop).
- [x] 4. Validar se o header exibe um **degradê suave na tonalidade azul** no lugar da imagem genérica de papel de parede.
- [x] 5. Verificar o contraste: textos de boas-vindas, saudação e ícones do header devem estar em **branco / tom claro** legível.
- [x] 6. Abrir as ferramentas de desenvolvedor (F12) e alternar para a visão Mobile (ex.: iPhone 14 / 390px).
- [x] 7. Recarregar a página e confirmar que o cabeçalho mobile (`mobile-header`) também renderiza o degradê azul com textos brancos legíveis.

#### Cenário 3 — Escola com Cor Clara e Alto Brilho (Ex.: Amarelo Ouro `#FFC700` ou Lima `#C8E600`) [Manual 👁]
- [x] 1. No Admin, alterar a cor primária do cliente para `"#FFC700"` e clicar em **Salvar**.
- [x] 2. Voltar ao app do aluno (`http://localhost:3000`) e atualizar a página (`F5`).
- [x] 3. Confirmar que a mudança refletiu imediatamente (cache invalidado sem precisar esperar).
- [x] 4. Observar que o degradê do header agora é amarelo.
- [x] 5. Validar o cálculo de contraste automático: como o fundo é claro, os textos e ícones devem ter mudado automaticamente para **tom escuro / preto grafite**, mantendo leitura perfeita sem letras brancas ilegíveis.
- [x] 6. Confirmar o mesmo contraste no cabeçalho mobile (DevTools / Mobile).

#### Cenário 4 — Precedência de Marca vs Papel de Parede do Aluno [Manual 👁]
- [x] 1. Estando logado como aluno de cliente com cor definida (`#1B4DB2`), clicar no avatar / menu de perfil ou no botão de temas no canto superior direito do header.
- [x] 2. Observar as opções do menu dropdown.
- [x] 3. Validar que o **seletor de papéis de parede (galeria com miniaturas)** NÃO está visível (oculto para respeitar a identidade visual da escola).
- [x] 4. No Django Admin, apagar a cor primária do cliente (deixar vazio e clicar em **Salvar**).
- [x] 5. Atualizar o app do aluno (`F5`).
- [x] 6. Confirmar que o header voltou a exibir o papel de parede clássico (foto/arte).
- [x] 7. Clicar novamente no menu de temas do aluno e validar que o **seletor de papéis de parede reapareceu** normalmente.![alt text](evidencias/image-1.png)

---

### 🔹 PARTE 3: Frontend Materiais & Copy (`LizeEdu/lize-student` — Branch: `feat/materiais-empty-states`)
> **Instrução de Setup**: No terminal de `lize-student`, você pode manter `feat/header-cor-da-escola` (que já herda todos os commits de materiais) ou alternar isoladamente para:
> ```bash
> git checkout feat/materiais-empty-states
> bun dev
> ```
> **Ambiente**: App do Aluno rodando em `http://localhost:3000`.  
> **Escopo desta branch**: 5 variantes especializadas de Empty States, filtro por "Tipo de arquivo" em pastas de disciplinas, clique direto para abrir material e diferenciação de copy para Listas de Exercícios.

#### Cenário 5 — Materiais de Estudo: Validação das Variantes de Empty States [Manual 👁]
- [x] 1. No app do aluno, clicar no item "**Materiais de estudo**" (`/painel/materiais-de-estudo`) na barra lateral de navegação.
- [x] 2. **Variante 1 (Pasta Vazia):** Clicar em uma pasta de disciplina que você sabe que não possui materiais cadastrados.
- [x] 3. Validar se a tela exibe o container pontilhado com ícone de pasta fechada, título `"Nenhum material nesta pasta"`, descrição explicativa e o botão `"**Voltar para o início**"`.
- [x] 4. Clicar no botão `"**Voltar para o início**"` e validar se a navegação retorna à raiz dos materiais.
- [x] 5. **Variante 2 (Busca sem Resultado):** Na barra de pesquisa de materiais, digitar um termo inexistente (ex.: `"qwertyxyz123"`).
- [x] 6. Validar se a tela exibe o empty state com ícone de lupa, título `"Nenhum resultado para "qwertyxyz123""` e o botão `"**Limpar busca**"`.
- [x] 7. Clicar no botão `"**Limpar busca**"` e confirmar que o campo é limpo e a listagem normal é restaurada.
- [x] 8. **Variante 3 (Sem Favoritos):** Ligar o filtro de "**Favoritos**" (ícone de estrela) quando nenhum material estiver favoritado.
- [x] 9. Validar a exibição da mensagem `"Você ainda não tem materiais favoritos"` e o botão `"**Ver todos os materiais**"`. ![alt text](./evidencias/image.png)

#### Cenário 6 — Filtro "Tipo de arquivo" e Clique Direto [Manual 👁]
- [ ] 1. Na listagem de materiais, entrar em uma pasta de disciplina que contenha arquivos (ex.: Matemática).
- [ ] 2. Observar os filtros superiores da barra de ferramentas.
- [ ] 3. Validar que o filtro de "**Disciplina**" sumiu e em seu lugar está o filtro "**Tipo de arquivo**" (com opções como Vídeo, Documento, Outro).
- [ ] 4. Selecionar um tipo específico (ex.: "Vídeo") e confirmar que a filtragem reage na hora.
- [ ] 5. Clicar diretamente sobre o título / nome de um material.
- [ ] 6. Validar se o arquivo abre diretamente (download ou visualizador/modal de vídeo), sem etapas desnecessárias.

#### Cenário 7 — App do Aluno: Ajuste de Copy ("Exercício" vs "Avaliação") [Manual 👁]
- [ ] 1. No app do aluno, acessar a tela "**Minhas provas**" (`/painel/minhas-provas`).
- [ ] 2. Localizar um card de **Prova Regular** (Avaliação):
  - [ ] O botão de ação deve dizer `"**iniciar avaliação**"` ou `"**Iniciar prova**"`.
  - [ ] Caso já realizada, deve indicar `"**prova já realizada**"`.
- [ ] 3. Localizar um card de **Lista de Exercícios** (Homework / Exercício):
  - [ ] O botão de ação deve exibir obrigatoriamente `"**iniciar exercício**"` (e NÃO "iniciar avaliação").
  - [ ] Se já realizado, deve exibir `"**exercício já realizado**"`.
  - [ ] Ao clicar no modal de confirmação para refazer, o título deve ser `"**Deseja realmente refazer este exercício?**"`.
- [ ] 4. Na tela inicial (**Início**), se houver apenas listas de exercícios agendadas, o card de aviso deve exibir: `"**Você tem novas listas de exercício agendadas**"`.

#### Cenário 8 — Usabilidade Mobile e Toque (Touch Check) [Manual 👁]
- [ ] 1. Em dispositivo móvel real ou simulador com Touch Emulation ativado no DevTools:
- [ ] 2. Tocar nos cards de materiais de estudo e cards de provas.
- [ ] 3. Validar que o toque dispara a ação imediatamente sem ficar com estado visual travado de "hover persistente" (bordas ou sombras presas que só desativam ao tocar fora).
- [ ] 4. Validar que a rolagem vertical da página inicial e da listagem de materiais flui suavemente sem quebras de layout.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

- [ ] **Comparação de Cores e Gradiente:** Validar que o degradê no topo não cria faixas abruptas de cor (banding visual). A transição deve ser orgânica e suave.
- [ ] **Simetria no Mobile:** O header mobile de 242px de altura não deve cortar a foto/avatar do aluno nem sobrepor o nome da escola.
- [ ] **Leiturabilidade Textual:** Em nenhum momento deve ocorrer texto branco sobre fundo amarelo ou texto preto sobre fundo azul marinho.
- [ ] **Captura de Evidências:** Anexar prints lado a lado demonstrando:
  1. Header com cor escura (`#1B4DB2`) ➔ Textos brancos.
  2. Header com cor clara (`#FFC700`) ➔ Textos escuros.
  3. Empty state de pasta vazia com botão de ação.
  4. Botão "iniciar exercício" na lista de exercícios.

---

## 7. Bugs and Observations (Problemas Encontrados)

> [!NOTE]
> Nenhum bug crítico impeditivo registrado até o momento. Utilize o modelo abaixo caso encontre divergências durante os testes:

<!--
> [!WARNING]
> **[UX/UI] Título do Problema**
> - **Causa / Contexto:** Detalhar se ocorreu no mobile ou desktop, e qual a cor configurada.
> - **Comportamento Esperado:** `(conforme OpenSpec: header-brand-gradient/spec.md L.45)` ou `(inferência de UX — Spec Gap)`.
> - **Workaround:** Como contornar para seguir testando.
-->

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> **[KPI de Desempenho]:** O item *"KPI de desempenho segmentado por provas e exercícios considerando apenas presença do aluno"* que constava na discussão preliminar deve ser planejado em uma task própria com backend dedicado, pois requer novos agregadores na API de relatórios do aluno.

> [!NOTE]
> **[Filtragem de Tipo de Arquivo Server-Side]:** Atualmente o filtro de "Tipo de arquivo" em materiais filtra apenas os itens da página corrente no cliente. Quando houver paginação pesada de materiais (>20 itens por pasta), será benéfico passar o parâmetro de tipo diretamente para a query da API.

---

## 8.1. Knowledge Base Notes (Mapeamento Contínuo de Usabilidade)

- [x] O arquivo de mapeamento foi verificado e atualizado com os novos seletores e componentes.
🔗 **[Ver Mapeamento de Tela (App Aluno - Header & Materiais)](docs/tests/usability/app_student_header_and_materials.md)**

### Identificadores Estáveis e Seletores do Frontend (`lize-student`):
- Header Backdrop Degradê: `.brand-header` (com estilo `--brand: <hex>`).
- Classes de Contraste: `.brand-fg-light` (conteúdo claro) e `.brand-fg-dark` (conteúdo escuro).
- Container de Empty State: `output` com classes `border-dashed border-slate-200`.
- Botões de Ação do Empty State: `button[aria-label="Voltar para o início"]`, `button[aria-label="Limpar busca"]`, `button[aria-label="Limpar filtros"]`.
- Botão de Lista de Exercício: `button:has-text("iniciar exercício")`.

---

## 9. QA Retrospective (Retrospectiva de QA)
- **Separação de Branches:** As tarefas que tocam o app do aluno demandam coordenação fina entre `lizeedu` (onde o Admin/DB reside) e `lize-student` (onde a SPA do aluno vive). A unificação do plano de testes em uma visão End-to-End evitou testes cegos e garantiu o alinhamento das duas pontas.

---

## 10. Sugestões de Melhorias para o Processo de QA
<!-- Anotações de melhorias no prompt ou no acervo coletadas durante o teste -->
