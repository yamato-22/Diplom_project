from rest_framework import serializers
from .models import User, Contact, Company, Category, Product, Property, ProductProperty, Order, OrderItem
from django.utils.translation import gettext_lazy as _


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
            'user': {'write_only': True},
            'phone': {'required': True, 'allow_blank': False},
            'city': {'required': True, 'allow_blank': False},
            'street': {'required': True, 'allow_blank': False},
            'apartment': {'required': True, 'allow_blank': False},
        }



class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)
    company = CompanySerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'middle_name',
                  'email', 'company', 'position', 'contacts')
        read_only_fields = ('id','email')

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
        fields = ('first_name', 'last_name', 'middle_name', 'position', 'username', 'email', 'password')
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'middle_name': {'required': False, 'allow_blank': True},
            'position': {'required': False, 'allow_blank': True},
            'username': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
            'password': {'write_only': True, 'required': True, 'allow_blank': False},
        }

    def create(self, validated_data):
        # Используем переопределенный в менеджере пользователей метод create_user
        return User.objects.create_user(**validated_data)


class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        max_length=128, write_only=True, required=True
    )
    new_password = serializers.CharField(
        max_length=128, min_length=8, write_only=True, required=True
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _('Your old password was entered incorrectly. Please enter it again.')
            )
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    company = CompanySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ('name', 'description', 'article', 'quantity', 'price', 'category', 'company')

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ('name', 'value')


class ProductPropertySerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    property = PropertySerializer(read_only=True)
    class Meta:
        model = ProductProperty
        fields = ('product', 'property', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(write_only=True)
    class Meta:
        model = Order
        fields = ('id', 'created_at', 'updated_at', 'status', 'total_amount','user')
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product', 'quantity', 'total_cost')
        read_only_fields = ('id')