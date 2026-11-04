#!/usr/bin/env python3
"""
Script de diagnóstico e remoção segura de colunas residuais (Schema Drift).
Acervo de QA — Lize Edu

Objetivo:
Identificar quando um erro de 'null value in column ... violates not-null constraint'
ou 'column ... does not exist' é causado por resíduo de migrações de OUTRAS branches
locais no PostgreSQL, validar se o campo REALMENTE não pertence à branch atual,
e fornecer (ou executar com autorização explícita) o DROP COLUMN seguro.
"""

import os
import re
import sys
import argparse
import subprocess

# Configura o ambiente Django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fiscallizeon.settings")

# Força DEBUG caso não esteja definido no env
if "DEBUG" not in os.environ or os.environ.get("DEBUG") == "release":
    os.environ["DEBUG"] = "1"

try:
    import django
    django.setup()
    from django.apps import apps
    from django.db import connection
except Exception as e:
    print(f"❌ Erro ao inicializar Django: {e}")
    sys.exit(1)


def get_current_git_branch():
    """Retorna o nome da branch atual do git."""
    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return "desconhecida"


def parse_error_string(error_text):
    """
    Extrai o nome da coluna e da tabela a partir de mensagens de erro do PostgreSQL/Django.
    Exemplos aceitos:
      - null value in column "has_pedagogical_automations" of relation "clients_historicalclient" violates not-null constraint
      - column clients_client.has_pedagogical_automations does not exist
      - has_pedagogical_automations
    """
    column_name = None
    table_name = None

    # Padrão 1: null value in column "XYZ" of relation "ABC"
    m1 = re.search(r'null value in column ["\']?([a-zA-Z0-9_]+)["\']? of relation ["\']?([a-zA-Z0-9_]+)["\']?', error_text)
    if m1:
        return m1.group(1), m1.group(2)

    # Padrão 2: column "XYZ" does not exist
    m2 = re.search(r'column ["\']?([a-zA-Z0-9_]+)["\']? does not exist', error_text)
    if m2:
        return m2.group(1), None

    # Padrão 3: column TABELA.COLUNA
    m3 = re.search(r'column ["\']?([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)["\']?', error_text)
    if m3:
        return m3.group(2), m3.group(1)

    # Se for apenas um identificador direto
    cleaned = error_text.strip().strip('"').strip("'")
    if re.match(r'^[a-zA-Z0-9_]+$', cleaned):
        return cleaned, None

    return None, None


def check_column_in_branch_models(column_name):
    """
    Verifica se a coluna pertence a algum modelo Django da branch atual.
    Retorna uma lista de strings descrevendo os modelos que possuem o campo.
    """
    found_in_models = []
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if hasattr(field, "name") and field.name == column_name:
                found_in_models.append(f"{model._meta.app_label}.{model.__name__} (campo: {field.name})")
            elif hasattr(field, "attname") and field.attname == column_name:
                found_in_models.append(f"{model._meta.app_label}.{model.__name__} (attname: {field.attname})")
    return list(set(found_in_models))


def find_db_tables_with_column(column_name):
    """
    Consulta o catálogo do PostgreSQL para descobrir todas as tabelas
    que contêm essa coluna física no banco de dados.
    """
    tables = []
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name, is_nullable
            FROM information_schema.columns
            WHERE column_name = %s
            AND table_schema = 'public'
            ORDER BY table_name;
        """, [column_name])
        for row in cursor.fetchall():
            tables.append({"table": row[0], "is_nullable": row[1]})
    return tables


def execute_drop_columns(tables_info, column_name):
    """Executa o DROP COLUMN para cada tabela informada."""
    executed = []
    with connection.cursor() as cursor:
        for t in tables_info:
            table = t["table"]
            sql = f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column_name};"
            cursor.execute(sql)
            executed.append(table)
    return executed


def main():
    parser = argparse.ArgumentParser(
        description="Diagnóstico e remoção segura de colunas residuais de Schema Drift (Lize Edu)."
    )
    parser.add_argument(
        "error_text",
        nargs="*",
        help="Mensagem de erro colada do traceback ou o nome direto da coluna."
    )
    parser.add_argument(
        "-c", "--column",
        help="Nome explícito da coluna a verificar."
    )
    parser.add_argument(
        "-e", "--execute",
        action="store_true",
        help="Executar a remoção das colunas residuais no PostgreSQL (requer confirmação se omitido)."
    )

    args = parser.parse_args()

    input_text = " ".join(args.error_text).strip()
    column_name = args.column

    if not column_name:
        if not input_text:
            print("❌ Erro: Informe a mensagem de erro do Postgres ou use --column <nome>.")
            sys.exit(1)
        parsed_col, parsed_tbl = parse_error_string(input_text)
        column_name = parsed_col

    if not column_name:
        print("❌ Não foi possível extrair o nome da coluna a partir do texto informado.")
        sys.exit(1)

    branch = get_current_git_branch()
    print("=" * 70)
    print("🔍 DIAGNÓSTICO DE SCHEMA DRIFT / COLUNAS RESIDUAIS")
    print("=" * 70)
    print(f"📌 Branch Git Atual:  {branch}")
    print(f"📌 Coluna Analisada:   {column_name}")
    print("-" * 70)

    # 1. VERIFICAÇÃO DE SEGURANÇA (A coluna pertence a esta branch?)
    models_with_field = check_column_in_branch_models(column_name)

    if models_with_field:
        print("🛑 ALERTA DE SEGURANÇA MÁXIMA — OPERAÇÃO BLOQUEADA!")
        print(f"A coluna '{column_name}' EXISTE no código da branch atual ({branch}):")
        for m in models_with_field:
            print(f"  • {m}")
        print("-" * 70)
        print("⚠️ Esta coluna NÃO É RESIDUAL! Ela faz parte da implementação desta tarefa.")
        print("O erro ocorreu porque o formulário ou a requisição não preencheu o campo obrigatório.")
        print("NÃO execute DROP COLUMN nesta coluna!")
        print("=" * 70)
        sys.exit(2)

    # 2. Se não está nos models, busca onde ela existe fisicamente no banco
    db_tables = find_db_tables_with_column(column_name)

    if not db_tables:
        print(f"ℹ️ A coluna '{column_name}' não foi encontrada nos modelos da branch nem no banco de dados físico.")
        sys.exit(0)

    print("✅ CONFIRMADO: RESÍDUO DE OUTRA BRANCH (Schema Drift)")
    print(f"O campo '{column_name}' NÃO EXISTE em nenhum modelo da branch atual ({branch}).")
    print(f"Ele está presente apenas no banco de dados local nas seguintes tabelas:")
    for t in db_tables:
        print(f"  • Tabela: {t['table']} (Nullable: {t['is_nullable']})")

    print("-" * 70)
    print("🛠️ Comandos SQL para limpeza:")
    for t in db_tables:
        print(f"  ALTER TABLE {t['table']} DROP COLUMN IF EXISTS {column_name};")
    print("-" * 70)

    # 3. Execução ou Dry-Run
    if args.execute:
        print("🚀 Executando remoção no banco local...")
        executed_tables = execute_drop_columns(db_tables, column_name)
        print("✅ Sucesso! Colunas residuais removidas das tabelas:")
        for tbl in executed_tables:
            print(f"  ✔ {tbl}")
        print("=" * 70)
    else:
        print("💡 Modo de inspeção (dry-run). Nenhuma alteração foi feita no banco.")
        print("Para aplicar a limpeza automaticamente, execute:")
        print(f"  ./venv/bin/python .ai_qa_acervo/scripts/drop_residual_column.py --column {column_name} --execute")
        print("Ou execute os comandos SQL acima no seu dbshell.")
        print("=" * 70)


if __name__ == "__main__":
    main()

