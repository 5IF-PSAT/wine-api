from wine_api.views import (
    ListView,
    SecondListView,
    RetrieveView,
    CreateView,
    UpdateView,
    DestroyView
)
from region.models import Region
from region.serializers import (
    RegionSerializer,
    FilterRegionSerializer,
    SecondRegionSerializer
)
from rest_framework import status
from django.db import transaction
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAdminUser, AllowAny
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from wine_api.settings import CACHE_TTL
import json


class RegionList(SecondListView, CreateView):
    """
    List all regions, or create a new region.
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        page = self.request.query_params.get('page', '1')
        page_size = self.request.query_params.get('page_size', '10')
        cache_key = f'region_list_{page}_{page_size}'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            returned_data = json.loads(cached_data)
            serializer = SecondRegionSerializer(returned_data, many=True)
            return serializer.data
        input_data = {
            "page": int(page),
            "page_size": int(page_size)
        }
        self.queryset = Region.objects.get_regions(**input_data)
        self.serializer_class = SecondRegionSerializer
        returned_data = Region.objects.get_regions(**input_data)
        serializer = SecondRegionSerializer(returned_data, many=True)
        cache.set(cache_key, json.dumps(serializer.data), timeout=CACHE_TTL)
        return serializer.data

    def post(self, request, *args, **kwargs):
        self.queryset = Region.objects.all()
        self.serializer_class = RegionSerializer
        data = JSONParser().parse(request)
        serializer = RegionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class RegionDetail(RetrieveView, UpdateView, DestroyView):
    """
    Retrieve, update or delete a region instance.
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        if cache.get(f'region_detail_{kwargs["pk"]}'):
            returned_data = json.loads(cache.get(f'region_detail_{kwargs["pk"]}'))
            serializer = RegionSerializer(returned_data)
            return serializer.data
        serializer = RegionSerializer(request.region)
        cache.set(f'region_detail_{kwargs["pk"]}', json.dumps(serializer.data), timeout=CACHE_TTL)
        return serializer.data

    def put(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        serializer = RegionSerializer(request.region, data=data)
        if serializer.is_valid():
            serializer.save()
            cache.set(f'region_detail_{kwargs["pk"]}', json.dumps(serializer.data), timeout=CACHE_TTL)
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        Region.objects.delete_region(request.region)
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class RegionFilter(ListView):
    """
    Filter regions by name and country
    """
    serializer_class = FilterRegionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        region_name = self.request.query_params.get('region_name', None)
        country = self.request.query_params.get('country', None)
        radius = self.request.query_params.get('radius', None)
        latitude = self.request.query_params.get('latitude', None)
        longitude = self.request.query_params.get('longitude', None)
        data = {
            "region_name": region_name,
            "country": country,
            "radius": radius,
            "latitude": latitude,
            "longitude": longitude
        }
        # Get list of regions matching the given filters
        list_regions = Region.objects.filter_regions(**data)
        return list_regions