from rest_framework import viewsets

from .models import Organization, Membership, Team
from .serializers import OrganizationSerializer, MembershipSerializer, TeamSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        user = self.request.user
        org_ids = user.org_memberships.values_list("organization_id", flat=True)
        return Organization.objects.filter(id__in=org_ids)


class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer

    def get_queryset(self):
        user = self.request.user
        org_ids = user.org_memberships.values_list("organization_id", flat=True)
        return Membership.objects.select_related("user", "organization").filter(
            organization_id__in=org_ids
        )


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer

    def get_queryset(self):
        user = self.request.user
        org_ids = user.org_memberships.values_list("organization_id", flat=True)
        return Team.objects.select_related("organization").prefetch_related("members").filter(
            organization_id__in=org_ids
        )
