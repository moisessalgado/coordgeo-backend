#!/usr/bin/env python
"""
Script de teste para validar endpoints implementados para frontend.

Testa:
1. Endpoint JWT token (/api/v1/token/)
2. Endpoint de bootstrap de organizações (/api/v1/user/organizations/)
3. Configuração de CORS
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Adicionar 'testserver' ao ALLOWED_HOSTS se não estiver lá
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from organizations.models import Organization, Membership
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def test_jwt_endpoint():
    """Testa se endpoint JWT está disponível e funciona"""
    print("\n✓ Testando JWT Token Endpoint (v1 + legado)...")
    
    # Limpar usuários de testes anteriores para evitar duplicatas
    User.objects.filter(email='test@example.com').delete()
    
    # Criar usuário de teste
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    client = APIClient()
    
    # Tentar obter token (canônico v1)
    response = client.post('/api/v1/token/', {
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    if response.status_code == 200:
        print(f"  ✓ POST /api/v1/token/ retornou status 200")
        print(f"  ✓ Response contém 'access' token: {'access' in response.json()}")
        print(f"  ✓ Response contém 'refresh' token: {'refresh' in response.json()}")
        legacy_response = client.post('/api/token/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        if legacy_response.status_code == 200:
            print(f"  ✓ POST /api/token/ (legado) retornou status 200")
            return True
        print(f"  ✗ POST /api/token/ (legado) retornou status {legacy_response.status_code}")
        return False
    else:
        print(f"  ✗ POST /api/v1/token/ retornou status {response.status_code}")
        print(f"  Response: {response.json()}")
        return False


def test_user_organizations_endpoint():
    """Testa se endpoint de organizações do usuário está disponível"""
    print("\n✓ Testando User Organizations Bootstrap Endpoint (v1 + legado)...")
    
    # Limpar dados de testes anteriores
    User.objects.filter(email='test2@example.com').delete()
    Organization.objects.filter(slug='test-org').delete()
    
    # Criar usuário, organização e membership
    user = User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123'
    )
    
    org = Organization.objects.create(
        name='Test Org',
        slug='test-org',
        owner=user  # Adicionar owner
    )
    
    Membership.objects.create(
        user=user,
        organization=org,
        role='ADMIN'
    )
    
    # Autenticar via JWT
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    # Chamar endpoint (sem X-Organization-ID header)
    response = client.get('/api/v1/user/organizations/')
    
    if response.status_code == 200:
        print(f"  ✓ GET /api/v1/user/organizations/ retornou status 200")
        orgs = response.json()
        print(f"  ✓ Response contém {len(orgs)} organização(ões)")
        if isinstance(orgs, list) and len(orgs) > 0:
            print(f"  ✓ Primeira org: {orgs[0].get('name', 'N/A')}")
        legacy_response = client.get('/api/user/organizations/')
        if legacy_response.status_code == 200:
            print(f"  ✓ GET /api/user/organizations/ (legado) retornou status 200")
            return True
        print(f"  ✗ GET /api/user/organizations/ (legado) retornou status {legacy_response.status_code}")
        return False
    else:
        print(f"  ✗ GET /api/v1/user/organizations/ retornou status {response.status_code}")
        print(f"  Response: {response.json()}")
        return False


def test_cors_configuration():
    """Testa se CORS está configurado"""
    print("\n✓ Verificando Configuração CORS...")
    
    from django.conf import settings
    
    if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
        print(f"  ✓ CORS_ALLOWED_ORIGINS configurado")
        print(f"    Origins: {settings.CORS_ALLOWED_ORIGINS}")
    else:
        print(f"  ✗ CORS_ALLOWED_ORIGINS não configurado")
        return False
    
    if hasattr(settings, 'CORS_ALLOW_CREDENTIALS'):
        print(f"  ✓ CORS_ALLOW_CREDENTIALS = {settings.CORS_ALLOW_CREDENTIALS}")
    else:
        print(f"  ✗ CORS_ALLOW_CREDENTIALS não configurado")
        return False
    
    if 'corsheaders' in settings.INSTALLED_APPS:
        print(f"  ✓ corsheaders em INSTALLED_APPS")
    else:
        print(f"  ✗ corsheaders não em INSTALLED_APPS")
        return False
    
    return True


def test_pagination_configuration():
    """Testa se paginação está configurada"""
    print("\n✓ Verificando Configuração de Paginação...")
    
    from django.conf import settings
    
    rest_config = settings.REST_FRAMEWORK
    
    if 'DEFAULT_PAGINATION_CLASS' in rest_config:
        print(f"  ✓ DEFAULT_PAGINATION_CLASS = {rest_config['DEFAULT_PAGINATION_CLASS']}")
    else:
        print(f"  ✗ DEFAULT_PAGINATION_CLASS não configurado")
        return False
    
    if 'PAGE_SIZE' in rest_config:
        print(f"  ✓ PAGE_SIZE = {rest_config['PAGE_SIZE']}")
    else:
        print(f"  ✗ PAGE_SIZE não configurado")
        return False
    
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 TESTE DE ENDPOINTS - FRONTEND PREREQUISITES")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("JWT Token Endpoint", test_jwt_endpoint()))
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        results.append(("JWT Token Endpoint", False))
    
    try:
        results.append(("User Organizations Endpoint", test_user_organizations_endpoint()))
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        results.append(("User Organizations Endpoint", False))
    
    try:
        results.append(("CORS Configuration", test_cors_configuration()))
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        results.append(("CORS Configuration", False))
    
    try:
        results.append(("Pagination Configuration", test_pagination_configuration()))
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        results.append(("Pagination Configuration", False))
    
    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSOU" if passed else "✗ FALHOU"
        print(f"{name:.<40} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓ Todos os testes passaram! Frontend pode começar desenvolvimento.")
        sys.exit(0)
    else:
        print("\n✗ Alguns testes falharam. Verifique os erros acima.")
        sys.exit(1)
