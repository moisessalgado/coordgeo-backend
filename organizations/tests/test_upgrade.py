from rest_framework.test import APITestCase
from rest_framework import status
import json
from accounts.models import User
from organizations.models import Organization, Membership


class OrganizationUpgradeTest(APITestCase):
    """Tests for the organization upgrade endpoint"""

    def setUp(self):
        # Create users
        self.user_admin = User.objects.create_user(
            username="admin-upgrade",
            email="admin-upgrade@test.com",
            password="password123"
        )
        self.user_member = User.objects.create_user(
            username="member-upgrade",
            email="member-upgrade@test.com",
            password="password123"
        )
        self.user_other = User.objects.create_user(
            username="other-upgrade",
            email="other-upgrade@test.com",
            password="password123"
        )

        # Create organizations
        self.org = Organization.objects.create(
            name="Test Org",
            slug="test-org-upgrade",
            owner=self.user_admin,
            org_type=Organization.OrgType.TEAM,
            plan=Organization.Plan.FREE
        )

        # Create memberships
        Membership.objects.create(
            user=self.user_admin,
            organization=self.org,
            role=Membership.Role.ADMIN
        )
        Membership.objects.create(
            user=self.user_member,
            organization=self.org,
            role=Membership.Role.MEMBER
        )

    def test_admin_can_upgrade_organization(self):
        """Admin user should be able to upgrade organization plan"""
        self.client.force_authenticate(user=self.user_admin)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org.id)}

        response = self.client.post(
            f"/api/v1/organizations/{self.org.id}/upgrade/",
            json.dumps({"plan": "pro"}),
            content_type='application/json',
            **headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan'], 'pro')
        
        # Verify in database
        self.org.refresh_from_db()
        self.assertEqual(self.org.plan, Organization.Plan.PRO)

    def test_member_cannot_upgrade_organization(self):
        """Member user should NOT be able to upgrade organization plan"""
        self.client.force_authenticate(user=self.user_member)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org.id)}

        response = self.client.post(
            f"/api/v1/organizations/{self.org.id}/upgrade/",
            json.dumps({"plan": "pro"}),
            content_type='application/json',
            **headers
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify plan didn't change
        self.org.refresh_from_db()
        self.assertEqual(self.org.plan, Organization.Plan.FREE)

    def test_non_member_cannot_upgrade_organization(self):
        """Non-member user should NOT be able to upgrade organization plan"""
        self.client.force_authenticate(user=self.user_other)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org.id)}

        response = self.client.post(
            f"/api/v1/organizations/{self.org.id}/upgrade/",
            json.dumps({"plan": "pro"}),
            content_type='application/json',
            **headers
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_plan_field(self):
        """Should return 400 if plan field is missing"""
        self.client.force_authenticate(user=self.user_admin)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org.id)}

        response = self.client.post(
            f"/api/v1/organizations/{self.org.id}/upgrade/",
            json.dumps({}),
            content_type='application/json',
            **headers
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_plan(self):
        """Should return 400 if plan is invalid"""
        self.client.force_authenticate(user=self.user_admin)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org.id)}

        response = self.client.post(
            f"/api/v1/organizations/{self.org.id}/upgrade/",
            json.dumps({"plan": "invalid-plan"}),
            content_type='application/json',
            **headers
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_personal_org_can_upgrade_to_pro(self):
        """Personal organization acts as the user's subscription anchor and can upgrade to PRO."""
        # Create personal org
        personal_org = Organization.objects.create(
            name="Personal Org",
            slug="personal-org-upgrade",
            owner=self.user_admin,
            org_type=Organization.OrgType.PERSONAL,
            plan=Organization.Plan.FREE
        )
        Membership.objects.create(
            user=self.user_admin,
            organization=personal_org,
            role=Membership.Role.ADMIN
        )

        self.client.force_authenticate(user=self.user_admin)
        headers = {'HTTP_X_ORGANIZATION_ID': str(personal_org.id)}

        response = self.client.post(
            f"/api/v1/organizations/{personal_org.id}/upgrade/",
            json.dumps({"plan": "pro"}),
            content_type='application/json',
            **headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify plan changed
        personal_org.refresh_from_db()
        self.assertEqual(personal_org.plan, Organization.Plan.PRO)

    def test_upgrade_requires_org_header(self):
        """Upgrade endpoint should require X-Organization-ID header"""
        self.client.force_authenticate(user=self.user_admin)

        response = self.client.post(
            f"/api/v1/organizations/{self.org.id}/upgrade/",
            json.dumps({"plan": "pro"}),
            content_type='application/json'
        )

        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_upgrade_to_enterprise(self):
        """Admin should also be able to upgrade to enterprise"""
        self.client.force_authenticate(user=self.user_admin)
        headers = {'HTTP_X_ORGANIZATION_ID': str(self.org.id)}

        response = self.client.post(
            f"/api/v1/organizations/{self.org.id}/upgrade/",
            json.dumps({"plan": "enterprise"}),
            content_type='application/json',
            **headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan'], 'enterprise')
        
        self.org.refresh_from_db()
        self.assertEqual(self.org.plan, Organization.Plan.ENTERPRISE)

    def test_user_cannot_create_team_org_without_pro(self):
        """Freemium users cannot create an additional organization."""
        personal_org = Organization.objects.create(
            name="Personal Org Create Team",
            slug="personal-org-create-team",
            owner=self.user_other,
            org_type=Organization.OrgType.PERSONAL,
            plan=Organization.Plan.FREE,
        )
        Membership.objects.create(
            user=self.user_other,
            organization=personal_org,
            role=Membership.Role.ADMIN,
        )

        self.client.force_authenticate(user=self.user_other)
        response = self.client.post(
            "/api/v1/organizations/create-team/",
            json.dumps({
                "name": "Nova Team",
                "slug": "nova-team",
                "description": "Org de equipe inicial",
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_create_single_team_org_after_personal_upgrade(self):
        """A PRO user can create one additional TEAM organization."""
        personal_org = Organization.objects.create(
            name="Personal Org Second Team",
            slug="personal-org-second-team",
            owner=self.user_other,
            org_type=Organization.OrgType.PERSONAL,
            plan=Organization.Plan.PRO,
        )
        Membership.objects.create(
            user=self.user_other,
            organization=personal_org,
            role=Membership.Role.ADMIN,
        )

        self.client.force_authenticate(user=self.user_other)
        response = self.client.post(
            "/api/v1/organizations/create-team/",
            json.dumps({
                "name": "First Team",
                "slug": "first-team",
                "description": "Outra org de equipe",
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['plan'], Organization.Plan.PRO)

    def test_user_cannot_create_second_team_org_even_with_pro(self):
        """PRO users are limited to one additional TEAM organization."""
        personal_org = Organization.objects.create(
            name="Personal Org Additional Limit",
            slug="personal-org-additional-limit",
            owner=self.user_other,
            org_type=Organization.OrgType.PERSONAL,
            plan=Organization.Plan.PRO,
        )
        first_team_org = Organization.objects.create(
            name="First Team Org",
            slug="first-team-org-limit",
            owner=self.user_other,
            org_type=Organization.OrgType.TEAM,
            plan=Organization.Plan.PRO,
        )
        Membership.objects.create(
            user=self.user_other,
            organization=personal_org,
            role=Membership.Role.ADMIN,
        )
        Membership.objects.create(
            user=self.user_other,
            organization=first_team_org,
            role=Membership.Role.ADMIN,
        )

        self.client.force_authenticate(user=self.user_other)
        response = self.client.post(
            "/api/v1/organizations/create-team/",
            json.dumps({
                "name": "Second Team",
                "slug": "second-team",
                "description": "Outra org de equipe",
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
