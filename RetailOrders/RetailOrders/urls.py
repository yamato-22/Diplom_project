"""
URL configuration for RetailOrders project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter


from backend.views import (RegisterAccount, UserRetrieveUpdate, ChangeUserPasswordView, ContactsView,
                           ContactDetailView, CompanyAPIView, ProductViewSet, CategoryViewSet,
                           PropertyViewSet,  ProductPropertyViewSet, ProductDetailView, OrderCreateView,
                           UserOrdersListView)

# Создаем экземпляр роутера
router = DefaultRouter()

# Регистрируем ViewSet
router.register(r'api/property', PropertyViewSet, basename='Property-List-Create')
router.register(r'api/property/<int:pk>', PropertyViewSet, basename='Property-Retrieve-Update')
router.register(r'api/category', CategoryViewSet, basename='Category-List-Create')
router.register(r'api/category/<int:pk>', CategoryViewSet, basename='Category-Retrieve-Update')
router.register(r'api/product', ProductViewSet, basename='Product-List-Create')
router.register(r'api/product/<int:pk>', ProductViewSet, basename='Product-R-U-D')
router.register(r'api/product_property', ProductPropertyViewSet, basename='ProductProperty-List-Create')
router.register(r'api/product_property/<int:pk>', ProductPropertyViewSet, basename='ProductProperty-R-U-D')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/register', RegisterAccount.as_view(), name='user-register'),
    path('api/user/retrieveupdate', UserRetrieveUpdate.as_view(), name='user-details'),
    path('api/user/changepassword', ChangeUserPasswordView.as_view(), name='user-changepassword'),
    path('api/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/user/contact', ContactsView.as_view(), name='contacts'),
    path('api/user/contact/<int:pk>/', ContactDetailView.as_view(), name='contact'),
    path('api/user/orders/', UserOrdersListView.as_view(), name='user-orders'),
    path('api/company/', CompanyAPIView.as_view(), name='company-list-create'),
    path('api/company/<int:company_id>/', CompanyAPIView.as_view(), name='company-get-update-delete'),
    path('api/productdetail/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('api/orders/create/', OrderCreateView.as_view(), name='order-create'),

]

# Включаем маршруты из роутера
urlpatterns += router.urls
