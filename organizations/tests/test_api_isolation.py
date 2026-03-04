from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from organizations.models import Organization, Membership, Team


class MultiTenantIsolationTest(APITestCase):

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
        # Users
        self.user_a = User.objects.create_user(
            username="usera-organizations",
            email="a-organizations@test.com",
            password="password123"
        )
        self.user_b = User.objects.create_user(
            username="userb-organizations",
            email="b-organizations@test.com",
            password="password123"
        )

        # Organizations
        self.org_a = Organization.objects.create(
            name="Org A",
            slug="org-a-organizations",
            owner=self.user_a
        )
        self.org_b = Organization.objects.create(
            name="Org B",
            slug="org-b-organizations",
            owner=self.user_b
        )

        # Memberships
        Membership.objects.create(
            user=self.user_a,
            organization=self.org_a,
            role=Membership.Role.ADMIN
        )
        Membership.objects.create(
            user=self.user_b,
            organization=self.org_b,
            role=Membership.Role.ADMIN
        )

        # Teams
        self.team_a = Team.objects.create(
            name="Team A",
            organization=self.org_a
        )
        self.team_b = Team.objects.create(
            name="Team B",
            organization=self.org_b
        )

    def test_01_user_a_list_teams_only_from_own_org(self):
        """[Teams/List] User A deve ver apenas Team A."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get("/api/teams/")

        self._assert_status(response, status.HTTP_200_OK, "Listagem de teams para User A")

        team_names = [team["name"] for team in self._items(response)]

        self.assertIn("Team A", team_names, f"User A deveria ver Team A. teams={team_names}")
        self.assertNotIn("Team B", team_names, f"User A não deveria ver Team B. teams={team_names}")

    def test_02_user_a_cannot_access_team_from_other_org(self):
        """[Teams/Detail] User A não deve acessar Team B."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f"/api/teams/{self.team_b.id}/")
        self._assert_status(response, status.HTTP_404_NOT_FOUND, "Detalhe de team de outra organização")

    def test_03_user_b_list_teams_only_from_own_org(self):
        """[Teams/List] User B deve ver apenas Team B."""
        self.client.force_authenticate(user=self.user_b)

        response = self.client.get("/api/teams/")

        self._assert_status(response, status.HTTP_200_OK, "Listagem de teams para User B")

        team_names = [team["name"] for team in self._items(response)]

        self.assertNotIn("Team A", team_names, f"User B não deveria ver Team A. teams={team_names}")
        self.assertIn("Team B", team_names, f"User B deveria ver Team B. teams={team_names}")

    def test_04_user_a_list_organizations_by_membership(self):
        """[Organizations/List] User A deve ver apenas Org A."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get("/api/organizations/")

        self._assert_status(response, status.HTTP_200_OK, "Listagem de organizações para User A")

        org_names = [org["name"] for org in self._items(response)]

        self.assertIn("Org A", org_names, f"User A deveria ver Org A. orgs={org_names}")
        self.assertNotIn("Org B", org_names, f"User A não deveria ver Org B. orgs={org_names}")

    def test_05_unauthenticated_user_cannot_access_teams(self):
        """[Auth] Usuário não autenticado deve receber 401."""
        response = self.client.get("/api/teams/")

        self._assert_status(response, status.HTTP_401_UNAUTHORIZED, "Acesso sem autenticação")

    def test_06_user_a_can_access_own_organization_detail(self):
        """[Organizations/Detail] User A deve acessar Org A."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f"/api/organizations/{self.org_a.id}/")

        self._assert_status(response, status.HTTP_200_OK, "Detalhe da própria organização")
        self.assertEqual(response.data["name"], "Org A", f"Esperado nome Org A, recebido {response.data}")

    def test_07_user_a_cannot_access_other_organization_detail(self):
        """[Organizations/Detail] User A não deve acessar Org B."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f"/api/organizations/{self.org_b.id}/")

        self._assert_status(response, status.HTTP_404_NOT_FOUND, "Detalhe de organização de outro tenant")