from rest_framework import serializers

from .models import Organization, Membership, Team


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"


class CreateTeamOrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a TEAM organization.
    Only allows name, slug, and description.
    owner and org_type are set by the view.
    """
    class Meta:
        model = Organization
        fields = ['name', 'slug', 'description']


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = "__all__"


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"
