from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from organizations.models import Organization, Membership
from rest_framework_simplejwt.tokens import RefreshToken


class JWTAuthTestMixin:
    """Mixin para gerar JWT tokens nos testes."""
    
    def get_jwt_token(self, user):
        """Gera um JWT token para um usuário."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)


class AccountsAPIIsolationTest(JWTAuthTestMixin, APITestCase):
    """Testes de isolamento multi-tenant para o endpoint de usuários."""

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
        """Cria dois usuários em organizações separadas."""
        # User A na Org A
        self.user_a = User.objects.create_user(
            username="usera-accounts",
            email="a-accounts@test.com",
            password="password123"
        )
        self.org_a = Organization.objects.create(
            name="Org A",
            slug="org-a-accounts",
            owner=self.user_a
        )
        Membership.objects.create(
            user=self.user_a,
            organization=self.org_a,
            role=Membership.Role.ADMIN
        )

        # User B na Org B
        self.user_b = User.objects.create_user(
            username="userb-accounts",
            email="b-accounts@test.com",
            password="password123"
        )
        self.org_b = Organization.objects.create(
            name="Org B",
            slug="org-b-accounts",
            owner=self.user_b
        )
        Membership.objects.create(
            user=self.user_b,
            organization=self.org_b,
            role=Membership.Role.ADMIN
        )

        # User C como membro da Org A
        self.user_c = User.objects.create_user(
            username="userc-accounts",
            email="c-accounts@test.com",
            password="password123"
        )
        Membership.objects.create(
            user=self.user_c,
            organization=self.org_a,
            role=Membership.Role.MEMBER
        )

    def test_01_user_lists_coworkers_from_same_org(self):
        """[Users/List] User A deve ver User C (mesmo org), não User B."""
        token_a = self.get_jwt_token(self.user_a)
        headers = {
            'HTTP_AUTHORIZATION': f'Bearer {token_a}',
            'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)
        }

        response = self.client.get("/api/v1/users/", **headers)

        self._assert_status(response, status.HTTP_200_OK, "Listagem de usuários")

        usernames = [u["username"] for u in self._items(response)]

        self.assertIn("usera-accounts", usernames, f"User A deveria listar a si mesmo. users={usernames}")
        self.assertIn("userc-accounts", usernames, f"User A deveria ver User C (colega). users={usernames}")
        self.assertNotIn("userb-accounts", usernames, f"User A não deveria ver User B (outro tenant). users={usernames}")

    def test_02_anon_cannot_list_users(self):
        """[Auth] Usuário não autenticado deve receber 401."""
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}
        response = self.client.get("/api/v1/users/", **headers)

        self._assert_status(response, status.HTTP_401_UNAUTHORIZED, "Acesso sem autenticação")

    def test_03_missing_organization_header(self):
        """[Header] Requisição sem X-Organization-ID deve retornar 400."""
        token_a = self.get_jwt_token(self.user_a)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token_a}'}
        response = self.client.get("/api/v1/users/", **headers)  # Sem header org

        self._assert_status(response, status.HTTP_400_BAD_REQUEST, "Header ausente")
        error_detail = str(response.data.get("detail", ""))
        self.assertIn("X-Organization-ID", error_detail)

    def test_04_unauthorized_organization_access(self):
        """[Org] User A não pode acessar com X-Organization-ID de Org B."""
        token_a = self.get_jwt_token(self.user_a)
        headers = {
            'HTTP_AUTHORIZATION': f'Bearer {token_a}',
            'HTTP_X_ORGANIZATION_ID': str(self.org_b.id)  # user_a não é membro de org_b
        }
        response = self.client.get("/api/v1/users/", **headers)

        self._assert_status(response, status.HTTP_403_FORBIDDEN, "Org não autorizada")
