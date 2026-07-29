## 0. Metadata (Metadados de QA)

| Campo | Valor |
|-------|-------|
| **Date** | 2026-07-29 |
| **Task Nature** | `[Technical/Internal]` - Dashboard interno para desenvolvedores, scripts de análise de código e documentação (READMEs) |
| **Feature Area** | Internal Tooling / Design System |
| **Risk Level** | Low (Não afeta fluxos críticos do usuário final, apenas adiciona rotas de debug/admin e scripts) |
| **OpenSpec Quality** | N/A (Feature de infraestrutura técnica/estudos) |

---

## 1. Summary of Changes (Resumo das Alterações)

*   **Backend & Scripts:**
    *   Criação do script `./scripts/ui/component-adoption.py` para gerar relatório de adoção (JSON/Texto/MD) que classifica templates em Tiers (A, B, C, D).
    *   Criação do script `./scripts/dev/generate-components-catalog.py` para regenerar o índice.
    *   Criação do módulo `fiscallizeon/core/component_catalog.py` e views.
*   **Frontend & Views:**
    *   Adição do Dashboard ao vivo (`/dev/components/adoption/`) listando componentes usados vs não usados.
    *   Rotas do Styleguide interno (`/dev/components/`).
*   **Documentação e CSS:**
    *   Adição de arquivos `README.md` detalhados dentro de todos os diretórios em `components/`.
    *   Criação de uma skill para IA em `.cursor/skills/lize-ui-components/SKILL.md`.
    *   Atualizações utilitárias no `tw.css` (Tailwind).

---

## 2. Scope Boundaries (Diferenças de Escopo)

*   **IN SCOPE:** Validar a execução correta do script de adoção (se processa os dados sem crash), renderização do novo dashboard/styleguide de componentes e validar se a atualização no CSS não quebrou telas legadas principais de forma catastrófica (Smoke Test visual).
*   **OUT OF SCOPE:** Não é necessário validar "pixel perfect" do styleguide contra o Figma (pois é uma ferramenta interna de dev). Não testaremos o funcionamento interno de cada componente da aplicação legada, apenas a adoção/apresentação deles na documentação nova.

---

## 3. Navegação e Camada Técnica (Navigation and Technical Layer)

| Destino | Rótulo real no menu UI | URL Django | View name |
|---------|------------------------|------------|-----------|
| Styleguide Home | (Sem Menu - Acesso Direto) | `/dev/components/` | `styleguide_index` |
| Dashboard Adoção | (Acesso via Home) | `/dev/components/adoption/` | `styleguide_adoption` |

---

## 4. Automated Tests & Fixtures (Testes Automatizados e Setup de Dados)

*   **Testes criados:** A branch inclui testes como `test_component_adoption_dashboard.py`, `test_component_catalog.py` e `test_component_styleguide.py`.
*   **Comando para rodar local:**
    ```bash
    pytest fiscallizeon/core/tests/test_component_*.py -v
    ```
*   **Persona:** Desenvolvedor / Admin. Não requer setup de permissões complexas de "professor" ou "unidade", porém o acesso à URL `/styleguide/` provavelmente exige `is_superuser=True` ou permissões de staff (necessário confirmar ao navegar).

---

## 5. Execution Test Script (Roteiro de Testes com Checkboxes)

### Configuração e Validação de Scripts CLI

- [x] `[Automatizável ✅]` **Ação humana/CLI:** Rodar o script gerador de catálogo: `./scripts/dev/generate-components-catalog.py`
    - **Referência técnica:** Deve criar/atualizar os metadados do catálogo de componentes.
- [x] `[Automatizável ✅]` **Ação humana/CLI:** Rodar o script de adoção no terminal: `./scripts/ui/component-adoption.py`
    - **Referência técnica:** Garantir que executa com sucesso e classifica os templates corretamente nos Tiers A (usa component), B (base redesign), C (include) e D (legado).

### Validação do Dashboard / Styleguide (Internal Tooling)

- [x] `[Automatizável ✅]` **Ação humana:** Fazer login e acessar a raiz do styleguide (`/dev/components/`).
    - **Estado esperado:** Renderização correta com a listagem de componentes, lendo os READMEs dinamicamente.
- [x] `[Apenas Manual 👁]` **Ação humana:** Clicar na aba ou link do Dashboard de Adoção (`/dev/components/adoption/`).
    - **Referência técnica:** Deve consultar `component_adoption_views.py`.
    - **Estado esperado:** Gráficos/tabelas exibindo a distribuição por Tiers (A, B, C, D) e componentes não usados.
- [ ] `[Apenas Manual 👁]` **Ação humana:** Acessar a página de detalhes/demos de pelo menos 3 componentes (ex: Accordion, Card, Toggle).
    - **Estado esperado:** A documentação renderizada a partir dos `.md` deve estar legível e a demonstração (`demos/*.html`) deve carregar e funcionar sem erros graves de console no navegador.

### Smoke Test de CSS Global (Regressão)

- [ ] `[Apenas Manual 👁]` **Ação humana:** Navegar brevemente por uma tela principal de produção (ex: Listagem de Provas ou Turmas).
    - **Estado esperado:** As adições ao `tw.css` não devem ter "vazado" ou quebrado layouts globais do sistema. Nenhuma quebra visual absurda é aceitável.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

*Note: Task Nature é `[Technical/Internal]`, portanto a validação visual foca na clareza dos dados apresentados (Information Architecture) e legibilidade da documentação dos componentes.*

- [x] Tirar screenshot da tela do **Dashboard de Adoção**, validando se as tabelas (Usados vs Não Usados) estão claras e corretas.
- [ ] Tirar screenshot de um **Componente Específico no Styleguide**, validando se a extração do `README.md` ficou bem renderizada para consulta do dev.

---

## 7. Bugs and Observations (Problemas Encontrados)

*(Preencher durante a execução)*

> [!BUG]
> **Título:** Lista de "Refs desconhecidas" com bullet point desalinhado no final do Dashboard de Adoção.
> **Context/Root Cause:** O bullet point (`li`) com o texto "nome" e a tag `{% endverbatim %}` quebrou o alinhamento da caixa amarela de alerta, provavelmente por falta de classes utilitárias de lista (como `tw-list-inside` ou `tw-ml-4`) no template.
> **Expected Behavior:** `(inferência de UX — Spec Gap)` A lista de refs desconhecidas deve estar com recuo adequado, perfeitamente alinhada dentro do box amarelo, sem vazar a margem.
> **Workaround:** Não bloqueia o uso, é apenas um glitch visual (`[UX/UI]`).

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> *(Adicionar ideias de melhorias futuras para a ferramenta de adoção aqui durante o teste)*

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Gargalo principal:** (Em branco por enquanto)
- **Melhoria para a próxima vez:** A separação `[Technical/Internal]` no plano economizou muito tempo ignorando testes de permissões complexas.
