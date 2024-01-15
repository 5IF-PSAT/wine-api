from django.http import HttpResponse, JsonResponse, FileResponse
from rest_framework.decorators import api_view, permission_classes
from django.core.cache import cache
from wine_api.settings import CACHE_TTL
from predict.serializers import (
    PredictSerializer,
    RatingSerializer
)
from nixtlats import TimeGPT
import pandas as pd
from region.models import Region
from wine.models import Wine
import json
from rest_framework.permissions import AllowAny
from wine_api.settings import BASE_DIR
import time
import pickle
import numpy as np
from tensorflow.keras.models import load_model


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
    weather_data = pd.read_parquet(f'{BASE_DIR}/model_data/agg_monthly.parquet')
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
    wine_id = request.query_params.get('wine_id', None)
    rating_year = request.query_params.get('rating_year', None)
    api_key = request.query_params.get('api_key', None)

    if wine_id is None or rating_year is None or api_key is None:
        return HttpResponse(content='Missing parameters: wine_id, rating_year, api_key', status=400)
    # Check if the request is cached
    cache_key = f'predict_rating_{wine_id}_{rating_year}'
    cached_response = cache.get(cache_key)
    if cached_response is not None:
        returned_data = json.loads(cached_response)
        serializer = RatingSerializer(returned_data)
        return JsonResponse(serializer.data, status=200)
    # Config
    h = 12
    frequency = 'MS'
    predict_field = ['avg_temperature', 'avg_precipitation',
                     'avg_humidity', 'avg_soil_temperature',
                     'avg_soil_moisture']
    batch_vintage = 2023

    # Get wine
    wine = Wine.objects.get_wine_by_id(wine_id)
    list_elaborate = [wine.elaborate] * h
    list_acidity = [wine.acidity] * h
    list_ABV = [wine.abv] * h
    list_body = [wine.body] * h

    # Get XWine region_id of the wine
    region = wine.region
    xwine_region_id = region.region_id

    # Initialize the model
    model = TimeGPT(
        token=api_key,
    )
    # Check if api_key is valid
    if not model.validate_token():
        return HttpResponse(content='Invalid api_key', status=400)

    # Get the weather data
    weather_data = pd.read_parquet(f'{BASE_DIR}/model_data/agg_monthly.parquet')
    weather_data = weather_data[weather_data['RegionID'] == xwine_region_id]

    # Add timestamp column
    weather_data['timestamp'] = pd.to_datetime(weather_data[['year', 'month']].assign(DAY=1))

    # Forecast weather
    forecast_df = []
    for field in predict_field:
        df = model.forecast(
            df=weather_data,
            h=h,
            time_col='timestamp',
            target_col=field,
            freq=frequency,
        )
        forecast_df.append(df)
        time.sleep(0.5)  # To avoid the 429 error: too many requests

    # Get and normalize data
    column_minmax = ['Elaborate', 'ABV', 'Body', 'Acidity',
                     'avg_temperature', 'avg_sunshine_duration',
                     'avg_precipitation', 'avg_rain', 'avg_snowfall',
                     'avg_humidity', 'avg_wind_speed', 'avg_soil_temperature',
                     'avg_soil_moisture']
    minmax_df = pd.DataFrame(columns=column_minmax)

    minmax_df['ABV'] = list_ABV
    minmax_df['Body'] = list_body
    minmax_df['Acidity'] = list_acidity
    minmax_df['Elaborate'] = list_elaborate
    minmax_df['avg_temperature'] = forecast_df[0]['TimeGPT'].tolist()
    minmax_df['avg_sunshine_duration'] = [0] * h
    minmax_df['avg_precipitation'] = forecast_df[1]['TimeGPT'].tolist()
    minmax_df['avg_rain'] = [0] * h
    minmax_df['avg_snowfall'] = [0] * h
    minmax_df['avg_humidity'] = forecast_df[2]['TimeGPT'].tolist()
    minmax_df['avg_wind_speed'] = [0] * h
    minmax_df['avg_soil_temperature'] = forecast_df[3]['TimeGPT'].tolist()
    minmax_df['avg_soil_moisture'] = forecast_df[4]['TimeGPT'].tolist()

    acid_dict = {'Low': 1, 'Medium': 2, 'High': 3}
    body_dict = {'Light-bodied': 1, 'Medium-bodied': 2, 'Full-bodied': 3, 'Very full-bodied': 4}
    elaborate_dict = {'Varietal/100%': 1, 'Varietal/>75%': 2, 'Assemblage/Blend': 3,
                     'Assemblage/Meritage Red Blend': 4, 'Assemblage/Rhône Red Blend': 5,
                     'Assemblage/Bordeaux Red Blend': 6,
                     'Assemblage/Portuguese White Blend': 7, 'Assemblage/Portuguese Red Blend': 8,
                     'Assemblage/Port Blend': 9,
                     'Assemblage/Provence Rosé Blend': 10, 'Assemblage/Champagne Blend': 11,
                     'Assemblage/Valpolicella Red Blend': 12,
                     'Assemblage/Tuscan Red Blend': 13, 'Assemblage/Rioja Red Blend': 14, 'Assemblage/Cava Blend': 15
                     }

    minmax_df['Acidity'] = minmax_df['Acidity'].map(acid_dict)
    minmax_df['Body'] = minmax_df['Body'].map(body_dict)
    minmax_df['Elaborate'] = minmax_df['Elaborate'].map(elaborate_dict)

    list_delta_time_rating = [int(rating_year) - batch_vintage] * h

    # load minmax_scaler
    with open(f'{BASE_DIR}/model/minmax_scaler.pickle', 'rb') as f:
        minmax_scaler = pickle.load(f)

    # load standard_scaler
    with open(f'{BASE_DIR}/model/std_scaler.pickle', 'rb') as f:
        standard_scaler = pickle.load(f)

    scaled_minmax_df = minmax_scaler.transform(minmax_df)
    scaled_list_delta_time_rating = standard_scaler.transform(np.array(list_delta_time_rating).reshape(-1, 1))

    list_all = []
    for i in range(0, h, 12):
        time_series_array = np.array([np.array(scaled_minmax_df[:, 4]), np.array(scaled_minmax_df[:, 6]),
                                      np.array(scaled_minmax_df[:, 9]),
                                      np.array(scaled_minmax_df[:, 11]),
                                      np.array(scaled_minmax_df[:, 12])])
        numerical_array = np.array([scaled_minmax_df[:, 1][i], scaled_minmax_df[:, 2][i],
                                    scaled_minmax_df[:, 3][i],
                                    scaled_list_delta_time_rating[i][0]])
        list_all.append((time_series_array, numerical_array))

    # Input data for CNN model
    time_series_input = np.array([element[0] for element in list_all])
    time_series_input = time_series_input.reshape(time_series_input.shape[0], time_series_input.shape[1],
                                                  time_series_input.shape[2], 1)
    numerical_input = np.array([element[1] for element in list_all])
    cnn_model = load_model(f'{BASE_DIR}/model/cnn_model.keras')

    # Make prediction
    predictions = cnn_model.predict([time_series_input, numerical_input])

    # Return the prediction
    returned_data = {
        'rating_year': int(rating_year),
        'predict_rating': float(predictions[0][0])
    }

    # Cache the response
    cache.set(cache_key, json.dumps(returned_data), timeout=CACHE_TTL)

    # Serialize the data
    serializer = RatingSerializer(data=returned_data)
    if serializer.is_valid():
        return JsonResponse(serializer.data, status=200)
    return HttpResponse(content='Invalid data', status=400)
