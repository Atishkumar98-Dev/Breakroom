from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.utils.timezone import localtime, now
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.utils.timezone import make_aware
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from decimal import Decimal
import io, os
from datetime import datetime, timedelta
import json
from .models import Bill, BillItem, Customer , Product, Category, Inventory
from .utils import generate_bill_no, recalc_bill

# ✅ Import ALL rates & menu from rates.py
from .rates import FOOD_MENU, COMBOS,DRINKS, pool_rate_for_time, ps5_price
from django.db.models import Sum, F, Q
from django.utils.timezone import now
from datetime import timedelta
from collections import defaultdict


# ------------------ HELPERS ------------------
def add_minutes_to_time(time_str, minutes):
    """ 'HH:MM' + minutes => 'HH:MM' """
    t = datetime.strptime(time_str, "%H:%M")
    t2 = t + timedelta(minutes=minutes)
    return t2.strftime("%H:%M")


def is_weekend_today():
    """ Saturday=5, Sunday=6 """
    return localtime(now()).weekday() in [5, 6]

from django.utils.timezone import localtime, now
from django.utils.timezone import localtime, now

def is_resource_busy_now(resource):
    today = localtime(now()).date()
    current_t = localtime(now()).time()

    items = BillItem.objects.filter(
        category="GAME",
        resource=resource,
        bill__created_at__date=today
    )

    # ✅ DEBUG
    print(f"\n[CHECK] Resource={resource} Today={today} Now={current_t} Items={items.count()}")

    for it in items:
        print("   ->", it.item_name, it.start_time, it.end_time)

        if not it.start_time or not it.end_time:
            continue

        if it.start_time <= current_t < it.end_time:
            print("   ✅ BUSY")
            return True

    print("   ✅ FREE")
    return False


def get_current_bill(request):
    """
    Always keep 1 OPEN bill in session.
    If not exists -> create new.
    """
    bill_id = request.session.get("bill_id")

    if bill_id:
        bill = Bill.objects.filter(id=bill_id, is_paid=False).first()
        if bill:
            return bill

    bill = Bill.objects.create(bill_no=generate_bill_no())
    request.session["bill_id"] = bill.id
    return bill
    


def is_resource_busy(resource, start_t, end_t):
    """
    ✅ Checks overlap on SAME DAY for both PAID & UNPAID bills.
    Uses Bill.created_at date as 'booking day'.
    """
    today = localtime(now()).date()

    items = BillItem.objects.filter(
        category="GAME",
        resource=resource,
        bill__created_at__date=today     # ✅ SAME DAY only
    )

    for it in items:
        if not it.start_time or not it.end_time:
            continue

        # ✅ overlap condition
        if start_t < it.end_time and end_t > it.start_time:
            return True

    return False

def has_overlap(bill, resource, start_t, end_t):
    """
    Prevent overlap inside same bill for same resource.
    """
    existing = BillItem.objects.filter(bill=bill, category="GAME", resource=resource)

    for item in existing:
        if not item.start_time or not item.end_time:
            continue

        if start_t < item.end_time and end_t > item.start_time:
            return True
    return False


def bill_category(bill):
    has_food = bill.billitem_set.filter(category="FOOD").exists()
    has_game = bill.billitem_set.filter(category="GAME").exists()
    has_combo = bill.billitem_set.filter(category="COMBO").exists()

    if has_combo:
        return "BOTH"
    if has_food and has_game:
        return "BOTH"
    if has_food:
        return "FOOD"
    if has_game:
        return "GAME"
    return "EMPTY"


# ------------------ STEP 1: CHOOSE ZONE ------------------
@login_required
def choose_zone(request):
    bill = get_current_bill(request)
    totals = recalc_bill(bill)

    return render(request, "pos/choose_zone.html", {
        "bill": bill,
        "totals": totals,
        "category": bill_category(bill),
    })


# ------------------ BILL SUMMARY ------------------
@login_required
def bill_summary(request):
    bill = get_current_bill(request)
    pending_bills = Bill.objects.filter(is_paid=False).order_by("-created_at")
    if request.method == "POST":
        action = request.POST.get("action")

        # ✅ Save customer once (Email based)
        if action == "save_customer":
            name = request.POST.get("customer_name", "").strip()
            email = request.POST.get("customer_email", "").strip()
            phone = request.POST.get("customer_phone", "").strip()

            if not email:
                messages.error(request, "❌ Email is required.")
                return redirect("pos:bill_summary")

            cust, created = Customer.objects.get_or_create(
                email=email,
                defaults={"name": name, "phone": phone}
            )
            if not created:
                # update info if changed
                cust.name = name
                if phone:
                    cust.phone = phone
                cust.save()

            bill.customer = cust
            bill.save()

            # ✅ Loyalty eligible only if prev paid total >= 999
            prev_total = cust.total_paid_amount()
            if prev_total >= 999:
                messages.success(request, f"🎁 Loyalty Eligible ✅ Previous Paid Total: Rs. {int(prev_total)}")
            else:
                messages.info(request, f"ℹ Loyalty rule: needs Rs.999 previous paid. Current: Rs. {int(prev_total)}")

        # ✅ Apply discounts
        if request.POST.get("action") == "apply_discount":
            discount_type = request.POST.get("discount_type")
            discount_percent = float(request.POST.get("discount_percent", 0))

            if discount_type == "FOOD":
                bill.food_discount_percent = discount_percent

            elif discount_type == "GAME":
                bill.game_discount_amount = discount_percent

            elif discount_type == "OVERALL":
                bill.Overall_Discount_percent = discount_percent

            bill.save()
            recalc_bill(bill)

            if bill.customer and bill.customer.total_paid_amount() < 999:
                messages.warning(request, "⚠ Not eligible for loyalty discount (needs Rs.999 previous paid).")

        recalc_bill(bill)
        return redirect("pos:bill_summary")

    totals = recalc_bill(bill)

    # ✅ Availability flags (inside this bill items)
    # pool1_busy = BillItem.objects.filter(bill=bill, resource="POOL-1").exists()
    # pool2_busy = BillItem.objects.filter(bill=bill, resource="POOL-2").exists()
    # ps5_65_busy = BillItem.objects.filter(bill=bill, resource="PS5-65").exists()
    # ps5_55_busy = BillItem.objects.filter(bill=bill, resource="PS5-55").exists()
    pool1_busy = is_resource_busy_now("POOL-1")
    pool2_busy = is_resource_busy_now("POOL-2")
    ps5_65_busy = is_resource_busy_now("PS5-65")
    ps5_55_busy = is_resource_busy_now("PS5-55")


    return render(request, "pos/bill_summary.html", {
        "bill": bill,
        "items": bill.billitem_set.all().order_by("created_at"),
        "totals": totals,
        "category": bill_category(bill),
        "pool1_busy": pool1_busy,
        "pool2_busy": pool2_busy,
        "ps5_65_busy": ps5_65_busy,
        "ps5_55_busy": ps5_55_busy,
        "pending_bills": pending_bills, 
    })

@login_required
def switch_bill(request, bill_id):
    bill = Bill.objects.filter(id=bill_id, is_paid=False).first()

    if not bill:
        messages.error(request, "❌ Pending bill not found!")
        return redirect("pos:bill_summary")

    request.session["bill_id"] = bill.id
    messages.success(request, f"✅ Switched to {bill.bill_no}")
    return redirect("pos:bill_summary")
# ------------------ ADD FOOD ------------------


@login_required
def add_food(request):
    bill = get_current_bill(request)

    # ✅ HANDLE CART POST
    if request.method == "POST":

        cart_data = request.POST.get("cart_data")

        if not cart_data:
            messages.error(request, "Cart is empty!")
            return redirect("pos:add_food")

        cart = json.loads(cart_data)

        for pid, item in cart.items():

            try:
                product = Product.objects.select_related(
                    "inventory"
                ).get(id=int(pid), is_available=True)
            except Product.DoesNotExist:
                continue

            qty = Decimal(str(item["qty"]))

            # ⭐ OPTIONAL STOCK CHECK
            if hasattr(product, "inventory"):
                if product.inventory.stock < qty:
                    messages.error(
                        request,
                        f"Only {product.inventory.stock} left for {product.name}"
                    )
                    continue

            BillItem.objects.create(
                bill=bill,
                product=product,
                category="FOOD",
                item_name=product.name,
                quantity=qty,
                rate=product.price,
            )

        recalc_bill(bill)

        messages.success(request, "Items added ✅")
        return redirect("pos:bill_summary")

    # ✅ LOAD FULL TREE
    categories = Category.objects.prefetch_related(
        "subcategories__products__inventory",
        "products__inventory"
    ).distinct()

    return render(request, "pos/add_food.html", {
        "bill": bill,
        "categories": categories
    })

def allocate_pool_table(preferred_table, start_t, end_t):
    if preferred_table in ["1", "2"]:
        try_order = [preferred_table, "2" if preferred_table == "1" else "1"]
    else:
        try_order = ["1", "2"]

    for t in try_order:
        res = f"POOL-{t}"
        if not is_resource_busy(res, start_t, end_t):
            if preferred_table and t != preferred_table:
                return t, f"⚠ Table {preferred_table} is busy. Booking Table {t} ✅"
            return t, None

    return None, "❌ No Pool Table Available in the given time. Please wait in Waiting Area 🪑"


# ------------------ ADD POOL ------------------
@login_required
def add_pool(request):
    bill = get_current_bill(request)

    if request.method == "POST":
        table_no = request.POST.get("pool_table")
        duration = request.POST.get("pool_duration")  # 30/60/120/180
        ft = request.POST.get("from_time")

        if table_no and duration and ft:
            minutes = int(duration)
            auto_to = add_minutes_to_time(ft, minutes)

            start_t = datetime.strptime(ft, "%H:%M").time()
            end_t = datetime.strptime(auto_to, "%H:%M").time()
            selected_table, msg = allocate_pool_table(table_no, start_t, end_t)

            if not selected_table:
                messages.error(request, msg)
                return redirect("pos:add_pool")   # ✅ message shown on Add Pool page

            if msg:
                messages.warning(request, msg)

            # ✅ Now use selected table
            resource = f"POOL-{selected_table}"

            weekend = is_weekend_today()
            rates = pool_rate_for_time(start_t, weekend)
            print(duration,rates,'duration')
            rate = rates.get(duration, 0)
            print(rate,'rate')
            if rate == 0:
                messages.error(request, "❌ Duration not available for selected time slot.")
                return redirect("pos:add_pool")

            qty = minutes / 60
            resource = f"POOL-{selected_table}"


            if has_overlap(bill, resource, start_t, end_t):
                messages.error(request, f"❌ Pool Table {table_no} BUSY during {ft}-{auto_to}")
                return redirect("pos:add_pool")

            name = f"Pool Table {selected_table} ({ft}-{auto_to})"
            today = localtime(now()).date()

            start_dt = make_aware(datetime.combine(today, datetime.strptime(ft, "%H:%M").time()))
            end_dt   = make_aware(datetime.combine(today, datetime.strptime(auto_to, "%H:%M").time()))


            BillItem.objects.create(
                bill=bill,
                category="GAME",
                item_name=name,
                quantity=qty,
                rate=rate,
                resource=resource,
                start_time=start_t,
                end_time=end_t,
                start_dt=start_dt,
                end_dt=end_dt,
            )
            messages.success(request, f"✅ Added {name}")

        return redirect("pos:bill_summary")

    return render(request, "pos/add_pool.html", {"bill": bill})


# ------------------ ADD PS5 ------------------
@login_required
def add_ps5(request):
    bill = get_current_bill(request)

    if request.method == "POST":
        tv_size = request.POST.get("ps5_tv")  # "65" or "55"
        controllers = int(request.POST.get("ps5_controllers", 1))
        duration = request.POST.get("ps5_duration")  # "30" or "60"
        ft = request.POST.get("from_time_ps5")

        if tv_size and duration and ft:
            minutes = int(duration)
            auto_to = add_minutes_to_time(ft, minutes)

            start_t = datetime.strptime(ft, "%H:%M").time()
            end_t = datetime.strptime(auto_to, "%H:%M").time()

            resource = "PS5-65" if tv_size == "65" else "PS5-55"

            if has_overlap(bill, resource, start_t, end_t):
                messages.error(request, f"❌ {resource} BUSY during {ft}-{auto_to}")
                return redirect("pos:add_ps5")

            rate = ps5_price(tv_size, controllers, duration)
            if rate == 0:
                messages.error(request, "❌ Invalid PS5 selection.")
                return redirect("pos:add_ps5")

            qty = minutes / 60
            name = f"PS5 ({tv_size} Inch) ({controllers} Ctrl) ({ft}-{auto_to})"

            BillItem.objects.create(
                bill=bill,
                category="GAME",
                item_name=name,
                quantity=qty,
                rate=rate,
                resource=resource,
                start_time=start_t,
                end_time=end_t,
            )
            messages.success(request, f"✅ Added {name}")

        return redirect("pos:bill_summary")

    return render(request, "pos/add_ps5.html", {"bill": bill})


# ------------------ ADD COMBO ------------------
@login_required
def add_combo(request):
    bill = get_current_bill(request)
    
    if request.method == "POST":
        combo_name = request.POST.get("combo_name")
        if combo_name in COMBOS:
            BillItem.objects.create(
                bill=bill,
                category="COMBO",
                item_name=combo_name,
                quantity=1,
                rate=float(COMBOS[combo_name]),
            )
            messages.success(request, f"✅ Added Combo: {combo_name}")
        return redirect("pos:bill_summary")

    return render(request, "pos/add_combo.html", {
        "bill": bill,
        "combos": COMBOS
    })


# ------------------ REMOVE ITEM ------------------
@login_required
def remove_item(request, item_id):
    bill = get_current_bill(request)
    BillItem.objects.filter(id=item_id, bill=bill).delete()
    messages.success(request, "✅ Item removed")
    return redirect("pos:bill_summary")

@login_required
def print_bill_by_id(request, bill_id):
    paid_bill = Bill.objects.filter(id=bill_id, is_paid=True).first()

    if not paid_bill:
        messages.error(request, "❌ Bill not found.")
        return redirect("pos:bill_summary")

    # 🔽 EVERYTHING BELOW REMAINS SAME AS YOUR EXISTING print_bill()
    # (PDF generation code)

# ------------------ MARK PAID ------------------
# Old version


# @login_required
# def mark_paid(request):
#     bill = get_current_bill(request)

#     if not bill.billitem_set.exists():
#         messages.error(request, "❌ Add items first!")
#         return redirect("pos:bill_summary")

#     # ✅ Final calculation
#     recalc_bill(bill)

#     bill.is_paid = True
#     bill.save()

#     # ✅ Auto new bill for next customer
#     request.session.pop("bill_id", None)
#     new_bill = Bill.objects.create(bill_no=generate_bill_no())
#     request.session["bill_id"] = new_bill.id

#     messages.success(request, f"✅ Paid Successfully! New Bill: {new_bill.bill_no}")
#     return redirect("pos:print_bill")


#  New Version

@login_required
def mark_paid(request):
    bill = get_current_bill(request)

    if not bill.billitem_set.exists():
        messages.error(request, "❌ Add items first!")
        return redirect("pos:bill_summary")

    # ✅ Final calculation
    recalc_bill(bill)

    # ✅ Mark current bill as PAID
    bill.is_paid = True
    bill.save()

    # ✅ CLEAR old bill from session
    request.session.pop("bill_id", None)

    # ✅ CREATE fresh bill for next customer
    new_bill = Bill.objects.create(bill_no=generate_bill_no())
    request.session["bill_id"] = new_bill.id

    # ✅ IMPORTANT:
    # return PDF response (opens in new tab)
    return redirect("pos:print_bill")


# ------------------ PRINT BILL (PDF + EMAIL) ------------------

@login_required
def print_bill(request):
    paid_bill = Bill.objects.filter(is_paid=True).order_by("-created_at").first()

    if not paid_bill:
        messages.error(request, "❌ No paid bill found.")
        return redirect("pos:bill_summary")

    # ✅ Slightly wider for better clarity
    width = 100 * mm
    height = 290 * mm

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(width, height))

    logo_path = os.path.join(settings.BASE_DIR, "static", "pos", "logo.png")

    # ✅ Watermark
    if os.path.exists(logo_path):
        p.saveState()
        try:
            p.setFillAlpha(0.06)
        except:
            pass
        p.translate(width / 2, height / 2 + 30)
        p.rotate(45)
        logo_img = ImageReader(logo_path)
        p.drawImage(logo_img, -95, -95, 190, 190, mask="auto")
        p.restoreState()

    y = height - 18

    # ✅ Header logo
    if os.path.exists(logo_path):
        logo_img = ImageReader(logo_path)
        p.drawImage(logo_img, width/2 - 20, y - 28, 40, 40, mask="auto")
        y -= 48

    p.setFont("Helvetica-Bold", 13)
    p.drawCentredString(width/2, y, "BREAKROOM")
    y -= 14

    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, y, "PLAY • EAT • REPEAT")
    y -= 12

    p.line(5, y, width-5, y)
    y -= 12

    # ✅ Bill Info
    p.setFont("Helvetica", 8)
    p.drawString(5, y, f"Bill No: {paid_bill.bill_no}")
    y -= 10
    p.drawString(5, y, f"Date: {localtime(paid_bill.created_at).strftime('%d-%m-%Y %I:%M %p')}")
    y -= 10

    # ✅ Category + Paid status
    cat = "EMPTY"
    has_food = paid_bill.billitem_set.filter(category="FOOD").exists()
    has_game = paid_bill.billitem_set.filter(category="GAME").exists()
    has_combo = paid_bill.billitem_set.filter(category="COMBO").exists()
    if has_combo or (has_food and has_game):
        cat = "BOTH"
    elif has_food:
        cat = "FOOD"
    elif has_game:
        cat = "GAME"

    p.drawString(5, y, f"Category: {cat}")
    y -= 10
    p.drawString(5, y, f"Status: {'PAID' if paid_bill.is_paid else 'OPEN'}")
    y -= 10

    # ✅ Customer info
    if paid_bill.customer:
        p.drawString(5, y, f"Customer: {paid_bill.customer.name}")
        y -= 10
        p.drawString(5, y, f"Email: {paid_bill.customer.email}")
        y -= 10
        if paid_bill.customer.phone:
            p.drawString(5, y, f"Phone: {paid_bill.customer.phone}")
            y -= 10

    p.line(5, y, width-5, y)
    y -= 12

    # ✅ Table Header
    item_x = 5
    qty_x = width - 50
    amt_x = width - 5

    p.setFont("Helvetica-Bold", 8)
    p.drawString(item_x, y, "Item")
    p.drawRightString(qty_x, y, "Qty")
    p.drawRightString(amt_x, y, "Amt")
    y -= 10

    p.line(5, y, width-5, y)
    y -= 8

    # ✅ Items
    p.setFont("Helvetica", 8)
    max_chars = 44

    for it in paid_bill.billitem_set.all().order_by("created_at"):
        name = it.item_name

        # ✅ game qty display
        qty_text = f"{it.quantity} hr" if it.category == "GAME" else str(it.quantity)
        amt_text = f"Rs. {int(it.total)}"

        # ✅ wrap line
        line1 = name[:max_chars]
        line2 = name[max_chars:max_chars*2] if len(name) > max_chars else ""

        p.drawString(item_x, y, line1)
        p.drawRightString(qty_x, y, qty_text)
        p.drawRightString(amt_x, y, amt_text)
        y -= 10

        if line2:
            p.drawString(item_x, y, line2)
            y -= 10

    y -= 4
    p.line(5, y, width-5, y)
    y -= 12

    # ✅ Subtotals + Discounts
    totals = recalc_bill(paid_bill)

    
    p.setFont("Helvetica", 8)

    # ✅ Show subtotals
    p.drawString(5, y, "Food Subtotal")
    p.drawRightString(amt_x, y, f"Rs. {int(totals.get('food_total', 0))}")
    y -= 10

    p.drawString(5, y, "Drinks Subtotal")
    p.drawRightString(amt_x, y, f"Rs. {int(totals.get('drinks_total', 0))}")
    y -= 10

    p.drawString(5, y, "Game Subtotal")
    p.drawRightString(amt_x, y, f"Rs. {int(totals.get('game_total', 0))}")
    y -= 10

    p.drawString(5, y, "Combo Subtotal")
    p.drawRightString(amt_x, y, f"Rs. {int(totals.get('combo_total', 0))}")
    y -= 10

    p.line(5, y, width-5, y)
    y -= 12

    # ✅ Discount breakdown
    if totals.get("food_discount_amount", 0) > 0:
        p.drawString(5, y, f"Food Discount ({paid_bill.food_discount_percent}%)")
        p.drawRightString(amt_x, y, f"- Rs. {int(totals['food_discount_amount'])}")
        y -= 10

    if totals.get("game_discount_amount", 0) > 0:
        p.drawString(5, y, f"Game Discount ({paid_bill.game_discount_amount}%)")
        p.drawRightString(amt_x, y, f"- Rs. {int(totals['game_discount_amount'])}")
        y -= 10

    if totals.get("overall_discount_amount", 0) > 0:
        p.drawString(5, y, f"Overall Discount ({paid_bill.Overall_Discount_percent}%)")
        p.drawRightString(amt_x, y, f"- Rs. {int(totals['overall_discount_amount'])}")
        y -= 10

    # ✅ Total Discount
    if totals.get("total_discount", 0) > 0:
        p.line(5, y, width-5, y)
        y -= 12
        p.drawString(5, y, "Total Discount")
        p.drawRightString(amt_x, y, f"- Rs. {int(totals['total_discount'])}")
        y -= 10

    p.line(5, y, width-5, y)
    y -= 14

    # ✅ Grand total
    p.setFont("Helvetica-Bold", 11)
    p.drawString(5, y, "GRAND TOTAL")
    p.drawRightString(amt_x, y, f"Rs. {int(paid_bill.grand_total)}")
    y -= 20

    # ✅ Footer
    p.setFont("Helvetica", 7)
    p.drawCentredString(width/2, y, "Thank you for visiting BREAKROOM")
    y -= 10
    p.drawCentredString(width/2, y, "Contact: +91-8422902750  | For updates follow us on Instagram : @breakroom_08")
    y -= 10
    p.drawCentredString(width/2, y, "Please visit again!")

    p.showPage()
    p.save()

    pdf_data = buffer.getvalue()
    buffer.close()

    # ✅ Email if available
    if paid_bill.customer and paid_bill.customer.email:
        try:
            email = EmailMessage(
                subject=f"BREAKROOM Receipt – {paid_bill.bill_no}",
                body=f"Thank you! Total: Rs. {int(paid_bill.grand_total)}.\nReceipt attached.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[paid_bill.customer.email],
            )
            email.attach(f"{paid_bill.bill_no}.pdf", pdf_data, "application/pdf")
            email.send()
        except:
            pass

    response = HttpResponse(pdf_data, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{paid_bill.bill_no}.pdf"'
    return response

# ------------------ DASHBOARD ------------------
@login_required
def dashboard(request):
    today = now().date()
    print('today',today)
    total_sales = Bill.objects.filter(is_paid=True).aggregate(Sum("grand_total"))["grand_total__sum"] or 0
    today_sales = Bill.objects.filter(is_paid=True, created_at__date=today).aggregate(Sum("grand_total"))["grand_total__sum"] or 0
    print(today_sales,'today_salestoday_salestoday_salestoday_sales')

    paid_bills = Bill.objects.filter(is_paid=True).count()
    unpaid_bills = Bill.objects.filter(is_paid=False).count()

    total_customers = Customer.objects.count()

    recent_bills = Bill.objects.order_by("-created_at")[:10]
    recent_items = BillItem.objects.order_by("-created_at")[:20]

    return render(request, "pos/dashboard.html", {
        "total_sales": total_sales,
        "today_sales": today_sales,
        "paid_bills": paid_bills,
        "unpaid_bills": unpaid_bills,
        "total_customers": total_customers,
        "recent_bills": recent_bills,
        "recent_items": recent_items,
    })


@login_required
def add_food_quick(request):
    bill = get_current_bill(request)

    if not bill.customer:
        messages.error(request, "❌ Please save Customer first.")
        return redirect("pos:pos_ui")

    if request.method == "POST":
        item = request.POST.get("food_item")
        qty = float(request.POST.get("qty") or 1)

        if item in FOOD_MENU:
            BillItem.objects.create(
                bill=bill,
                category="FOOD",
                item_name=item,
                quantity=qty,
                rate=float(FOOD_MENU[item]),
            )
            messages.success(request, f"✅ Added {item}")

    return redirect("pos:pos_ui")


@login_required
def add_combo_quick(request):
    bill = get_current_bill(request)

    if not bill.customer:
        messages.error(request, "❌ Please save Customer first.")
        return redirect("pos:pos_ui")

    if request.method == "POST":
        combo_name = request.POST.get("combo_name")
        if combo_name in COMBOS:
            BillItem.objects.create(
                bill=bill,
                category="COMBO",
                item_name=combo_name,
                quantity=1,
                rate=float(COMBOS[combo_name])
            )
            messages.success(request, f"✅ Added Combo")

    return redirect("pos:pos_ui")



@login_required
def add_pool_quick(request):
    bill = get_current_bill(request)

    if not bill.customer:
        messages.error(request, "❌ Please save Customer first.")
        return redirect("pos:pos_ui")

    if request.method == "POST":
        duration = request.POST.get("duration")  # 30/60/120/180
        ft = request.POST.get("from_time")
        table_pref = request.POST.get("pool_table", "")  # optional

        if not duration or not ft:
            messages.error(request, "❌ Please select From Time and Duration")
            return redirect("pos:pos_ui")

        minutes = int(duration)
        auto_to = add_minutes_to_time(ft, minutes)

        start_t = datetime.strptime(ft, "%H:%M").time()
        end_t = datetime.strptime(auto_to, "%H:%M").time()

        selected_table, msg = allocate_pool_table(table_pref, start_t, end_t)
        if not selected_table:
            messages.error(request, msg)
            return redirect("pos:pos_ui")

        if msg:
            messages.warning(request, msg)

        weekend = is_weekend_today()
        rates = pool_rate_for_time(start_t, weekend)
        rate = rates.get(duration, 0)

        if rate == 0:
            messages.error(request, "❌ This duration is not allowed at this timing.")
            return redirect("pos:pos_ui")

        qty = minutes / 60
        resource = f"POOL-{selected_table}"
        name = f"Pool Table {selected_table} ({ft}-{auto_to})"

        BillItem.objects.create(
            bill=bill,
            category="GAME",
            item_name=name,
            quantity=qty,
            rate=rate,
            resource=resource,
            start_time=start_t,
            end_time=end_t,
        )

        messages.success(request, f"✅ Added {name}")

    return redirect("pos:pos_ui")

# ---------- QUICK ADD PS5 ----------
@login_required
def add_ps5_quick(request):
    bill = get_current_bill(request)

    if not bill.customer:
        messages.error(request, "❌ Please save Customer first.")
        return redirect("pos:pos_ui")

    if request.method == "POST":
        tv_size = request.POST.get("tv")  # 65/55
        controllers = int(request.POST.get("controllers") or 1)
        duration = request.POST.get("duration")  # 30/60
        ft = request.POST.get("from_time")

        if not (tv_size and duration and ft):
            messages.error(request, "❌ PS5 requires TV, Duration and From time")
            return redirect("pos:pos_ui")

        minutes = int(duration)
        auto_to = add_minutes_to_time(ft, minutes)

        start_t = datetime.strptime(ft, "%H:%M").time()
        end_t = datetime.strptime(auto_to, "%H:%M").time()

        resource = "PS5-65" if tv_size == "65" else "PS5-55"

        if is_resource_busy(resource, start_t, end_t):
            messages.error(request, f"❌ PS5 {tv_size}\" BUSY during {ft}-{auto_to}")
            return redirect("pos:pos_ui")

        rate = ps5_price(tv_size, controllers, duration)
        if rate == 0:
            messages.error(request, "❌ Invalid PS5 selection.")
            return redirect("pos:pos_ui")

        qty = minutes / 60
        name = f"PS5 ({tv_size} Inch) ({controllers} Ctrl) ({ft}-{auto_to})"

        BillItem.objects.create(
            bill=bill,
            category="GAME",
            item_name=name,
            quantity=qty,
            rate=rate,
            resource=resource,
            start_time=start_t,
            end_time=end_t,
        )

        messages.success(request, f"✅ Added {name}")

    return redirect("pos:pos_ui")


# ---------- REMOVE ITEM ----------
@login_required
def remove_item_quick(request, item_id):
    bill = get_current_bill(request)
    BillItem.objects.filter(id=item_id, bill=bill).delete()
    return redirect("pos:pos_ui")


# ---------- CUSTOMER SAVE ----------
@login_required
def save_customer(request):
    bill = get_current_bill(request)

    if request.method == "POST":
        name = request.POST.get("customer_name", "").strip()
        email = request.POST.get("customer_email", "").strip()
        phone = request.POST.get("customer_phone", "").strip()

        if not name or not email:
            messages.error(request, "❌ Name and Email are required.")
            return redirect("pos:pos_ui")

        cust, created = Customer.objects.get_or_create(
            email=email,
            defaults={"name": name, "phone": phone}
        )

        if not created:
            cust.name = name
            if phone:
                cust.phone = phone
            cust.save()

        bill.customer = cust
        bill.save()

        prev_total = cust.total_paid_amount()
        if prev_total >= 999:
            messages.success(request, f"🎁 Loyalty Eligible ✅ Previous Paid: Rs. {int(prev_total)}")
        else:
            messages.info(request, f"ℹ Loyalty unlocks after Rs.999 previous paid. Current: Rs. {int(prev_total)}")

    return redirect("pos:pos_ui")

def apply_discount_quick(request):
    bill = get_current_bill(request)

    if not bill.customer:
        messages.error(request, "❌ Save customer first to apply discount.")
        return redirect("pos:pos_ui")

    if request.method == "POST":
        food_disc = float(request.POST.get("food_disc_percent") or 0)
        game_disc = float(request.POST.get("game_disc_amount") or 0)

        # ✅ loyalty condition
        if bill.customer.total_paid_amount() < 999 and (food_disc > 0 or game_disc > 0):
            messages.warning(request, "⚠ Not eligible for loyalty discount (needs Rs.999 previous paid).")

        bill.food_discount_percent = food_disc
        bill.game_discount_amount = game_disc
        bill.save()

    return redirect("pos:pos_ui")

@login_required
def pos_ui(request):
    bill = get_current_bill(request)
    totals = recalc_bill(bill)

    return render(request, "pos/pos_main.html", {
        "bill": bill,
        "items": bill.billitem_set.all().order_by("created_at"),
        "totals": totals,
        "food_menu": FOOD_MENU,
        "combos": COMBOS,
    })


@login_required
def new_bill(request):
    bill = Bill.objects.create(bill_no=generate_bill_no())
    request.session["bill_id"] = bill.id
    messages.success(request, f"✅ New Bill Created: {bill.bill_no}")
    return redirect("pos:bill_summary")



@login_required
def profit_dashboard(request):
    today = now().date()
    month_start = today.replace(day=1)

    category_map = defaultdict(float)

    items = (
        BillItem.objects
        .filter(bill__is_paid=True)
        .annotate(line_total=F("quantity") * F("rate"))
    )

    for it in items:
        total = float(it.total or 0)

        if it.category in ["FOOD", "COMBO"]:
            category_map["Food"] += total

        elif it.category == "DRINKS":
            category_map["Beverages"] += total

        elif it.category == "GAME":
            if it.resource and it.resource.startswith("POOL"):
                category_map["Pool"] += total
            elif it.resource and it.resource.startswith("PS5"):
                category_map["PS5"] += total

    categories = list(category_map.keys())
    category_totals = list(category_map.values())

    # =============================
    # TOP ITEMS
    # =============================
    top_items_qs = (
        BillItem.objects
        .filter(bill__is_paid=True)
        .values("item_name")
        .annotate(total=Sum(F("quantity") * F("rate")))
        .order_by("-total")[:5]
    )

    top_items = [i["item_name"] for i in top_items_qs]
    top_items_total = [float(i["total"]) for i in top_items_qs]

    # =============================
    # KPIs
    # =============================
    today_sales = (
        Bill.objects.filter(is_paid=True, created_at__date=today)
        .aggregate(total=Sum("grand_total"))["total"] or 0
    )

    month_sales = (
        Bill.objects.filter(is_paid=True, created_at__date__gte=month_start)
        .aggregate(total=Sum("grand_total"))["total"] or 0
    )

    return render(request, "pos/profit_dashboard.html", {
        "categories": categories,
        "category_totals": category_totals,
        "top_items": top_items,
        "top_items_total": top_items_total,
        "today_sales": today_sales,
        "month_sales": month_sales,
        "category_map": category_map,
        "top_items_qs": top_items_qs,
    })