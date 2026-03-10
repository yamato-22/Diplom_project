from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .models import Order


# @receiver(pre_save, sender=Order)
# def send_email_on_order_status_change(sender, instance, **kwargs):
#     previous_instance = Order.objects.filter(pk=instance.pk).first()
#
#     if previous_instance and previous_instance.status != instance.status:
#         subject = f"Состояние вашего заказа №{instance.id} изменилось!"
#         message = f"Ваш заказ №{instance.id} теперь имеет статус: {instance.get_status_display()}."
#
#         # Получаем email пользователя, сделавшего заказ
#         recipient_email = instance.user.email
#
#         send_mail(
#             subject=subject,
#             message=message,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[recipient_email],
#             fail_silently=False
#         )


@receiver(pre_save, sender=Order)
def notify_supplier_on_confirmation(sender, instance, **kwargs):
    """
    Отправка e-mail поставщику при подтверждении заказа покупателем
    """

    try:
        old_instance = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return  # Если запись новая, пропускаем обработку

    if old_instance.status != 'confirmed' and instance.status == 'confirmed':
        products_in_order = instance.order.all()
        supplier_emails = set()

        for item in products_in_order:
            supplier_company = item.product.company
            supplier_emails.add(supplier_company.owner.email)

        subject = f"Подтверждение заказа №{instance.id}"
        message = f"Заказ №{instance.id} подтвержден покупателем.\\n\\nОбщее количество товара: {len(products_in_order)}\\nСумма заказа: {instance.total_amount}\\n"

        email = EmailMessage(subject, message, to=list(supplier_emails))
        email.send(fail_silently=False)


@receiver(pre_save, sender=Order)
def notify_buyer_on_status_change(sender, instance, **kwargs):
    """
    Отправка e-mail покупателю при изменении статуса заказа поставщиком
    """
    try:
        old_instance = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return  # Если запись новая, пропускаем обработку

    if old_instance.status != instance.status:
        buyer = instance.user
        subject = f"Смена статуса вашего заказа №{instance.id}"
        message = f"Изменился статус вашего заказа №{instance.id}: {old_instance.status} → {instance.status}.\\n\\nОбщая сумма заказа: {instance.total_amount}\\n"

        email = EmailMessage(subject, message, to=[buyer.email])
        email.send(fail_silently=False)