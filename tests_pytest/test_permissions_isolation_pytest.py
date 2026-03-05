"""
Testes de isolamento multi-tenant para permissions.
Migrado de: permissions/tests/test_api_isolation.py
"""
import pytest
from rest_framework import status
from organizations.models import Membership
from permissions.models import Permission


@pytest.mark.api
class TestPermissionsAPIIsolation:
    """Testes de isolamento multi-tenant para permissões."""

    @pytest.fixture
    def multi_permission_setup(
        self, user_factory, org_factory, membership_factory, team_factory, permission_factory
    ):
        """
        Setup de cenário multi-permission:
        - User A (admin) na Org A com Team A e Perm A
        - User B (admin) na Org B com Team B e Perm B
        - User C (member) na Org A
        """
        # User A + Org A
        user_a = user_factory(
            username="usera-permissions",
            email="a-permissions@test.com",
            password="password123"
        )
        org_a = org_factory(
            name="Org A",
            slug="org-a-permissions",
            owner=user_a
        )
        membership_factory(
            user=user_a,
            organization=org_a,
            role=Membership.Role.ADMIN
        )

        # User C em Org A (para receber permissão)
        user_c = user_factory(
            username="userc-permissions",
            email="c-permissions@test.com",
            password="password123"
        )
        membership_factory(
            user=user_c,
            organization=org_a,
            role=Membership.Role.MEMBER
        )

        # Team A em Org A
        team_a = team_factory(name="Team A", organization=org_a)

        # Permissão: User C tem acesso à Org A
        perm_a = permission_factory(
            subject_user=user_c,
            resource_type=Permission.ResourceType.ORGANIZATION,
            resource_id=org_a.id,
            role=Permission.Role.VIEW,
            granted_by=user_a
        )

        # User B + Org B
        user_b = user_factory(
            username="userb-permissions",
            email="b-permissions@test.com",
            password="password123"
        )
        org_b = org_factory(
            name="Org B",
            slug="org-b-permissions",
            owner=user_b
        )
        membership_factory(
            user=user_b,
            organization=org_b,
            role=Membership.Role.ADMIN
        )

        # Team B em Org B
        team_b = team_factory(name="Team B", organization=org_b)

        # Permissão: Team B tem acesso à Org B
        perm_b = permission_factory(
            subject_team=team_b,
            resource_type=Permission.ResourceType.ORGANIZATION,
            resource_id=org_b.id,
            role=Permission.Role.EDIT,
            granted_by=user_b
        )

        return {
            "user_a": user_a, "org_a": org_a, "team_a": team_a, "perm_a": perm_a,
            "user_b": user_b, "org_b": org_b, "team_b": team_b, "perm_b": perm_b,
            "user_c": user_c,
        }

    @staticmethod
    def _items(response):
        """Extrai lista de items da resposta (suporta paginação)."""
        data = response.data
        return data.get("results", data) if isinstance(data, dict) else data

    def test_01_user_lists_only_org_permissions(
        self, api_client, multi_permission_setup, org_headers_factory
    ):
        """
        [Permissions/List] User A deve ver apenas permissões da Org A.
        
        Valida:
        - Isolamento de permissões entre organizações
        - User A vê apenas permissões da Org A
        """
        user_a = multi_permission_setup["user_a"]
        org_a = multi_permission_setup["org_a"]
        perm_a = multi_permission_setup["perm_a"]
        perm_b = multi_permission_setup["perm_b"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get("/api/v1/permissions/", **headers)

        assert response.status_code == status.HTTP_200_OK, (
            f"Listagem de permissões: esperado HTTP 200, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

        perms = self._items(response)
        org_a_perm_ids = [p["id"] for p in perms if p.get("resource_type") == "organization"]

        assert perm_a.id in org_a_perm_ids, (
            f"User A deveria ver Perm A. perms={org_a_perm_ids}"
        )
        assert perm_b.id not in org_a_perm_ids, (
            f"User A não deveria ver Perm B. perms={org_a_perm_ids}"
        )

    def test_02_anon_cannot_list_permissions(self, api_client):
        """
        [Auth] Usuário não autenticado deve receber 401.
        
        Valida:
        - Endpoints de permissions requerem autenticação
        """
        response = api_client.get("/api/v1/permissions/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Acesso sem autenticação: esperado HTTP 401, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_03_missing_organization_header_returns_400(
        self, api_client, multi_permission_setup, jwt_token_factory
    ):
        """
        [Header Validation] Requisição sem X-Organization-ID deve retornar 400.
        
        Valida:
        - Header X-Organization-ID é obrigatório
        """
        user_a = multi_permission_setup["user_a"]
        token = jwt_token_factory(user_a)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        response = api_client.get("/api/v1/permissions/", **headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            f"Header X-Organization-ID ausente: esperado HTTP 400, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_04_unauthorized_organization_returns_403(
        self, api_client, multi_permission_setup, jwt_token_factory
    ):
        """
        [Header Validation] User A não é membro de Org B, deve retornar 403.
        
        Valida:
        - Usuários não podem acessar orgs às quais não pertencem
        """
        user_a = multi_permission_setup["user_a"]
        org_b = multi_permission_setup["org_b"]
        token = jwt_token_factory(user_a)
        headers = {
            "HTTP_AUTHORIZATION": f"Bearer {token}",
            "HTTP_X_ORGANIZATION_ID": str(org_b.id),  # User A não é membro de Org B
        }

        response = api_client.get("/api/v1/permissions/", **headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN, (
            f"User não autorizado para org especificada: esperado HTTP 403, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_05_create_org_permission_enforces_active_resource(
        self, api_client, multi_permission_setup, org_headers_factory
    ):
        """
        [Permissions/Create] resource_id para organização deve ser forçado para org ativa.
        
        Valida:
        - O resource_id do request body é sobrescrito pelo resource_id da org do header
        - Permission sempre criada com resource_id da org ativa
        """
        user_a = multi_permission_setup["user_a"]
        org_a = multi_permission_setup["org_a"]
        org_b = multi_permission_setup["org_b"]
        user_c = multi_permission_setup["user_c"]
        headers = org_headers_factory(user=user_a, org=org_a)

        payload = {
            "subject_user": user_c.id,
            "resource_type": Permission.ResourceType.ORGANIZATION,
            "resource_id": org_b.id,  # Tenta enviar org_b
            "role": Permission.Role.MANAGE,
        }
        response = api_client.post("/api/v1/permissions/", payload, format="json", **headers)

        assert response.status_code == status.HTTP_201_CREATED, (
            f"Criação de permissão com resource_id forçado: esperado HTTP 201, "
            f"recebido {response.status_code}. Payload={response.data}"
        )
        assert response.data["resource_id"] == org_a.id, (
            f"Permission deveria estar na Org A (header), não na Org B (payload). "
            f"resource_id={response.data.get('resource_id')}"
        )
