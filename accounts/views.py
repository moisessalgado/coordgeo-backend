from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import UserSerializer
from organizations.models import Organization
from organizations.permissions import IsOrgMember
from organizations.serializers import OrganizationSerializer


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        # Filter users by active organization membership
        # active_organization é setado pela permission class IsOrgMember
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        return User.objects.filter(
            org_memberships__organization=active_org
        ).distinct()


class UserOrganizationsView(APIView):
    """
    Endpoint para listar organizações do usuário logado.
    
    Usado no bootstrap do frontend para permitir que o usuário selecione
    qual organização deseja usar (sem paradoxo de header obrigatório).
    
    Não requer X-Organization-ID header.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Retorna todas as organizações do usuário autenticado
        organizations = Organization.objects.filter(
            members__user=request.user
        ).distinct()
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
