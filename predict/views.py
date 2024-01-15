from django.http import HttpResponse, JsonResponse, FileResponse
from rest_framework.decorators import api_view
from django.core.cache import cache
from wine_api.settings import CACHE_TTL
from predict.serializers import PredictSerializer
from nixtlats import TimeGPT
import pandas as pd
from region.models import Region
import json


@api_view(['GET'])
def forecast_weather(request):
    region_id = request.query_params.get('region_id', None)
    predict_field = request.query_params.get('predict_field', None)
    nb_months = request.query_params.get('nb_months', None)
    frequency = request.query_params.get('freq', None)
    api_key = request.query_params.get('api_key', None)
    if region_id is None or predict_field is None or \
            nb_months is None or frequency is None or api_key is None:
        return HttpResponse(content='Missing parameters: region_id, predict_field, nb_months, freq, api_key', status=400)
    # Check if the request is cached
    cache_key = f'forecast_weather_{region_id}_{predict_field}_{nb_months}_{frequency}'
    cached_response = cache.get(cache_key)
    if cached_response is not None:
        returned_data = json.loads(cached_response)
        return returned_data

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
    weather_data = pd.read_parquet(f'./model_data/agg_monthly.parquet')
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