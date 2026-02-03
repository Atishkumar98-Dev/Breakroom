# from django.urls import path
# from . import views

# app_name = "pos"

# urlpatterns = [
#     path("", views.pos_ui, name="choose_zone"),

#     path("bill/", views.bill_summary, name="bill_summary"),
#     path("save-customer/", views.save_customer, name="save_customer"),
    


#     path("add-pool/", views.add_pool_quick, name="add_pool_quick"),
#     path("add-ps5/", views.add_ps5_quick, name="add_ps5_quick"),

#     path("remove-item/<int:item_id>/", views.remove_item_quick, name="remove_item_quick"),

#     # path("apply-discount/", views.apply_discount_quick, name="apply_discount_quick"),

#     path("mark-paid/", views.mark_paid, name="mark_paid"),
#     path("print/", views.print_bill, name="print_bill"),

#     path("dashboard/", views.dashboard, name="dashboard"),
#     path("add/combo/", views.add_combo, name="add_combo"),
#     path("apply-discount/", views.apply_discount_quick, name="apply_discount_quick"),
#     path("remove/<int:item_id>/", views.remove_item, name="remove_item"),

#     path("paid/", views.mark_paid, name="mark_paid"),
#     path("print/", views.print_bill, name="print_bill"),

#     path("dashboard/", views.dashboard, name="dashboard"),
# ]



from django.urls import path
from . import views

app_name = "pos"

urlpatterns = [
    # path("", views.pos_ui, name="pos_ui"),
    path("", views.choose_zone, name="choose_zone"),
    path("bill/new/", views.new_bill, name="new_bill"),
    path("save-customer/", views.save_customer, name="save_customer"),
    path("bill/switch/<int:bill_id>/", views.switch_bill, name="switch_bill"),
    path("add-food/", views.add_food_quick, name="add_food_quick"),
    path("add-combo/", views.add_combo_quick, name="add_combo_quick"),

    path("add-pool/", views.add_pool_quick, name="add_pool_quick"),
    path("add-ps5/", views.add_ps5_quick, name="add_ps5_quick"),

    path("remove-item/<int:item_id>/", views.remove_item_quick, name="remove_item_quick"),

    path("apply-discount/", views.apply_discount_quick, name="apply_discount_quick"),

    path("mark-paid/", views.mark_paid, name="mark_paid"),
    path("print/", views.print_bill, name="print_bill"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("add/food/", views.add_food, name="add_food"),
    path("add/pool/", views.add_pool, name="add_pool"),
    path("add/ps5/", views.add_ps5, name="add_ps5"),
    path("add/combo/", views.add_combo, name="add_combo"),
    path("bill/", views.bill_summary, name="bill_summary"),
    path("remove/<int:item_id>/", views.remove_item, name="remove_item"),
    path("bill/print/<int:bill_id>/", views.print_bill_by_id, name="print_bill_by_id"),
    path("dashboard/profit/", views.profit_dashboard, name="profit_dashboard"),


]