# KI Navegação: Sidebar e Menus Principais

> **Status:** Em construção contínua
> **Objetivo:** Mapear os rótulos REAIS da interface (Sidebar) para os respectivos caminhos/URLs no sistema, eliminando a adivinhação da IA na hora de instruir o QA humano ou criar testes Playwright.

---

## 📚 Menu: Cadernos
*(Mapeado a partir do perfil de Professor/Coordenador)*

Quando o usuário clica no item principal **Cadernos** na barra lateral, o dropdown revela as seguintes opções exatas:

| Rótulo Real na UI (Texto do link) | Ação / Destino Lógico | Observações |
|-----------------------------------|-----------------------|-------------|
| **Todos os cadernos** | Listagem geral de provas/cadernos disponíveis para o perfil. | Acesso primário para visualizar/editar cadernos globais. |
| **Listas de exercícios** | Listagem específica de listas de exercícios (homeworks). | URL geralmente usa `category=homework`. |
| **Solicitações de elaboração** | Fluxo de pedidos de criação de questões/provas. | |
| **Para você revisar** | Cadernos/Questões que aguardam revisão do usuário atual. | |
| **Revisões** | Histórico ou painel geral de revisões. | |

---

## 📝 Menu: Instrumentos Avaliativos
*(Mapeado a partir do perfil de Coordenador)*

| Rótulo Real na UI (Texto do link) | Ação / Destino Lógico | Observações |
|-----------------------------------|-----------------------|-------------|
| **Instrumentos Avaliativos** | Listagem principal de provas da escola (`/provas/?category=exam`). | Rótulo real usado para Coordenadores (o equivalente a "Todos os cadernos"). |

---
*Nota para a IA:* Sempre que encontrar uma divergência entre o nome da View (`exams_list`) e o rótulo da UI, consulte este documento antes de pedir para o usuário clicar em "Provas" ou "Exames".
