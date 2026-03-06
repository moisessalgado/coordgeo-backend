from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import UserSerializer, RegisterSerializer
from organizations.models import Organization
from organizations.permissions import IsOrgMember
from organizations.serializers import OrganizationSerializer


class RegisterView(APIView):
    """
    Endpoint público para registro de novos usuários.
    
    POST /api/v1/auth/register/
    Body: { "email": "user@example.com", "password": "senha123" }
    Response: { "id": 1, "email": "user@example.com", "username": "user" }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    
    Retorna TODAS as organizações (membros + owned).
    Filtragem de visibilidade (esconder PERSONAL, etc) fica para o frontend.
    
    Não requer X-Organization-ID header.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Retorna todas as organizações do usuário autenticado
        # Combina:
        # 1. Organizações onde é membro (via Membership)
        # 2. Organizações que ele criou (owned_organizations)
        from django.db.models import Q
        
        organizations = Organization.objects.filter(
            Q(members__user=request.user) |  # Membro de organização
            Q(owner=request.user)            # Proprietário de organização
        ).distinct()
        
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDefaultOrganizationView(APIView):
    """
    Retorna a organização padrão do usuário (primeira PERSONAL ou primeira da lista).
    
    Usado para auto-selecionar organização para usuários freemium que não veem
    a lista de organizações.
    
    Não requer X-Organization-ID header.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Buscar organizações do usuário
        organizations = Organization.objects.filter(
            members__user=request.user
        ).distinct()
        
        # Prioridade: PERSONAL > primeira da lista
        default_org = (
            organizations.filter(org_type=Organization.OrgType.PERSONAL).first()
            or organizations.first()
        )
        
        if not default_org:
            return Response(
                {"detail": "Usuário não tem organizações."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = OrganizationSerializer(default_org)
        return Response(serializer.data, status=status.HTTP_200_OK)
