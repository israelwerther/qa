#!/usr/bin/env python3
"""
Script de Smoke Test do Playwright para QA no Lize Edu.
Testa a conectividade com a aplicação local, renderização do navegador e geração de evidência visual.
"""
import argparse
import os
import sys
import time

def run_smoke_test(url: str, output_path: str, headless: bool = True):
    start_time = time.time()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    print(f"🔍 Iniciando Smoke Test do Playwright...")
    print(f"🌐 Alvo: {url}")
    print(f"📸 Evidência esperada em: {output_path}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Erro: Playwright não encontrado no ambiente Python atual.")
        print("Execute usando o venv do projeto: ./venv/bin/python .ai_qa_acervo/scripts/smoke/playwright_smoke.py")
        sys.exit(1)

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=headless)
            except Exception as launch_err:
                if "Executable doesn't exist" in str(launch_err) or "playwright install" in str(launch_err):
                    print("⚠️ Navegador Chromium não encontrado. Instalando automaticamente via playwright...")
                    import subprocess
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                    browser = p.chromium.launch(headless=headless)
                else:
                    raise launch_err

            context = browser.new_context(viewport={"width": 1280, "height": 720})
            page = context.new_page()

            response = page.goto(url, wait_until="networkidle", timeout=15000)
            status_code = response.status if response else "N/A"

            page.wait_for_selector("body", timeout=5000)
            page.screenshot(path=output_path, full_page=False)

            title = page.title()
            browser.close()

            elapsed = round(time.time() - start_time, 2)
            print(f"✅ Smoke Test concluído com sucesso em {elapsed}s!")
            print(f"📄 Título da Página: {title}")
            print(f"📡 Status HTTP: {status_code}")
            print(f"🖼️ Screenshot salvo: {output_path}")
            return True
    except Exception as e:
        print(f"❌ Falha durante a execução do Playwright: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Smoke Test do Playwright para QA Lize Edu")
    parser.add_argument("-u", "--url", default="http://127.0.0.1:8000/conta/entrar/", help="URL para validação (default: login local)")
    parser.add_argument("-o", "--output", default=".ai_qa_acervo/evidencias/mcp_health.png", help="Caminho do screenshot de saída")
    parser.add_argument("--headed", action="store_true", help="Executar com navegador visível")

    args = parser.parse_args()
    success = run_smoke_test(url=args.url, output_path=args.output, headless=not args.headed)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
