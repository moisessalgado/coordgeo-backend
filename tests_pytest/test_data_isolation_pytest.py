"""
Testes de isolamento multi-tenant para datasources.
Migrado de: data/tests/test_api_isolation.py
"""
import pytest
from rest_framework import status
from organizations.models import Membership
from data.models import Datasource


@pytest.mark.api
class TestDataAPIIsolation:
    """Testes de isolamento multi-tenant para datasources."""

    @pytest.fixture
    def multi_datasource_setup(
        self, user_factory, org_factory, membership_factory, datasource_factory
    ):
        """
        Setup de cenário multi-datasource:
        - User A (admin) na Org A com Datasource A (raster)
        - User B (admin) na Org B com Datasource B (vector)
        """
        # User A + Org A + Datasource A
        user_a = user_factory(
            username="usera-data",
            email="a-data@test.com",
            password="password123"
        )
        org_a = org_factory(
            name="Org A",
            slug="org-a-data",
            owner=user_a
        )
        membership_factory(
            user=user_a,
            organization=org_a,
            role=Membership.Role.ADMIN
        )
        datasource_a = datasource_factory(
            name="Raster Data A",
            organization=org_a,
            created_by=user_a,
            datasource_type="raster",
            storage_url="s3://bucket/raster_a.tif"
        )

        # User B + Org B + Datasource B
        user_b = user_factory(
            username="userb-data",
            email="b-data@test.com",
            password="password123"
        )
        org_b = org_factory(
            name="Org B",
            slug="org-b-data",
            owner=user_b
        )
        membership_factory(
            user=user_b,
            organization=org_b,
            role=Membership.Role.ADMIN
        )
        datasource_b = datasource_factory(
            name="Vector Data B",
            organization=org_b,
            created_by=user_b,
            datasource_type="vector",
            storage_url="s3://bucket/vector_b.geojson"
        )

        return {
            "user_a": user_a,
            "org_a": org_a,
            "datasource_a": datasource_a,
            "user_b": user_b,
            "org_b": org_b,
            "datasource_b": datasource_b,
        }

    @staticmethod
    def _items(response):
        """Extrai lista de items da resposta (suporta paginação)."""
        data = response.data
        return data.get("results", data) if isinstance(data, dict) else data

    def test_01_user_lists_own_datasources(
        self, api_client, multi_datasource_setup, org_headers_factory
    ):
        """
        [Datasources/List] User A deve ver apenas Datasource A.
        
        Valida:
        - Isolamento de datasources entre organizações
        - User A vê apenas datasources da Org A
        """
        user_a = multi_datasource_setup["user_a"]
        org_a = multi_datasource_setup["org_a"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get("/api/v1/datasources/", **headers)

        assert response.status_code == status.HTTP_200_OK, (
            f"Listagem de datasources: esperado HTTP 200, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

        ds_names = [ds["name"] for ds in self._items(response)]

        assert "Raster Data A" in ds_names, (
            f"User A deveria ver Datasource A. datasources={ds_names}"
        )
        assert "Vector Data B" not in ds_names, (
            f"User A não deveria ver Datasource B. datasources={ds_names}"
        )

    def test_02_user_cannot_get_other_datasource(
        self, api_client, multi_datasource_setup, org_headers_factory
    ):
        """
        [Datasources/Detail] User A não deve acessar Datasource B.
        
        Valida:
        - Acesso a datasource de outra org retorna 404
        """
        user_a = multi_datasource_setup["user_a"]
        org_a = multi_datasource_setup["org_a"]
        datasource_b = multi_datasource_setup["datasource_b"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get(f"/api/v1/datasources/{datasource_b.id}/", **headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"Acesso a datasource de outro tenant: esperado HTTP 404, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_03_anon_cannot_list_datasources(self, api_client):
        """
        [Auth] Usuário não autenticado deve receber 401.
        
        Valida:
        - Endpoints de datasources requerem autenticação
        """
        response = api_client.get("/api/v1/datasources/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Acesso sem autenticação: esperado HTTP 401, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_04_missing_organization_header_returns_400(
        self, api_client, multi_datasource_setup, jwt_token_factory
    ):
        """
        [Header Validation] Requisição sem X-Organization-ID deve retornar 400.
        
        Valida:
        - Header X-Organization-ID é obrigatório
        """
        user_a = multi_datasource_setup["user_a"]
        token = jwt_token_factory(user_a)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        response = api_client.get("/api/v1/datasources/", **headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            f"Header X-Organization-ID ausente: esperado HTTP 400, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_05_unauthorized_organization_returns_403(
        self, api_client, multi_datasource_setup, jwt_token_factory
    ):
        """
        [Header Validation] User A não é membro de Org B, deve retornar 403.
        
        Valida:
        - Usuários não podem acessar orgs às quais não pertencem
        """
        user_a = multi_datasource_setup["user_a"]
        org_b = multi_datasource_setup["org_b"]
        token = jwt_token_factory(user_a)
        headers = {
            "HTTP_AUTHORIZATION": f"Bearer {token}",
            "HTTP_X_ORGANIZATION_ID": str(org_b.id),  # User A não é membro de Org B
        }

        response = api_client.get("/api/v1/datasources/", **headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN, (
            f"User não autorizado para org especificada: esperado HTTP 403, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_06_create_datasource_enforces_active_organization(
        self, api_client, multi_datasource_setup, org_headers_factory
    ):
        """
        [Datasources/Create] Org enviada no payload deve ser ignorada em favor da org ativa.
        
        Valida:
        - A organization do request body é sobrescrita pela org do header
        - Datasource criado sempre na org do X-Organization-ID header
        """
        user_a = multi_datasource_setup["user_a"]
        org_a = multi_datasource_setup["org_a"]
        org_b = multi_datasource_setup["org_b"]
        headers = org_headers_factory(user=user_a, org=org_a)

        payload = {
            "name": "Datasource Enforced Org",
            "organization": org_b.id,  # Tenta enviar org_b
            "datasource_type": Datasource.Type.VECTOR,
            "storage_url": "s3://bucket/enforced.geojson",
        }
        response = api_client.post("/api/v1/datasources/", payload, format="json", **headers)

        assert response.status_code == status.HTTP_201_CREATED, (
            f"Criação de datasource com org forçada: esperado HTTP 201, "
            f"recebido {response.status_code}. Payload={response.data}"
        )
        assert response.data["organization"] == org_a.id, (
            f"Datasource deveria estar na Org A (header), não na Org B (payload). "
            f"organization={response.data.get('organization')}"
        )
