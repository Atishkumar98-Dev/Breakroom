# from .models import Bill

# def generate_bill_no(bill_type):
#     prefix_map = {
#         'G': 'BR-G',
#         'F': 'BR-F',
#         'P': 'BR-P',
#         'C': 'BR-C',
#     }

#     count = Bill.objects.filter(bill_type=bill_type).count() + 1
#     return f"{prefix_map[bill_type]}-{count:03d}"
import subprocess
import subprocess
import qrcode
import os
from .models import Bill
from django.core.mail import EmailMessage

def generate_bill_no():
    count = Bill.objects.count() + 1
    return f"BR-C-{count:03d}"


def detect_printer_width():
    try:
        out = subprocess.check_output(
            "lpoptions -l | grep PageSize",
            shell=True
        ).decode()
        if "80" in out:
            return 80
    except:
        pass
    return 58


def generate_upi_qr(amount):
    upi = f"upi://pay?pa=yourupi@bank&pn=BREAKROOM&am={int(amount)}&cu=INR"
    path = "/tmp/upi_qr.png"
    qrcode.make(upi).save(path)
    return path


from django.core.mail import EmailMessage
from django.conf import settings

def send_bill_email(bill, pdf_path):
    if not bill.customer_email:
        return

    email = EmailMessage(
        subject=f"BREAKROOM Receipt – {bill.bill_no}",
        body=f"""
                Thank you for visiting BREAKROOM 🎮🍔

                Bill No: {bill.bill_no}
                Amount Paid: ₹{bill.grand_total}

                Your receipt is attached.

                Play • Eat • Repeat
                BREAKROOM
                """,
        from_email=settings.DEFAULT_FROM_EMAIL,   # ✅ no-reply
        to=[bill.customer_email],
    )

    email.attach_file(pdf_path)
    email.send()







def detect_printer_width():
    try:
        output = subprocess.check_output(
            "lpoptions -l | grep PageSize",
            shell=True
        ).decode()

        if "80" in output:
            return 80
        return 58
    except:
        return 58  # default


import qrcode
import os

def generate_upi_qr(amount):
    upi_string = f"upi://pay?pa=atishkumar31518@oksbi&pn=Atish&am={int(amount)}&cu=INR"
    qr = qrcode.make(upi_string)

    path = "/tmp/upi_qr.png"
    qr.save(path)
    return path