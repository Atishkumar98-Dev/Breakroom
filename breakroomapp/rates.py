# pos/rates.py
from datetime import time


# ✅ FOOD MENU
FOOD_MENU = {
    "French Fries": 119,
    "Peri Peri Fries": 129,
    "Cheesy Fries": 139,
    "Cheesy Poppers": 179,
    "Crispy Cheese Sticks": 189,
    "Potato Wedges": 129,
    "Maggie": 49,
    "Banta Soda" : 39,
    "Cold Coffee": 99,
    "Iced Tea": 49,
    "Hot Chocolate": 109,
    "Coffee": 49,
    "Special Tea": 29,
    "Lemon Tea": 39,
    "Mayonise": 29,
    "Chipotle": 29,
    "Cheese Dip": 39,
    "Peri Peri": 29,
    "Honey Mustard": 39,
    "Half Veg Momo's": 79,
    "Half Paneer Momo's": 89,
    "Half Cheese Chilly Momo's": 99,
    "Half Veg Peri Peri Momo's": 89,
    "Half Paneer Peri peri Momo's": 99,
    "Half Paneer Mix Dumplings": 99,
    "Half Peri Peri Paneer Dumplings": 109,
    "Veg Momo's": 139,
    "Paneer Momo's": 149,
    "Cheese Chilly Momo's": 159,
    "Veg Peri Peri Momo's": 149,
    "Paneer Peri peri Momo's": 159,
    "Paneer Mix Dumplings": 159,
    "Peri Peri Paneer Dumplings": 179,
    "Steamed BAO Spicy" : 199,
    "NACHOS":49,
    "Water Bottle": 20,
    "Amchi": 135,
}

DRINKS = {
"Energy Drink 350ml": 125,
    "Energy Drink 300ml": 60,
    "Diet Coke": 40,
    "Thumps Up Can":40,
    "Sprite Can": 40,
    "Minute Maid 250ml": 25,
    "Soft Drink 250ml": 20,
    "Soft Drink 200ml": 20,
}

ICECREAM = {
    # ✅ CANDIES
    "Crunchy Choco": 70,
    "Choco Fudge (Choco Bar)": 70,
    "Mango Choco": 40,
    "Vanilla Choco": 40,

    "Creamy Chocolate": 90,
    "Choco Fudge (Boss Bar)": 90,
    "Orange Chocolate": 90,
    "Dark Chocolate": 90,
    "Raspberry": 90,
    "Strawberry (Boss Bar)": 65,
    "Mango (Boss Bar)": 65,

    "Chocoboom Bar": 45,
    "Mango (Chaboom)": 30,

    # ✅ CUPS
    "Butterscotch (Scooperstar 125ml)": 55,
    "Blueberry Cheesecake (Scooperstar 125ml)": 55,
    "Mango Coconut (Scooperstar 125ml)": 55,
    "Rajbhog (Scooperstar 125ml)": 55,
    "Hazelnut Mudslide (Scooperstar 125ml)": 55,
    "Choco Chips (Scooperstar 125ml)": 45,
    "American Nuts (Scooperstar 125ml)": 45,
    "Vanilla (Scooperstar 125ml)": 30,

    "Vanilla (Classic Cup)": 30,
    "Strawberry (Classic Cup)": 30,
    "Tutti Frutti (Classic Cup)": 30,
    "Mango (Classic Cup)": 30,
    "Kesar Pista (Classic Cup)": 30,
    "Butter Scotch (Classic Cup)": 30,
    "Chocolate (Classic Cup)": 30,

    "Choco Brownie (Sundae Cup)": 75,
    "Oreo Sundae (Sundae Cup)": 75,
    "Golden Fantasy (Sundae Cup)": 115,
    "Mango Sundae (Sundae Cup)": 75,

    # ✅ KULFIS
    "Choco Fudge Kulfi": 70,
    "Shahi Kulfi": 40,
    "Malai Kulfi": 40,
    "Kesar Pista Kulfi": 40,

    # ✅ CONES
    "Choco Madness (Chill’O Cone)": 110,
    "Dark Chocolate (Chill’O Cone)": 110,
    "Butterscotch (Chill’O Cone)": 110,
    "Strawberry Cheesecake (Chill’O Cone)": 110,
    "Black Forest (Chill’O Cone)": 110,
    "Chocolate Overload (Chill’O Cone)": 110,

    "Hazelnut Mudslide (Oh! Cone)": 95,
    "Nutty Chocolate (Oh! Cone)": 95,
    "Choco Vanilla (Oh! Cone)": 90,

    "Choco Vanilla (Bro Cone)": 40,
    "Butterscotch (Bro Cone)": 40,

    # ✅ NOVELTIES
    "Choco Brownie Ice Cream": 120,
    "Ice Cream Sandwich": 100,

    # ✅ TUBS
    "Vanilla Tub": 140,
    "Strawberry Tub": 140,
    "Mango Tub": 140,
    "Chocolate Tub": 160,
    "Butter Scotch Tub": 160,
    "Kesar Pista Tub": 180,
    "American Nuts Tub": 180,
    "Black Forest Tub": 200,
    "Rajbhog Tub": 200,

    # ✅ COMBO PACKS (700 ml)
    "Choco Vanilla (Combo Pack 700ml)": 200,
    "Strawberry (Combo Pack 700ml)": 200,
    "Butterscotch (Combo Pack 700ml)": 200,
    "Chocolate (Combo Pack 700ml)": 200,
    "Vanilla (Combo Pack 700ml)": 200,

    # ✅ HEALTHIES
    "Kaju Anjeer": 250,
    "Choco Chocolate (Healthies)": 250,
    "Creamy Coconut": 250,
    "Mango Tropical Mix": 250,

    # ✅ BON BON
    "Choco Bon Bon": 10,
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
PS5_65_SINGLE = {"30": 180, "60": 250,"120": 500, "180": 750}
PS5_65_MULTI  = {"30": 120,  "60": 150,"120": 300, "180": 450}

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
