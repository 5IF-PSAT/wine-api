from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from django.core.cache import cache
from wine_api.settings import CACHE_TTL
from predict.serializers import (
    PredictSerializer,
    RatingSerializer,
    ListRatingSerializer,
)
from nixtlats import TimeGPT
import pandas as pd
from region.models import Region
from wine.models import Wine
import json
from rest_framework.permissions import AllowAny
from wine_api.settings import BASE_DIR
from likewines.processor import PredictDataProcessor
from likewines.model import PredictModel


@api_view(['GET'])
@permission_classes([AllowAny])
def forecast_weather(request):
    region_id = request.query_params.get('region_id', None)
    predict_field = request.query_params.get('predict_field', None)
    nb_months = request.query_params.get('nb_months', None)
    frequency = request.query_params.get('freq', None)
    api_key = request.query_params.get('api_key', None)
    if region_id is None or predict_field is None or \
            nb_months is None or frequency is None or api_key is None:
        return HttpResponse(content='Missing parameters: region_id, predict_field, nb_months, freq, api_key',
                            status=400)
    list_fields = ['avg_temperature', 'min_temperature', 'max_temperature',
                   'avg_sunshine_duration', 'min_sunshine_duration', 'max_sunshine_duration',
                   'avg_precipitation', 'avg_rain', 'avg_snowfall',
                   'avg_humidity', 'avg_wind_speed', 'avg_soil_temperature',
                   'avg_soil_moisture']
    if predict_field not in list_fields:
        return HttpResponse(content='''predict_field must be in this list: avg_temperature, min_temperature,
        max_temperature, avg_sunshine_duration, min_sunshine_duration, max_sunshine_duration, avg_precipitation,
        avg_rain, avg_snowfall, avg_humidity, avg_wind_speed, avg_soil_temperature, avg_soil_moisture''',
                            status=400)
    # Check if the request is cached
    cache_key = f'forecast_weather_{region_id}_{predict_field}_{nb_months}_{frequency}'
    cached_response = cache.get(cache_key)
    if cached_response is not None:
        returned_data = json.loads(cached_response)
        serializer = PredictSerializer(returned_data)
        return JsonResponse(serializer.data, status=200)

    # Initialize the model
    model = TimeGPT(
        token=api_key,
    )
    # Check if api_key is valid
    if not model.validate_token():
        return HttpResponse(content='Invalid api_key', status=400)

    # Get the region
    region = Region.objects.get_region_by_id(region_id)
    if region is None:
        return HttpResponse(content='Invalid region_id', status=400)

    # Get the xwine_id
    xwine_id = region.region_id

    # Get the weather data
    weather_data = pd.read_parquet(f'{BASE_DIR}/predict_data/agg_monthly.parquet')
    weather_data = weather_data[weather_data['RegionID'] == xwine_id]

    # Add timestamp column
    weather_data['timestamp'] = pd.to_datetime(weather_data[['year', 'month']].assign(DAY=1))

    # Forecast weather
    forecast_df = model.forecast(
        df=weather_data,
        h=int(nb_months),
        time_col='timestamp',
        target_col=predict_field,
        freq=frequency,
    )

    # Return the forecast
    returned_data = {
        'timestamp': forecast_df['timestamp'].tolist(),
        'predict_field': predict_field,
        'predict_value': forecast_df['TimeGPT'].tolist(),
    }

    # Cache the response
    cache.set(cache_key, json.dumps(returned_data), timeout=CACHE_TTL)

    # Serialize the data
    serializer = PredictSerializer(data=returned_data)
    if serializer.is_valid():
        return JsonResponse(serializer.data, status=200)
    return HttpResponse(content='Invalid data', status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def predict_rating(request):
    """
    Predict the rating of a wine with maximum vintage of 2023
    :param request:
    :return:
    """
    wine_id = request.query_params.get('wine_id', None)
    batch_vintage = request.query_params.get('batch_vintage', '2023')
    rating_year = request.query_params.get('rating_year', None)

    if wine_id is None or rating_year is None:
        return HttpResponse(content='Missing parameters: wine_id, rating_year', status=400)
    # Get wine
    wine = Wine.objects.get_wine_by_id(wine_id)
    if wine is None:
        return HttpResponse(content='There is no wine with this id', status=400)
    batch_vintage = int(batch_vintage)
    rating_year = int(rating_year)
    if batch_vintage > 2023 or batch_vintage < 1949:
        return HttpResponse(content='batch_vintage must be between 1949 and 2023', status=400)
    if batch_vintage > rating_year:
        return HttpResponse(content='rating_year must be greater than batch_vintage', status=400)
    # Check if the request is cached
    cache_key = f'predict_rating_{wine_id}_{batch_vintage}_{rating_year}'
    cached_response = cache.get(cache_key)
    if cached_response is not None:
        returned_data = json.loads(cached_response)
        serializer = RatingSerializer(returned_data)
        return JsonResponse(serializer.data, status=200)
    # Configure the batch_vintage
    batch_vintage = [batch_vintage]

    # Read forecast data
    path_forecast_df = f'{BASE_DIR}/predict_data/forecast_agg_monthly.parquet'

    # Initialize the data processor
    data_processor = PredictDataProcessor(
        wine=wine,
        rating_year=rating_year,
        path_forecast_df=path_forecast_df,
        batch_vintage=batch_vintage,
        path_minmax_scaler=f'{BASE_DIR}/model/minmax_scaler.save',
        path_standard_scaler=f'{BASE_DIR}/model/std_scaler.save',
    )

    # Process the data
    time_series_input, numerical_input = data_processor.process_data()

    # Initialize the model
    cnn_model = PredictModel(
        path_cnn_model=f'{BASE_DIR}/model/cnn_model.h5',
    )
    list_predict_rating = cnn_model.predict(
        time_series_input=time_series_input,
        numerical_input=numerical_input,
    )
    prediction = list_predict_rating[0]

    # Return the prediction
    returned_data = {
        'wine_id': wine_id,
        'batch_vintage': batch_vintage[0],
        'rating_year': rating_year,
        'predict_rating': prediction
    }

    # Cache the response
    cache.set(cache_key, json.dumps(returned_data), timeout=CACHE_TTL)

    # Serialize the data
    serializer = RatingSerializer(data=returned_data)
    if serializer.is_valid():
        return JsonResponse(serializer.data, status=200)
    return HttpResponse(content='Invalid data', status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def predict_all_rating(request):
    """
    Predict the ratings of wine from 1949 to 2023
    :param request:
    :return:
    """
    wine_id = request.query_params.get('wine_id', None)
    rating_year = request.query_params.get('rating_year', '2023')

    if wine_id is None:
        return HttpResponse(content='Missing parameters: wine_id', status=400)
    # Get wine
    wine = Wine.objects.get_wine_by_id(wine_id)
    if wine is None:
        return HttpResponse(content='There is no wine with this id', status=400)
    rating_year = int(rating_year)
    if rating_year < 2023:
        return HttpResponse(content='rating_year must be greater than 2023', status=400)
    # Check if the request is cached
    cache_key = f'predict_all_rating_{wine_id}_{rating_year}'
    cached_response = cache.get(cache_key)
    if cached_response is not None:
        returned_data = json.loads(cached_response)
        serializer = ListRatingSerializer(returned_data)
        return JsonResponse(serializer.data, status=200)

    # Get XWine wine_id of the wine
    xwine_wine_id = wine.wine_id

    # Read forecast data
    path_forecast_df = f'{BASE_DIR}/predict_data/forecast_agg_monthly.parquet'

    # Get Vintage to predict
    wine_ratings = pd.read_parquet(f'{BASE_DIR}/db_data/wine_ratings.parquet')
    filter_wine_ratings = wine_ratings[wine_ratings['WineID'] == xwine_wine_id]
    batch_vintage = filter_wine_ratings['Vintage'].tolist()
    list_actual_rating = filter_wine_ratings['AverageRating'].tolist()

    # Initialize the data processor
    data_processor = PredictDataProcessor(
        wine=wine,
        rating_year=rating_year,
        path_forecast_df=path_forecast_df,
        batch_vintage=batch_vintage,
        path_minmax_scaler=f'{BASE_DIR}/model/minmax_scaler.save',
        path_standard_scaler=f'{BASE_DIR}/model/std_scaler.save',
    )

    # Process the data
    time_series_input, numerical_input = data_processor.process_data()

    # Initialize the model
    model = PredictModel(
        path_cnn_model=f'{BASE_DIR}/model/cnn_model.h5',
    )
    list_predict_rating = model.predict(
        time_series_input=time_series_input,
        numerical_input=numerical_input,
    )

    returned_data = {
        'wine_id': wine_id,
        'rating_year': rating_year,
        'list_ratings': [
            {
                'batch_vintage': batch_vintage[i],
                'actual_rating': list_actual_rating[i],
                'predict_rating': list_predict_rating[i]
            } for i in range(len(list_predict_rating))
        ]
    }

    # Cache the response
    cache.set(cache_key, json.dumps(returned_data), timeout=CACHE_TTL)

    # Serialize the data
    serializer = ListRatingSerializer(data=returned_data)
    if serializer.is_valid():
        return JsonResponse(serializer.data, status=200)
    return HttpResponse(content='Invalid data', status=400)
