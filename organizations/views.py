from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

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

    def perform_create(self, serializer):
        """
        Criar uma nova organização.
        Restrições:
        - TEAM orgs só podem ser criadas por users com plano PRO/ENTERPRISE
        - Um usuário PRO pode criar apenas uma organização adicional além da personal
        - User será automaticamente o owner
        """
        from django.db.models import Q
        
        org_type = serializer.validated_data.get('org_type', Organization.OrgType.TEAM)
        
        # Apenas TEAM orgs podem ser criadas via API na prática
        # (PERSONAL são criadas automaticamente no signup)
        if org_type == Organization.OrgType.TEAM:
            # Verificar se user tem pelo menos uma organização PRO
            user_orgs = Organization.objects.filter(
                Q(owner=self.request.user) | Q(members__user=self.request.user)
            ).distinct()
            
            has_paid_plan = user_orgs.filter(
                plan__in=[Organization.Plan.PRO, Organization.Plan.ENTERPRISE]
            ).exists()
            existing_team_orgs = user_orgs.filter(org_type=Organization.OrgType.TEAM).count()

            if not has_paid_plan:
                raise PermissionDenied(
                    'Você precisa ter plano PRO para criar organizações em equipe. '
                    'Faça upgrade de uma organização existente primeiro.'
                )

            if existing_team_orgs >= 1:
                raise PermissionDenied(
                    'Seu plano PRO permite apenas uma organização adicional além da personal.'
                )
        
        # User será o owner da nova organização
        serializer.save(owner=self.request.user)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],  # Override viewset's IsOrgMember
        url_path='create-team'
    )
    def create_team(self, request):
        """
        Criar uma nova organização TEAM.
        Requer plano PRO/Enterprise em alguma organização existente.
        Permite apenas uma organização TEAM adicional além da personal.
        
        POST /organizations/create-team/
        Body: { "name": "...", "slug": "...", "description": "..." }
        """
        from django.db.models import Q
        from organizations.serializers import CreateTeamOrganizationSerializer
        
        # Verificar se user tem pelo menos uma organização PRO
        user_orgs = Organization.objects.filter(
            Q(owner=request.user) | Q(members__user=request.user)
        ).distinct()
        
        paid_orgs = user_orgs.filter(
            plan__in=[Organization.Plan.PRO, Organization.Plan.ENTERPRISE]
        )
        has_paid_plan = paid_orgs.exists()
        team_org_count = user_orgs.filter(org_type=Organization.OrgType.TEAM).count()

        if not has_paid_plan:
            raise PermissionDenied(
                'Você precisa ter plano PRO para criar organizações em equipe. '
                'Faça upgrade da sua organização pessoal primeiro.'
            )

        if team_org_count >= 1:
            raise PermissionDenied(
                'Seu plano PRO permite apenas uma organização adicional além da personal.'
            )

        paid_plan = Organization.Plan.ENTERPRISE if paid_orgs.filter(
            plan=Organization.Plan.ENTERPRISE
        ).exists() else Organization.Plan.PRO
        
        # Criar a nova TEAM org usando serializer específico
        serializer = CreateTeamOrganizationSerializer(data=request.data)
        if serializer.is_valid():
            # Garantir que é TEAM org e set owner
            org = serializer.save(
                org_type=Organization.OrgType.TEAM,
                plan=paid_plan,
                owner=request.user
            )
            
            # Criar membership automático como admin
            Membership.objects.create(
                user=request.user,
                organization=org,
                role=Membership.Role.ADMIN
            )
            
            return Response(
                OrganizationSerializer(org).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        active_org = self.request.active_organization
        active_membership = getattr(self.request, 'active_membership', None)

        if active_org.org_type != Organization.OrgType.TEAM:
            raise PermissionDenied(
                'Teams só podem ser criados em organizações em equipe.'
            )

        if active_org.plan not in [Organization.Plan.PRO, Organization.Plan.ENTERPRISE]:
            raise PermissionDenied(
                'Você precisa ter plano PRO para criar teams nesta organização.'
            )

        if active_membership is None or active_membership.role != Membership.Role.ADMIN:
            raise PermissionDenied(
                'Apenas admins podem criar teams.'
            )

        serializer.save(organization=active_org)
