from .models import Bill, BillItem
from django.db.models import Sum

def generate_bill_no():
    count = Bill.objects.count() + 1
    return f"BR-{count:05d}"

def recalc_bill(bill):
    food_total = sum(i.total for i in bill.billitem_set.filter(category="FOOD"))
    game_total = sum(i.total for i in bill.billitem_set.filter(category="GAME"))
    combo_total = sum(i.total for i in bill.billitem_set.filter(category="COMBO"))

    food_discount = (food_total * bill.food_discount_percent / 100) if bill.food_discount_percent else 0
    game_discount = min(bill.game_discount_amount, game_total)

    grand = (food_total - food_discount) + (game_total - game_discount) + combo_total

    bill.subtotal = food_total + game_total + combo_total
    bill.grand_total = max(grand, 0)
    bill.save()

    return {
        "food_total": food_total,
        "game_total": game_total,
        "combo_total": combo_total,
        "food_discount": food_discount,
        "game_discount": game_discount,
        "grand_total": bill.grand_total,
    }
