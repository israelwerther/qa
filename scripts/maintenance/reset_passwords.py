#!/usr/bin/env python
"""
Resetador de Senhas e Acessos para QA (Lize Edu)
Local: .ai_qa_acervo/scripts/maintenance/reset_passwords.py

Reseta senhas de usuários para acesso em ambientes locais de teste:
- Define senha padrão ('123456' ou informada)
- Desativa obrigatoriedade de troca de senha (must_change_password=False)
- Habilita acesso ao app do aluno (can_access_app=True)
- Desativa 2FA e obrigatoriedade de login Google nos clientes
- Limpa sessões ativas para login limpo
"""

import os
import sys
import argparse

# Setup dinâmico do ambiente Django
current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir != '/' and not os.path.exists(os.path.join(current_dir, 'manage.py')):
    current_dir = os.path.dirname(current_dir)
BASE_DIR = current_dir
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fiscallizeon.settings')

import django
django.setup()

from django.db.models import Q
from django.contrib.sessions.models import Session
from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client


def reset_passwords(password='123456', user_filter=None, keep_2fa=False, keep_sessions=False):
    print("=" * 60)
    print(" 🔑 RESET DE SENHAS E ACESSOS PARA QA (Lize Edu)")
    print("=" * 60)

    # 1. Reset de Usuário(s)
    if user_filter:
        users_qs = User.objects.filter(Q(username__iexact=user_filter) | Q(email__iexact=user_filter))
        count = users_qs.count()
        if count == 0:
            print(f"❌ Nenhum usuário encontrado com username/email: '{user_filter}'")
            return False
        
        for u in users_qs:
            u.set_password(password)
            u.must_change_password = False
            u.can_access_app = True
            u.save()
        print(f"✅ Senha atualizada para {count} usuário(s) com filtro '{user_filter}'.")
    else:
        # Gera o hash uma vez e aplica em lote via bulk update
        sample = User.objects.first()
        if not sample:
            print("❌ Nenhum usuário cadastrado no banco de dados.")
            return False
        
        sample.set_password(password)
        hashed_password = sample.password

        updated_count = User.objects.all().update(
            password=hashed_password,
            must_change_password=False,
            can_access_app=True
        )
        print(f"✅ Senha atualizada em lote para TODOS os {updated_count} usuários.")

    print(f"🔑 Nova senha definida: '{password}'")

    # 2. Desativação de 2FA e Google Login obrigatório
    if not keep_2fa:
        client_count = Client.objects.all().update(
            allow_login_only_google=False,
            two_factor_enabled=False
        )
        print(f"🛡️  2FA e login exclusivo Google desativados em {client_count} clientes.")
    else:
        print("ℹ️  Configurações de 2FA/Google mantidas (--keep-2fa).")

    # 3. Limpeza de Sessões
    if not keep_sessions:
        deleted_sessions, _ = Session.objects.all().delete()
        print(f"🧹 {deleted_sessions} sessões ativas limpas.")
    else:
        print("ℹ️  Sessões mantidas (--keep-sessions).")

    # 4. Amostra de contas disponíveis para teste
    print("-" * 60)
    print("👥 Contas principais prontas para acesso:")
    sample_users = User.objects.filter(
        Q(is_superuser=True) |
        Q(email__icontains='admin') |
        Q(email__icontains='coord') |
        Q(email__icontains='teacher') |
        Q(username='fiscallize_geral')
    ).values('username', 'email')[:6]

    for su in sample_users:
        ident = su['email'] or su['username']
        print(f"   • {ident:<35} | Senha: {password}")

    print("=" * 60)
    print("🎉 Pronto! Você já pode fazer login normalmente na interface.")
    print("=" * 60)
    return True


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Resetador de Senhas e Acessos para Ambientes de QA (Lize Edu)"
    )
    parser.add_argument(
        '-p', '--password',
        type=str,
        default='123456',
        help="Nova senha a ser definida (padrão: 123456)"
    )
    parser.add_argument(
        '-u', '--user',
        type=str,
        default=None,
        help="Username ou e-mail específico para resetar (se omitido, reseta todos)"
    )
    parser.add_argument(
        '--keep-2fa',
        action='store_true',
        help="Não alterar configurações de 2FA e login Google dos clientes"
    )
    parser.add_argument(
        '--keep-sessions',
        action='store_true',
        help="Não encerrar as sessões ativas existentes"
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    reset_passwords(
        password=args.password,
        user_filter=args.user,
        keep_2fa=args.keep_2fa,
        keep_sessions=args.keep_sessions,
    )
