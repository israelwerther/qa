#!/usr/bin/env python3
"""
Servidor HTTP autônomo e interativo para Checklist de QA — Lize Edu.
Acervo de QA — .ai_qa_acervo/scripts/checklist_server.py

Permite que o desenvolvedor ou QA marque os itens do Plano de Testes
diretamente pelo navegador com um clique, sincronizando em tempo real
com o arquivo .md no disco, sem nenhuma dependência de chat de IA.
"""

import http.server
import json
import re
import os
import sys
import argparse
import subprocess
import glob

PORT = 8002
ACERVO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QA_PLANS_DIR = os.path.join(ACERVO_DIR, "QA Plans")


def get_current_git_branch():
    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return ""


def find_active_qa_plan(explicit_file=None):
    if explicit_file and os.path.isfile(explicit_file):
        return os.path.abspath(explicit_file)

    # 1. Tenta encontrar plano pelo nome da branch atual
    branch = get_current_git_branch()
    clean_branch = re.sub(r'^(feat|fix|chore|hotfix)/', '', branch)
    
    plan_files = glob.glob(os.path.join(QA_PLANS_DIR, "*.md"))
    if not plan_files:
        return None

    if clean_branch:
        for p in plan_files:
            if clean_branch in os.path.basename(p):
                return p
        # Tenta pelo ID ClickUp (ex.: CU-86ak8r20g ou 86ak8r20g)
        m = re.search(r'(CU-[a-zA-Z0-9]+|[0-9][a-zA-Z0-9]{7,})', branch)
        if m:
            task_id = m.group(1).replace('CU-', '')
            for p in plan_files:
                if task_id in os.path.basename(p):
                    return p

    # 2. Se não encontrou pelo branch, pega o mais recentemente modificado
    plan_files.sort(key=os.path.getmtime, reverse=True)
    return plan_files[0]


class ChecklistHandler(http.server.BaseHTTPRequestHandler):
    plan_path = None

    def log_message(self, format, *args):
        pass  # Silencia logs padrão do HTTP server

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            if not self.plan_path or not os.path.isfile(self.plan_path):
                self.send_error(404, "Plano de testes não encontrado.")
                return

            with open(self.plan_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            items = []
            total = 0
            checked = 0
            current_section = "Roteiro de Testes"
            current_scenario = ""

            for idx, line in enumerate(lines):
                s_strip = line.strip()
                if s_strip.startswith("### "):
                    current_section = s_strip.replace("### ", "").strip()
                elif s_strip.startswith("#### "):
                    current_scenario = s_strip.replace("#### ", "").strip()

                m = re.match(r"^(\s*-\s*\[)([ xX])(\]\s*)(.*)$", line)
                if m:
                    if "O arquivo de mapeamento foi nomeado" in line:
                        continue
                    is_done = m.group(2).lower() == "x"
                    total += 1
                    if is_done:
                        checked += 1
                    items.append({
                        "line": idx,
                        "checked": is_done,
                        "text": m.group(4).strip(),
                        "section": current_section,
                        "scenario": current_scenario
                    })

            percent = int((checked / total * 100)) if total > 0 else 0
            plan_name = os.path.basename(self.plan_path)

            cards_html = ""
            last_section = None
            last_scenario = None

            for it in items:
                sec = it["section"]
                scen = it["scenario"]

                if sec != last_section:
                    if last_section is not None:
                        cards_html += "</div>"
                    cards_html += f'<div class="section-card"><div class="section-title">{sec}</div>'
                    last_section = sec
                    last_scenario = None

                if scen and scen != last_scenario:
                    cards_html += f'<div class="scenario-title">{scen}</div>'
                    last_scenario = scen

                chk = "checked" if it["checked"] else ""
                clean_text = it["text"].replace("`", "").replace("**", "").replace('"', "&quot;")
                cards_html += f'''
    <label class="item" onclick="toggleItem({it['line']}, this, event)">
      <input type="checkbox" {chk} onclick="event.stopPropagation(); toggleItem({it['line']}, this.parentElement, event)">
      <span class="item-text">{clean_text}</span>
    </label>'''

            if last_section is not None:
                cards_html += "</div>"

            html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QA Checklist Interativo — Lize Edu</title>
<style>
  :root {{ --primary: #EA580C; --bg: #0F172A; --card: #1E293B; --text: #F8FAFC; --muted: #94A3B8; --border: #334155; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 24px; display: flex; justify-content: center; }}
  .container {{ max-width: 860px; width: 100%; }}
  .header {{ background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 20px 24px; margin-bottom: 24px; position: sticky; top: 16px; z-index: 10; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); backdrop-filter: blur(12px); }}
  .plan-subtitle {{ font-size: 12px; color: var(--muted); margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .title {{ margin: 0 0 8px 0; font-size: 18px; font-weight: 700; color: #fff; display: flex; justify-content: space-between; align-items: center; }}
  .badge {{ background: rgba(234, 88, 12, 0.2); color: #FB923C; border: 1px solid rgba(234, 88, 12, 0.4); padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }}
  .progress-bar-bg {{ background: var(--border); height: 8px; border-radius: 999px; overflow: hidden; margin-top: 12px; }}
  .progress-bar-fill {{ background: linear-gradient(90deg, #F97316, #EA580C); height: 100%; width: {percent}%; transition: width 0.25s ease; }}
  .stats {{ font-size: 13px; color: var(--muted); margin-top: 10px; display: flex; justify-content: space-between; }}
  .section-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 18px; }}
  .section-title {{ font-size: 13px; font-weight: 700; color: #FB923C; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }}
  .scenario-title {{ font-size: 14px; font-weight: 600; color: #E2E8F0; margin: 16px 0 8px 0; border-left: 3px solid var(--primary); padding-left: 8px; }}
  .item {{ display: flex; align-items: flex-start; gap: 12px; padding: 10px 12px; border-radius: 8px; transition: background 0.15s; cursor: pointer; user-select: none; margin-bottom: 4px; }}
  .item:hover {{ background: rgba(255, 255, 255, 0.05); }}
  .item input[type="checkbox"] {{ appearance: none; width: 20px; height: 20px; border: 2px solid #64748B; border-radius: 6px; cursor: pointer; position: relative; margin-top: 2px; flex-shrink: 0; transition: all 0.15s; background: transparent; }}
  .item input[type="checkbox"]:checked {{ background: var(--primary); border-color: var(--primary); }}
  .item input[type="checkbox"]:checked::after {{ content: "✓"; color: white; position: absolute; top: -1px; left: 4px; font-size: 14px; font-weight: bold; }}
  .item-text {{ font-size: 14px; line-height: 1.5; color: #CBD5E1; transition: color 0.15s; }}
  .item input[type="checkbox"]:checked ~ .item-text {{ color: #64748B; text-decoration: line-through; }}
  .footer-hint {{ text-align: center; color: var(--muted); font-size: 12px; margin-top: 28px; padding-bottom: 40px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="plan-subtitle">📄 {plan_name}</div>
    <div class="title">
      <span>Checklist Interativo de QA</span>
      <span class="badge" id="badge-pct">{percent}% Concluído</span>
    </div>
    <div class="progress-bar-bg">
      <div class="progress-bar-fill" id="p-bar"></div>
    </div>
    <div class="stats">
      <span id="stats-txt">{checked} de {total} itens marcados</span>
      <span>⚡ Sincronizado com o arquivo .md</span>
    </div>
  </div>
  <div id="list">
    {cards_html}
  </div>
  <div class="footer-hint">✨ Cada clique atualiza o arquivo markdown no disco em tempo real.</div>
</div>
<script>
let total = {total};
let checked = {checked};

function toggleItem(line, el, ev) {{
  const chk = el.querySelector('input[type="checkbox"]');
  if (ev.target !== chk) {{
    chk.checked = !chk.checked;
  }}
  const isChecked = chk.checked;
  if (isChecked) {{ checked++; }} else {{ checked--; }}
  updateProgress();

  fetch('/toggle', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ line: line, checked: isChecked }})
  }}).catch(err => console.error(err));
}}

function updateProgress() {{
  const pct = Math.round((checked / total) * 100);
  document.getElementById('badge-pct').innerText = pct + '% Concluído';
  document.getElementById('p-bar').style.width = pct + '%';
  document.getElementById('stats-txt').innerText = checked + ' de ' + total + ' itens marcados';
}}
</script>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/toggle":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            target_line = data.get("line")
            target_checked = data.get("checked")

            with open(self.plan_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if 0 <= target_line < len(lines):
                line = lines[target_line]
                if target_checked:
                    new_line = re.sub(r"^((\s*-\s*\[)[\s](\]))", r"\g<2>x\g<3>", line)
                else:
                    new_line = re.sub(r"^((\s*-\s*\[)[xX](\]))", r"\g<2> \g<3>", line)
                lines[target_line] = new_line
                with open(self.plan_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def main():
    parser = argparse.ArgumentParser(description="Servidor de Checklist Interativo de QA.")
    parser.add_argument("-f", "--file", help="Caminho do arquivo de plano de testes .md")
    parser.add_argument("-p", "--port", type=int, default=PORT, help=f"Porta HTTP (padrão: {PORT})")
    args = parser.parse_args()

    plan_path = find_active_qa_plan(args.file)
    if not plan_path:
        print("❌ Nenhum arquivo de plano de testes encontrado em .ai_qa_acervo/QA Plans/.")
        sys.exit(1)

    ChecklistHandler.plan_path = plan_path

    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), ChecklistHandler)
    print("=" * 60)
    print("🚀 SERVIDO DE CHECKLIST INTERATIVO DE QA")
    print("=" * 60)
    print(f"📄 Plano Ativo: {os.path.basename(plan_path)}")
    print(f"🔗 URL:         http://127.0.0.1:{args.port}/")
    print("=" * 60)
    server.serve_forever()


if __name__ == "__main__":
    main()
