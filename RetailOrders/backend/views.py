from rest_framework.parsers import MultiPartParser
from django.contrib.auth.password_validation import validate_password
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from django.http import JsonResponse
from rest_framework import status
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import add_product_to_order, remove_product_from_order, load_data_from_yaml, set_confirm_order_user
from .models import Contact, Company, Product, Category, Property, ProductProperty, Order
from .serializers import (UserSerializer, UserCreateSerializer, UserChangePasswordSerializer,
                          ContactSerializer, CompanySerializer, ProductSerializer,
                          CategorySerializer, PropertySerializer, ProductPropertySerializer,
                          ProductAllPropertySerializer, OrderCreateSerializer, OrderSerializer,
                          OrderDetailSerializer)


# Create your views here.
class RegisterAccount(APIView):
    """
    Регистрация юзеров
    """
    permission_classes = (AllowAny,)


    def post(self, request, *args, **kwargs):

        if {'first_name', 'last_name', 'email', 'password', 'username'}.issubset(request.data):

            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                user_serializer = UserCreateSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user_serializer.save()
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})



class UserRetrieveUpdate(APIView):
    """
    Retrieve details and Update authenticated user
    Methods:
    - get: Retrieve the details of the authenticated user.
    - post: Update the details of the authenticated user.
    """

    # Allow only authenticated users to access this url
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request: Request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        serializer = UserSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()  # Сохраняем обновленные данные
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangeUserPasswordView(APIView):
    """
    Changing the password of an authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UserChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            return Response({"Message": "Password was changed"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContactsView(APIView):
    """
    Getting a list of contacts and creating a new contact
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Retrieve the contact information of the authenticated user
        :param request: standard request
        :return: standard response
        """

        contact = Contact.objects.filter(
            user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new contact for the authenticated user.
        :param request: standard request
        :return: standard response
        """
        request.data._mutable = True
        request.data.update({'user': request.user.id})
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContactDetailView(APIView):
    """
    Viewing, updating, and deleting a specific user contact.
    The user must be authenticated.
    Methods:
    - get: Retrieve the details of the specific user contact.
    - put: Update the details of the specific user contact.
    - delete: Delete the specific user contact.
    """
    
    permission_classes = [IsAuthenticated,]

    def get_contact(self, pk, user):
        try:
            return Contact.objects.get(pk=pk, user=user)
        except Contact.DoesNotExist:
            return None

    def get(self, request, pk):
        contact = self.get_contact(pk, user = request.user)
        if contact is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ContactSerializer(contact)
        return Response(serializer.data)

    def put(self, request, pk):
        contact = self.get_contact(pk, user = request.user)
        if contact is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ContactSerializer(contact, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        contact = self.get_contact(pk, user = request.user)
        if contact is None:
            return Response({"Message": f"Contact id = {pk} not found"},
                            status=status.HTTP_404_NOT_FOUND)
        contact.delete()
        return Response({"Message": f"Contact id = {pk} successfully deleted"},
                        status=status.HTTP_204_NO_CONTENT)

class CompanyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_company(self, company_id):
        try:
            return Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return None

    def get(self, request, company_id=None):
        if company_id:
            company = self.get_company(company_id)
            if company is None:
                return Response({"Company": f"Company id = {company_id} not found"},
                                status=status.HTTP_404_NOT_FOUND)
            serializer = CompanySerializer(company)
            return Response(serializer.data)
        else:
            companies = Company.objects.all()
            serializer = CompanySerializer(companies, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, company_id):
        company = self.get_company(company_id)

        if company:
            # Проверяем, является ли текущий пользователь владельцем компании
            if company.owner != request.user:
                return Response({"Message": 'You are not the owner of this company'},
                                status=status.HTTP_403_FORBIDDEN)
            serializer = CompanySerializer(company, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"Company": f"Company id = {company_id} not found"},
                                status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, company_id):
        company = self.get_company(company_id)
        if company is None:
            return Response({"Company": f"Company id = {company_id} not found"},
                            status=status.HTTP_404_NOT_FOUND)
        # Проверяем, является ли текущий пользователь владельцем компании
        if company.owner != request.user:
            return Response({"Message": 'You are not the owner of this company'},
                            status=status.HTTP_403_FORBIDDEN)
        company_name = company.name
        company.delete()
        return Response({"Message": f"Company  {company_name} successfully deleted"},
                        status=status.HTTP_204_NO_CONTENT)

class CategoryViewSet(ModelViewSet):
    """
    ViewSet for CRUD operations with product categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    http_method_names = ['get', 'post', 'patch']

class ProductViewSet(ModelViewSet):
    """
    ViewSet for CRUD operations with product.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDetailView(generics.RetrieveAPIView):
    """
    Вид для получения детальной информации о продукте и его характеристиках.
    """
    queryset = Product.objects.all()  # Все доступные продукты
    serializer_class = ProductAllPropertySerializer  # Используемый сериализатор


class PropertyViewSet(ModelViewSet):
    """
    ViewSet for CRUD operations with property of product.
    """
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    http_method_names = ['get', 'post', 'patch']

class ProductPropertyViewSet(ModelViewSet):
    """
    ViewSet for CRUD operations with property of product.
    """
    queryset = ProductProperty.objects.all()
    serializer_class = ProductPropertySerializer
    http_method_names = ['get', 'post', 'patch', 'delete']


class OrderCreateView(generics.CreateAPIView):
    """
    Представление для создания новых заказов с автоматическим назначением пользователя и статуса.
    """
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Устанавливаем текущего аутентифицированного пользователя в качестве покупателя
        и устанавливаем статус заказа "new".
        """
        serializer.save(user=self.request.user, status="new", total_amount=0)

class UserOrdersListView(generics.ListAPIView):
    """
    Возвращает список заказов, созданных текущим аутентифицированным пользователем.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Фильтрует заказы по текущему пользователю.
        """
        user = self.request.user
        return Order.objects.filter(user=user)

class AddDeleteItemOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Добавление товара в заказ.
        """
        order_id = request.data.get('order_id')  # Получить id заказа из тела запроса
        product_id = request.data.get('product_id')  # Получить id продукта из тела запроса

        try:
            quantity = round(float(request.data.get('quantity')))
        except ValueError as e:
            return Response({'error': f'Invalid value for quantity: {request.data.get("quantity")}'}, status=400)

        user_id = request.user.id

        try:
            add_product_to_order(user_id, order_id, product_id, quantity)
            return Response({'message': 'Товар успешно добавлен в заказ.'}, status=201)
        except Exception as e:
            return Response({'Error': str(e)}, status=400)

    def delete(self, request, product_id):
        order_id = request.data.get('order_id')  # Получить id заказа из тела запроса
        user_id = request.user.id
        try:
            remove_product_from_order(user_id, order_id, product_id)
            return Response({'message': 'Товар успешно удален из заказа'}, status=201)
        except Exception as e:
            return Response({'Error': str(e)}, status=400)

class ConfirmOrderUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        """
        Устанавливаем статус подтверждения заказа пользователем
        """
        user_id = request.user.id

        try:
            # Запускаем процедуру подтверждения заказа
            confirmed_order = set_confirm_order_user(user_id, order_id)

            # Возвращаем информацию о подтверждённом заказе
            return Response({
                'Message': 'Статус заказа изменён на Подтвержден',
                'Order': {
                    'ID': confirmed_order.id,
                    'Status': confirmed_order.status
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'Error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, order_id):

        try:
            # Получаем заказ по заданному ID
            order = Order.objects.prefetch_related("order").get(pk=order_id)
        except Order.DoesNotExist:
            return Response({"Error": "Order NOT found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if order.user_id != user.id:
            return Response({"Error": "You don't own this order"}, status=status.HTTP_404_NOT_FOUND)

        # Сериализуем заказ и его элементы
        serializer = OrderDetailSerializer(order)

        # Возвращаем сериализованную версию заказа
        return Response(serializer.data, status=status.HTTP_200_OK)


class UploadYamlFileView(APIView):
    """
    Представление для загрузки данных магазина и товаров из YAML-файла.
    """
    permission_classes = [IsAuthenticated]  # Требуется аутентификация
    parser_classes = [MultiPartParser]  # Необходимый парсер для обработки multipart-загрузки

    def post(self, request, format=None):
        uploaded_file = request.FILES.get('shop.yaml')
        if not uploaded_file:
            return Response({'Error': 'File shop.yaml has not been sent '}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Переводим полученный файл в строку и загружаем данные
            yaml_data = uploaded_file.read()
            user = request.user
            result = load_data_from_yaml(yaml_data, user)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'Error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)