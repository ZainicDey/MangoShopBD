from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
# Create your models here.
class Seller(models.Model):
    seller = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.seller.username

class Mango(models.Model):
    name = models.CharField(max_length=120)
    image = models.ImageField(upload_to='media/mangoes')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mango = models.ForeignKey(Mango, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    ordered_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.pk: 
            self.mango.quantity -= self.quantity
            self.mango.save()
            send_mail(
                'Order Confirmation',
                f'Thank you for your order of {self.quantity} {self.mango.name}(s). Your order status is {self.status}.',
                'ihanik.ad@gmail.com',
                [self.user.email],
                fail_silently=False,
            )
        elif self.status == 'Completed':
            send_mail(
                'Order Completed',
                f'Your order of {self.quantity} {self.mango.name}(s) has been completed.',
                'ihanik.ad@gmail.com',
                [self.user.email],
                fail_silently=False,
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Order {self.id} by {self.user.username}'