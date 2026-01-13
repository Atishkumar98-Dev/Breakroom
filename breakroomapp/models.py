from django.db import models

class Bill(models.Model):
    bill_no = models.CharField(max_length=20, unique=True)

    subtotal = models.FloatField(default=0)
    gst = models.FloatField(default=0)
    service_charge = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)

    is_paid = models.BooleanField(default=False)
    customer_email = models.EmailField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.bill_no


class BillItem(models.Model):
    bill = models.ForeignKey('Bill', on_delete=models.CASCADE)
    item_name = models.CharField(max_length=150)

    quantity = models.FloatField()
    rate = models.FloatField()
    total = models.FloatField(default=0)

    category = models.CharField(max_length=10, default="FOOD")  # FOOD / GAME / COMBO

    # ✅ NEW for booking
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    resource = models.CharField(max_length=50, blank=True, null=True)  
    # resource example: "POOL-1", "POOL-2", "PS5"

    def save(self, *args, **kwargs):

        # ✅ FOOD → normal calc
        if self.category == "FOOD":
            self.total = self.quantity * self.rate

        # ✅ GAME → package-based pricing
        elif self.category == "GAME":
            # total should equal the rate (fixed price package)
            self.total = self.rate

        # ✅ COMBO → fixed price
        elif self.category == "COMBO":
            self.total = self.rate

        else:
            self.total = self.quantity * self.rate

        super().save(*args, **kwargs)


