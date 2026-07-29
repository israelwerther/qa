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
    *   Criação do script `scripts/ui/component-adoption.py` para gerar relatório de adoção de django-components.
    *   Criação do módulo `fiscallizeon/core/component_catalog.py` e views `component_adoption_views.py` e `component_styleguide_views.py`.
*   **Frontend & Views:**
    *   Adição de um novo dashboard interativo (`/styleguide/adoption/` ou similar) para acompanhar a adoção e listar componentes não usados.
    *   Criação do `styleguide/index.html` e templates de demonstração de componentes (Accordion, Card, Charts, etc.).
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
| Styleguide Home | (Sem Menu - Acesso Direto) [verificar] | `/styleguide/` [verificar] | `styleguide_index` [verificar] |
| Dashboard Adoção | (Acesso via Home do Styleguide) [verificar] | `/styleguide/adoption/` [verificar] | `styleguide_adoption` [verificar] |

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

- [ ] `[Automatizável ✅]` **Ação humana/CLI:** Rodar o script de adoção no terminal: `python scripts/ui/component-adoption.py`
    - **Referência técnica:** Garantir que o script executa do início ao fim com `exit_code 0`.
    - **Estado esperado:** O terminal deve printar os relatórios ou gerar algum output sem stacktraces (Errors).

### Validação do Dashboard / Styleguide (Internal Tooling)

- [ ] `[Automatizável ✅]` **Ação humana:** Fazer login com usuário `superuser` e acessar a URL raiz do styleguide (`/styleguide/`).
    - **Estado esperado:** A tela deve renderizar corretamente o `index.html` com a listagem de componentes disponíveis no projeto, lendo os novos READMEs e documentações geradas.
- [ ] `[Apenas Manual 👁]` **Ação humana:** Clicar na aba ou link do Dashboard de Adoção (`/styleguide/adoption/`).
    - **Referência técnica:** Deve consultar `component_adoption_views.py`.
    - **Estado esperado:** Os gráficos ou tabelas devem mostrar quais componentes são usados, quais não são, conforme os dados gerados em tempo real, validando o output no UI (Data Validation).
- [ ] `[Apenas Manual 👁]` **Ação humana:** Acessar a página de detalhes/demos de pelo menos 3 componentes (ex: Accordion, Card, Toggle).
    - **Estado esperado:** A documentação renderizada a partir dos `.md` deve estar legível e a demonstração (`demos/*.html`) deve carregar e funcionar sem erros graves de console no navegador.

### Smoke Test de CSS Global (Regressão)

- [ ] `[Apenas Manual 👁]` **Ação humana:** Navegar brevemente por uma tela principal de produção (ex: Listagem de Provas ou Turmas).
    - **Estado esperado:** As adições ao `tw.css` não devem ter "vazado" ou quebrado layouts globais do sistema. Nenhuma quebra visual absurda é aceitável.

---

## 6. Visual and Layout Validation (Validação Visual e de Layout)

*Note: Task Nature é `[Technical/Internal]`, portanto a validação visual foca na clareza dos dados apresentados (Information Architecture) e legibilidade da documentação dos componentes.*

- [ ] Tirar screenshot da tela do **Dashboard de Adoção**, validando se as tabelas (Usados vs Não Usados) estão claras e corretas.
- [ ] Tirar screenshot de um **Componente Específico no Styleguide**, validando se a extração do `README.md` ficou bem renderizada para consulta do dev.

---

## 7. Bugs and Observations (Problemas Encontrados)

*(Preencher durante a execução)*

> [!WARNING] (Exemplo)
> **Título:** O script de adoção não considera templates na pasta `X`
> **Root Cause:** Regex não pega tags customizadas
> **Expected Behavior:** `(inferência de UX — Spec Gap)` O script deveria contabilizar todos os diretórios mapeados no settings.

---

## 8. Future Improvements & Tech Debt (Melhorias Futuras)

> [!NOTE]
> *(Adicionar ideias de melhorias futuras para a ferramenta de adoção aqui durante o teste)*

---

## 9. QA Retrospective (Retrospectiva de QA)

- **Gargalo principal:** (Em branco por enquanto)
- **Melhoria para a próxima vez:** A separação `[Technical/Internal]` no plano economizou muito tempo ignorando testes de permissões complexas.
