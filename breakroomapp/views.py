from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.timezone import localtime
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
import io, os, subprocess
from datetime import datetime, timedelta
from django.contrib import messages

from .models import Bill, BillItem
from .utils import generate_bill_no, send_bill_email

def add_minutes_to_time(time_str, minutes):
    """ time_str: 'HH:MM' => returns 'HH:MM' """
    t = datetime.strptime(time_str, "%H:%M")
    t2 = t + timedelta(minutes=minutes)
    return t2.strftime("%H:%M")


def has_overlap(bill, resource, start_t, end_t):
    """
    Prevent overlap inside same bill session bookings.
    """
    existing = BillItem.objects.filter(bill=bill, category="GAME", resource=resource)

    for item in existing:
        if not item.start_time or not item.end_time:
            continue

        # overlap condition: start < existing_end and end > existing_start
        if start_t < item.end_time and end_t > item.start_time:
            return True
    return False


# ✅ FOOD MENU
FOOD_MENU = {
    "French Fries": 119,
    "Momo’s": 149,
    "Smoked Momo’s": 169,
    "Cheesy Poppers": 179,
    "Crispy Cheese Sticks": 189,
    "Potato Wedges": 129,
    "Maggie": 39,
    "Virgin Mojito": 79,
    "Cold Coffee": 99,
    "Hot Chocolate": 109,
    "Coffee": 89,
    "Kesar Tea": 49,
    "Lemon Tea": 39,
    "Mayonise": 29,
    "Chipotle": 29,
    "Cheese Dip": 39,
    "Peri Peri": 29,
    "Honey Mustard": 39
}

# ✅ GAMING RATES
POOL_RATES = {"30": 150, "60": 250}
PS5_SINGLE = {"30": 150, "60": 200}
PS5_MULTI  = {"30": 90,  "60": 150}   # ✅ half hour is 90 (fixed)

# ✅ COMBOS (Food + Gaming both)
COMBOS = {
    "PS5 (1 Ctrl) + Fries + Cold Coffee": 299,
    "Pool 30min + Nachos + Mojito": 349,
    "PS5 (2 Ctrl) 30min + Fries": 399,
}

def recalc_bill(bill, food_disc_percent=0, game_disc_amount=0):
    food_items = bill.billitem_set.filter(category="FOOD")
    game_items = bill.billitem_set.filter(category="GAME")
    combo_items = bill.billitem_set.filter(category="COMBO")

    food_subtotal = sum(i.total for i in food_items)
    game_subtotal = sum(i.total for i in game_items)
    combo_subtotal = sum(i.total for i in combo_items)

    # Food discount (%) only
    food_discount = food_subtotal * float(food_disc_percent) / 100 if food_disc_percent else 0

    # Gaming discount (₹) only (applies on GAME subtotal only)
    game_discount = float(game_disc_amount) if game_disc_amount else 0
    game_discount = min(game_discount, game_subtotal)

    food_after = max(food_subtotal - food_discount, 0)
    game_after = max(game_subtotal - game_discount, 0)

    grand_total = food_after + game_after + combo_subtotal

    bill.subtotal = food_subtotal + game_subtotal + combo_subtotal
    bill.gst = 0
    bill.service_charge = 0
    bill.grand_total = grand_total
    bill.save()

    return {
        "food_subtotal": food_subtotal,
        "game_subtotal": game_subtotal,
        "combo_subtotal": combo_subtotal,
        "food_discount": food_discount,
        "game_discount": game_discount,
        "grand_total": grand_total,
    }


@login_required
def billing_page(request):
    bill_id = request.session.get("bill_id")

    if bill_id:
        bill = Bill.objects.get(id=bill_id)
    else:
        bill = Bill.objects.create(bill_no=generate_bill_no())
        request.session["bill_id"] = bill.id

    food_disc_percent = request.session.get("food_disc_percent", 0)
    game_disc_amount = request.session.get("game_disc_amount", 0)

    if request.method == "POST":
        action = request.POST.get("action")

        # ✅ Customer details save
        if action == "save_customer":
            bill.customer_email = request.POST.get("customer_email") or ""
            bill.save()
            request.session["customer_name"] = request.POST.get("customer_name", "")
            request.session["customer_phone"] = request.POST.get("customer_phone", "")
            return redirect("billing:billing")

        # ✅ Add Food
        if action == "add_food":
            item = request.POST.get("food_item")
            qty = request.POST.get("food_qty")
            if item and qty:
                BillItem.objects.create(
                    bill=bill,
                    item_name=item,
                    quantity=float(qty),
                    rate=float(FOOD_MENU.get(item, 0)),
                    category="FOOD"
                )

        # ✅ Add Pool
        elif action == "add_pool":
            table_no = request.POST.get("pool_table")
            duration = request.POST.get("pool_duration")
            ft = request.POST.get("from_time")

            if table_no and duration and ft:
                minutes = 30 if duration == "30" else 60
                auto_to = add_minutes_to_time(ft, minutes)

                start_t = datetime.strptime(ft, "%H:%M").time()
                end_t = datetime.strptime(auto_to, "%H:%M").time()

                resource = f"POOL-{table_no}"

                # ✅ Check overlap
                if has_overlap(bill, resource, start_t, end_t):
                    messages.error(request, f"❌ Pool Table {table_no} is BUSY during {ft} - {auto_to}")
                    return redirect("billing:billing")
                # qty = 1
                # rate = POOL_RATES.get(duration, 0)

                rate = POOL_RATES.get(duration, 0)
                qty = 0.5 if duration == "30" else 1

                name = f"Pool Table {table_no} ({ft}-{auto_to})"

                BillItem.objects.create(
                    bill=bill,
                    item_name=name,
                    quantity=qty,
                    rate=rate,
                    category="GAME",
                    start_time=start_t,
                    end_time=end_t,
                    resource=resource
                )

        # ✅ Add PS5
        elif action == "add_ps5":
            controllers = int(request.POST.get("ps5_controllers", 1))
            duration = request.POST.get("ps5_duration")
            ft = request.POST.get("from_time_ps5")

            if duration and ft:
                minutes = 30 if duration == "30" else 60
                auto_to = add_minutes_to_time(ft, minutes)

                start_t = datetime.strptime(ft, "%H:%M").time()
                end_t = datetime.strptime(auto_to, "%H:%M").time()

                resource = "PS5"

                # ✅ Check overlap (PS5 considered one resource here)
                if has_overlap(bill, resource, start_t, end_t):
                    messages.error(request, f"❌ PS5 is BUSY during {ft} - {auto_to}")
                    return redirect("billing:billing")

                if controllers == 1:
                    rate = PS5_SINGLE.get(duration, 0)
                else:
                    rate = PS5_MULTI.get(duration, 0) * controllers

                qty = 0.5 if duration == "30" else 1
                name = f"PS5 ({controllers} Ctrl) ({ft}-{auto_to})"

                BillItem.objects.create(
                    bill=bill,
                    item_name=name,
                    quantity=qty,
                    rate=rate,
                    category="GAME",
                    start_time=start_t,
                    end_time=end_t,
                    resource=resource
                )


        # ✅ Add Combo
        elif action == "add_combo":
            combo_name = request.POST.get("combo_name")
            if combo_name in COMBOS:
                BillItem.objects.create(
                    bill=bill,
                    item_name=combo_name,
                    quantity=1,
                    rate=float(COMBOS[combo_name]),
                    category="COMBO"
                )

        # ✅ Apply discounts
        elif action == "apply_discounts":
            request.session["food_disc_percent"] = float(request.POST.get("food_disc_percent") or 0)
            request.session["game_disc_amount"] = float(request.POST.get("game_disc_amount") or 0)

        recalc_bill(bill,
                    request.session.get("food_disc_percent", 0),
                    request.session.get("game_disc_amount", 0))

        return redirect("billing:billing")

    totals = recalc_bill(bill, food_disc_percent, game_disc_amount)
    pool1_busy = BillItem.objects.filter(bill=bill, resource="POOL-1").exists()
    pool2_busy = BillItem.objects.filter(bill=bill, resource="POOL-2").exists()
    ps5_busy = BillItem.objects.filter(bill=bill, resource="PS5").exists()

    return render(request, "billing/billing.html", {
        "bill": bill,
        "items": bill.billitem_set.all(),
        "menu": FOOD_MENU,
        "combos": COMBOS,
        "totals": totals,
        "food_disc_percent": food_disc_percent,
        "game_disc_amount": game_disc_amount,
        "customer_name": request.session.get("customer_name", ""),
        "customer_phone": request.session.get("customer_phone", ""),
        "customer_email": bill.customer_email or "",
        "pool1_busy": pool1_busy,
        "pool2_busy": pool2_busy,
        "ps5_busy": ps5_busy,

    })


@login_required
def remove_item(request, item_id):
    BillItem.objects.filter(id=item_id).delete()
    return redirect("billing:billing")


@login_required
def mark_paid(request):
    bill = Bill.objects.get(id=request.session["bill_id"])

    if request.method == "POST":
        bill.is_paid = True
        bill.customer_email = request.POST.get("email") or bill.customer_email
        bill.save()

    return redirect("billing:print_bill")


@login_required
def print_bill(request):
    bill = Bill.objects.get(id=request.session["bill_id"])

    # ✅ force 80mm (you can change to 58)
    width = 80 * mm
    height = 280 * mm

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(width, height))

    logo_path = os.path.join(settings.BASE_DIR, "breakroom", "static", "billing", "logo.png")

    # Watermark shifted a little up
    if os.path.exists(logo_path):
        p.saveState()
        try:
            p.setFillAlpha(0.06)
        except:
            pass

        p.translate(width/2, height/2 + 20)
        p.rotate(45)
        p.drawImage(logo_path, -90, -90, 180, 180, mask='auto')
        p.restoreState()

    y = height - 20

    # Header logo slightly up
    if os.path.exists(logo_path):
        p.drawImage(logo_path, width/2 - 22, y - 35, 44, 44, mask='auto')
        y -= 50

    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width/2, y, "BREAKROOM")
    y -= 14

    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, y, "PLAY • EAT • REPEAT")
    y -= 12

    p.line(5, y, width - 5, y)
    y -= 12

    p.setFont("Helvetica", 8)
    p.drawString(5, y, f"Bill No: {bill.bill_no}")
    y -= 10
    p.drawString(5, y, f"Date: {localtime(bill.created_at).strftime('%d-%m-%Y %H:%M')}")
    y -= 10
    p.line(5, y, width - 5, y)
    y -= 12

    p.setFont("Helvetica-Bold", 8)
    p.drawString(5, y, "Item")
    p.drawRightString(width - 30, y, "Qty")
    p.drawRightString(width - 5, y, "Amt")
    y -= 10
    p.line(5, y, width - 5, y)
    y -= 8

    p.setFont("Helvetica", 8)
    for item in bill.billitem_set.all():
        p.drawString(5, y, item.item_name[:22])
        p.drawRightString(width - 30, y, str(item.quantity))
        p.drawRightString(width - 5, y, f"{int(item.total)}")
        y -= 10

    y -= 5
    p.line(5, y, width - 5, y)
    y -= 12

    p.setFont("Helvetica-Bold", 9)
    p.drawString(5, y, "TOTAL")
    p.drawRightString(width - 5, y, f"₹ {int(bill.grand_total)}")

    y -= 20
    p.setFont("Helvetica", 7)
    p.drawCentredString(width/2, y, "Thank You! Visit Again 🎮🍔")

    p.showPage()
    p.save()

    pdf_path = f"/tmp/{bill.bill_no}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(buffer.getvalue())

    # Silent print
    subprocess.Popen(["lp", pdf_path])

    # Send mail if PAID
    if bill.is_paid:
        send_bill_email(bill, pdf_path)

    return redirect("billing:billing")


@login_required
def new_bill(request):
    request.session.pop("bill_id", None)
    request.session["food_disc_percent"] = 0
    request.session["game_disc_amount"] = 0
    request.session["customer_name"] = ""
    request.session["customer_phone"] = ""
    return redirect("billing:billing")
