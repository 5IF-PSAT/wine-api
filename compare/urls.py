from django.urls import path
from compare.views import compare_wine


urlpatterns = [
    path("compare_wine/", compare_wine, name="compare_wine"),
]
