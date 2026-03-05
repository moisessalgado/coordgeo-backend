"""
Testes de compatibilidade de API em pytest.
Migrado de: api/tests.py (APIVersioningCompatibilityTest)
"""
import pytest
from rest_framework import status
from organizations.models import Membership, Organization


@pytest.mark.api
class TestAPIVersioningCompatibility:
    """Testes de versionamento e disponibilidade de endpoints da API."""

    @pytest.fixture
    def setup_user_and_org(self, user_factory, org_factory, membership_factory):
        """Setup compartilhado: cria usuário, org e membership."""
        user = user_factory(
            username="version-user",
            email="version-user@example.com"
        )
        org = org_factory(
            name="Version Org",
            slug="version-org",
            org_type=Organization.OrgType.TEAM,
            plan=Organization.Plan.PRO,
            owner=user
        )
        membership_factory(
            user=user,
            organization=org,
            role=Membership.Role.ADMIN
        )
        return {"user": user, "org": org}

    def test_token_endpoint_available_on_v1_only(self, api_client, setup_user_and_org):
        """
        [API/v1] Endpoint /api/v1/token/ deve estar disponível e funcional.
        
        Valida:
        - POST /api/v1/token/ retorna 200 OK
        - Resposta contém tokens 'access' e 'refresh'
        """
        payload = {
            "email": "version-user@example.com",
            "password": "testpass123",
        }

        response_v1 = api_client.post("/api/v1/token/", payload, format="json")
        
        assert response_v1.status_code == status.HTTP_200_OK
        assert "access" in response_v1.data
        assert "refresh" in response_v1.data

    def test_user_organizations_endpoint_available_on_v1_only(
        self, api_client, setup_user_and_org
    ):
        """
        [API/v1] Endpoint /api/v1/user/organizations/ deve estar disponível.
        
        Valida:
        - GET /api/v1/user/organizations/ retorna 200 OK
        - Resposta contém pelo menos 1 organização
        """
        user = setup_user_and_org["user"]
        api_client.force_authenticate(user=user)

        response_v1 = api_client.get("/api/v1/user/organizations/")
        
        assert response_v1.status_code == status.HTTP_200_OK
        assert len(response_v1.data) >= 1
