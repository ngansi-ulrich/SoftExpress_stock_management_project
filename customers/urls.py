from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.customer_list,
        name="customer_list"
    ),

    path(
        "add/",
        views.add_customer,
        name="add_customer"
    ),

    path(
        "edit/<int:id>/",
        views.customer_edit,
        name="customer_edit"
    ),

    path(
        "<int:id>/",
        views.customer_detail,
        name="customer_detail"
    ),

    path(
        "delete/<int:id>/",
        views.customer_delete,
        name="customer_delete"
    ),

]