from .models import Bill, BillItem
from django.db.models import Sum
from django.forms.models import model_to_dict


def generate_bill_no():
    count = Bill.objects.count() + 1
    return f"BR-{count:05d}"



def recalc_bill(bill):
    # Total of all bill items
    subtotal = sum(i.total for i in bill.billitem_set.all())
    combo_total = sum(i.total for i in bill.billitem_set.filter(category="COMBO"))
    # Common discount (percentage)
    discount_amount = 0
    print(model_to_dict(bill))
    if bill.Overall_Discount_percent:

        discount_amount = (subtotal * bill.Overall_Discount_percent) / 100
    # Final grand total
    grand_total = max(subtotal - discount_amount, 0)

    # Save to bill
    bill.subtotal = subtotal + combo_total
    bill.discount_amount = discount_amount
    bill.grand_total = grand_total
    bill.save()

    return {
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "Percent_Discount" : bill.Overall_Discount_percent,
        "combo_total": combo_total,
        "grand_total": grand_total,
    }
