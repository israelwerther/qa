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
mixer.blend(ClientQuestionsConfiguration, client=client)
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
