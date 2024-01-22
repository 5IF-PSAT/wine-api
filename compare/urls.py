from django.urls import path
from compare.views import compare_wine, get_list_vintages


urlpatterns = [
    path("list_vintages/", get_list_vintages, name="list_vintages"),
    path("compare_wine/", compare_wine, name="compare_wine"),
]
