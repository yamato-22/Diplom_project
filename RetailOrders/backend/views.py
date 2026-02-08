#from django.shortcuts import render
from django.contrib.auth.password_validation import validate_password
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import JsonResponse
from rest_framework import status
from rest_framework.request import Request
#from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Contact
from .serializers import UserSerializer, UserCreateSerializer, UserChangePasswordSerializer, ContactSerializer


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

class ChangePasswordView(APIView):
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
            return Response({"Message": f"Contact id = {pk} not found"}, status=status.HTTP_404_NOT_FOUND)
        contact.delete()
        return Response({"Message": f"Contact id = {pk} successfully deleted"}, status=status.HTTP_204_NO_CONTENT)
