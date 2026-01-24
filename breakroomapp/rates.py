# pos/rates.py
from datetime import time


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


# ✅ COMBOS
COMBOS = {
    "Pool 30 + Fries + Virgin Mojito": 319,
    "Pool 1 hr + Smoked Momo’s + Virgin Mojito": 479,
    "PS5 65\" 30 + Fries + Cold Coffee": 349,
    "PS5 55\" 30 + Maggie + Cold Coffee": 259,
    "Dip Pack (Mayo + Peri Peri)": 49,
    "Cheese Dip Add-on": 39,
}


# -----------------------------
# ✅ POOL RATE LOGIC (TIME BASED)
# -----------------------------
def pool_rate_for_time(start_time, is_weekend):
    """
    Returns a dict of duration -> price for pool based on time/day.

    ✅ Weekdays:
        11am-5pm : 30=120, 60=200, offers 120=360, 180=500
        5pm+     : 30=150, 60=250

    ✅ Weekends:
        11am-2pm : 30=120, 60=200
        2pm+     : 30=150, 60=250
    """
    if not is_weekend:
        # Weekdays
        if start_time < time(17, 0):  # before 5 PM
            return {"30": 120, "60": 200, "120": 360, "180": 500}
        else:
            return {"30": 150, "60": 250, "120": 500, "180": 750}

    # Weekends
    if start_time < time(14, 0):  # before 2 PM
        return {"30": 120, "60": 200, "120": 360, "180": 500}
    else:
        return {"30": 150, "60": 250,"120": 360, "180": 500}


# -----------------------------
# ✅ PS5 RATES (STATIC)
# -----------------------------
# (Your earlier fixed PS5 rules)
PS5_65_SINGLE = {"30": 150, "60": 250,"120": 500, "180": 750}
PS5_65_MULTI  = {"30": 90,  "60": 150,"120": 300, "180": 450}

PS5_55_SINGLE = {"30": 140, "60": 220,"120": 440, "180": 660}
PS5_55_MULTI  = {"30": 80,  "60": 140,"120": 280, "180": 420}


def ps5_price(tv_size, controllers, duration):
    """
    ✅ Returns PS5 price based on:
    - TV size: 65 or 55
    - controllers: 1 or more
    - duration: "30" / "60"
    """
    if tv_size == "65":
        if controllers == 1:
            return PS5_65_SINGLE.get(duration, 0)
        return PS5_65_MULTI.get(duration, 0) * controllers

    # 55 inch
    if controllers == 1:
        return PS5_55_SINGLE.get(duration, 0)
    return PS5_55_MULTI.get(duration, 0) * controllers
