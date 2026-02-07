from django.shortcuts import render
from django.contrib.auth.password_validation import validate_password
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import JsonResponse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, UserCreateSerializer


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
    Methods:
    - get: Retrieve the details of the authenticated user.
    - post: Update the account details of the authenticated user.
    """
    # Allow only authenticated users to access this url
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request: Request, *args, **kwargs):
        # serializer to handle turning our `User` object into something that
        # can be JSONified and sent to the client.
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
