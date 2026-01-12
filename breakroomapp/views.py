from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.timezone import localtime
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from PIL import Image
import io, os, subprocess

from .models import Bill, BillItem
from .utils import (
    generate_bill_no, detect_printer_width,
    generate_upi_qr, send_bill_email
)

GST = 18
SERVICE = 5


def recalc(bill):
    subtotal = sum(i.total for i in bill.billitem_set.all())
    bill.subtotal = subtotal
    bill.gst = subtotal * GST / 100
    bill.service_charge = subtotal * SERVICE / 100
    bill.grand_total = bill.subtotal + bill.gst + bill.service_charge
    bill.save()


@login_required
def billing_page(request):
    bill_id = request.session.get("bill_id")

    if bill_id:
        bill = Bill.objects.get(id=bill_id)
    else:
        bill = Bill.objects.create(bill_no=generate_bill_no())
        request.session["bill_id"] = bill.id

    if request.method == "POST":
        name = request.POST.get("item")
        qty = request.POST.get("qty")
        rate = request.POST.get("rate")

        if name and qty and rate:
            BillItem.objects.create(
                bill=bill,
                item_name=name,
                quantity=float(qty),
                rate=float(rate)
            )
            recalc(bill)

        return redirect("/")

    return render(request, "billing/billing.html", {
        "bill": bill,
        "items": bill.billitem_set.all()
    })


@login_required
def remove_item(request, item_id):
    item = get_object_or_404(BillItem, id=item_id)
    bill = item.bill
    item.delete()
    recalc(bill)
    return redirect("/")


@login_required
def edit_item(request, item_id):
    item = get_object_or_404(BillItem, id=item_id)
    item.quantity = float(request.POST["qty"])
    item.rate = float(request.POST["rate"])
    item.save()
    recalc(item.bill)
    return redirect("/")


@login_required
def new_bill(request):
    request.session.pop("bill_id", None)
    return redirect("/")


@login_required
def mark_paid(request):
    bill = Bill.objects.get(id=request.session["bill_id"])
    bill.is_paid = True
    bill.customer_email = request.POST.get("email")
    bill.save()
    return redirect("billing:print_bill")


@login_required
def print_bill(request):
    bill = Bill.objects.get(id=request.session["bill_id"])

    # -------- THERMAL SIZE (AUTO) --------
    paper_mm = detect_printer_width()   # 58 or 80
    width = paper_mm * mm
    height = 260 * mm

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(width, height))

    # -------- LOGO PATH (PNG WITH TRANSPARENCY) --------
    logo_path = os.path.join(
    settings.BASE_DIR,     # 👈 project folder
    "static",
    "billing",
    "logo.png"
)
    print("LOGO FOUND:", logo_path, os.path.exists(logo_path))

    # -------- WATERMARK (VERY LIGHT & CLEAN) --------
    if os.path.exists(logo_path):
        p.saveState()

        # Perfect opacity for thermal
        try:
            p.setFillAlpha(0.06)
        except:
            pass

        p.translate(width / 2, height / 1.5 + 1.5)
        p.rotate(45)

        p.drawImage(
            logo_path,
            -90, -90,
            width=180,
            height=180,
            mask='auto'   # 🔥 keeps transparency
        )

        p.restoreState()

    y = height - 20

    # -------- HEADER LOGO --------
    if os.path.exists(logo_path):
        p.drawImage(
            logo_path,
            width / 2 - 22,
            y - 35,
            width=44,
            height=44,
            mask='auto'
        )
        y -= 50

    # -------- HEADER TEXT --------
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width / 2, y, "BREAKROOM")
    y -= 14

    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2, y, "PLAY • EAT • REPEAT")
    y -= 12

    p.line(5, y, width - 5, y)
    y -= 12

    # -------- BILL INFO --------
    p.setFont("Helvetica", 8)
    p.drawString(5, y, f"Bill No: {bill.bill_no}")
    y -= 10
    p.drawString(
        5, y,
        f"Date: {localtime(bill.created_at).strftime('%d-%m-%Y %H:%M')}"
    )
    y -= 12

    p.line(5, y, width - 5, y)
    y -= 12

    # -------- TABLE HEADER --------
    p.setFont("Helvetica-Bold", 8)
    p.drawString(5, y, "Item")
    p.drawRightString(width - 30, y, "Qty")
    p.drawRightString(width - 5, y, "Amt")
    y -= 10

    p.line(5, y, width - 5, y)
    y -= 8

    # -------- ITEMS --------
    p.setFont("Helvetica", 8)
    for item in bill.billitem_set.all():
        p.drawString(5, y, item.item_name[:22])
        p.drawRightString(width - 30, y, str(item.quantity))
        p.drawRightString(width - 5, y, f"{int(item.total)}")
        y -= 10

    y -= 5
    p.line(5, y, width - 5, y)
    y -= 12

    # -------- TOTALS --------
    p.setFont("Helvetica", 8)
    p.drawString(5, y, "Subtotal")
    p.drawRightString(width - 5, y, f" Rs. {int(bill.subtotal)}")
    y -= 10

    p.drawString(5, y, "GST (18%)")
    p.drawRightString(width - 5, y, f" Rs. {int(bill.gst)}")
    y -= 10

    p.drawString(5, y, "Service (5%)")
    p.drawRightString(width - 5, y, f" Rs. {int(bill.service_charge)}")
    y -= 10

    p.line(5, y, width - 5, y)
    y -= 12

    p.setFont("Helvetica-Bold", 9)
    p.drawString(5, y, "TOTAL")
    p.drawRightString(width - 5, y,  f" Rs. {int(bill.grand_total)}")
    y -= 15

    p.line(5, y, width - 5, y)
    y -= 15

    # -------- FOOTER --------
    p.setFont("Helvetica-Bold", 8)
    p.drawCentredString(width / 2, y, "Thank You!")
    y -= 12

    p.setFont("Helvetica", 7)
    p.drawCentredString(width / 2, y, "Visit Again 🎮🍔")

    p.showPage()
    p.save()

    # -------- SAVE PDF --------
    pdf_path = f"/tmp/{bill.bill_no}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(buffer.getvalue())

    # -------- SILENT PRINT --------
    subprocess.Popen(["lp", pdf_path])

    # -------- EMAIL (ONLY IF PAID) --------
    if bill.is_paid:
        send_bill_email(bill, pdf_path)

    return redirect("billing:billing")
