from django.urls import path
from wine.views import (
    WineList,
    SecondWineList,
    WineDetail,
    WineFilter,
)

urlpatterns = [
    path("", WineList.as_view({"post": "create"})),
    path("list/", SecondWineList.as_view({"get": "list"})),
    path("<int:pk>/", WineDetail.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
    path("filter/", WineFilter.as_view({"get": "list"})),
]
