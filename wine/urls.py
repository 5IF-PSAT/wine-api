from django.urls import path
from wine.views import WineList, WineDetail


urlpatterns = [
    path("", WineList.as_view({"get": "list", "post": "create"})),
    path("<int:pk>/", WineDetail.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
]
