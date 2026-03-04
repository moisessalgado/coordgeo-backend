from rest_framework.routers import DefaultRouter

from accounts.views import UserViewSet
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

urlpatterns = router.urls
