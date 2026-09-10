# Mapeamento de Usabilidade: App do Aluno (Header, Branding e Materiais de Estudo)

> **Caminho no Código (`lize-student`):**
> - `src/components/layout/app-header.tsx`
> - `src/components/layout/mobile-header.tsx`
> - `src/components/layout/header-backdrop.tsx`
> - `src/components/study-materials/empty-state.tsx`
> - `src/components/study-materials/filters.tsx`
> - `src/lib/brand-theme.ts`
> - `src/lib/application-copy.ts`

---

## 1. URLs e Navegação
- **Início do Painel do Aluno:** `http://localhost:5173/painel`
- **Minhas Provas:** `http://localhost:5173/painel/minhas-provas`
- **Materiais de Estudo:** `http://localhost:5173/painel/materiais-de-estudo`
- **Pasta da Disciplina:** `http://localhost:5173/painel/materiais-de-estudo?disciplineId=<id>`
- **Admin do Backend (`lizeedu`):** `http://localhost:8000/admin/clients/client/<uuid>/change/`

---

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

### Backend (`lizeedu`):
- O cliente precisa ter o campo `primary_color` preenchido (ex.: `"#1B4DB2"` para teste de cor escura ou `"#FFC700"` para cor clara).
- O payload de `/api/v3/user/` deve retornar `client.primaryColor`.
- Aluno ativo vinculado ao cliente com senha `123456`.

```python
from fiscallizeon.clients.models import Client
from fiscallizeon.accounts.models import User

client = Client.objects.first()
client.primary_color = "#1B4DB2"
client.save()

student = User.objects.filter(client=client, type_profile=User.STUDENT).first()
if student:
    student.set_password("123456")
    student.save()
```

---

## 3. Seletores DOM e Ações

### Header e Branding:
- **Container do Degradê:** `.brand-header`
- **Variável CSS da Cor:** `style="--brand: #RRGGBB"`
- **Classes de Luminância / Contraste:**
  - Conteúdo Claro (para fundos escuros): `.brand-fg-light`
  - Conteúdo Escuro (para fundos claros): `.brand-fg-dark`
- **Wallpaper Fallback:** `img[src*="/backgrounds/bgd"]` (quando `client.primaryColor` é `null`)

### Materiais de Estudo & Empty States:
- **Container de Empty State:** `output.border-dashed`
- **Ação "Voltar para o início" (Pasta Vazia):** `button[aria-label="Voltar para o início"]`
- **Ação "Limpar busca" (Busca Vazia):** `button[aria-label="Limpar busca"]`
- **Ação "Limpar filtros" (Filtros Vazios):** `button[aria-label="Limpar filtros"]`
- **Ação "Ver todos os materiais" (Sem Favoritos):** `button[aria-label="Ver todos os materiais"]`
- **Ação "Tentar novamente" (Erro de Conexão):** `button[aria-label="Tentar novamente"]`

### Copy de Aplicações (Listas de Exercício):
- **Botão Iniciar Exercício:** `button:has-text("iniciar exercício")`
- **Botão Refazer Exercício:** `button:has-text("refazer exercício")`
- **Status Concluído:** `*:has-text("exercício já realizado")`
