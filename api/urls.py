from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path

from accounts.views import UserViewSet, UserOrganizationsView
from organizations.views import OrganizationViewSet, MembershipViewSet, TeamViewSet
from projects.views import ProjectViewSet, LayerViewSet
from data.views import DatasourceViewSet
from permissions.views import PermissionViewSet


# Create a single router for the entire API
router = DefaultRouter()

# Register all viewsets with explicit basenames
router.register(r"users", UserViewSet, basename="user")
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"memberships", MembershipViewSet, basename="membership")
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"layers", LayerViewSet, basename="layer")
router.register(r"datasources", DatasourceViewSet, basename="datasource")
router.register(r"permissions", PermissionViewSet, basename="permission")

# JWT Authentication endpoints
urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/organizations/', UserOrganizationsView.as_view(), name='user_organizations'),
]

urlpatterns += router.urls
