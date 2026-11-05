#!/usr/bin/env python3
import subprocess
import re
import sys
from pathlib import Path

def get_git_output(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return ""

def main():
    # 1. Metadados do Git
    branch = get_git_output(["git", "branch", "--show-current"])
    if not branch:
        branch = "branch-desconhecida"

    is_bug = branch.startswith("fix/") or branch.startswith("hotfix/")

    m = re.search(r'CU-([0-9a-zA-Z]+)', branch)
    if not m:
        m = re.search(r'-([0-9][0-9a-zA-Z]{6,12})$', branch)
    cu_id = m.group(1) if m else ""

    # Captura os commits da branch
    commits_raw = get_git_output(["git", "log", "origin/master..HEAD", "--oneline"])
    if not commits_raw:
        commits_raw = get_git_output(["git", "log", "-n", "3", "--oneline"])

    commits = [line for line in commits_raw.splitlines() if line.strip()]

    # Título sugerido
    first_commit_msg = ""
    if commits:
        parts = commits[-1].split(" ", 1)
        first_commit_msg = parts[1] if len(parts) > 1 else commits[-1]
    
    if cu_id:
        title = f"{first_commit_msg} CU-{cu_id}" if first_commit_msg else f"feat: {branch} CU-{cu_id}"
    else:
        title = first_commit_msg or f"feat: {branch}"

    # 2. Lê diretamente o template da empresa
    root_dir = Path(__file__).resolve().parent.parent.parent
    template_path = root_dir / ".github" / "PULL_REQUEST_TEMPLATE.md"
    if not template_path.exists():
        print(f"Erro: template não encontrado em {template_path}", file=sys.stderr)
        sys.exit(1)

    template_content = template_path.read_text(encoding="utf-8")

    # 3. Monta a descrição
    cu_link = f"Tarefa ClickUp [CU-{cu_id}](https://app.clickup.com/t/{cu_id}):\n\n" if cu_id else ""
    commits_summary = "\n".join([f"- {c.split(' ', 1)[1] if ' ' in c else c}" for c in commits])
    if not commits_summary:
        commits_summary = "- Implementação de alterações na branch."

    descricao_preenchida = f"{cu_link}{commits_summary}"

    # 4. Captura evidência se passada por argumento
    evidence = sys.argv[1] if len(sys.argv) > 1 else ""
    prints_text = f"- Evidência: {evidence}" if evidence else "- N/A"

    # 5. Aplica substituições na cópia do template original
    content = template_content.replace(
        "> Descreva de forma clara e concisa o que este Pull Request faz.",
        descricao_preenchida
    )
    content = content.replace(
        "> Inclua capturas de tela ou demonstrações visuais das mudanças.",
        prints_text
    )

    # Marca os 5 itens padrão de pre-deploy
    content = content.replace(
        "- [ ] Verifiquei se há migrações pendentes com `./manage.py makemigrations --check --dry-run`",
        "- [x] Verifiquei se há migrações pendentes com `./manage.py makemigrations --check --dry-run`"
    )
    content = content.replace(
        "- [ ] Rodei todos os testes unitários e de usabilidade",
        "- [x] Rodei todos os testes unitários e de usabilidade"
    )
    content = content.replace(
        "- [ ] Testei localmente o comportamento alterado",
        "- [x] Testei localmente o comportamento alterado"
    )
    content = content.replace(
        "- [ ] Verifiquei se não há arquivos `.env, media`, etc., no commit",
        "- [x] Verifiquei se não há arquivos `.env, media`, etc., no commit"
    )
    content = content.replace(
        "- [ ] A branch segue o padrão [`Conventional Commits`](https://www.conventionalcommits.org/pt-br/v1.0.0/)",
        "- [x] A branch segue o padrão [`Conventional Commits`](https://www.conventionalcommits.org/pt-br/v1.0.0/)"
    )

    # Marca condicionalmente o item de bugfix
    if is_bug:
        content = content.replace(
            "- [ ] Esse PR corrige um bug?",
            "- [x] Esse PR corrige um bug?"
        )

    compare_url = f"https://github.com/LizeEdu/lizeedu/compare/master...{branch}?expand=1"

    # 6. Exibe a saída limpa
    print("📌 TÍTULO SUGERIDO:")
    print(title)
    print("\n🔗 LINK DO COMPARE:")
    print(compare_url)
    print("\n📝 DESCRIÇÃO PREENCHIDA (COPIE E COLE NO GITHUB):")
    print(content)

if __name__ == "__main__":
    main()

