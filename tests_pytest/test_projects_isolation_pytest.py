"""
Testes de isolamento multi-tenant para projetos e layers.
Migrado de: projects/tests/test_api_isolation.py
"""
import pytest
from rest_framework import status
from organizations.models import Membership


@pytest.mark.api
class TestProjectsAPIIsolation:
    """Testes de isolamento multi-tenant para projetos e layers."""

    @pytest.fixture
    def multi_project_setup(
        self, user_factory, org_factory, membership_factory, project_factory, datasource_factory, layer_factory
    ):
        """
        Setup de cenário multi-project:
        - User A (admin) na Org A com Project A, Datasource A, Layer A
        - User B (admin) na Org B com Project B, Datasource B, Layer B
        """
        # User A + Org A + Project A
        user_a = user_factory(
            username="usera-projects",
            email="a-projects@test.com",
            password="password123"
        )
        org_a = org_factory(
            name="Org A",
            slug="org-a-projects",
            owner=user_a
        )
        membership_factory(
            user=user_a,
            organization=org_a,
            role=Membership.Role.ADMIN
        )
        project_a = project_factory(
            name="Project A",
            organization=org_a,
            created_by=user_a
        )
        datasource_a = datasource_factory(
            name="Data A",
            organization=org_a,
            created_by=user_a,
            datasource_type="raster",
            storage_url="s3://bucket/data_a.tif"
        )
        layer_a = layer_factory(
            name="Layer A",
            project=project_a,
            datasource=datasource_a
        )

        # User B + Org B + Project B
        user_b = user_factory(
            username="userb-projects",
            email="b-projects@test.com",
            password="password123"
        )
        org_b = org_factory(
            name="Org B",
            slug="org-b-projects",
            owner=user_b
        )
        membership_factory(
            user=user_b,
            organization=org_b,
            role=Membership.Role.ADMIN
        )
        project_b = project_factory(
            name="Project B",
            organization=org_b,
            created_by=user_b
        )
        datasource_b = datasource_factory(
            name="Data B",
            organization=org_b,
            created_by=user_b,
            datasource_type="vector",
            storage_url="s3://bucket/data_b.geojson"
        )
        layer_b = layer_factory(
            name="Layer B",
            project=project_b,
            datasource=datasource_b
        )

        return {
            "user_a": user_a, "org_a": org_a, "project_a": project_a,
            "datasource_a": datasource_a, "layer_a": layer_a,
            "user_b": user_b, "org_b": org_b, "project_b": project_b,
            "datasource_b": datasource_b, "layer_b": layer_b,
        }

    @staticmethod
    def _items(response):
        """Extrai lista de items da resposta (suporta paginação)."""
        data = response.data
        return data.get("results", data) if isinstance(data, dict) else data

    def test_01_user_lists_own_projects(
        self, api_client, multi_project_setup, org_headers_factory
    ):
        """
        [Projects/List] User A deve ver apenas Project A.
        
        Valida:
        - Isolamento de projetos entre organizações
        - User A vê apenas projetos da Org A
        """
        user_a = multi_project_setup["user_a"]
        org_a = multi_project_setup["org_a"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get("/api/v1/projects/", **headers)

        assert response.status_code == status.HTTP_200_OK, (
            f"Listagem de projetos: esperado HTTP 200, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

        project_names = [p["name"] for p in self._items(response)]

        assert "Project A" in project_names, (
            f"User A deveria ver Project A. projects={project_names}"
        )
        assert "Project B" not in project_names, (
            f"User A não deveria ver Project B. projects={project_names}"
        )

    def test_02_user_cannot_get_other_project(
        self, api_client, multi_project_setup, org_headers_factory
    ):
        """
        [Projects/Detail] User A não deve acessar Project B.
        
        Valida:
        - Acesso a projekt de outra org retorna 404
        """
        user_a = multi_project_setup["user_a"]
        org_a = multi_project_setup["org_a"]
        project_b = multi_project_setup["project_b"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get(f"/api/v1/projects/{project_b.id}/", **headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"Acesso a projeto de outro tenant: esperado HTTP 404, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_03_user_lists_layers_from_own_projects(
        self, api_client, multi_project_setup, org_headers_factory
    ):
        """
        [Layers/List] User A deve ver apenas Layer A.
        
        Valida:
        - Isolamento de layers entre organizações
        - User A vê apenas layers da Org A
        """
        user_a = multi_project_setup["user_a"]
        org_a = multi_project_setup["org_a"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get("/api/v1/layers/", **headers)

        assert response.status_code == status.HTTP_200_OK, (
            f"Listagem de layers: esperado HTTP 200, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

        layer_names = [l["name"] for l in self._items(response)]

        assert "Layer A" in layer_names, (
            f"User A deveria ver Layer A. layers={layer_names}"
        )
        assert "Layer B" not in layer_names, (
            f"User A não deveria ver Layer B. layers={layer_names}"
        )

    def test_04_user_cannot_get_other_layer(
        self, api_client, multi_project_setup, org_headers_factory
    ):
        """
        [Layers/Detail] User A não deve acessar Layer B.
        
        Valida:
        - Acesso a layer de outra org retorna 404
        """
        user_a = multi_project_setup["user_a"]
        org_a = multi_project_setup["org_a"]
        layer_b = multi_project_setup["layer_b"]
        headers = org_headers_factory(user=user_a, org=org_a)

        response = api_client.get(f"/api/v1/layers/{layer_b.id}/", **headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"Acesso a layer de outro tenant: esperado HTTP 404, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_05_anon_cannot_list_projects(self, api_client):
        """
        [Auth] Usuário não autenticado deve receber 401.
        
        Valida:
        - Endpoints de projects requerem autenticação
        """
        response = api_client.get("/api/v1/projects/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Acesso sem autenticação: esperado HTTP 401, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_06_missing_organization_header_returns_400(
        self, api_client, multi_project_setup, jwt_token_factory
    ):
        """
        [Header Validation] Requisição sem X-Organization-ID deve retornar 400.
        
        Valida:
        - Header X-Organization-ID é obrigatório
        """
        user_a = multi_project_setup["user_a"]
        token = jwt_token_factory(user_a)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        response = api_client.get("/api/v1/projects/", **headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            f"Header X-Organization-ID ausente: esperado HTTP 400, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_07_unauthorized_organization_returns_403(
        self, api_client, multi_project_setup, jwt_token_factory
    ):
        """
        [Header Validation] User A não é membro de Org B, deve retornar 403.
        
        Valida:
        - Usuários não podem acessar orgs às quais não pertencem
        """
        user_a = multi_project_setup["user_a"]
        org_b = multi_project_setup["org_b"]
        token = jwt_token_factory(user_a)
        headers = {
            "HTTP_AUTHORIZATION": f"Bearer {token}",
            "HTTP_X_ORGANIZATION_ID": str(org_b.id),  # User A não é membro de Org B
        }

        response = api_client.get("/api/v1/projects/", **headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN, (
            f"User não autorizado para org especificada: esperado HTTP 403, "
            f"recebido {response.status_code}. Payload={response.data}"
        )

    def test_08_create_project_enforces_active_organization(
        self, api_client, multi_project_setup, org_headers_factory
    ):
        """
        [Projects/Create] Org enviada no payload deve ser ignorada em favor da org ativa.
        
        Valida:
        - A organization do request body é sobrescrita pela org do header
        - Projeto criado sempre na org do X-Organization-ID header
        """
        user_a = multi_project_setup["user_a"]
        org_a = multi_project_setup["org_a"]
        org_b = multi_project_setup["org_b"]
        headers = org_headers_factory(user=user_a, org=org_a)

        payload = {
            "name": "Project Enforced Org",
            "organization": org_b.id,  # Tenta enviar org_b
        }
        response = api_client.post("/api/v1/projects/", payload, format="json", **headers)

        assert response.status_code == status.HTTP_201_CREATED, (
            f"Criação de projeto com org forçada: esperado HTTP 201, "
            f"recebido {response.status_code}. Payload={response.data}"
        )
        assert response.data["organization"] == org_a.id, (
            f"Projeto deveria estar na Org A (header), não na Org B (payload). "
            f"organization={response.data.get('organization')}"
        )
