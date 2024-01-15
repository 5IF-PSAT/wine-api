from django.urls import path
from predict.views import forecast_weather


urlpatterns = [
    path("forecast_weather/", forecast_weather, name="forecast_weather"),
]
