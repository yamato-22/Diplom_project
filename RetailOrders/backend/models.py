import jwt

from datetime import datetime, timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AbstractUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import validate_email
from django.db.models import ForeignKey
from django.utils.translation import gettext_lazy as _

# Create your models here.

ROLE_CHOICES = (
    ('supplier', 'Поставщик'),
    ('buyer', 'Покупатель'),

)

STATUS_CHOICES = (
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('closed','Закрыт'),
    ('canceled', 'Отменен'),
)

class UserManager(BaseUserManager):
    """
    Менеджер пользователя, требуемый Django для работы с кастомной моделью пользователя.
    """
    def create_user(self, username, email, password=None, **extra_fields):
        """
        Создаем стандартного  позователся с логином и паролем
        :param username:
        :param email:
        :param password:
        :param extra_fields:
        :return:
        """
        if username is None:
            raise ValueError('username - обязательный параметр')
        if email is None:
            raise ValueError('email -обязательный параметр')
        extra_fields.setdefault('is_active', True)
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        """
        Создаем пользователя с полномочиями адммминистратора
        :param username:
        :param email:
        :param password:
        :param extra_fields:
        :return:
        """
        if password is None:
            raise ValueError('Требуется задать пароль')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Кастомная модель пользователя, построенная с нуля.
    """

    # Валидатор для имени пользователя
    username_validator = UnicodeUsernameValidator()
    # Понятный идентификатор,
    # для предоставления User в пользовательском интерфейсе
    username = models.CharField(
        _('username'), db_index=True, max_length=255,
        unique=True, help_text=_('Required. 250 characters or fewer. Letters, '
                                 'digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    # Email - наиболее распространенная форма учетных данных
    email = models.EmailField(_('email address'), db_index=True, unique=True)
    position = models.CharField(verbose_name='Должность', max_length=100, blank=True)
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'The flag determines whether the user is active or deleted'
        ),
    )
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    role = models.CharField(verbose_name='Тип пользователя', choices=ROLE_CHOICES, max_length=8, default='buyer')
    # Временная метка создания объекта.
    created_at = models.DateTimeField(auto_now_add=True)
    # Временная метка показывающая время последнего обновления объекта.
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'  # Основной идентификатор пользователя — email
    REQUIRED_FIELDS = ['username']  # Обязательные поля при создании пользователя

    objects = UserManager()

    def __str__(self):
        return f'{self.username} {self.email}'

    @property
    def token(self):
        """
        Позволяет получить токен пользователя путем вызова user.token, вместо
        user._generate_jwt_token(). Декоратор @property выше делает это
        возможным, "token" называется "динамическим свойством".
        """
        return self._generate_jwt_token()

    def get_full_name(self):
        """
        Этот метод требуется Django для таких вещей, как обработка электронной
        почты. Обычно это имя фамилия пользователя, но поскольку мы не
        используем их, будем возвращать username.
        """
        return self.username

    def get_short_name(self):
        """ Аналогично методу get_full_name(). """
        return self.username

    def _generate_jwt_token(self):
        """
        Генерирует веб-токен JSON, в котором хранится идентификатор этого
        пользователя, срок действия токена составляет 1 день от создания
        """
        dt = datetime.now() + timedelta(days=1)

        token = jwt.encode({
            'id': self.pk,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')

        return token.decode('utf-8')


    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)


class Company(models.Model):
    objects = models.Manager()

    name = models.CharField(max_length=100,
                            verbose_name='Название компании')
    url = models.URLField(verbose_name='Ссылка на сайт компании',
                          null=True, blank=True)
    state_orders = models.BooleanField(verbose_name='Статус получения заказов',
                                       default=True)
    owner = models.ForeignKey(User, verbose_name='Владелец компании',
                              null=True, blank=True, on_delete=models.CASCADE)


    class Meta:
        verbose_name = 'Компания розничной торговли'
        verbose_name_plural = "Список компаний розничной торговли"
        ordering = ('-name',)

    def __str__(self):
        return self.name

class Contact(models.Model):
    objects = models.Manager()

    lastname = models.CharField(max_length=100,
                            verbose_name='Фамилия', blank=True, null=True)
    firstname = models.CharField(max_length=100,
                                verbose_name='Имя', blank=True, null=True)
    middlename = models.CharField(max_length=100,
                                 verbose_name='Отчество', blank=True, null=True)
    email = models.EmailField(_('email address'), blank=False, null=False,
                              validators=[validate_email],
                              error_messages={
                                  'invalid': _("Invalid email format"),
                              },
    )
    phone_number = models.CharField(max_length=16, verbose_name='Номер телефона',
                                    blank=False, null=False)
    city = models.CharField(max_length=50, verbose_name='Город', blank=True)
    street = models.CharField(max_length=100, verbose_name='Улица', blank=True)
    house = models.CharField(max_length=5, verbose_name='Дом', blank=True)
    structure = models.CharField(max_length=5, verbose_name='Корпус', blank=True)
    building = models.CharField(max_length=5, verbose_name='Строение', blank=True)
    apartment = models.CharField(max_length=5, verbose_name='Квартира', blank=True)
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='contacts', null=False, blank=False,
                             on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Список контактов пользователя"

    def __str__(self):
        return f'{self.lastname} {self.firstname} {self.middlename} {self.city}'


class Category(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=50, verbose_name='Название', unique=True)
    companies = models.ManyToManyField(Company, verbose_name='Компании', related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Список категорий"
        ordering = ('-name',)

    def __str__(self):
        return self.name

class Product(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=80, verbose_name='Название')
    description = models.CharField(max_length=150, verbose_name='Описание')
    article = models.PositiveIntegerField(verbose_name='Артикул',
                                          unique=True, blank=False)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    category = models.ForeignKey(Category, verbose_name='Категория',
                                 related_name='products', blank=True,
                                 on_delete=models.CASCADE)
    company = models.ForeignKey(Company, verbose_name="Поставщик",
                                related_name='products', blank=True,
                                on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = "Список продуктов"
        ordering = ('-name',)

    def __str__(self):
        return f'{self.name} {self.article}'

class Property(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=30, verbose_name="Название", blank=False)
    value = models.CharField(max_length=10, verbose_name="Единица измерения", blank=True)

    class Meta:
        verbose_name = 'Характеристика'
        verbose_name_plural = "Список характеристик"
        constraints = [
            models.UniqueConstraint(fields=['name', 'value'], name='unique_property'),
        ]
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductProperty(models.Model):
    objects = models.Manager()
    quantity = models.CharField(max_length=50,
                                verbose_name="Значение параметра", blank=True)
    property = models.ForeignKey(Property, verbose_name="Характеристика",
                                 related_name='properties', blank=True,
                                 on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='Продукт',
                                 related_name='products', blank=True,
                                 on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Характеристика продукта'
        verbose_name_plural = "Список характеристик"
        constraints = [
            models.UniqueConstraint(fields=['product', 'property'], name='unique_product_parameter'),
        ]

    def __str__(self):
        return f'{self.product.name} {self.property.name}'

class Order(models.Model):
    objects = models.Manager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(choices=STATUS_CHOICES, default="new")
    total_amount = models.PositiveIntegerField(default=0)
    user=ForeignKey(User, verbose_name='Покупатель', related_name='user',
                    blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказов"

    def __str__(self):
        return f'{self.id} {self.status} {self.total_amount}'

class OrderItem(models.Model):
    objects = models.Manager()
    order = ForeignKey(Order, verbose_name='Заказ', related_name='order',
                    blank=True, on_delete=models.CASCADE)
    product = ForeignKey(Product, verbose_name='Товар', related_name='product',
                    blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Строка заказа'
        verbose_name_plural = "Список элементов заказа"

    def __str__(self):
        return f'{self.product.name} {self.quantity} {self.total_cost}'


    def save(self, *args, **kwargs):
        self.total_cost = self.product.price * self.quantity
        super().save(*args, **kwargs)