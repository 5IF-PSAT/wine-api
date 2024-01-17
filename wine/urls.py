from django.urls import path
from wine.views import WineList, WineDetail, WineFilter


urlpatterns = [
    path("", WineList.as_view({"get": "list", "post": "create"})),
    path("<int:pk>/", WineDetail.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
    path("filter/", WineFilter.as_view({"get": "list"})),
]
