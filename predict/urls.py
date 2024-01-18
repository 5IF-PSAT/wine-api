from django.urls import path
from predict.views import (
    forecast_weather,
    predict_rating,
    predict_all_rating,
)


urlpatterns = [
    path("forecast_weather/", forecast_weather, name="forecast_weather"),
    path("predict_rating/", predict_rating, name="predict_rating"),
    path("predict_all_rating/", predict_all_rating, name="predict_all_rating"),
]
