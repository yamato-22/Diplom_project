from django.db import transaction
from django.apps import apps
from rest_framework.exceptions import ValidationError, PermissionDenied
import yaml
from .models import Order, OrderItem, Product, Property, ProductProperty, Company, Category, STATUS_CHOICES


@transaction.atomic
def add_product_to_order(user_id, order_id, product_id, quantity):
    """
    Функция добавляет продукт в существующий заказ или создает новый элемент заказа.

    :param user_id: ID пользователя добавляющего товар в заказ
    :param order_id: ID заказа
    :param product_id: ID добавляемого продукта
    :param quantity: Количество добавляемого продукта
    """
    try:
        # Получаем объект заказа
        order = Order.objects.select_related('user').get(id=order_id)

        if order.user_id != user_id:
            raise PermissionDenied("You don't own this order")

        if order.status != STATUS_CHOICES[0][0]:
            raise ValidationError(f"Order {order.pk} have NOT CHANGE status {order.status} ")

        # Получаем продукт
        product = Product.objects.select_for_update().get(id=product_id)

        if not isinstance(quantity, int) or quantity <= 0:
            raise ValidationError("Incorrect quantity value")

        # Проверяем доступность товаров на складе
        if product.quantity < quantity:
            raise ValidationError(f"The product '{product.name}' insufficient quantity in stock")

        # Уменьшаем количество товара на складе
        product.quantity -= quantity
        product.save()

        # Проверяем, существует ли уже этот продукт в заказе
        existing_item = None
        try:
            existing_item = OrderItem.objects.get(order=order, product=product)
        except OrderItem.DoesNotExist:
            pass

        if existing_item:
            # Если элемент уже существует, увеличиваем его количество
            new_quantity = existing_item.quantity + quantity
            existing_item.quantity = new_quantity
            existing_item.save()
        else:
            # Cоздаем новый элемент заказа
            item_total_cost = product.price * quantity
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                total_cost=item_total_cost
            )

        # Пересчитываем общую стоимость заказа
        calculate_and_update_total_amount(order)

    except Order.DoesNotExist:
        raise ValidationError('Order not found')
    except Product.DoesNotExist:
        raise ValidationError('Product not found')

@transaction.atomic
def remove_product_from_order(user_id, order_id, product_id):
    """
    Удаляет товар из заказа и возвращает его количество на склад.

    :param user_id: ID пользователя, инициирующего удаление
    :param order_id: ID заказа
    :param product_id: ID товара, подлежащего удалению
    """
    try:
        # Получаем объект заказа
        order = Order.objects.select_related('user').get(id=order_id)
        if order.user_id != user_id:
            raise PermissionDenied("You don't own this order.")

        if order.status != STATUS_CHOICES[0][0]:
            raise ValidationError(f"Order {order.pk} have NOT CHANGE status {order.status} ")

        product = Product.objects.select_for_update().get(id=product_id)
        item = OrderItem.objects.get(order=order, product=product)

        # Возврат товара на склад
        product.quantity += item.quantity
        product.save()

        # Удаляем элемент заказа
        item.delete()

        # Пересчёт общей стоимости заказа
        calculate_and_update_total_amount(order)

    except Order.DoesNotExist:
        raise ValidationError('Order not found.')
    except Product.DoesNotExist:
        raise ValidationError('Product not found.')
    except OrderItem.DoesNotExist:
        raise ValidationError('Product is not present in the order')


def calculate_and_update_total_amount(order):
    """Рассчитывает общую стоимость заказа."""
    items = order.order.all()  # получаем все элементы текущего заказа
    total_sum = sum(item.total_cost for item in items)
    order.total_amount = total_sum
    order.save()

@transaction.atomic
def set_confirm_order_user(user_id, order_id):
    """
    Подтверждение пользователем своего заказа,
    после подтверждения заказ отправляется Поставщику,
    пользователь не может редактировать заказ.
    :param user_id:
    :param order_id:
    :return:
    """
    try:
        order = Order.objects.select_related('user').get(id=order_id)

        if order.user_id != user_id:
            raise PermissionDenied("You don't own this order")

        if order.status != STATUS_CHOICES[0][0]:
            raise ValidationError(f"Order {order.pk} have NOT CHANGE status {order.status} ")

        if check_order_supplier_unique(order):
            order.status = STATUS_CHOICES[1][0]
            order.save()
            return order
        else:
            raise ValidationError("All products in the order must belong to the same supplier.")

    except Order.DoesNotExist:
        raise ValidationError('Order not found.')



def check_order_supplier_unique(order):
    """
    Проверка заказа на принадлежность товаров к одному поставщику
    :param order:
    :return:
    """
    suppliers_ids = set(order.orderitem_set.values_list('product__company_id', flat=True))

    if len(suppliers_ids) > 1:
        return False
    return True

@transaction.atomic
def change_status_order_supplier(supplier, order_id, new_status):
    """
    Изменение статуса заказа Поставщиком,
    в процессе обработки подтвержденного покупателем заказа
    пользователь не может редактировать заказ.
    :param user_id:
    :param order_id:
    :return:
    """

    try:
        order = Order.objects.get(id=order_id)
        current_status = order.status
        company = order.products.first().company
        if company is None:
            raise ValidationError("Not items found in order")
        owner = company.owner
        if owner.id != supplier.id:
            raise PermissionDenied("You don't own this order.")
        if new_status not in [status[1] for status in STATUS_CHOICES]:
            raise ValidationError("Invalid status value.")
        if new_status in [STATUS_CHOICES[0][1], STATUS_CHOICES[1][1]]:
            raise ValidationError("This status ONLY customer")

        # Составляем словарь соответствия названий статусов их индексам
        status_indexes = {status_label: index for index, (_, status_label) in enumerate(STATUS_CHOICES)}

        # Получаем индексы текущего и целевого статусов
        current_index = status_indexes.get(current_status)
        target_index = status_indexes.get(new_status)
        if target_index != current_index + 1:
            raise ValidationError(f"Status '{new_status}' not next after '{current_status}'.")

        # проверяем, возможен ли новый статус
        order.status = new_status
        order.save()
        return order

    except Order.DoesNotExist:
        raise ValidationError('Order not found.')






def load_data_from_yaml(yaml_file, user):
    """
    Первоначальная загрузка данных из yaml файла
    :param yaml_file: shop.yaml
    :return: Словарь с результатами загрузки
    """
    data = yaml.safe_load(yaml_file)

    # Результаты загрузки будем хранить в словаре
    results = {'created_objects': [], 'errors': []}

    shop_data = data.get('shop', None)
    categories_data = data.get('categories', [])
    products_data = data.get('goods', [])

    # Создание компании (если магазин указан)
    if shop_data:
        company_obj, created = Company.objects.get_or_create(name=shop_data, defaults={'owner': user})
        if created:
            # Объект успешно создан
            results['created_objects'].append(f"Создана компания '{company_obj.name}'")
            print(user)
        else:
            # Если объект уже существует, проверяем владельца
            if company_obj.owner != user:
                raise PermissionDenied("Вы не можете редактировать компанию другого пользователя.")

    # Создание категорий
    for category in categories_data:
        category_id = category.get('id')
        category_name = category.get('name')
        category, _ = Category.objects.get_or_create(id=category_id, defaults={'name': category_name})
        results['created_objects'].append(f"Создана категория '{category.name}'")

    # Создание товаров и свойств товаров
    for product in products_data:
        product_id = product.get('id')
        category_id = product.get('category')
        name = product.get('name')
        model = product.get('model')
        price = product.get('price')
        price_rrc = product.get('price_rrc')
        quantity = product.get('quantity')
        params = product.get('parameters', {})

        # Создаем продукт
        try:
            category_obj = Category.objects.get(pk=category_id)
            product, _ = Product.objects.update_or_create(
                pk=product_id,
                defaults={
                    'name': name,
                    'model': model,
                    'description': '',  # Описание пустое, можем заполнить позже
                    'article': product_id,
                    'quantity': quantity,
                    'price': price,
                    'price_rrc': price_rrc,
                    'category': category_obj,
                    'company': company_obj
                }
            )
            results['created_objects'].append(f"Создан товар '{product.name}'")

            # Добавляем свойства товара
            for param_key, param_value in params.items():
                prop, _ = Property.objects.get_or_create(name=param_key)

                # Сохраняем значение свойства для текущего товара
                ProductProperty.objects.create(product=product, property=prop, quantity=str(param_value))
                results['created_objects'].append(
                    f"Добавлено свойство '{prop.name}' со значением '{param_value}' для товара '{product.name}'")
        except Exception as e:
            results['errors'].append(f"Произошла ошибка при обработке товара ID={product_id}: {e}")

    return results


def clean_database_with_orm(app_label=None, exclude_models=[]):
    """
    Функция очищает все таблицы указанной группы приложений или всей базы данных используя ORM.
    Пример использования:
    clean_database_with_orm('your_app_label') - Очищает все таблицы указанного приложения
    clean_database_with_orm(exclude_models=['User'])  - Очищает всю базу данных, кроме модели User

    """
    with transaction.atomic():
        all_models = []
        if app_label:
            app_config = apps.get_app_config(app_label)
            all_models.extend(app_config.get_models())
        else:
            all_models = apps.get_models()

        target_models = [model for model in all_models if model.__name__ not in exclude_models]

        for model in target_models:
            # Массивное удаление всех записей данной модели
            model.objects.all().delete()