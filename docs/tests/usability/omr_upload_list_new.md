# Mapeamento de Usabilidade: omr_upload_list_new

## 1. URLs e Navegação

| Destino | URL Django | View name | Como navegar |
|---------|-----------|-----------|--------------|
| Lista de envios de gabaritos | `/gabaritos/` | `omr:omr_upload_list` | Menu Gabaritos → "Enviar respostas" |
| Detalhe do envio | `/gabaritos/detalhes/<uuid>/` | `omr:omr_upload_detail` | Clicar no botão "**Resolver**" (quando há pendência) ou "**Detalhes**", ou no selo "**Pendências**" |

> **Nota:** não existe query parameter de filtro. Todos os caminhos de acesso abrem o mesmo detalhe e a mesma organização em abas ("Alunos com erro" / "Alunos finalizados").

## 2. Pré-requisitos para Automação (Fixtures e Permissões)

- **Permissão:** `omr.view_omrupload` (perfis: Coordenação, Professor, Staff)
- **Usuário:** `mixer.blend(User, is_staff=True)` ou coordenador com client `CLOUDLAB`
- **Dados mínimos:**
  - `Client` → `Application` → `Exam` → `OMRUpload` (status=3, com `omr_students` em estados mistos)

```python
# Snippet de setup com Mixer
from mixer.backend.django import mixer
from fiscallizeon.omr.models import OMRUpload
from fiscallizeon.exams.models import Exam
from fiscallizeon.applications.models import Application
from fiscallizeon.core.models import Client
from django.contrib.auth import get_user_model

User = get_user_model()
client = mixer.blend(Client)
user = mixer.blend(User, client=client, is_staff=True)
exam = mixer.blend(Exam, client=client, questions_count=10)
application = mixer.blend(Application, exam=exam, client=client)
upload = mixer.blend(OMRUpload, application=application, client=client, status=3)
```

## 3. Seletores DOM e Ações

### Tabela de envios (`#table-uploads` ou grid equivalente)

| Elemento | Seletor / Descrição | Ação |
|----------|---------------------|------|
| Botão "Resolver" | `<a :id="\`resolve-${omrUpload.id}\`">` com `:href="redirectToUploadDetail(omrUpload.id)"` | Abre detalhe |
| Selo "Pendências" | `<a aria-label="Respostas aguardando correção">` com `:href="redirectToUploadDetail(omrUpload.id)"` | Abre detalhe |
| Botão "Detalhes" | `<button :id="\`details-${omrUpload.id}\`">` | Abre menu/ detalhe |

### Métodos Alpine.js relevantes

- `redirectToUploadDetail(uploadId)` — gera a URL do detalhe (sem parâmetro de filtro).
