from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.models import Membership, Organization


User = get_user_model()


class RegisterPlanTest(APITestCase):
    endpoint = "/api/v1/auth/register/"

    def test_register_defaults_to_free_plan(self):
        response = self.client.post(
            self.endpoint,
            {
                "email": "free-default@test.com",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="free-default@test.com")
        personal_org = Organization.objects.get(owner=user, org_type=Organization.OrgType.PERSONAL)
        self.assertEqual(personal_org.plan, Organization.Plan.FREE)

        membership = Membership.objects.get(user=user, organization=personal_org)
        self.assertEqual(membership.role, Membership.Role.ADMIN)

    def test_register_accepts_pro_plan(self):
        response = self.client.post(
            self.endpoint,
            {
                "email": "pro-signup@test.com",
                "password": "password123",
                "plan": "pro",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="pro-signup@test.com")
        personal_org = Organization.objects.get(owner=user, org_type=Organization.OrgType.PERSONAL)
        self.assertEqual(personal_org.plan, Organization.Plan.PRO)

    def test_register_rejects_enterprise_plan(self):
        response = self.client.post(
            self.endpoint,
            {
                "email": "enterprise-signup@test.com",
                "password": "password123",
                "plan": "enterprise",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("plan", response.data)

    def test_register_rejects_invalid_plan(self):
        response = self.client.post(
            self.endpoint,
            {
                "email": "invalid-plan@test.com",
                "password": "password123",
                "plan": "invalid",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("plan", response.data)
