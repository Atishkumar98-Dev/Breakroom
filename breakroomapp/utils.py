from .models import Bill, BillItem
from django.db.models import Sum
from django.forms.models import model_to_dict


def generate_bill_no():
    count = Bill.objects.count() + 1
    return f"BR-{count:05d}"
def recalc_bill(bill):
    items = bill.billitem_set.all()

    # ✅ Category subtotals
    food_total = sum(i.total for i in items.filter(category="FOOD"))
    drinks_total = sum(i.total for i in items.filter(category="DRINKS"))  # ✅ ADD THIS
    game_total = sum(i.total for i in items.filter(category="GAME"))
    combo_total = sum(i.total for i in items.filter(category="COMBO"))

    # ✅ Subtotal includes drinks now
    subtotal = food_total + drinks_total + game_total + combo_total

    # ✅ Discountable totals ONLY
    food_discountable_total = sum(
        i.total for i in items.filter(category="FOOD", is_discountable=True)
    )
    game_discountable_total = sum(
        i.total for i in items.filter(category="GAME", is_discountable=True)
    )
    combo_discountable_total = sum(
        i.total for i in items.filter(category="COMBO", is_discountable=True)
    )
    # DRINKS is not discountable so not included

    discountable_subtotal = food_discountable_total + game_discountable_total + combo_discountable_total

    # ✅ Discounts in %
    food_discount_amount = 0
    game_discount_amount = 0
    overall_discount_amount = 0

    if bill.food_discount_percent:
        food_discount_amount = (food_discountable_total * bill.food_discount_percent) / 100

    if bill.game_discount_amount:
        game_discount_amount = (game_discountable_total * bill.game_discount_amount) / 100

    # ✅ Overall discount applies only on discountable subtotal
    after_cat_discountable = discountable_subtotal - (food_discount_amount + game_discount_amount)

    if bill.Overall_Discount_percent:
        overall_discount_amount = (after_cat_discountable * bill.Overall_Discount_percent) / 100

    total_discount = food_discount_amount + game_discount_amount + overall_discount_amount
    grand_total = max(subtotal - total_discount, 0)

    # ✅ Save bill
    bill.subtotal = subtotal
    bill.discount_amount = total_discount
    bill.grand_total = grand_total
    bill.save()

    return {
        "subtotal": subtotal,
        "food_total": food_total,
        "drinks_total": drinks_total,   # ✅ RETURN THIS
        "game_total": game_total,
        "combo_total": combo_total,

        "food_discount_amount": food_discount_amount,
        "game_discount_amount": game_discount_amount,
        "overall_discount_amount": overall_discount_amount,
        "total_discount": total_discount,
        "grand_total": grand_total,
    }
