#!/usr/bin/env python3
import urllib.parse
import subprocess
import re
import sys

def get_current_branch():
    res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    return res.stdout.strip()

def main():
    branch = get_current_branch()
    if not branch:
        branch = "fix/exams-unificar-visualizacao-alternativas-revisao-CU-17tu7rpaqj8"
    
    # Check if bugfix
    is_bug = branch.startswith("fix/") or branch.startswith("hotfix/")
    
    # Extract ClickUp ID
    m = re.search(r'CU-([0-9a-zA-Z]+)', branch)
    if not m:
        m = re.search(r'-([0-9][0-9a-zA-Z]{6,12})$', branch)
    cu_id = m.group(1) if m else "17tu7rpaqj8"
    
    title = f"fix(exams): unificar estilo de alternativas na revisao e atualizar estado ao editar CU-{cu_id}"
    bug_check = "[x]" if is_bug else "[ ]"
    
    # We use Setext headings (text followed by dashes) so no '#' is used in the URL query string.
    # This prevents the %23 literal bug caused by GitHub's decodeURI implementation.
    body = f"""🚀 Descrição do PR
-------------------

Correção da tarefa ClickUp [CU-{cu_id}](https://app.clickup.com/t/3120759/{cu_id}):

- **Unificação visual e correção do botão de negrito:** Remove a classe `tw-font-semibold` do contêiner de alternativas no modal de revisão (`modal_review.html`). Com isso, a alternativa correta passa a ter peso de fonte neutro (idêntico à edição completa, diagramação e prova impressa), e o botão "B" do editor inline volta a refletir a aplicação e remoção de negrito imediatamente na tela.
- **Reatividade ao salvar na edição completa:** Atualiza o callback `call(result)` em `exam_request_create_update_new.html` para sincronizar os dados da questão aberta (`selectedExamQuestionReview`) e exibir o toast de confirmação padrão da plataforma (`alertTop`), eliminando a necessidade de atualizar a página (F5).

***

✅ Checklist do Pre-Deploy
---------------------------

Marque os itens que foram verificados **antes de abrir este PR**:

- [x] Verifiquei se há migrações pendentes com `./manage.py makemigrations --check --dry-run`
- [x] Rodei todos os testes unitários e de usabilidade
- [x] Testei localmente o comportamento alterado
- [x] Verifiquei se não há arquivos `.env, media`, etc., no commit
- [x] A branch segue o padrão [`Conventional Commits`](https://www.conventionalcommits.org/pt-br/v1.0.0/)
- {bug_check} Esse PR corrige um bug?

***

📸 Prints / GIFs (se aplicável)
--------------------------------

- Vídeo de reprodução da issue: https://jam.dev/c/f7be4445-e2cf-4779-aaad-f1dd73b8def2
"""

    base_url = f"https://github.com/LizeEdu/lizeedu/compare/master...{branch}"
    encoded_title = urllib.parse.quote(title)
    encoded_body = urllib.parse.quote(body, safe='?')
    
    full_url = f"{base_url}?quick_pull=1&title={encoded_title}&body={encoded_body}"
    print(full_url)
    
    if "--open" in sys.argv:
        try:
            subprocess.Popen(["google-chrome", full_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("🚀 Aberto com sucesso no Google Chrome!")
        except Exception as e:
            print(f"Erro ao abrir Chrome: {e}")

if __name__ == "__main__":
    main()
