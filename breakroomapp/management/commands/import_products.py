from django.core.management.base import BaseCommand
from breakroomapp.models import Category, Product


# ✅ YOUR MENUS
FOOD_MENU = {
    "French Fries": 119,
    "Peri Peri Fries": 129,
    "Cheesy Fries": 139,
    "Cheesy Poppers": 179,
    "Crispy Cheese Sticks": 189,
    "Potato Wedges": 129,
    "Maggie": 49,
    "Banta Soda": 39,
    "Cold Coffee": 99,
    "Iced Tea": 49,
    "Hot Chocolate": 109,
    "Coffee": 49,
    "Special Tea": 29,
    "Lemon Tea": 39,
    "Mayonise": 29,
    "Chipotle": 29,
    "Cheese Dip": 39,
    "Peri Peri": 29,
    "Honey Mustard": 39,
    "Half Veg Momo's": 79,
    "Half Paneer Momo's": 89,
    "Half Cheese Chilly Momo's": 99,
    "Half Veg Peri Peri Momo's": 89,
    "Half Paneer Peri peri Momo's": 99,
    "Half Paneer Mix Dumplings": 99,
    "Half Peri Peri Paneer Dumplings": 109,
    "Veg Momo's": 139,
    "Paneer Momo's": 149,
    "Cheese Chilly Momo's": 159,
    "Veg Peri Peri Momo's": 149,
    "Paneer Peri peri Momo's": 159,
    "Paneer Mix Dumplings": 159,
    "Peri Peri Paneer Dumplings": 179,
    "Steamed BAO Spicy": 199,
    "NACHOS": 49,
    "Water Bottle": 20,
    "Amchi": 135,
}

DRINKS = {
    "Energy Drink 350ml": 125,
    "Energy Drink 300ml": 60,
    "Diet Coke": 40,
    "Thumps Up Can": 40,
    "Sprite Can": 40,
    "Minute Maid 250ml": 25,
    "Soft Drink 250ml": 20,
    "Soft Drink 200ml": 20,
}

ICECREAM = {
    "Crunchy Choco": 70,
    "Choco Fudge (Choco Bar)": 70,
    "Mango Choco": 40,
    "Vanilla Choco": 40,
    "Creamy Chocolate": 90,
    "Dark Chocolate": 90,
    "Raspberry": 90,
    "Chocoboom Bar": 45,
    "Vanilla (Classic Cup)": 30,
    "Chocolate Tub": 160,
    "Rajbhog Tub": 200,
    "Kaju Anjeer": 250,
    "Choco Bon Bon": 10,
}


class Command(BaseCommand):
    help = "Import menu into Product table"

    def create_products(self, category_name, items):
        category, _ = Category.objects.get_or_create(name=category_name)

        for name, price in items.items():

            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "price": price,
                    "sku": name.replace(" ", "-").upper(),
                },
            )

            if not created:
                # update price if changed
                product.price = price
                product.category = category
                product.save()

        self.stdout.write(self.style.SUCCESS(f"{category_name} imported ✅"))

    def handle(self, *args, **kwargs):

        self.create_products("FOOD", FOOD_MENU)
        self.create_products("DRINKS", DRINKS)
        self.create_products("ICECREAM", ICECREAM)

        self.stdout.write(self.style.SUCCESS("ALL PRODUCTS IMPORTED 🚀"))
