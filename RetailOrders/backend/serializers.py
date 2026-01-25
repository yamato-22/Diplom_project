from rest_framework import serializers
from .models import User, Contact, Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name', 'url', 'state_orders', 'owner',)
        read_only_fields = ('id',)
        extra_kwargs = {
            'owner': {'write_only': True}
        }

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'phone', 'city', 'street', 'structure', 'building', 'apartment', 'user')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)
    company = CompanySerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'company', 'position', 'contacts')
        read_only_fields = ('id',)

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Создание нового юзера
    """

    # Пароль содержит не менее 8 символов, не более 128,
    # не может быть прочитан клиентской стороной
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'username': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
            'password': {'write_only': True, 'required': True, 'allow_blank': False},
        }

    def create(self, validated_data):
        # Используем свой метод create_user
        return User.objects.create_user(**validated_data)