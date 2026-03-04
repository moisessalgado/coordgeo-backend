from rest_framework import serializers

from .models import Datasource


class DatasourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Datasource
        fields = "__all__"
