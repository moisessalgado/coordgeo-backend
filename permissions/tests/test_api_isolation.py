from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from organizations.models import Organization, Membership, Team
from permissions.models import Permission


class PermissionsAPIIsolationTest(APITestCase):
    """Testes de isolamento multi-tenant para permissões."""

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
        """Cria permissões em organizações separadas."""
        # User A + Org A
        self.user_a = User.objects.create_user(
            username="usera-permissions",
            email="a-permissions@test.com",
            password="password123"
        )
        self.org_a = Organization.objects.create(
            name="Org A",
            slug="org-a-permissions",
            owner=self.user_a
        )
        Membership.objects.create(
            user=self.user_a,
            organization=self.org_a,
            role=Membership.Role.ADMIN
        )

        # User C em Org A (para receber permissão)
        self.user_c = User.objects.create_user(
            username="userc-permissions",
            email="c-permissions@test.com",
            password="password123"
        )
        Membership.objects.create(
            user=self.user_c,
            organization=self.org_a,
            role=Membership.Role.MEMBER
        )

        # Team A em Org A
        self.team_a = Team.objects.create(
            name="Team A",
            organization=self.org_a
        )

        # Permissão: User C tem acesso à Org A
        self.perm_a = Permission.objects.create(
            subject_user=self.user_c,
            resource_type=Permission.ResourceType.ORGANIZATION,
            resource_id=self.org_a.id,
            role=Permission.Role.VIEW,
            granted_by=self.user_a
        )

        # User B + Org B
        self.user_b = User.objects.create_user(
            username="userb-permissions",
            email="b-permissions@test.com",
            password="password123"
        )
        self.org_b = Organization.objects.create(
            name="Org B",
            slug="org-b-permissions",
            owner=self.user_b
        )
        Membership.objects.create(
            user=self.user_b,
            organization=self.org_b,
            role=Membership.Role.ADMIN
        )

        # Team B em Org B
        self.team_b = Team.objects.create(
            name="Team B",
            organization=self.org_b
        )

        # Permissão: Team B tem acesso à Org B
        self.perm_b = Permission.objects.create(
            subject_team=self.team_b,
            resource_type=Permission.ResourceType.ORGANIZATION,
            resource_id=self.org_b.id,
            role=Permission.Role.EDIT,
            granted_by=self.user_b
        )

    def test_01_user_lists_only_org_permissions(self):
        """[Permissions/List] User A deve ver apenas permissões da Org A."""
        self.client.force_authenticate(user=self.user_a)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}

        response = self.client.get("/api/permissions/", **headers)

        self._assert_status(response, status.HTTP_200_OK, "Listagem de permissões")

        perms = self._items(response)
        org_a_perm_ids = [p["id"] for p in perms if p.get("resource_type") == "organization"]

        self.assertIn(self.perm_a.id, org_a_perm_ids, f"User A deveria ver Perm A. perms={org_a_perm_ids}")
        self.assertNotIn(self.perm_b.id, org_a_perm_ids, f"User A não deveria ver Perm B. perms={org_a_perm_ids}")

    def test_02_anon_cannot_list_permissions(self):
        """[Auth] Usuário não autenticado deve receber 401."""
        response = self.client.get("/api/permissions/")

        self._assert_status(response, status.HTTP_401_UNAUTHORIZED, "Acesso sem autenticação")
    def test_03_missing_organization_header_returns_400(self):
        """[Header Validation] Requisição sem X-Organization-ID deve retornar 400."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get("/api/permissions/")  # Sem header

        self._assert_status(response, status.HTTP_400_BAD_REQUEST, "Header X-Organization-ID ausente")

    def test_04_unauthorized_organization_returns_403(self):
        """[Header Validation] User A não é membro de Org B, deve retornar 403."""
        self.client.force_authenticate(user=self.user_a)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_b.id)}  # User A não é membro de Org B
        
        response = self.client.get("/api/permissions/", **headers)

        self._assert_status(response, status.HTTP_403_FORBIDDEN, "User não autorizado para org especificada")

    def test_05_create_org_permission_enforces_active_resource(self):
        """[Permissions/Create] resource_id para organização deve ser forçado para org ativa."""
        self.client.force_authenticate(user=self.user_a)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}

        payload = {
            "subject_user": self.user_c.id,
            "resource_type": Permission.ResourceType.ORGANIZATION,
            "resource_id": self.org_b.id,
            "role": Permission.Role.MANAGE,
        }
        response = self.client.post("/api/permissions/", payload, format="json", **headers)

        self._assert_status(response, status.HTTP_201_CREATED, "Criação de permissão com resource_id forçado")
        self.assertEqual(response.data["resource_id"], self.org_a.id)