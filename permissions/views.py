from rest_framework import viewsets
from django.db.models import Q

from .models import Permission
from .serializers import PermissionSerializer
from organizations.models import Organization
from projects.models import Project
from data.models import Datasource


class PermissionViewSet(viewsets.ModelViewSet):
    serializer_class = PermissionSerializer

    def get_queryset(self):
        user = self.request.user
        org_ids = list(user.org_memberships.values_list("organization_id", flat=True))
        # permissions on organizations they belong to
        qs = Permission.objects.select_related("subject_user", "subject_team", "granted_by")
        return qs.filter(
            Q(resource_type="organization", resource_id__in=org_ids)
            | Q(resource_type="project", resource_id__in=Project.objects.filter(organization_id__in=org_ids).values_list("id", flat=True))
            | Q(resource_type="datasource", resource_id__in=Datasource.objects.filter(organization_id__in=org_ids).values_list("id", flat=True))
        )
