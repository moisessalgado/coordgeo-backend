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
def project_factory(db):
    """
    Factory para criar projetos.
    
    Uso:
        project = project_factory(name="My Project", organization=org)
    """
    from projects.models import Project

    def factory(*, name: str, organization, created_by=None, description: str = ""):
        return Project.objects.create(
            name=name,
            organization=organization,
            created_by=created_by,
            description=description,
        )

    return factory


@pytest.fixture
def datasource_factory(db):
    """
    Factory para criar datasources.
    
    Uso:
        datasource = datasource_factory(
            name="My Data",
            organization=org,
            created_by=user,
            datasource_type="vector",
            storage_url="s3://bucket/data.geojson"
        )
    """
    from data.models import Datasource

    def factory(
        *,
        name: str,
        organization,
        created_by,
        datasource_type: str = Datasource.Type.VECTOR,
        storage_url: str = "s3://bucket/data.geojson",
        description: str = "",
    ):
        return Datasource.objects.create(
            name=name,
            organization=organization,
            created_by=created_by,
            datasource_type=datasource_type,
            storage_url=storage_url,
            description=description,
        )

    return factory


@pytest.fixture
def layer_factory(db):
    """
    Factory para criar layers.
    
    Uso:
        layer = layer_factory(name="My Layer", project=project, datasource=datasource)
    """
    from projects.models import Layer

    def factory(
        *,
        name: str,
        project,
        datasource,
        description: str = "",
        visibility: bool = True,
        z_index: int = 0,
    ):
        return Layer.objects.create(
            name=name,
            project=project,
            datasource=datasource,
            description=description,
            visibility=visibility,
            z_index=z_index,
        )

    return factory


@pytest.fixture
def api_client():
    """
    Cliente DRF para testes de API.
    
    Uso:
        response = api_client.get("/api/v1/users/", **headers)
    """
    return APIClient()
