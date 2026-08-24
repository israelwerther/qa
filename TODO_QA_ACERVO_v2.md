# TODO — Evolução do QA Test Plan para Acervo Autônomo

> Criado em: 2026-07-03
> Retomar em: próxima conversa
> Contexto: discussão iniciada durante QA da branch `feat/multiplas-questoes-prova-CU-86ahj6guq`

---

## Objetivo Final

Construir um **acervo de conhecimento operacional do Lize para a IA**, de forma que no futuro a IA consiga:
- Navegar pelo sistema com autonomia (usando o browser subagent)
- Criar dados de teste via **mixer** (já existente no projeto)
- Executar os testes Playwright no lugar do QA humano
- Validar features novas sem intervenção do usuário

O QA humano executa os planos agora **enquanto o acervo é construído**. O objetivo é tornar essa fase progressivamente opcional.

---

## Problemas Identificados no Prompt Atual

### 1. Navegação inferida ≠ navegação real
- **O erro:** O prompt me instrui a investigar `urls.py` e templates para inferir caminhos de menu
- **O que aconteceu:** Inferí `Cadernos > Provas` a partir do HTML, mas o menu real é `Instrumentos Avaliativos`
- **Raiz do problema:** HTML ≠ UI real. Texto no código pode não ser o rótulo visível ao usuário

### 2. Documento escrito para humano, não para IA executar
- O plano atual usa linguagem em prosa suficiente para um humano com contexto
- Para a IA executar via browser subagent, precisa de: URL exata, seletores DOM reais, dados determinísticos

### 3. Dados de teste vagos
- "Abrir uma prova com 5 questões" — o humano improvisa, o Playwright (e a IA) falha
- Precisa integrar o **mixer** existente para criar fixtures determinísticas

### 4. IA atribui origem "conforme OpenSpec" a comportamentos que ela mesma inferiu
- **O erro:** Ao documentar um bug, escrevi "Comportamento esperado (conforme OpenSpec): elementos clicáveis devem oferecer feedback visual consistente ao hover" — mas isso **não estava no OpenSpec**. Foi uma inferência minha de boas práticas de UX.
- **O impacto:** O QA pode gastar tempo procurando no OpenSpec algo que não existe, ou pior, reportar ao dev como "violação de spec" quando na verdade é um Spec Gap.
- **Raiz do problema:** O prompt não instrui explicitamente a IA a verificar se o comportamento esperado descrito num bug **está de fato documentado no OpenSpec** antes de citá-lo como fonte.
- **Correção necessária no prompt:** Adicionar regra: ao preencher o campo "Comportamento esperado" de um bug, a IA DEVE indicar explicitamente a fonte — `(conforme OpenSpec: spec.md L.XX)` com citação direta, ou `(inferência de UX — Spec Gap)` quando não houver referência. Jamais escrever "conforme OpenSpec" sem citar o trecho exato.

---

## O que Precisa Mudar no Prompt

### Mudança 1 — Mapa de Navegação Verificado
Adicionar instrução para o prompt criar uma tabela de navegação canônica no documento, marcando itens como `[verificar]` quando inferidos do código (nunca assumir como verdade absoluta).

Formato:
```
| Destino            | Rótulo real no menu UI    | URL Django              | View name      |
|--------------------|---------------------------|-------------------------|----------------|
| Lista de provas    | Instrumentos Avaliativos  | /exams/?category=exam   | exams_list     |
| Visualizar Prova   | (link na listagem)        | /exams/<uuid>/visualizar | exams_preview |
```

### Mudança 2 — Dupla camada em cada cenário
Cada cenário do roteiro deve ter dois blocos:

```markdown
**Ação humana:** Clicar em "Selecionar" de uma questão.

**Referência técnica (para automação):**
- URL: `/exams/<uuid>/visualizar`
- Seletor: `button:has-text("Selecionar")` (coluna de ações)
- Estado esperado no DOM: `outline: 2px solid #FF6900` na `span.rounded-circle`
- Fixture: `python manage.py mixer_exam --questions=5 --ets=2` (verificar comando real)
```

### Mudança 3 — Tag de automatizabilidade
Cada cenário classificado como:
- `[Automatizável ✅]` — pode virar teste Playwright
- `[Apenas Manual 👁]` — requer julgamento humano (visual, UX, comparação com Figma)

---

## Próximos Passos (Atualizado - Aguardando Nova Task)

- [x] **1. Analisar os testes Playwright e Mixer:** Foi identificado que o projeto usa Playwright integrado ao Python/pytest (`tests/usability/`) e gera fixtures dinamicamente via `mixer.blend()` no banco de testes.
- [x] **2. Elaborar Prompt V2:** O prompt inicial foi reescrito (V2) para incorporar a "Camada Técnica" e mapear o sistema de forma estruturada.
- [ ] **3. Testar V2 na Prática:** Aguardar a próxima feature/branch do usuário para rodar a V2 do prompt, gerar o QA Test Plan e validar a utilidade prática no ambiente real.
- [ ] **4. Destilação de Conhecimento (KIs):** Após validar os primeiros planos com a V2, extrair os caminhos de navegação confiáveis e fluxos validados para um Knowledge Item (KI) central (ex: `KI_Navegacao.md`), evitando contexto fragmentado.
  - *O que isso significa?* Em vez de mantermos dezenas de arquivos `QA_TEST_PLAN_...md` dispersos e isolados, cada vez que um QA for executado manualmente e as rotas reais forem confirmadas, nós vamos consolidar esses atalhos, seletores reais da UI (ex: `#submit-btn`) e nomes corretos num único repositório de conhecimento (o KI). O objetivo é ensinar a IA a navegar no projeto real, desviando das "telas mortas" ou nomes de sidebar que não batem com o código fonte.
- [ ] **5. Conexão com Mixer e Automação (O "Santo Graal"):** Nos planos futuros, começar a mapear a "Camada Técnica" com comandos exatos de setup de banco (`mixer.blend(...)`), permitindo que a IA traduza cenários manuais em testes autônomos (Python Playwright) mais facilmente.
  - *O que isso significa?* Visto que o projeto usa testes Playwright em Python com a biblioteca `mixer` para simular o banco (ex: `mixer.blend(Application, exam=obj)`), o próximo estágio é fazer o QA Plan exigir que a gente documente *qual* estrutura inicial de dados precisou ser criada. Quando a IA tiver: (A) As rotas validadas pelo KI e (B) O setup de banco catalogado pelo Mixer, você poderá simplesmente pedir *"Faça um teste automatizado para blindar essa regra de negócio"* e a IA terá todo o contexto (Setup + Navegação) pronto para gerar ou executar o teste sem tropeços.

---

## Contexto de Conversa para Retomar

- Conversa ID: `c4dfa98e-92cd-456a-9191-7996c5211c91` (2026-07-03)
- Branch testada: `feat/multiplas-questoes-prova-CU-86ahj6guq`
- Feature: Seleção e ações em massa na tela Visualizar Prova (`exam_preview_new.html`)
- Plano gerado: `QA_TEST_PLAN_feat_multiplas-questoes-prova-CU-86ahj6guq.md`

---

## Anexo: Prompt V2 (QA Test Plan Generator)

🔗 **[Ver Prompt V2 completo](QA_PROMPT_V2.md)**

*Resumo: Role & Objective, regra anti-alucinação, estrutura de 10 seções
(Metadata, Summary, Escopo, Navegação, Testes/Fixtures, Roteiro humano,
Validação Visual, Bugs, Melhorias, Mapeamento de Usabilidade, Retrospectiva).*

## Objetivos da Sessão Atual de Teste (Validação do Prompt V2)

Durante os testes da branch atual (como "prova de fogo" do Prompt V2), nosso foco é validar e garantir os seguintes pontos ao final:
1. **Otimização:** Descobrir formas de otimizar ainda mais o Prompt V2.
2. **Entendimento de Fluxo:** Validar se a forma como o plano é estruturado realmente ajuda a IA a compreender com clareza o fluxo da tela testada.
3. **Mapeamento para Automação Futura:** Confirmar se o mapeamento técnico criado (seletores, URLs reais, fixtures) permitiria à IA testar *novas funcionalidades* desta tela no futuro, com total autonomia.
4. **Sugestões de Melhorias:** Registrar ativamente minhas sugestões (como IA) de ajustes ou correções na especificação, no teste ou no próprio prompt durante a nossa interação.
