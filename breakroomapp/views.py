from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.timezone import localtime, now
from django.contrib import messages
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.db.models import Sum

from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

import io, os
from datetime import datetime, timedelta

from .models import Bill, BillItem, Customer
from .utils import generate_bill_no


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
# ✅ POOL RATES
POOL_RATES = {"30": 150, "60": 250}

# ✅ PS5 65 INCH
PS5_65_SINGLE = {"30": 150, "60": 250}
PS5_65_MULTI  = {"30": 90,  "60": 150}

# ✅ PS5 55 INCH
PS5_55_SINGLE = {"30": 140, "60": 220}
PS5_55_MULTI  = {"30": 80,  "60": 140}
  # ✅ half hour multi controller = 90 (per controller)

# ✅ COMBOS (Food + Gaming both)
COMBOS = {
    # POOL
    "Pool 30 + Fries + Virgin Mojito": 319,
    "Pool 30 + Wedges + Cold Coffee": 329,
    "Pool 30 + Momo’s + Lemon Tea": 329,
    "Pool 1 hr + Fries + Cold Coffee": 429,
    "Pool 1 hr + Smoked Momo’s + Virgin Mojito": 479,
    "Pool 1 hr + Cheesy Poppers + Hot Chocolate": 499,

    # PS5 65
    "PS5 65\" 30 + Fries + Cold Coffee": 349,
    "PS5 65\" 30 + Momo’s + Virgin Mojito": 349,
    "PS5 65\" 1 hr + Smoked Momo’s + Cold Coffee": 499,
    "PS5 65\" 1 hr + Cheesy Poppers + Virgin Mojito": 499,
    "PS5 65\" (2 Ctrl) 30 + Fries x2 + Mojito": 449,
    "PS5 65\" (2 Ctrl) 30 + Momo’s + Fries + Cold Coffee": 449,
    "PS5 65\" (2 Ctrl) 1 hr + Fries + Cold Coffee": 529,
    "PS5 65\" (2 Ctrl) 1 hr + Smoked Momo’s + Virgin Mojito": 579,

    # PS5 55
    "PS5 55\" 30 + Fries + Lemon Tea": 299,
    "PS5 55\" 30 + Maggie + Cold Coffee": 259,
    "PS5 55\" 1 hr + Momo’s + Cold Coffee": 419,
    "PS5 55\" 1 hr + Cheesy Poppers + Virgin Mojito": 449,
    "PS5 55\" (2 Ctrl) 30 + Fries + Cold Coffee": 349,
    "PS5 55\" (2 Ctrl) 30 + Wedges + Mojito": 349,
    "PS5 55\" (2 Ctrl) 1 hr + Fries + Cold Coffee": 479,
    "PS5 55\" (2 Ctrl) 1 hr + Smoked Momo’s + Virgin Mojito": 529,

    # UPSELL
    "Dip Pack (Mayo + Peri Peri)": 49,
    "Cheese Dip Add-on": 39,
    "Lemon Tea Add-on": 39,
    "Cold Coffee Upgrade": 99,
}


def add_minutes_to_time(time_str, minutes):
    t = datetime.strptime(time_str, "%H:%M")
    t2 = t + timedelta(minutes=minutes)
    return t2.strftime("%H:%M")


def has_overlap(bill, resource, start_t, end_t):
    existing = BillItem.objects.filter(bill=bill, category="GAME", resource=resource)

    for item in existing:
        if not item.start_time or not item.end_time:
            continue

        if start_t < item.end_time and end_t > item.start_time:
            return True
    return False


def update_bill_category(bill):
    has_food = bill.billitem_set.filter(category="FOOD").exists()
    has_game = bill.billitem_set.filter(category="GAME").exists()
    has_combo = bill.billitem_set.filter(category="COMBO").exists()

    # ✅ combo counts as BOTH
    if has_combo:
        bill.bill_category = "BOTH"
    elif has_food and has_game:
        bill.bill_category = "BOTH"
    elif has_food:
        bill.bill_category = "FOOD"
    elif has_game:
        bill.bill_category = "GAME"
    else:
        bill.bill_category = "FOOD"

    bill.save()


def recalc_bill(bill, food_disc_percent=0, game_disc_amount=0):
    food_items = bill.billitem_set.filter(category="FOOD")
    game_items = bill.billitem_set.filter(category="GAME")
    combo_items = bill.billitem_set.filter(category="COMBO")

    food_subtotal = sum(i.total for i in food_items)
    game_subtotal = sum(i.total for i in game_items)
    combo_subtotal = sum(i.total for i in combo_items)

    # ✅ discounts
    food_discount = food_subtotal * float(food_disc_percent) / 100 if food_disc_percent else 0
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

        # ✅ SAVE CUSTOMER (EMAIL BASED)
        if action == "save_customer":
            name = request.POST.get("customer_name", "").strip()
            phone = request.POST.get("customer_phone", "").strip()
            email = request.POST.get("customer_email", "").strip()

            if not email:
                messages.error(request, "❌ Email is required for customer history!")
                return redirect("billing:billing")

            bill.customer_name = name
            bill.customer_phone = phone
            bill.customer_email = email
            bill.save()

            cust, created = Customer.objects.get_or_create(
                email=email,
                defaults={"name": name, "phone": phone}
            )
            if not created:
                cust.name = name
                if phone:
                    cust.phone = phone
                cust.save()

            if cust.visits >= 4:
                messages.success(request, f"🎁 Loyalty! {cust.visits} visits. Discount option available ✅")

            return redirect("billing:billing")

        # ✅ ADD FOOD
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

        # ✅ ADD POOL
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

                if has_overlap(bill, resource, start_t, end_t):
                    messages.error(request, f"❌ Pool Table {table_no} BUSY during {ft}-{auto_to}")
                    return redirect("billing:billing")

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

        # ✅ ADD PS5
        elif action == "add_ps5":
            tv_size = request.POST.get("ps5_tv")  # ✅ 65 / 55
            controllers = int(request.POST.get("ps5_controllers", 1))
            duration = request.POST.get("ps5_duration")
            ft = request.POST.get("from_time_ps5")

            if tv_size and duration and ft:
                minutes = 30 if duration == "30" else 60
                auto_to = add_minutes_to_time(ft, minutes)

                start_t = datetime.strptime(ft, "%H:%M").time()
                end_t = datetime.strptime(auto_to, "%H:%M").time()

                # ✅ Separate resource for each PS5
                resource = "PS5-65" if tv_size == "65" else "PS5-55"

                # ✅ overlap check for that particular PS5
                if has_overlap(bill, resource, start_t, end_t):
                    messages.error(request, f"❌ {resource} BUSY during {ft}-{auto_to}")
                    return redirect("billing:billing")

                # ✅ Pricing logic depends on TV size + controllers
                if tv_size == "65":
                    if controllers == 1:
                        rate = PS5_65_SINGLE.get(duration, 0)
                    else:
                        rate = PS5_65_MULTI.get(duration, 0) * controllers

                    name = f"PS5 (65 Inch) ({controllers} Ctrl) ({ft}-{auto_to})"

                else:  # 55 inch
                    if controllers == 1:
                        rate = PS5_55_SINGLE.get(duration, 0)
                    else:
                        rate = PS5_55_MULTI.get(duration, 0) * controllers

                    name = f"PS5 (55 Inch) ({controllers} Ctrl) ({ft}-{auto_to})"

                qty = 0.5 if duration == "30" else 1

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


        # ✅ ADD COMBO
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

        # ✅ APPLY DISCOUNTS
        elif action == "apply_discounts":
            request.session["food_disc_percent"] = float(request.POST.get("food_disc_percent") or 0)
            request.session["game_disc_amount"] = float(request.POST.get("game_disc_amount") or 0)

        recalc_bill(bill,
                    request.session.get("food_disc_percent", 0),
                    request.session.get("game_disc_amount", 0))

        update_bill_category(bill)
        return redirect("billing:billing")

    totals = recalc_bill(bill, food_disc_percent, game_disc_amount)
    update_bill_category(bill)

    pool1_busy = BillItem.objects.filter(bill=bill, resource="POOL-1").exists()
    pool2_busy = BillItem.objects.filter(bill=bill, resource="POOL-2").exists()
    ps5_65_busy = BillItem.objects.filter(bill=bill, resource="PS5-65").exists()
    ps5_55_busy = BillItem.objects.filter(bill=bill, resource="PS5-55").exists()


    return render(request, "billing/billing.html", {
        "bill": bill,
        "items": bill.billitem_set.all(),
        "menu": FOOD_MENU,
        "combos": COMBOS,
        "totals": totals,
        "food_disc_percent": food_disc_percent,
        "game_disc_amount": game_disc_amount,
        "customer_name": bill.customer_name or "",
        "customer_phone": bill.customer_phone or "",
        "customer_email": bill.customer_email or "",
        "pool1_busy": pool1_busy,
        "pool2_busy": pool2_busy,
       "ps5_65_busy": ps5_65_busy,
        "ps5_55_busy": ps5_55_busy,

    })


@login_required
def remove_item(request, item_id):
    item = BillItem.objects.filter(id=item_id).first()
    if item:
        bill = item.bill
        item.delete()
        update_bill_category(bill)
    return redirect("billing:billing")


@login_required
def mark_paid(request):
    bill = Bill.objects.get(id=request.session["bill_id"])

    # ✅ No email asked again
    bill.is_paid = True
    bill.save()

    # ✅ increase visits by EMAIL
    if bill.customer_email:
        cust = Customer.objects.filter(email=bill.customer_email).first()
        if cust:
            cust.visits += 1
            cust.save()

    return redirect("billing:print_bill")


@login_required
def print_bill(request):
    bill = Bill.objects.get(id=request.session["bill_id"])

    # ✅ wider than 80mm (you asked)
    width = 95 * mm
    height = 280 * mm

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(width, height))

    # ✅ logo from static
    logo_path = os.path.join(settings.BASE_DIR, "static", "billing", "logo.png")

    # ---------- WATERMARK ----------
    if os.path.exists(logo_path):
        p.saveState()
        try:
            p.setFillAlpha(0.06)
        except:
            pass

        p.translate(width / 2, height / 2 + 20)
        p.rotate(45)
        logo_img = ImageReader(logo_path)
        p.drawImage(logo_img, -90, -90, 180, 180, mask="auto")
        p.restoreState()

    y = height - 20

    # ---------- HEADER LOGO ----------
    if os.path.exists(logo_path):
        logo_img = ImageReader(logo_path)
        p.drawImage(logo_img, width / 2 - 22, y - 35, 44, 44, mask="auto")
        y -= 50

    # ---------- HEADER ----------
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width / 2, y, "BREAKROOM")
    y -= 14

    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2, y, "PLAY • EAT • REPEAT")
    y -= 12

    p.line(5, y, width - 5, y)
    y -= 12

    # ---------- BILL INFO ----------
    p.setFont("Helvetica", 8)
    p.drawString(5, y, f"Bill No: {bill.bill_no}")
    y -= 10
    p.drawString(5, y, f"Date: {localtime(bill.created_at).strftime('%d-%m-%Y %H:%M')}")
    y -= 10
    p.drawString(5, y, f"Category: {bill.bill_category}")
    y -= 12

    p.line(5, y, width - 5, y)
    y -= 12

    # ---------- TABLE HEADER ----------
    p.setFont("Helvetica-Bold", 8)

    item_x = 5
    qty_x = width - 45   # shift qty (adjust if you want)
    amt_x = width - 5

    p.drawString(item_x, y, "Item (Time)")
    p.drawRightString(qty_x, y, "Qty")
    p.drawRightString(amt_x, y, "Amt")
    y -= 10

    p.line(5, y, width - 5, y)
    y -= 8

    # ---------- ITEMS ----------
    p.setFont("Helvetica", 8)
    max_chars = 38

    for item in bill.billitem_set.all():
        name = item.item_name
        qty_text = f"{item.quantity} hr" if item.category == "GAME" else str(item.quantity)
        amt_text = f"Rs. {int(item.total)}"

        line1 = name[:max_chars]
        line2 = name[max_chars:max_chars * 2] if len(name) > max_chars else ""

        p.drawString(item_x, y, line1)
        p.drawRightString(qty_x, y, qty_text)
        p.drawRightString(amt_x, y, amt_text)
        y -= 10

        if line2:
            p.drawString(item_x, y, line2)
            y -= 10

    y -= 5
    p.line(5, y, width - 5, y)
    y -= 12

    # ---------- TOTAL ----------
    p.setFont("Helvetica-Bold", 10)
    p.drawString(5, y, "TOTAL")
    p.drawRightString(amt_x, y, f"Rs. {int(bill.grand_total)}")
    y -= 18

    p.setFont("Helvetica", 7)
    p.drawCentredString(width / 2, y, "Thank You! Visit Again 🎮🍔")

    p.showPage()
    p.save()

    pdf_data = buffer.getvalue()
    buffer.close()

    # ✅ email only when paid
    if bill.is_paid and bill.customer_email:
        email = EmailMessage(
            subject=f"BREAKROOM Receipt – {bill.bill_no}",
            body=f"Thank you! Your total was Rs. {int(bill.grand_total)}.\nReceipt attached.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[bill.customer_email],
        )
        email.attach(f"{bill.bill_no}.pdf", pdf_data, "application/pdf")
        email.send()

    response = HttpResponse(pdf_data, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{bill.bill_no}.pdf"'
    return response


@login_required
def new_bill(request):
    request.session.pop("bill_id", None)
    request.session["food_disc_percent"] = 0
    request.session["game_disc_amount"] = 0
    return redirect("billing:billing")


@login_required
def dashboard(request):
    total_sales = Bill.objects.filter(is_paid=True).aggregate(Sum("grand_total"))["grand_total__sum"] or 0
    total_bills = Bill.objects.filter(is_paid=True).count()

    total_customers = Customer.objects.count()
    returning_customers = Customer.objects.filter(visits__gte=2).count()

    today = now().date()
    today_sales = Bill.objects.filter(is_paid=True, created_at__date=today).aggregate(Sum("grand_total"))["grand_total__sum"] or 0
    today_bills = Bill.objects.filter(is_paid=True, created_at__date=today).count()

    return render(request, "billing/dashboard.html", {
        "total_sales": total_sales,
        "total_bills": total_bills,
        "total_customers": total_customers,
        "returning_customers": returning_customers,
        "today_sales": today_sales,
        "today_bills": today_bills,
    })
