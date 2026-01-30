from django.contrib import admin
from .models import Bill, BillItem, Customer
from django.contrib import admin
from .models import Category, Product, Inventory,SubCategory
from django.utils.html import format_html

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


class InventoryInline(admin.StackedInline):
    model = Inventory
    extra = 0

from django.utils.html import format_html

def discount_tag(self, obj):
    if obj.is_discountable:
        return format_html("<span style='color:green;'>✔ Discount Allowed</span>")
    return format_html("<span style='color:red;font-weight:bold;'>NO DISCOUNT</span>")

discount_tag.short_description = "Discount Rule"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "category",
        "subcategory",
        "price",
        "is_discountable",
        "stock_status",
        "is_available",
    )

    def stock_status(self, obj):

        # If inventory not created yet
        if not hasattr(obj, "inventory"):
            return "No Stock Record"

        if obj.inventory.stock == 0:
            color = "red"
            text = "Out of Stock"

        elif obj.inventory.stock <= obj.inventory.low_stock_alert:
            color = "orange"
            text = "Low Stock"

        else:
            color = "green"
            text = "In Stock"

        return format_html(
            "<b style='color:{}'>{}</b>",
            color,
            text
        )

    stock_status.short_description = "Stock"



class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "category",
    )

    list_filter = (
        "category",
    )

    search_fields = (
        "name",
        "category__name",
    )

    ordering = ("category", "name")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [SubCategoryInline]


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "stock",
        "low_stock_alert",
        "updated_at",
    )

    search_fields = ("product__name",)