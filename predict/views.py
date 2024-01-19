from django.http import HttpResponse, JsonResponse, FileResponse
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
import joblib
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
    # Config
    h = 12
    # predict_field = ['avg_temperature', 'avg_sunshine_duration',
    #                  'avg_precipitation', 'avg_humidity',
    #                  'avg_soil_temperature', 'avg_soil_moisture']

    # Get wine
    wine = Wine.objects.get_wine_by_id(wine_id)
    list_elaborate = [wine.elaborate] * h
    list_acidity = [wine.acidity] * h
    list_ABV = [wine.abv] * h
    list_body = [wine.body] * h

    # Get XWine region_id of the wine
    region = wine.region
    xwine_region_id = region.region_id

    # Read forecast data
    forecast_df = pd.read_parquet(f'{BASE_DIR}/predict_data/forecast_agg_monthly.parquet')
    # Add timestamp column
    forecast_df['timestamp'] = pd.to_datetime(forecast_df[['year', 'month']].assign(DAY=1))
    # Filter data by region_id and year
    forecast_df = forecast_df[(forecast_df['RegionID'] == xwine_region_id) & (forecast_df['year'] == batch_vintage)]

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
    minmax_df['avg_temperature'] = forecast_df['avg_temperature'].tolist()
    minmax_df['avg_sunshine_duration'] = forecast_df['avg_sunshine_duration'].tolist()
    minmax_df['avg_precipitation'] = forecast_df['avg_precipitation'].tolist()
    minmax_df['avg_rain'] = [0] * h
    minmax_df['avg_snowfall'] = [0] * h
    minmax_df['avg_humidity'] = forecast_df['avg_humidity'].tolist()
    minmax_df['avg_wind_speed'] = [0] * h
    minmax_df['avg_soil_temperature'] = forecast_df['avg_soil_temperature'].tolist()
    minmax_df['avg_soil_moisture'] = forecast_df['avg_soil_moisture'].tolist()

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

    list_delta_time_rating = [rating_year - batch_vintage] * h

    # load minmax_scaler
    with open(f'{BASE_DIR}/model/minmax_scaler.save', 'rb') as f:
        minmax_scaler = joblib.load(f)

    # load standard_scaler
    with open(f'{BASE_DIR}/model/std_scaler.save', 'rb') as f:
        standard_scaler = joblib.load(f)

    scaled_minmax_df = minmax_scaler.transform(minmax_df)
    scaled_list_delta_time_rating = standard_scaler.transform(np.array(list_delta_time_rating).reshape(-1, 1))

    time_series_array = np.array([scaled_minmax_df[:, 4][0:12],
                                  scaled_minmax_df[:, 5][0:12],
                                  scaled_minmax_df[:, 6][0:12],
                                  scaled_minmax_df[:, 9][0:12],
                                  scaled_minmax_df[:, 11][0:12],
                                  scaled_minmax_df[:, 12][0:12]])
    numerical_array = np.array([scaled_minmax_df[:, 1][0], scaled_minmax_df[:, 2][0],
                                scaled_minmax_df[:, 3][0],
                                scaled_list_delta_time_rating[0][0]])
    list_all = [(time_series_array, numerical_array)]

    # Input data for CNN model
    time_series_input = np.array([element[0] for element in list_all])
    time_series_input = time_series_input.reshape(time_series_input.shape[0], time_series_input.shape[1],
                                                  time_series_input.shape[2], 1)
    numerical_input = np.array([element[1] for element in list_all])
    cnn_model = load_model(f'{BASE_DIR}/model/cnn_model.h5')

    # Make prediction
    predictions = cnn_model.predict([time_series_input, numerical_input])

    # Return the prediction
    returned_data = {
        'wine_id': wine_id,
        'batch_vintage': batch_vintage,
        'rating_year': rating_year,
        'predict_rating': float(predictions[0][0])
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
    # Config
    # predict_field = ['avg_temperature', 'avg_sunshine_duration',
    #                  'avg_precipitation', 'avg_humidity',
    #                  'avg_soil_temperature', 'avg_soil_moisture']

    # Get wine
    wine = Wine.objects.get_wine_by_id(wine_id)
    # Get XWine region_id of the wine
    region = wine.region
    xwine_region_id = region.region_id

    # Read forecast data
    forecast_df = pd.read_parquet(f'{BASE_DIR}/predict_data/forecast_agg_monthly.parquet')
    # Add timestamp column
    forecast_df['timestamp'] = pd.to_datetime(forecast_df[['year', 'month']].assign(DAY=1))
    # Filter data by region_id
    forecast_df = forecast_df[forecast_df['RegionID'] == xwine_region_id]

    # Get and normalize data
    length = len(forecast_df)
    column_minmax = ['Elaborate', 'ABV', 'Body', 'Acidity',
                     'avg_temperature', 'avg_sunshine_duration',
                     'avg_precipitation', 'avg_rain', 'avg_snowfall',
                     'avg_humidity', 'avg_wind_speed', 'avg_soil_temperature',
                     'avg_soil_moisture']
    minmax_df = pd.DataFrame(columns=column_minmax)
    minmax_df['ABV'] = [wine.abv] * length
    minmax_df['Body'] = [wine.body] * length
    minmax_df['Acidity'] = [wine.acidity] * length
    minmax_df['Elaborate'] = [wine.elaborate] * length
    minmax_df['avg_temperature'] = forecast_df['avg_temperature'].tolist()
    minmax_df['avg_sunshine_duration'] = forecast_df['avg_sunshine_duration'].tolist()
    minmax_df['avg_precipitation'] = forecast_df['avg_precipitation'].tolist()
    minmax_df['avg_rain'] = [0] * length
    minmax_df['avg_snowfall'] = [0] * length
    minmax_df['avg_humidity'] = forecast_df['avg_humidity'].tolist()
    minmax_df['avg_wind_speed'] = [0] * length
    minmax_df['avg_soil_temperature'] = forecast_df['avg_soil_temperature'].tolist()
    minmax_df['avg_soil_moisture'] = forecast_df['avg_soil_moisture'].tolist()

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
    list_rating_year = [rating_year] * length
    list_delta_time_rating = np.array(list_rating_year) - np.array(forecast_df['year'].tolist())
    # Convert list_delta_time_rating to list
    list_delta_time_rating = list(list_delta_time_rating)

    # load minmax_scaler
    with open(f'{BASE_DIR}/model/minmax_scaler.save', 'rb') as f:
        minmax_scaler = joblib.load(f)

    # load standard_scaler
    with open(f'{BASE_DIR}/model/std_scaler.save', 'rb') as f:
        standard_scaler = joblib.load(f)

    scaled_minmax_df = minmax_scaler.transform(minmax_df)
    scaled_list_delta_time_rating = standard_scaler.transform(np.array(list_delta_time_rating).reshape(-1, 1))

    list_all = []
    for i in range(0, length, 12):
        time_series_array = np.array([scaled_minmax_df[:, 4][i:i + 12],
                                      scaled_minmax_df[:, 5][i:i + 12],
                                      scaled_minmax_df[:, 6][i:i + 12],
                                      scaled_minmax_df[:, 9][i:i + 12],
                                      scaled_minmax_df[:, 11][i:i + 12],
                                      scaled_minmax_df[:, 12][i:i + 12]])
        numerical_array = np.array([scaled_minmax_df[:, 1][i], scaled_minmax_df[:, 2][i],
                                    scaled_minmax_df[:, 3][i],
                                    scaled_list_delta_time_rating[i][0]])
        list_all.append((time_series_array, numerical_array))

    # Input data for CNN model
    time_series_input = np.array([element[0] for element in list_all])
    time_series_input = time_series_input.reshape(time_series_input.shape[0], time_series_input.shape[1],
                                                  time_series_input.shape[2], 1)
    numerical_input = np.array([element[1] for element in list_all])

    cnn_model = load_model(f'{BASE_DIR}/model/cnn_model.h5')

    # Make prediction
    predictions = cnn_model.predict([time_series_input, numerical_input])

    # Return the prediction
    list_predict_rating = predictions.tolist()
    list_predict_rating = [item for sublist in list_predict_rating for item in sublist]
    list_predict_rating = [float(item) for item in list_predict_rating]
    returned_data = {
        'wine_id': wine_id,
        'rating_year': rating_year,
        'predict_rating': [
            {
                'batch_vintage': forecast_df['year'].tolist()[i*12],
                'rating': list_predict_rating[i]
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
