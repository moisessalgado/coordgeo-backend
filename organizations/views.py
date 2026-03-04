from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Organization, Membership, Team
from .serializers import OrganizationSerializer, MembershipSerializer, TeamSerializer
from organizations.permissions import IsOrgMember


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        # Return only the active organization
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        return Organization.objects.filter(id=active_org.id)


class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        # Show members of active organization only
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        return Membership.objects.select_related("user", "organization").filter(
            organization=active_org
        )


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        # Show teams of active organization only
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        return Team.objects.select_related("organization").prefetch_related("members").filter(
            organization=active_org
        )
