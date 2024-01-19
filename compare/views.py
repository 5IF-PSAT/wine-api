from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from django.core.cache import cache
from wine_api.settings import CACHE_TTL
from compare.serializers import WineCompareSerializer
import pandas as pd
from wine.models import Wine
import json
from rest_framework.permissions import AllowAny
from wine_api.settings import BASE_DIR
import joblib


@api_view(["GET"])
@permission_classes([AllowAny])
def compare_wine(request):
    """
    Get the list of wines similar to the wine_id passed in the request
    :param request:
    :return:
    """
    wine_id = request.query_params.get("wine_id", None)
    vintage = request.query_params.get("vintage", None)
    nb_wines = request.query_params.get("nb_wines", '10')
    if wine_id is None or vintage is None:
        return HttpResponse("wine_id and vintage are required parameters", status=400)
    wine_id = int(wine_id)
    vintage = int(vintage)
    nb_wines = int(nb_wines)
    if nb_wines <= 0:
        return HttpResponse("nb_wines must be a positive integer", status=400)
    # Check if the data is in the cache
    cache_key = f'compare_wine_{wine_id}_{vintage}_{nb_wines}'
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        returned_data = json.loads(cached_data)
        serializer = WineCompareSerializer(returned_data)
        return JsonResponse(serializer.data, status=200)
    # Get the wine
    pertinent_wine_ratings = pd.read_parquet(f'{BASE_DIR}/compare_data/pertinent_wine_ratings.parquet')
    pertinent_ratings_non_null = pd.read_parquet(f'{BASE_DIR}/compare_data/pertinent_ratings_non_null.parquet')
    aggregated_doc_vector = pd.read_csv(f'{BASE_DIR}/compare_data/aggregated_doc_vector.csv')
    normalized_wine_data = pd.read_parquet(f'{BASE_DIR}/compare_data/normalized_wine_data.parquet')

    wine = Wine.objects.get_wine_by_id(wine_id)
    xwine_wine_id = wine.wine_id

    checked_exist_df = pertinent_wine_ratings[(pertinent_wine_ratings['WineID'] == xwine_wine_id) &
                                              (pertinent_wine_ratings['Vintage'] == vintage)]
    if checked_exist_df.empty:
        return HttpResponse("wine_id and vintage must be valid", status=400)

    reference_wine_composition_and_weather = normalized_wine_data[(normalized_wine_data['WineID'] == xwine_wine_id) &
                                                                  (normalized_wine_data['Vintage'] == vintage)]
    checked_review_df = pertinent_ratings_non_null[(pertinent_ratings_non_null['WineID'] == xwine_wine_id) &
                                                   (pertinent_ratings_non_null['Vintage'] == vintage)]
    wine_text_review_vec = aggregated_doc_vector.copy()
    have_text_review = False
    if not checked_review_df.empty:
        have_text_review = True
        reference_wine_text_review = wine_text_review_vec[(wine_text_review_vec['WineID'] == xwine_wine_id) &
                                                          (wine_text_review_vec['Vintage'] == vintage)]

    input_wine_composition_and_weather = reference_wine_composition_and_weather.drop(['WineID', 'Vintage', 'WineName'],
                                                                                     axis=1).to_numpy().reshape(1, -1)

    if have_text_review:
        input_wine_text_review = reference_wine_text_review.drop(['WineID', 'Vintage'], axis=1).to_numpy().reshape(1, -1)

    # Load the KD Tree
    wine_composition_weather_tree = joblib.load(f'{BASE_DIR}/model/wine_composition_weather_tree.joblib')
    wine_text_review_tree = joblib.load(f'{BASE_DIR}/model/wine_text_review_tree.joblib')

    # Query the KD Tree, get the distances and indices of the nearest neighbors
    dist_composition_weather, ind_composition_weather = wine_composition_weather_tree.query(
        input_wine_composition_and_weather, k=len(normalized_wine_data)
    )

    if have_text_review:
        dist_text_review, ind_text_review = wine_text_review_tree.query(
            input_wine_text_review, k=len(wine_text_review_vec)
        )

    # create a dictionary with ind as key and dist as value
    dict_composition_weather_wine = dict(zip(ind_composition_weather[0], dist_composition_weather[0]))

    if have_text_review:
        dict_text_review_wine = dict(zip(ind_text_review[0], dist_text_review[0]))

    normalized_wine_name_data = normalized_wine_data[['WineID', 'Vintage', 'WineName']]
    normalized_wine_name_data['distance_no_text'] = normalized_wine_data.index.map(dict_composition_weather_wine)

    wine_name_data = wine_text_review_vec[['WineID', 'Vintage']]
    if have_text_review:
        wine_name_data['distance_text'] = wine_text_review_vec.index.map(dict_text_review_wine)

    # Merge the datasets based on 'Name' and 'Age'
    merged_wine_data = pd.merge(normalized_wine_name_data, wine_name_data, on=['WineID', 'Vintage'], how='left')

    if have_text_review:
        # Fill null values with 0 before adding 'ScoreDay1' and 'ScoreDay2'
        merged_wine_data['distance'] = merged_wine_data['distance_no_text'].fillna(0) + merged_wine_data['distance_text'].fillna(0)

        # Drop the redundant 'ScoreDay1' and 'ScoreDay2' columns if needed
        merged_wine_data = merged_wine_data.drop(['distance_no_text', 'distance_text'], axis=1)

    if have_text_review:
        distance_column = 'distance'
    else:
        distance_column = 'distance_no_text'

    sorted_df = merged_wine_data.sort_values(by=[distance_column])

    top_wines_plus_one = sorted_df.head(nb_wines + 1)
    # Remove the wine itself from the list
    if xwine_wine_id in top_wines_plus_one['WineID'].values and vintage in top_wines_plus_one['Vintage'].values:
        top_wines = top_wines_plus_one[(top_wines_plus_one['WineID'] != xwine_wine_id) |
                                       (top_wines_plus_one['Vintage'] != vintage)]
    else:
        top_wines = top_wines_plus_one.head(nb_wines)

    # Get the list of wines
    wines = []
    for index, row in top_wines.iterrows():
        wine = Wine.objects.get_wine_by_wine_id(row['WineID'])
        returned_wine = {
            "id": wine.id,
            "wine_id": row['WineID'],
            "vintage": row['Vintage'],
            "distance": row[distance_column],
            "wine_name": wine.wine_name,
            "type": wine.type,
            "elaborate": wine.elaborate,
            "abv": wine.abv,
            "body": wine.body,
            "acidity": wine.acidity,
            "winery": wine.winery.winery_name,
            "region": wine.region.region_name
        }
        wines.append(returned_wine)

    # Serialize the list of wines
    returned_data = {
        "ref_wine_id": wine_id,
        "ref_vintage": vintage,
        "nb_wines": nb_wines,
        "list_wines": wines
    }
    # Cache the data
    cache.set(cache_key, json.dumps(returned_data), timeout=CACHE_TTL)

    serializer = WineCompareSerializer(data=returned_data)
    if serializer.is_valid():
        return JsonResponse(serializer.data, status=200)
    return HttpResponse(content='Invalid data', status=400)