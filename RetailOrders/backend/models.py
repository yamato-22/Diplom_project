from django.db import models
from django.contrib.auth.models import AbstractBaseUser, AbstractUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _

# Create your models here.

ROLE_CHOICES = (
    ('supplier', 'Поставщик'),
    ('buyer', 'Покупатель'),

)

class UserManager(BaseUserManager):
    """
    Менеджер пользователя, требуемый Django для работы с кастомной моделью пользователя.
    """
    def create_user(self, login, email, password=None, **extra_fields):
        """
        Создаем стандартного  позователся с логином и паролем
        :param login:
        :param email:
        :param password:
        :param extra_fields:
        :return:
        """
        if login is None:
            raise ValueError('Обязательный параметр')
        if email is None:
            raise ValueError('Обязательный параметр')
        extra_fields.setdefault('is_active', True)
        email = self.normalize_email(email)
        user = self.model(login=login, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, email, password, **extra_fields):
        """
        Создаем пользователя с полномочиями адммминистратора
        :param login:
        :param email:
        :param password:
        :param extra_fields:
        :return:
        """
        if password is None:
            raise ValueError('Требуется задать пароль')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(login, email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Кастомная модель пользователя, построенная с нуля.
    """

    USERNAME_FIELD = 'email'  # Основной идентификатор пользователя — email
    REQUIRED_FIELDS = ['username']  # Обязательные поля при создании пользователя

    email = models.EmailField(_('email address'), unique=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    company = models.CharField(verbose_name='Компания', max_length=40, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=40, blank=True)
    # is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    role = models.CharField(verbose_name='Тип пользователя', choices=ROLE_CHOICES, max_length=5, default='buyer')



    objects = UserManager()

    def __str__(self):
        return self.email


# class User(AbstractUser):
#     """
#     Стандартная модель пользователей
#     """
#     REQUIRED_FIELDS = []
#     objects = UserManager()
#     USERNAME_FIELD = 'email'
#     email = models.EmailField(_('email address'), unique=True)
#     company = models.CharField(verbose_name='Компания', max_length=40, blank=True)
#     position = models.CharField(verbose_name='Должность', max_length=40, blank=True)
#     username_validator = UnicodeUsernameValidator()
#     username = models.CharField(
#         _('username'),
#         max_length=150,
#         help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
#         validators=[username_validator],
#         error_messages={
#             'unique': _("A user with that username already exists."),
#         },
#     )
#     is_active = models.BooleanField(
#         _('active'),
#         default=False,
#         help_text=_(
#             'Designates whether this user should be treated as active. '
#             'Unselect this instead of deleting accounts.'
#         ),
#     )
#     type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')
#
#     def __str__(self):
#         return f'{self.first_name} {self.last_name}'
#
#     class Meta:
#         verbose_name = 'Пользователь'
#         verbose_name_plural = "Список пользователей"
#         ordering = ('email',)