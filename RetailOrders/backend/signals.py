from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
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