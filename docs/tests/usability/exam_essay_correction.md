# Mapeamento de Tela: exam_essay_correction.html (e componentes associados)

> **Nota de Acervo:** Este arquivo é alimentado de forma incremental e colaborativa. Sempre que uma nova funcionalidade for testada nesta tela, o mapeamento de IDs e seletores estáveis deve ser atualizado aqui. O objetivo é criar um repositório centralizado para facilitar a automação via Playwright, sem depender de classes CSS frágeis.

## 1. URLs e Navegação
- **URL da Tela de Correção:** `/provas/<uuid>/redacoes/correcao/?application_student=<uuid>&school_class=<uuid>`
- **Navegação:** Na listagem de redações (`/provas/<exam_id>/redacoes/`), ao clicar em um aluno da lista, o usuário é direcionado para esta tela de correção.

## 2. Pré-requisitos para Automação (Fixtures e Permissões)
> **Acesso ao Módulo (Permissões):** O professor ou coordenador precisa de privilégios e o cliente precisa ter a flag `has_essay_system=True`. Para o Painel Lize AI aparecer, a questão de redação precisa utilizar as `Competências ENEM`.

> **Dica:** Para habilitar a correção com a Lize AI num teste automatizado, é necessário gerar a prova e a redação usando o mixer (ou factories) com a flag correspondente ativada no cliente e a questão de redação configurada corretamente:
```python
from mixer.backend.django import mixer
from fiscallizeon.core.models import Client

# Garantir que o cliente possui o sistema de redação habilitado
client = mixer.blend(Client, has_essay_system=True)

# Outros setups de Exam, ExamQuestion (tipo redação) e ApplicationStudent...
```

## 3. Seletores DOM e Ações

### 3.1. Painel Lize AI e Texto Digitalizado
- **Toggle Texto Digitalizado:** `.digitalized-toggle button:contains("Texto digitalizado")` (botão para alternar a visualização).
- **Toggle Texto Original:** `.digitalized-toggle button:contains("Texto original")` (botão para alternar a visualização).
- **Marcadores de Desvio no Texto (Highlights):** `.lize-ai-mark` (classes como `.is-accepted` indicam o estado aprovado).
- **Linha/Card de Sugestão:** `.lize-ai-suggestion-row`
- **Botão de Aceitar (Check):** `.lize-ai-action-btn.accept`
- **Botão de Rejeitar (X):** `.lize-ai-action-btn.reject`
