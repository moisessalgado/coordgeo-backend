from rest_framework import serializers

from .models import User


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

    class Meta:
        model = User
        fields = ['email', 'password', 'username']
        extra_kwargs = {
            'username': {'required': False}  # username será gerado automaticamente
        }

    def create(self, validated_data):
        # Se username não foi fornecido, gerar a partir do email
        if 'username' not in validated_data or not validated_data['username']:
            validated_data['username'] = validated_data['email'].split('@')[0]
        
        # Criar usuário usando create_user (que já faz hash da senha)
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

