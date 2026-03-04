from rest_framework import viewsets

from .models import Datasource
from .serializers import DatasourceSerializer


class DatasourceViewSet(viewsets.ModelViewSet):
    serializer_class = DatasourceSerializer

    def get_queryset(self):
        user = self.request.user
        org_ids = user.org_memberships.values_list("organization_id", flat=True)
        return Datasource.objects.select_related("organization", "created_by").filter(
            organization_id__in=org_ids
        )
