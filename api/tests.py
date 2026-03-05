from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.models import Membership


User = get_user_model()


class APIVersioningCompatibilityTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="version-user",
            email="version-user@example.com",
            password="testpass123",
        )
        self.organization = self.user.owned_organizations.create(
            name="Version Org",
            slug="version-org",
        )
        Membership.objects.get_or_create(
            user=self.user,
            organization=self.organization,
            defaults={"role": Membership.Role.ADMIN},
        )

    def test_token_endpoint_available_on_v1_and_legacy(self):
        payload = {
            "email": "version-user@example.com",
            "password": "testpass123",
        }

        response_v1 = self.client.post("/api/v1/token/", payload, format="json")
        self.assertEqual(response_v1.status_code, status.HTTP_200_OK)
        self.assertIn("access", response_v1.data)
        self.assertIn("refresh", response_v1.data)

        response_legacy = self.client.post("/api/token/", payload, format="json")
        self.assertEqual(response_legacy.status_code, status.HTTP_200_OK)
        self.assertIn("access", response_legacy.data)
        self.assertIn("refresh", response_legacy.data)

    def test_user_organizations_endpoint_available_on_v1_and_legacy(self):
        self.client.force_authenticate(user=self.user)

        response_v1 = self.client.get("/api/v1/user/organizations/")
        self.assertEqual(response_v1.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response_v1.data), 1)

        response_legacy = self.client.get("/api/user/organizations/")
        self.assertEqual(response_legacy.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response_legacy.data), 1)
