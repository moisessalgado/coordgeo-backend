from rest_framework import viewsets

from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        # restrict to users in same organizations
        org_ids = user.org_memberships.values_list("organization_id", flat=True)
        return User.objects.filter(org_memberships__organization_id__in=org_ids).distinct()
