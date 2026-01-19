from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("", views.billing_page, name="billing"),
    path("remove/<int:item_id>/", views.remove_item, name="remove_item"),
    path("paid/", views.mark_paid, name="mark_paid"),
    path("print/", views.print_bill, name="print_bill"),
    path("new/", views.new_bill, name="new_bill"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
