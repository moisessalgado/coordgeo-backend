"""
Testes de isolamento multi-tenant para endpoints de usuários.
Migrado de: accounts/tests/test_api_isolation.py
"""
import pytest
from rest_framework import status
from organizations.models import Membership


@pytest.mark.api
class TestAccountsAPIIsolation:
    """Testes de isolamento multi-tenant para o endpoint de usuários."""

    @pytest.fixture
    def multi_tenant_setup(
        self, user_factory, org_factory, membership_factory
    ):
        """
        Setup de cenário multi-tenant:
        - User A (admin) e User C (member) na Org A
        - User B (admin) na Org B
        """
        # User A na Org A
        user_a = user_factory(
            username="usera-accounts",
            email="a-accounts@test.com",
            password="password123"
        )
        org_a = org_factory(
            name="Org A",
            slug="org-a-accounts",
            owner=user_a
        )
        membership_factory(
            user=user_a,
            organization=org_a,
            role=Membership.Role.ADMIN
        )

        # User B na Org B
        user_b = user_factory(
            username="userb-accounts",
            email="b-accounts@test.com",
            password="password123"
        )
        org_b = org_factory(
            name="Org B",
            slug="org-b-accounts",
            owner=user_b
        )
        membership_factory(
            user=user_b,
            organization=org_b,
            role=Membership.Role.ADMIN
        )

        # User C como membro da Org A
        user_c = user_factory(
            username="userc-accounts",
            email="c-accounts@test.com",
            password="password123"
        )
        membership_factory(
            user=user_c,
            organization=org_a,
            role=Membership.Role.MEMBER
        )

        return {
            "user_a": user_a,
            "org_a": org_a,
            "user_b": user_b,
            "org_b": org_b,
            "user_c": user_c,
        }

    @staticmethod
    def _items(response):
        """Extrai lista de items da resposta (suporta paginação)."""
        data = response.data
        return data.get("results", data) if isinstance(data, dict) else data

    def test_01_user_lists_coworkers_from_same_org(
        self, api_client, multi_tenant_setup, org_headers_factory
    ):
        """
        [Users/List] User A deve ver User C (mesma org), não User B.
        
        Valida:
        - Isolamento multi-tenant: usuários só veem colegas da mesma org
        - User A vê a si mesmo e User C (ambos na Org A)
        - User A não vê User B (Org B)
        """
        user_a = multi_tenant_setup["user_a"]
        org_a = multi_tenant_setup["org_a"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get("/api/v1/users/", **headers)

        assert response.status_code == status.HTTP_200_OK, (
            f"Listagem de usuários: esperado HTTP 200, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

        usernames = [u["username"] for u in self._items(response)]

        assert "usera-accounts" in usernames, (
            f"User A deveria listar a si mesmo. users={usernames}"
        )
        assert "userc-accounts" in usernames, (
            f"User A deveria ver User C (colega). users={usernames}"
        )
        assert "userb-accounts" not in usernames, (
            f"User A não deveria ver User B (outro tenant). users={usernames}"
        )

    def test_02_anon_cannot_list_users(self, api_client, multi_tenant_setup):
        """
        [Auth] Usuário não autenticado deve receber 401.
        
        Valida:
        - Endpoints requerem autenticação JWT
        - Resposta 401 UNAUTHORIZED para requisições anônimas
        """
        org_a = multi_tenant_setup["org_a"]
        headers = {"HTTP_X_ORGANIZATION_ID": str(org_a.id)}
        
        response = api_client.get("/api/v1/users/", **headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Acesso sem autenticação: esperado HTTP 401, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_03_missing_organization_header(
        self, api_client, multi_tenant_setup, jwt_token_factory
    ):
        """
        [Header] Requisição sem X-Organization-ID deve retornar 400.
        
        Valida:
        - Header X-Organization-ID é obrigatório
        - Resposta 400 BAD_REQUEST com mensagem indicando header ausente
        """
        user_a = multi_tenant_setup["user_a"]
        token = jwt_token_factory(user_a)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        
        response = api_client.get("/api/v1/users/", **headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            f"Header ausente: esperado HTTP 400, "
            f"recebido {response.status_code}. Payload={response.data}"
        )
        
        error_detail = str(response.data.get("detail", ""))
        assert "X-Organization-ID" in error_detail, (
            f"Mensagem de erro deveria mencionar X-Organization-ID. "
            f"Detail: {error_detail}"
        )

    def test_04_unauthorized_organization_access(
        self, api_client, multi_tenant_setup, jwt_token_factory
    ):
        """
        [Org] User A não pode acessar com X-Organization-ID de Org B.
        
        Valida:
        - Usuários não podem acessar dados de organizações às quais não pertencem
        - Resposta 403 FORBIDDEN quando user tenta acessar org não autorizada
        """
        user_a = multi_tenant_setup["user_a"]
        org_b = multi_tenant_setup["org_b"]
        token = jwt_token_factory(user_a)
        headers = {
            "HTTP_AUTHORIZATION": f"Bearer {token}",
            "HTTP_X_ORGANIZATION_ID": str(org_b.id),  # user_a não é membro
        }
        
        response = api_client.get("/api/v1/users/", **headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN, (
            f"Org não autorizada: esperado HTTP 403, "
            f"recebido {response.status_code}. Payload={response.data}"
        )
