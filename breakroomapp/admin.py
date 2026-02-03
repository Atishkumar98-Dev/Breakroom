from django.contrib import admin
from .models import Bill, BillItem, Customer
from django.contrib import admin
from .models import Category, Product, Inventory,SubCategory
from .models import *
from django.utils.html import format_html

class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 0

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        "bill_no",
        "grand_total",
        "payment_badge",
        "paid_upi",
        "paid_cash",
        "is_paid",
        "created_at",
    )

    list_filter = (
        "is_paid",
        "payment_status",
        "created_at",
    )

    search_fields = (
        "bill_no",
        "customer__email",
    )

    readonly_fields = (
        "paid_upi",
        "paid_cash",
        "payment_status",
    )

    inlines = [BillItemInline]

    def payment_badge(self, obj):
        if not obj.is_paid:
            return format_html("<b style='color:gray;'>UNPAID</b>")

        if obj.payment_status == "FULL":
            if obj.paid_upi > 0:
                return format_html("<b style='color:green;'>UPI</b>")
            return format_html("<b style='color:#A8DF8E;'>CASH</b>")

        return format_html("<b style='color:orange;'>SPLIT</b>")

    payment_badge.short_description = "Payment Mode"

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


@admin.register(CustomerMembership)
class CustomerMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "plan",
        "hours_remaining",
        "expires_at",
        "weekend_access",
        "is_active",
    )
    list_filter = ("plan", "weekend_access", "is_active")
    search_fields = ("customer__email",)


from django.contrib import admin
from .models import MembershipPlan

@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "total_hours",
        "price",
        "regular_price",
        "validity_days",
        "weekday_only",
    )

    list_filter = ("weekday_only",)
    search_fields = ("name",)
