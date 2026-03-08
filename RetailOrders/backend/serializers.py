import re
from rest_framework import serializers
from .models import User, Contact, Company, Category, Product, Property, ProductProperty, Order, OrderItem
from django.utils.translation import gettext_lazy as _


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name', 'url', 'state_orders', 'owner',)
        read_only_fields = ('id',)

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
                  'email', 'company', 'position', 'role', 'contacts')
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

    def validate_password(self, value):
        """
        Проверка пароля на сложность
        """

        if len(value) < 8:
            raise serializers.ValidationError("The password length must be at least 8 characters")

        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("The password must contain at least one digit")

        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("The password must contain one uppercase letter")

        if not any(char.islower() for char in value):
            raise serializers.ValidationError("The password must contain one lowercase letter")

        special_characters = r"[ !@#$%^&*()?/{}|~<>]"
        if not re.search(special_characters, value):
            raise serializers.ValidationError("The password must contain at least one special character")

        return value

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
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())

    class Meta:
        model = Product
        fields = ('id', 'name', 'model', 'description', 'article', 'quantity', 'price',
                  'price_rrc', 'category', 'company')
        read_only_fields = ('id',)
        extra_kwargs = {
            'name': {'required': True, 'allow_blank': False},
            'model': {'required': False, 'allow_blank': True},
            'description': {'required': False, 'allow_blank': True},
            'article': {'required': True, 'allow_blank': False},
            'quantity': {'required': True},
            'price': {'required': True},
            'price_rrc': {'required': True},
            'category': {'required': True},
            'company': {'required': True},
        }

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ('id', 'name', 'value')
        read_only_fields = ('id',)



class ProductPropertySerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())

    class Meta:
        model = ProductProperty
        fields = ('id', 'product', 'property', 'quantity')
        read_only_fields = ('id',)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['product_name'] = instance.product.name
        representation['property_name'] = instance.property.name
        return representation

class PropertyNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ('name',)
        read_only_fields = ('name',)

class ProductPropertySetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для набора характеристик продукта.
    """
    name = serializers.CharField(source='property.name', read_only=True)

    class Meta:
        model = ProductProperty
        fields = ('name', 'quantity')

class ProductAllPropertySerializer(serializers.ModelSerializer):
    """
    Главный сериализатор для модели продукта, содержащий вложенный сериализатор характеристик.
    """
    company = serializers.CharField(source='company.name', read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)
    properties = ProductPropertySetSerializer(source='products', many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'article', 'quantity', 'price', 'price_rrc',
            'category', 'company', 'properties',
        )
        read_only_fields = ('id',)

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(write_only=True)
    class Meta:
        model = Order
        fields = ('id', 'created_at', 'updated_at', 'status', 'total_amount','user')
        read_only_fields = ('id',)

class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'status', 'total_amount')
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product', 'quantity', 'total_cost')
        read_only_fields = ('id',)

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'total_cost']

class OrderDetailSerializer(serializers.ModelSerializer):
    order_items = ItemSerializer(source='order', many=True, read_only=True)
    class Meta:
        model = Order
        fields = ('id', 'created_at', 'updated_at', 'status', 'total_amount', 'order_items')
        read_only_fields = ('id',)
