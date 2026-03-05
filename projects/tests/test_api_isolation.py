from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from organizations.models import Organization, Membership
from projects.models import Project, Layer
from data.models import Datasource


class ProjectsAPIIsolationTest(APITestCase):
    """Testes de isolamento multi-tenant para projetos e layers."""

    @staticmethod
    def _items(response):
        data = response.data
        return data.get("results", data) if isinstance(data, dict) else data

    def _assert_status(self, response, expected_status, context):
        self.assertEqual(
            response.status_code,
            expected_status,
            f"{context}: esperado HTTP {expected_status}, recebido {response.status_code}. Payload={response.data}",
        )

    def setUp(self):
        """Cria dois projetos em organizações separadas."""
        # User A + Org A + Project A
        self.user_a = User.objects.create_user(
            username="usera-projects",
            email="a-projects@test.com",
            password="password123"
        )
        self.org_a = Organization.objects.create(
            name="Org A",
            slug="org-a-projects",
            owner=self.user_a
        )
        Membership.objects.create(
            user=self.user_a,
            organization=self.org_a,
            role=Membership.Role.ADMIN
        )
        self.project_a = Project.objects.create(
            name="Project A",
            organization=self.org_a
        )
        self.datasource_a = Datasource.objects.create(
            name="Data A",
            organization=self.org_a,
            created_by=self.user_a,
            storage_url="s3://bucket/data_a.tif",
            datasource_type=Datasource.Type.RASTER
        )
        self.layer_a = Layer.objects.create(
            name="Layer A",
            project=self.project_a,
            datasource=self.datasource_a
        )

        # User B + Org B + Project B
        self.user_b = User.objects.create_user(
            username="userb-projects",
            email="b-projects@test.com",
            password="password123"
        )
        self.org_b = Organization.objects.create(
            name="Org B",
            slug="org-b-projects",
            owner=self.user_b
        )
        Membership.objects.create(
            user=self.user_b,
            organization=self.org_b,
            role=Membership.Role.ADMIN
        )
        self.project_b = Project.objects.create(
            name="Project B",
            organization=self.org_b
        )
        self.datasource_b = Datasource.objects.create(
            name="Data B",
            organization=self.org_b,
            created_by=self.user_b,
            storage_url="s3://bucket/data_b.geojson",
            datasource_type=Datasource.Type.VECTOR
        )
        self.layer_b = Layer.objects.create(
            name="Layer B",
            project=self.project_b,
            datasource=self.datasource_b
        )

    def test_01_user_lists_own_projects(self):
        """[Projects/List] User A deve ver apenas Project A."""
        self.client.force_authenticate(user=self.user_a)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}

        response = self.client.get("/api/v1/projects/", **headers)

        self._assert_status(response, status.HTTP_200_OK, "Listagem de projetos")

        project_names = [p["name"] for p in self._items(response)]

        self.assertIn("Project A", project_names, f"User A deveria ver Project A. projects={project_names}")
        self.assertNotIn("Project B", project_names, f"User A não deveria ver Project B. projects={project_names}")

    def test_02_user_cannot_get_other_project(self):
        """[Projects/Detail] User A não deve acessar Project B."""
        self.client.force_authenticate(user=self.user_a)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}

        response = self.client.get(f"/api/v1/projects/{self.project_b.id}/", **headers)

        self._assert_status(response, status.HTTP_404_NOT_FOUND, "Acesso a projeto de outro tenant")

    def test_03_user_lists_layers_from_own_projects(self):
        """[Layers/List] User A deve ver apenas Layer A."""
        self.client.force_authenticate(user=self.user_a)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}

        response = self.client.get("/api/v1/layers/", **headers)

        self._assert_status(response, status.HTTP_200_OK, "Listagem de layers")

        layer_names = [l["name"] for l in self._items(response)]

        self.assertIn("Layer A", layer_names, f"User A deveria ver Layer A. layers={layer_names}")
        self.assertNotIn("Layer B", layer_names, f"User A não deveria ver Layer B. layers={layer_names}")

    def test_04_user_cannot_get_other_layer(self):
        """[Layers/Detail] User A não deve acessar Layer B."""
        self.client.force_authenticate(user=self.user_a)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}

        response = self.client.get(f"/api/v1/layers/{self.layer_b.id}/", **headers)

        self._assert_status(response, status.HTTP_404_NOT_FOUND, "Acesso a layer de outro tenant")

    def test_05_anon_cannot_list_projects(self):
        """[Auth] Usuário não autenticado deve receber 401."""
        response = self.client.get("/api/v1/projects/")

        self._assert_status(response, status.HTTP_401_UNAUTHORIZED, "Acesso sem autenticação")
    def test_06_missing_organization_header_returns_400(self):
        """[Header Validation] Requisição sem X-Organization-ID deve retornar 400."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get("/api/v1/projects/")  # Sem header

        self._assert_status(response, status.HTTP_400_BAD_REQUEST, "Header X-Organization-ID ausente")

    def test_07_unauthorized_organization_returns_403(self):
        """[Header Validation] User A não é membro de Org B, deve retornar 403."""
        self.client.force_authenticate(user=self.user_a)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_b.id)}  # User A não é membro de Org B
        
        response = self.client.get("/api/v1/projects/", **headers)

        self._assert_status(response, status.HTTP_403_FORBIDDEN, "User não autorizado para org especificada")

    def test_08_create_project_enforces_active_organization(self):
        """[Projects/Create] Org enviada no payload deve ser ignorada em favor da org ativa."""
        self.client.force_authenticate(user=self.user_a)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}

        payload = {
            "name": "Project Enforced Org",
            "organization": self.org_b.id,
        }
        response = self.client.post("/api/v1/projects/", payload, format="json", **headers)

        self._assert_status(response, status.HTTP_201_CREATED, "Criação de projeto com org forçada")
        self.assertEqual(response.data["organization"], self.org_a.id)