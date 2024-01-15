from django.urls import path
from predict.views import (
    forecast_weather,
    predict_rating
)


urlpatterns = [
    path("forecast_weather/", forecast_weather, name="forecast_weather"),
    path("predict_rating/", predict_rating, name="predict_rating"),
]
