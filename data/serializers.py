from rest_framework import serializers

from .models import Datasource


class DatasourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Datasource
        fields = "__all__"
        read_only_fields = ("organization", "created_by", "created_at", "updated_at")
