from django.urls import path
from . import views

urlpatterns = [

    path("", views.employee_list, name="employee_list"),

    path("add/", views.add_employee, name="add_employee"),

    path("edit/<int:id>/", views.employee_edit, name="employee_edit"),

    path("delete/<int:id>/", views.employee_delete, name="employee_delete"),

]