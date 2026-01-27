from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def total_paid_amount(self):
        return sum(b.grand_total for b in self.bill_set.filter(is_paid=True))

    def __str__(self):
        return self.email


class Bill(models.Model):
    bill_no = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT,null=True)


    subtotal = models.FloatField(default=0)
    food_discount_percent = models.FloatField(default=0)
    game_discount_amount = models.FloatField(default=0)
    Overall_Discount_percent = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)

    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.bill_no


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    category = models.CharField(max_length=10)   # FOOD / GAME / COMBO
    start_dt = models.DateTimeField(null=True, blank=True)
    end_dt   = models.DateTimeField(null=True, blank=True)
    is_discountable = models.BooleanField(default=True)
    item_name = models.CharField(max_length=200)
    quantity = models.FloatField(default=1)
    rate = models.FloatField(default=0)
    total = models.FloatField(default=0)

    # gaming booking
    resource = models.CharField(max_length=20, blank=True, null=True)  # POOL-1, POOL-2, PS5-65, PS5-55
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Food -> qty*rate
        if self.category == "FOOD":
            self.total = self.quantity * self.rate
        else:
            # GAME & COMBO fixed package
            self.total = self.rate

        super().save(*args, **kwargs)
