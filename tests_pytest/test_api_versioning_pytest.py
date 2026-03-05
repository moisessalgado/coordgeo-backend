import pytest
import uuid
from rest_framework import status
from rest_framework.test import APIClient

from organizations.models import Membership, Organization


@pytest.mark.django_db
def test_token_endpoint_available_on_v1_only(user_factory):
    user_factory(
        username="version-user-pytest",
        email="version-user-pytest@example.com",
        password="testpass123",
    )

    client = APIClient()

    payload = {
        "email": "version-user-pytest@example.com",
        "password": "testpass123",
    }

    response_v1 = client.post("/api/v1/token/", payload, format="json")
    assert response_v1.status_code == status.HTTP_200_OK
    assert "access" in response_v1.data
    assert "refresh" in response_v1.data


@pytest.mark.django_db
def test_user_organizations_endpoint_available_on_v1_only(user_factory):
    user = user_factory(
        username="version-org-pytest",
        email="version-org-pytest@example.com",
        password="testpass123",
    )

    # Usar UUID para garantir slug único
    unique_slug = f"version-org-pytest-{uuid.uuid4().hex[:8]}"
    
    organization = user.owned_organizations.create(
        name="Version Org Pytest",
        slug=unique_slug,
        org_type=Organization.OrgType.TEAM,
        plan=Organization.Plan.PRO,
    )

    Membership.objects.get_or_create(
        user=user,
        organization=organization,
        defaults={"role": Membership.Role.ADMIN},
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response_v1 = client.get("/api/v1/user/organizations/")
    assert response_v1.status_code == status.HTTP_200_OK
    assert len(response_v1.data) >= 1
