from rest_framework import viewsets

from .models import Project, Layer
from .serializers import ProjectSerializer, LayerSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        org_ids = user.org_memberships.values_list("organization_id", flat=True)
        return Project.objects.select_related("organization", "created_by").filter(
            organization_id__in=org_ids
        )


class LayerViewSet(viewsets.ModelViewSet):
    serializer_class = LayerSerializer

    def get_queryset(self):
        user = self.request.user
        org_ids = user.org_memberships.values_list("organization_id", flat=True)
        return Layer.objects.select_related("project", "datasource").filter(
            project__organization_id__in=org_ids
        )
