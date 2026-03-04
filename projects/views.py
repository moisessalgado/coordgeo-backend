from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Project, Layer
from .serializers import ProjectSerializer, LayerSerializer
from organizations.permissions import IsOrgMember


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        # Filter projects by active organization
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        return Project.objects.select_related("organization", "created_by").filter(
            organization=active_org
        )


class LayerViewSet(viewsets.ModelViewSet):
    serializer_class = LayerSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        # Filter layers by active organization (via project)
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        return Layer.objects.select_related("project", "datasource").filter(
            project__organization=active_org
        )
