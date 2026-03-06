from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOrgMember])
    def upgrade(self, request, pk=None):
        """
        Upgrade an organization's plan.
        Only admins can upgrade their organization.
        """
        org = self.get_object()
        
        # Check if user is admin of this organization
        membership = getattr(request, 'active_membership', None)
        if membership is None or membership.role != Membership.Role.ADMIN:
            return Response(
                {'detail': 'Only admins can upgrade the organization plan'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the target plan from request body
        target_plan = request.data.get('plan')
        if not target_plan:
            return Response(
                {'detail': 'plan field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate plan choice
        valid_plans = [choice[0] for choice in Organization.Plan.choices]
        if target_plan not in valid_plans:
            return Response(
                {'detail': f'Invalid plan. Valid options: {valid_plans}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # PERSONAL orgs can only have FREE plan
        if org.org_type == Organization.OrgType.PERSONAL and target_plan != Organization.Plan.FREE:
            return Response(
                {'detail': 'Personal organizations can only use the free plan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the plan
        org.plan = target_plan
        org.save(update_fields=['plan'])
        
        serializer = self.get_serializer(org)
        return Response(serializer.data, status=status.HTTP_200_OK)


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

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)


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

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)
