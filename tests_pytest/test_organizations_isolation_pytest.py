"""
Testes de isolamento multi-tenant para endpoints de organizations e teams.
Migrado de: organizations/tests/test_api_isolation.py
"""
import pytest
from rest_framework import status
from organizations.models import Membership


@pytest.mark.api
class TestOrganizationsAPIIsolation:
    """Testes de isolamento multi-tenant para endpoints de organizations e teams."""

    @pytest.fixture
    def team_factory(self, db):
        """Factory para criar teams."""
        from organizations.models import Team

        def factory(*, name: str, organization):
            return Team.objects.create(
                name=name,
                organization=organization
            )

        return factory

    @pytest.fixture
    def multi_org_setup(
        self, user_factory, org_factory, membership_factory, team_factory
    ):
        """
        Setup de cenário multi-org:
        - User A (admin) na Org A com Team A
        - User B (admin) na Org B com Team B
        """
        # User A
        user_a = user_factory(
            username="usera-organizations",
            email="a-organizations@test.com",
            password="password123"
        )
        # User B
        user_b = user_factory(
            username="userb-organizations",
            email="b-organizations@test.com",
            password="password123"
        )

        # Organizations
        org_a = org_factory(
            name="Org A",
            slug="org-a-organizations",
            owner=user_a
        )
        org_b = org_factory(
            name="Org B",
            slug="org-b-organizations",
            owner=user_b
        )

        # Memberships
        membership_factory(
            user=user_a,
            organization=org_a,
            role=Membership.Role.ADMIN
        )
        membership_factory(
            user=user_b,
            organization=org_b,
            role=Membership.Role.ADMIN
        )

        # Teams
        team_a = team_factory(name="Team A", organization=org_a)
        team_b = team_factory(name="Team B", organization=org_b)

        return {
            "user_a": user_a,
            "user_b": user_b,
            "org_a": org_a,
            "org_b": org_b,
            "team_a": team_a,
            "team_b": team_b,
        }

    @staticmethod
    def _items(response):
        """Extrai lista de items da resposta (suporta paginação)."""
        data = response.data
        return data.get("results", data) if isinstance(data, dict) else data

    def test_01_user_a_list_teams_only_from_own_org(
        self, api_client, multi_org_setup, org_headers_factory
    ):
        """
        [Teams/List] User A deve ver apenas Team A.
        
        Valida:
        - Isolamento de teams entre organizações
        - User A vê apenas teams da Org A
        """
        user_a = multi_org_setup["user_a"]
        org_a = multi_org_setup["org_a"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get("/api/v1/teams/", **headers)

        assert response.status_code == status.HTTP_200_OK, (
            f"Listagem de teams para User A: esperado HTTP 200, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

        team_names = [team["name"] for team in self._items(response)]

        assert "Team A" in team_names, (
            f"User A deveria ver Team A. teams={team_names}"
        )
        assert "Team B" not in team_names, (
            f"User A não deveria ver Team B. teams={team_names}"
        )

    def test_02_user_a_cannot_access_team_from_other_org(
        self, api_client, multi_org_setup, org_headers_factory
    ):
        """
        [Teams/Detail] User A não deve acessar Team B.
        
        Valida:
        - Acesso a team de outra org retorna 404
        - Detalhes de resources cross-tenant são bloqueados
        """
        user_a = multi_org_setup["user_a"]
        org_a = multi_org_setup["org_a"]
        team_b = multi_org_setup["team_b"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get(f"/api/v1/teams/{team_b.id}/", **headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"Detalhe de team de outra organização: esperado HTTP 404, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_03_user_b_list_teams_only_from_own_org(
        self, api_client, multi_org_setup, org_headers_factory
    ):
        """
        [Teams/List] User B deve ver apenas Team B.
        
        Valida:
        - Isolamento recíproco entre organizações
        - User B vê apenas teams da Org B
        """
        user_b = multi_org_setup["user_b"]
        org_b = multi_org_setup["org_b"]
        headers = org_headers_factory(user=user_b, org=org_b)

        response = api_client.get("/api/v1/teams/", **headers)

        assert response.status_code == status.HTTP_200_OK, (
            f"Listagem de teams para User B: esperado HTTP 200, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

        team_names = [team["name"] for team in self._items(response)]

        assert "Team A" not in team_names, (
            f"User B não deveria ver Team A. teams={team_names}"
        )
        assert "Team B" in team_names, (
            f"User B deveria ver Team B. teams={team_names}"
        )

    def test_04_user_a_list_organizations_by_membership(
        self, api_client, multi_org_setup, org_headers_factory
    ):
        """
        [Organizations/List] User A deve ver apenas Org A.
        
        Valida:
        - Listagem de orgs filtrada por membership do usuário
        - User A vê apenas organizações às quais pertence
        """
        user_a = multi_org_setup["user_a"]
        org_a = multi_org_setup["org_a"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get("/api/v1/organizations/", **headers)

        assert response.status_code == status.HTTP_200_OK, (
            f"Listagem de organizações para User A: esperado HTTP 200, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

        org_names = [org["name"] for org in self._items(response)]

        assert "Org A" in org_names, (
            f"User A deveria ver Org A. orgs={org_names}"
        )
        assert "Org B" not in org_names, (
            f"User A não deveria ver Org B. orgs={org_names}"
        )

    def test_05_unauthenticated_user_cannot_access_teams(
        self, api_client, multi_org_setup
    ):
        """
        [Auth] Usuário não autenticado deve receber 401.
        
        Valida:
        - Endpoints de teams requerem autenticação
        - Resposta 401 para requisições anônimas
        """
        org_a = multi_org_setup["org_a"]
        headers = {"HTTP_X_ORGANIZATION_ID": str(org_a.id)}

        response = api_client.get("/api/v1/teams/", **headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Acesso sem autenticação: esperado HTTP 401, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_06_user_a_can_access_own_organization_detail(
        self, api_client, multi_org_setup, org_headers_factory
    ):
        """
        [Organizations/Detail] User A deve acessar Org A.
        
        Valida:
        - Acesso a detalhes da própria organização permitido
        - Dados retornados correspondem à organização correta
        """
        user_a = multi_org_setup["user_a"]
        org_a = multi_org_setup["org_a"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get(f"/api/v1/organizations/{org_a.id}/", **headers)

        assert response.status_code == status.HTTP_200_OK, (
            f"Detalhe da própria organização: esperado HTTP 200, "
            f"recebido {response.status_code}. Payload={response.data}"
        )
        assert response.data["name"] == "Org A", (
            f"Esperado nome 'Org A', recebido {response.data}"
        )

    def test_07_user_a_cannot_access_other_organization_detail(
        self, api_client, multi_org_setup, org_headers_factory
    ):
        """
        [Organizations/Detail] User A não deve acessar Org B.
        
        Valida:
        - Acesso a detalhes de outra organização retorna 404
        - Isolamento de dados entre tenants
        """
        user_a = multi_org_setup["user_a"]
        org_a = multi_org_setup["org_a"]
        org_b = multi_org_setup["org_b"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get(f"/api/v1/organizations/{org_b.id}/", **headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"Detalhe de organização de outro tenant: esperado HTTP 404, "
            f"recebido {response.status_code}. Payload={response.data}"
        )
