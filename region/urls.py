from django.urls import path
from region.views import RegionList, RegionDetail


urlpatterns = [
    path("", RegionList.as_view({"get": "list", "post": "create"})),
    path("<int:pk>/", RegionDetail.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
]
