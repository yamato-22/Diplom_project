# Дипломный проект по курсу "Python-разработчик: расширенный курс"

## Описание проекта

Дипломный проект представляет собой backend-приложение для автоматизации покупок покупателями товаров в розничной сети.
Project name - "RetailOrders", Application name - "backend"
Приложение представляет собой API для управления пользователями, продавцами, товарами, заказами.
Проект реализован с использованием Django Rest Framework.

## Описание бизнес логики проекта 
[См. ссылку](docs/concept.md)

## Текущий статус работ по проекту
[См. ссылку](status_project.md)

## Требования и зависимости

- Python 3.13
- Django 6.0.1
- Django Rest Framework 3.16.1
- PostgreSQL

Установите зависимости, выполнив команду:

```bash
pip install -r requirements.txt
```

## Установка и настройка

1. Склонируйте репозиторий:

```bash
git clone git@github.com:yamato-22/Diplom_project.git
```

2. Активируйте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4. Перейдите в папку проекта:
```bash
cd RetailOrders
```

5. Выполните миграции базы данных:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Архитектура проекта

Проект организован следующим образом:

- `RetailOrders`: Основной каталог проекта.
- `RetailOrders/backend`: каталог c файлами приложения.
- `backend/models.py`: Модель данных.
- `backend/apps.py`: файл для подключения обработчиков сигналов.
- `backend/serializers.py`: файл содержащий сериализаторы данных приложения.
- `backend/services.py`: файл содержащий сервисные функции приложения.
- `backend/signals.py`: файл содержащий обработчики сигналов приложения.
- `backend/views.py`: файл содержащий обработчики запросов.

## Описание API

Ниже приведены URL реализованного API. Полный URL выглядит как 'http://127.0.0.1:8000/link',
где link приведен и описан в документации ниже.

### [Работа с пользователями](docs/users_api.md)
### [Работа с контактами пользователя](docs/contacts_api.md)
### [Работа с компаниями](docs/company_api.md)
### [Работа с категориями товаров](docs/category_api.md)
### [Работа со свойствами товаров](docs/properties_api.md)
### [Работа со свойствами конкретного товара](docs/productproperty_api.md)
### [Работа с товарами](docs/products_api.md)
### [Работа с заказами](docs/orders_api.md)
### [Загрузка данных](docs/load_data_api.md)

