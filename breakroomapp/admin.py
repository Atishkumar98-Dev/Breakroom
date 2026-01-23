from django.contrib import admin
from .models import Bill, BillItem, Customer

class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 0

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("bill_no", "grand_total", "is_paid", "created_at")
    list_filter = ("is_paid", "created_at")
    search_fields = ("bill_no", "customer__email")
    inlines = [BillItemInline]

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "phone", "created_at")
    search_fields = ("email", "name")

admin.site.register(BillItem)
