from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import  Order, OrderItem, Product


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
            raise PermissionDenied("This order belongs to another user")

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
            new_total_cost = product.price * new_quantity
            existing_item.quantity = new_quantity
            existing_item.total_cost = new_total_cost
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


def calculate_and_update_total_amount(order):
    """Рассчитывает общую стоимость заказа."""
    items = order.order.all()  # получаем все элементы текущего заказа
    total_sum = sum(item.total_cost for item in items)
    order.total_amount = total_sum
    order.save()