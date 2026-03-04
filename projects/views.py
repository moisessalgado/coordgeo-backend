from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

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

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.active_organization,
            created_by=self.request.user,
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

    def perform_create(self, serializer):
        active_org = self.request.active_organization
        project = serializer.validated_data.get("project")
        datasource = serializer.validated_data.get("datasource")

        if project and project.organization_id != active_org.id:
            raise ValidationError({"project": "Project must belong to active organization."})

        if datasource and datasource.organization_id != active_org.id:
            raise ValidationError({"datasource": "Datasource must belong to active organization."})

        serializer.save()
