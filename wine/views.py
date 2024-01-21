from wine_api.views import (
    ListView,
    SecondListView,
    RetrieveView,
    CreateView,
    UpdateView,
    DestroyView
)
from wine.models import Wine
from wine.serializers import WineSerializer, FilterWineSerializer, SecondWineSerializer
from rest_framework import status
from django.db import transaction
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAdminUser, AllowAny
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from wine_api.settings import CACHE_TTL
import json


class WineList(CreateView):
    """
    Create a new wine.
    """
    queryset = Wine.objects.all()
    serializer_class = WineSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        serializer = WineSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class SecondWineList(SecondListView):
    """
    List all wines.
    """
    serializer_class = SecondWineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        page = self.request.query_params.get('page', '1')
        page_size = self.request.query_params.get('page_size', '10')
        page = int(page)
        page_size = int(page_size)
        if page < 1:
            return HttpResponse(content="Page must be greater than 0", status=status.HTTP_400_BAD_REQUEST)
        if page_size < 1:
            return HttpResponse(content="Page size must be greater than 0", status=status.HTTP_400_BAD_REQUEST)
        cache_key = f'wine_list_{page}_{page_size}'
        # Get data from cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            # If data is in cache, return it
            returned_data = json.loads(cached_data)
            serializer = SecondWineSerializer(returned_data, many=True)
            return serializer.data
        input_data = {
            "page": page,
            "page_size": page_size
        }
        returned_data = Wine.objects.get_wines(**input_data)
        serializer = SecondWineSerializer(returned_data, many=True)
        # If data is not in cache, cache it
        cache.set(cache_key, json.dumps(serializer.data), timeout=CACHE_TTL)
        return serializer.data


class WineDetail(RetrieveView, UpdateView, DestroyView):
    """
    Retrieve, update or delete a wine instance.
    """
    queryset = Wine.objects.all()
    serializer_class = WineSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        cached_data = cache.get(f'wine_detail_{kwargs["pk"]}')
        if cached_data is not None:
            returned_data = json.loads(cached_data)
            serializer = WineSerializer(data=returned_data)
            return serializer.data
        serializer = WineSerializer(request.wine)
        cache.set(f'wine_detail_{kwargs["pk"]}', json.dumps(serializer.data), timeout=CACHE_TTL)
        return serializer.data

    def put(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        serializer = WineSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        Wine.objects.delete_wine(request.wine)
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class WineFilter(ListView):
    """
    Filter wines
    """
    serializer_class = FilterWineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        wine_name = self.request.query_params.get('wine_name', None)
        type = self.request.query_params.get('type', None)
        elaborate = self.request.query_params.get('elaborate', None)
        abv = self.request.query_params.get('abv', None)
        body = self.request.query_params.get('body', None)
        acidity = self.request.query_params.get('acidity', None)
        winery_id = self.request.query_params.get('winery_id', None)
        region_id = self.request.query_params.get('region_id', None)
        data = {
            "wine_name": wine_name,
            "type": type,
            "elaborate": elaborate,
            "abv": abv,
            "body": body,
            "acidity": acidity,
            "winery_id": winery_id,
            "region_id": region_id,
        }
        # Get list of wines matching the given filters
        list_wines = Wine.objects.filter_wines(**data)
        # Serialize list of wines
        return list_wines
