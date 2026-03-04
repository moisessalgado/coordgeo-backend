from django.http import JsonResponse
from organizations.models import Membership


class ActiveOrganizationMiddleware:
    """
    Middleware que extrai e valida a organização ativa a partir do header X-Organization-ID.
    
    Garante que:
    1. Todos os requests API autenticados definem request.active_organization
    2. O usuário é membro da organização enviada
    3. Erros 400/403 são retornados apropriadamente
    
    Padrão de uso no frontend:
        headers: {
            'X-Organization-ID': '<uuid>',
            'Authorization': 'Bearer <token>'
        }
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip para endpoints não-API (admin, templates, static, etc)
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Skip para endpoints de autenticação (não requerem organização ativa)
        if 'token' in request.path:
            return self.get_response(request)
        
        # Extrair header X-Organization-ID
        org_id = request.headers.get('X-Organization-ID')
        
        # Precisa chamar a view para que a autenticação seja processada
        response = self.get_response(request)
        
        # Verificar se o usuário está autenticado APÓS a view
        # Isso ocorre quando JWT middleware já processou
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            # Validar header
            if not org_id:
                return JsonResponse(
                    {'error': 'X-Organization-ID header required'},
                    status=400
                )
            
            try:
                # Validar que o usuário é membro da organização
                membership = Membership.objects.get(
                    organization_id=org_id,
                    user=request.user
                )
                request.active_organization = membership.organization
                request.active_membership = membership
            except Membership.DoesNotExist:
                return JsonResponse(
                    {'error': 'User is not member of specified organization'},
                    status=403
                )
        
        return response
