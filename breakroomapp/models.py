from django.db import models

class Bill(models.Model):
    BILL_TYPE_CHOICES = (
        ('G', 'Gaming'),
        ('F', 'Food'),
        ('P', 'Pool'),
        ('C', 'Combined'),
    )

    bill_type = models.CharField(max_length=1, choices=BILL_TYPE_CHOICES)
    bill_no = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    subtotal = models.FloatField(default=0)
    gst = models.FloatField(default=0)
    service_charge = models.FloatField(default=0)
    is_paid = models.BooleanField(default=False)
    customer_email = models.EmailField(blank=True, null=True)
    grand_total = models.FloatField(default=0)


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    quantity = models.FloatField()
    rate = models.FloatField()
    total = models.FloatField()

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.rate
        super().save(*args, **kwargs)

