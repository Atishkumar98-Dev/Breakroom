# 🧾 BREAKROOM – Gaming & Café Billing System (Django POS)

A **professional Django-based POS (Point of Sale) system** designed for **gaming zones, cafés, and breakrooms**.
Supports **gaming + food billing in a single bill**, **thermal receipt printing**, **email receipts**, and **cashier login**.

---

## 🚀 Features

### 🎮 Gaming & Food Billing

* Separate **Gaming Zone** and **Food Zone**
* Pool / PS5 billed by hours
* Food billed by quantity
* All items added into **one live bill**

### 🧾 Billing & Payments

* Sequential bill numbers (`BR-C-001`, `BR-C-002`, …)
* GST (18%) and Service Charge (5%)
* Edit quantity & rate
* Remove items
* Mark bill as **PAID**
* Lock & print after payment

### 🖨️ Thermal Receipt (PDF)

* Professional **58mm / 80mm thermal PDF**
* Auto printer width support
* Clean layout (receipt style)
* **Transparent logo in header**
* **Light watermark logo**
* Silent auto-print on Linux (CUPS)

### 📧 Email Receipt

* Sends **PDF receipt by email** when paid
* Sent from **no-reply address**
* Uses Gmail SMTP with App Password
* PDF attached automatically

### 🔐 Authentication

* Cashier login (Django auth)
* Billing page protected
* Logout supported

---

## 🛠️ Tech Stack

* **Backend**: Django 5.x
* **Database**: SQLite (default)
* **PDF**: ReportLab
* **Email**: SMTP (Gmail)
* **Printing**: CUPS (Linux)
* **Frontend**: HTML + CSS (POS-style UI)

---

## 📁 Project Structure

```
breakroom/
│
├── manage.py
├── breakroom/
│   ├── settings.py
│   ├── urls.py
│
├── billing/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── utils.py
│   ├── templates/
│   │   └── billing/
│   │       ├── billing.html
│   │       └── login.html
│   └── static/
│       └── billing/
│           ├── style.css
│           └── logo.png
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the project

```bash
git clone <your-repo-url>
cd breakroom
```

### 2️⃣ Create virtual environment

```bash
python3 -m venv venv_breakroom
source venv_breakroom/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install django reportlab pillow qrcode
```

### 4️⃣ System dependencies (Linux)

```bash
sudo apt update
sudo apt install python3-tk cups
```

---

## 🗄️ Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

Create cashier/admin user:

```bash
python manage.py createsuperuser
```

---

## ▶️ Run the Server

```bash
python manage.py runserver
```

Open in browser:

```
http://127.0.0.1:8000/
```

---

## 🔐 Login

* Login required to access billing
* Uses Django authentication
* Logout supported

---

## 🖨️ Thermal Printing (Linux)

* Uses **CUPS**
* Ensure printer is added:

```bash
lpstat -p
```

* Silent print is handled via:

```bash
lp <file>.pdf
```

---

## 📧 Email Configuration (Gmail)

### Enable:

* Google **2-Step Verification**
* Create **App Password**

### `settings.py`

```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = "yourgmail@gmail.com"
EMAIL_HOST_PASSWORD = "APP_PASSWORD"

DEFAULT_FROM_EMAIL = "BREAKROOM <no-reply@breakroom.com>"
```

> ⚠️ Never use normal Gmail password. Always use App Password.

---

## 🖼️ Logo Requirements

* Location:

```
breakroom/static/billing/logo.png
```

* Format:

  * PNG
  * Transparent background (recommended)

Used for:

* Header logo
* Light watermark on receipt

---

## 🧪 Testing Email (Without Sending)

For testing:

```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

Emails will print in terminal.

---

## 🔒 Security Notes

* Login required for billing
* Email credentials should be moved to environment variables in production
* WhatsApp integration intentionally **not enabled** (paid service)

---

## 📌 Current Limitations

* SQLite database (can be upgraded to PostgreSQL)
* No WhatsApp receipt (by choice)
* No daily report UI (can be added)

---

## 🚀 Possible Future Enhancements

* Daily / monthly sales reports
* PAID watermark on receipt
* Cash drawer trigger
* WhatsApp receipt (optional, paid)
* Cloud deployment (AWS / DigitalOcean)
* Touch-screen optimized UI

---

## 🧑‍💻 Author

**BREAKROOM POS System**
Built with ❤️ for gaming zones & cafés.

---

## 📄 License

This project is for **internal / commercial use**.
Add a license file if distributing publicly.

---


