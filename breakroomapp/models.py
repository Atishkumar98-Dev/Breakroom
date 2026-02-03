from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=120,null=True)

    def __str__(self):
        return self.name

SUBCATEGORY_CHOICES = [
    ("FRIES", "Fries"),
    ("MOMOS", "Momos"),
    ("DIPS", "Dips"),
    ("BEVERAGES", "Beverages"),
    ("COLD_DRINKS", "Cold Drinks"),
    ("ICE_CREAMS", "Ice Creams"),
]


from django.utils.text import slugify


class SubCategory(models.Model):

    category = models.ForeignKey(
        Category,
        related_name="subcategories",
        on_delete=models.CASCADE,null=True,
    )

    name = models.CharField(max_length=120)

    slug = models.SlugField(blank=True)
    
    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",null=True
    )
    subcategory = models.ForeignKey(
    SubCategory,
    null=True,
    blank=True,
    related_name="products",
    on_delete=models.SET_NULL
)

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    sku = models.CharField(max_length=100, unique=True)

    is_available = models.BooleanField(default=True)

    # ⭐ ADD THIS
    is_discountable = models.BooleanField(
        default=True,
        help_text="Uncheck if discounts should NOT apply to this product."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (₹{self.price})"
    


class Inventory(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE
    )

    stock = models.IntegerField(default=0)

    low_stock_alert = models.IntegerField(default=5)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.stock}"


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
    PAYMENT_STATUS = (
        ("FULL", "Full Payment"),
        ("PARTIAL", "Partial Payment"),
    )
    bill_no = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT,null=True)
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS,
        default="FULL"
    )
    paid_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_upi = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    payment_note = models.CharField(max_length=255, blank=True)

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
    product = models.ForeignKey(   # ✅ ADD THIS
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    category = models.CharField(max_length=10, null=True)   # FOOD / GAME / COMBO
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


