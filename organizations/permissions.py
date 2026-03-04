from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from organizations.models import Membership


class IsOrgMember(permissions.BasePermission):
    """
    Permission que valida se o usuário é membro da organização especificada via header.
    
    Requisitos:
    1. Usuário deve estar autenticado (checado por IsAuthenticated)
    2. Header X-Organization-ID deve estar presente  
    3. Usuário deve ser membro da organização especificada
    """
    
    message = "Permission denied or organization context is missing."
    
    def has_permission(self, request, view):
        # Extrair header X-Organization-ID
        org_id = request.headers.get('X-Organization-ID')
        
        if not org_id:
            raise ValidationError({'detail': 'X-Organization-ID header required'})
        
        try:
            # Validar que o usuário é membro da organização
            membership = Membership.objects.get(
                organization_id=org_id,
                user=request.user
            )
            # Settar no request para uso posterior nos ViewSets
            request.active_organization = membership.organization
            request.active_membership = membership
            return True
        except Membership.DoesNotExist:
            raise PermissionDenied(
                'User is not member of specified organization'
            )
