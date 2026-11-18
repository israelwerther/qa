# Mapeamento de Usabilidade — Configurações das Questões

## 1. URLs e Navegação

| Destino | URL Django | View name | Como navegar |
|---------|------------|-----------|--------------|
| Configurações das questões | `/membros/questoes/configuracoes` | `questions_configuration` | Menu lateral → Configurações → Questões |

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

```python
from mixer.backend.django import mixer
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client, ClientQuestionsConfiguration

# Usuário coordenação (acesso à configuração)
coordination_user = mixer.blend(User, user_type='coordination')
client = mixer.blend(Client)
# A flag de ortografia é opcional; default False
mixer.blend(
    ClientQuestionsConfiguration,
    client=client,
    block_approval_with_pending_spelling=False,
)
```

**Permissões necessárias:**
- `user_type == 'coordination'` (ou acesso equivalente)
- Pertencer ao `Client` correto

## 3. Seletores DOM e Ações

### Toggle "Revisores específicos podem editar questões no período de revisão"

| Elemento | Seletor | Descrição |
|----------|---------|-----------|
| Checkbox | `input[name="reviewers_can_edit_questions"]` | Toggle principal |
| Label | `label[for="id_reviewers_can_edit_questions"]` | Texto do toggle |
| Help text | `label[for="id_reviewers_can_edit_questions"] + p` | Texto de ajuda abaixo |

### Toggle "Professores coordenadores podem editar questões de outros professores"

| Elemento | Seletor | Descrição |
|----------|---------|-----------|
| Checkbox | `input[name="teachers_coordinations_can_edit_questions"]` | Toggle principal |
| Label | `label[for="id_teachers_coordinations_can_edit_questions"]` | Texto do toggle |

### Toggle "Sugestão ortográfica pendente impede aprovar a questão" (CU-86akt81t1)

| Elemento | Seletor | Descrição |
|----------|---------|-----------|
| Checkbox | `input[name="block_approval_with_pending_spelling"]` | Toggle principal; default `False`. |
| Label | `label[for="id_block_approval_with_pending_spelling"]` | Texto: `Sugestão ortográfica pendente impede aprovar a questão`. |
| Help text | `label[for="id_block_approval_with_pending_spelling"] + p` | Explica que o bloqueio é da questão, nunca do caderno, e que desligado a sugestão só informa. |

- Ligado: a questão com sugestão ortográfica pendente não pode ser aprovada até cada sugestão ser aplicada ou ignorada (backend bloqueia; UI mostra o botão desabilitado).
- Desligado: a sugestão é apenas informativa.
- A regra vale para o cliente dono do caderno (`Exam` → coordenação → unidade → cliente).

### Botão Salvar

| Elemento | Seletor | Descrição |
|----------|---------|-----------|
| Botão | `button[type="submit"]` | Botão de salvar formulário |

## 4. API Routes

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/membros/questoes/configuracoes` | GET | Renderiza formulário de configurações |
| `/membros/questoes/configuracoes` | POST | Salva configurações |

## 5. Complex Database Entities

- `Client` — cliente/tenant
- `ClientQuestionsConfiguration` — configurações de questões do cliente
  - `reviewers_can_edit_questions` (boolean, default=False)
  - `teachers_coordinations_can_edit_questions` (boolean, default=False)
  - `block_approval_with_pending_spelling` (boolean, default=False) — liga o bloqueio de aprovação por sugestão ortográfica pendente.
