from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Permission
from .serializers import PermissionSerializer
from organizations.permissions import IsOrgMember
from projects.models import Project
from data.models import Datasource


class PermissionViewSet(viewsets.ModelViewSet):
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        # Permissions on resources owned by active organization
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        qs = Permission.objects.select_related("subject_user", "subject_team", "granted_by")
        return qs.filter(
            Q(resource_type="organization", resource_id=active_org.id)
            | Q(resource_type="project", resource_id__in=Project.objects.filter(organization=active_org).values_list("id", flat=True))
            | Q(resource_type="datasource", resource_id__in=Datasource.objects.filter(organization=active_org).values_list("id", flat=True))
        )
