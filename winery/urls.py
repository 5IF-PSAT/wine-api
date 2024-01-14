from django.urls import path
from winery.views import WineryList, WineryDetail


urlpatterns = [
    path("", WineryList.as_view({"get": "list", "post": "create"})),
    path("<int:pk>/", WineryDetail.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
]
