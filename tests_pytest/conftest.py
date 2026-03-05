import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def user_factory(db):
    """
    Factory para criar usuários.
    
    Uso:
        user = user_factory(username="alice", email="alice@test.com")
    """
    user_model = get_user_model()

    def factory(*, username: str, email: str, password: str = "testpass123"):
        return user_model.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

    return factory


@pytest.fixture
def org_factory(db, user_factory):
    """
    Factory para criar organizações.
    
    Uso:
        owner = user_factory(username="owner", email="owner@test.com")
        org = org_factory(name="My Org", slug="my-org", owner=owner)
    """
    from organizations.models import Organization

    def factory(
        *,
        name: str,
        slug: str,
        owner,
        org_type: str = Organization.OrgType.PERSONAL,
        plan: str = Organization.Plan.FREE,
        description: str = "",
    ):
        return Organization.objects.create(
            name=name,
            slug=slug,
            owner=owner,
            org_type=org_type,
            plan=plan,
            description=description,
        )

    return factory


@pytest.fixture
def membership_factory(db):
    """
    Factory para criar memberships (relacionamento user-org).
    
    Uso:
        membership = membership_factory(user=user, organization=org, role="admin")
    """
    from organizations.models import Membership

    def factory(*, user, organization, role: str = Membership.Role.MEMBER):
        return Membership.objects.create(
            user=user,
            organization=organization,
            role=role,
        )

    return factory


@pytest.fixture
def jwt_token_factory():
    """
    Factory para gerar tokens JWT de autenticação.
    
    Uso:
        token = jwt_token_factory(user)
    """
    def factory(user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    return factory


@pytest.fixture
def org_headers_factory(jwt_token_factory):
    """
    Factory para gerar headers HTTP completos com autenticação e org scope.
    
    Uso:
        headers = org_headers_factory(user=user, org=org)
        response = api_client.get("/api/v1/users/", **headers)
    """
    def factory(*, user, org):
        token = jwt_token_factory(user)
        return {
            'HTTP_AUTHORIZATION': f'Bearer {token}',
            'HTTP_X_ORGANIZATION_ID': str(org.id),
        }

    return factory


@pytest.fixture
def api_client():
    """
    Cliente DRF para testes de API.
    
    Uso:
        response = api_client.get("/api/v1/users/", **headers)
    """
    return APIClient()
