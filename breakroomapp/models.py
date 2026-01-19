from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)  # ✅ email unique
    phone = models.CharField(max_length=20, blank=True, null=True)

    visits = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


class Bill(models.Model):
    bill_no = models.CharField(max_length=20, unique=True)

    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)

    bill_category = models.CharField(max_length=10, default="FOOD")  # FOOD / GAME / BOTH

    subtotal = models.FloatField(default=0)
    gst = models.FloatField(default=0)
    service_charge = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)

    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.bill_no


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=150)

    quantity = models.FloatField()
    rate = models.FloatField()

    total = models.FloatField(default=0)

    category = models.CharField(max_length=10, default="FOOD")  # FOOD / GAME / COMBO

    # ✅ booking fields for gaming
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    resource = models.CharField(max_length=50, blank=True, null=True)  # POOL-1 / POOL-2 / PS5

    def save(self, *args, **kwargs):
        # ✅ FOOD totals normal
        if self.category == "FOOD":
            self.total = self.quantity * self.rate

        # ✅ GAME uses fixed rate packages
        elif self.category == "GAME":
            self.total = self.rate

        # ✅ COMBO fixed package
        elif self.category == "COMBO":
            self.total = self.rate

        else:
            self.total = self.quantity * self.rate

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_name} ({self.bill.bill_no})"
