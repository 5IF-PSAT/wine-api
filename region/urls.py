from django.urls import path
from region.views import RegionList, RegionDetail, RegionFilter


urlpatterns = [
    path("", RegionList.as_view({"get": "list", "post": "create"})),
    path("<int:pk>/", RegionDetail.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
    path("filter/", RegionFilter.as_view({"get": "list"})),
]
