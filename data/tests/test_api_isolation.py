from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from organizations.models import Organization, Membership
from data.models import Datasource


class DataAPIIsolationTest(APITestCase):
    """Testes de isolamento multi-tenant para datasources."""

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
        """Cria datasources em organizações separadas."""
        # User A + Org A + Datasource A
        self.user_a = User.objects.create_user(
            username="usera-data",
            email="a-data@test.com",
            password="password123"
        )
        self.org_a = Organization.objects.create(
            name="Org A",
            slug="org-a-data",
            owner=self.user_a
        )
        Membership.objects.create(
            user=self.user_a,
            organization=self.org_a,
            role=Membership.Role.ADMIN
        )
        self.datasource_a = Datasource.objects.create(
            name="Raster Data A",
            organization=self.org_a,
            created_by=self.user_a,
            storage_url="s3://bucket/raster_a.tif",
            datasource_type=Datasource.Type.RASTER
        )

        # User B + Org B + Datasource B
        self.user_b = User.objects.create_user(
            username="userb-data",
            email="b-data@test.com",
            password="password123"
        )
        self.org_b = Organization.objects.create(
            name="Org B",
            slug="org-b-data",
            owner=self.user_b
        )
        Membership.objects.create(
            user=self.user_b,
            organization=self.org_b,
            role=Membership.Role.ADMIN
        )
        self.datasource_b = Datasource.objects.create(
            name="Vector Data B",
            organization=self.org_b,
            created_by=self.user_b,
            storage_url="s3://bucket/vector_b.geojson",
            datasource_type=Datasource.Type.VECTOR
        )

    def test_01_user_lists_own_datasources(self):
        """[Datasources/List] User A deve ver apenas Datasource A."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get("/api/datasources/")

        self._assert_status(response, status.HTTP_200_OK, "Listagem de datasources")

        ds_names = [ds["name"] for ds in self._items(response)]

        self.assertIn("Raster Data A", ds_names, f"User A deveria ver Datasource A. datasources={ds_names}")
        self.assertNotIn("Vector Data B", ds_names, f"User A não deveria ver Datasource B. datasources={ds_names}")

    def test_02_user_cannot_get_other_datasource(self):
        """[Datasources/Detail] User A não deve acessar Datasource B."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f"/api/datasources/{self.datasource_b.id}/")

        self._assert_status(response, status.HTTP_404_NOT_FOUND, "Acesso a datasource de outro tenant")

    def test_03_anon_cannot_list_datasources(self):
        """[Auth] Usuário não autenticado deve receber 401."""
        response = self.client.get("/api/datasources/")

        self._assert_status(response, status.HTTP_401_UNAUTHORIZED, "Acesso sem autenticação")
