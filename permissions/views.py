from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db.models import Q

from .models import Permission
from .serializers import PermissionSerializer
from organizations.permissions import IsOrgMember
from organizations.models import Membership
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

    def perform_create(self, serializer):
        active_org = self.request.active_organization
        resource_type = serializer.validated_data.get("resource_type")
        resource_id = serializer.validated_data.get("resource_id")
        subject_user = serializer.validated_data.get("subject_user")
        subject_team = serializer.validated_data.get("subject_team")

        if subject_team and subject_team.organization_id != active_org.id:
            raise ValidationError({"subject_team": "Team must belong to active organization."})

        if subject_user and not Membership.objects.filter(
            organization=active_org,
            user=subject_user,
        ).exists():
            raise ValidationError({"subject_user": "User must be member of active organization."})

        if resource_type == Permission.ResourceType.ORGANIZATION:
            serializer.save(
                resource_id=active_org.id,
                granted_by=self.request.user,
            )
            return

        if resource_type == Permission.ResourceType.PROJECT:
            if not Project.objects.filter(id=resource_id, organization=active_org).exists():
                raise ValidationError({"resource_id": "Project must belong to active organization."})
            serializer.save(granted_by=self.request.user)
            return

        if resource_type == Permission.ResourceType.DATASOURCE:
            if not Datasource.objects.filter(id=resource_id, organization=active_org).exists():
                raise ValidationError({"resource_id": "Datasource must belong to active organization."})
            serializer.save(granted_by=self.request.user)
            return

        raise ValidationError({"resource_type": "Unsupported resource_type."})
