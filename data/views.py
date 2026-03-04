from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Datasource
from .serializers import DatasourceSerializer
from organizations.permissions import IsOrgMember


class DatasourceViewSet(viewsets.ModelViewSet):
    serializer_class = DatasourceSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        # Filter datasources by active organization
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        return Datasource.objects.select_related("organization", "created_by").filter(
            organization=active_org
        )
