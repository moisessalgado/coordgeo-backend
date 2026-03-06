from rest_framework import serializers

from .models import Project, Layer


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ("organization", "created_by", "created_at", "updated_at")


class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")
