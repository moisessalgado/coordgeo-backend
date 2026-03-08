from rest_framework import serializers

from .models import User
from organizations.models import Organization


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Creates a new user with email and password.
    """
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    email = serializers.EmailField(required=True)
    plan = serializers.ChoiceField(
        choices=[Organization.Plan.FREE, Organization.Plan.PRO],
        required=False,
        default=Organization.Plan.FREE,
        write_only=True,
    )

    class Meta:
        model = User
        fields = ['email', 'password', 'username', 'plan']
        extra_kwargs = {
            'username': {'required': False}  # username será gerado automaticamente
        }

    def create(self, validated_data):
        selected_plan = validated_data.pop('plan', Organization.Plan.FREE)

        # Se username não foi fornecido, gerar a partir do email
        if 'username' not in validated_data or not validated_data['username']:
            validated_data['username'] = validated_data['email'].split('@')[0]
        
        # Build and save the user explicitly so post_save sees the selected plan.
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
        )
        user._selected_signup_plan = selected_plan
        user.set_password(validated_data['password'])
        user.save()
        return user

