from rest_framework import serializers
from models import User


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор Юзера  (создание нового, регистраця существующего).
    """

    # Пароль содержит не менее 8 символов, не более 128,
    # не может быть прочитан клиентской стороной
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True
    )

    # Клиент не имеет права отправлять токен в запросе на регистрацию,
    # только на чтение.
    token = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        # Разрешенные поля в запросе или ответе
        fields = ['email', 'username', 'password', 'token']

    def create(self, validated_data):
        # Используем свой метод create_user
        return User.objects.create_user(**validated_data)