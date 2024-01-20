from wine_api.views import (
    ListView,
    RetrieveView,
    CreateView,
    UpdateView,
    DestroyView
)
from winery.models import Winery
from winery.serializers import WinerySerializer, FilterWinerySerializer
from rest_framework import status
from django.db import transaction
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAdminUser, AllowAny
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from wine_api.settings import CACHE_TTL
import json


class WineryList(ListView, CreateView):
    """
    List all wineries, or create a new winery.
    """
    queryset = Winery.objects.all()
    serializer_class = WinerySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        cached_data = cache.get('winery_list')
        if cached_data is not None:
            returned_data = json.loads(cached_data)
            serializer = WinerySerializer(returned_data, many=True)
            return serializer.data
        serializer = WinerySerializer(Winery.objects.all(), many=True)
        cache.set('winery_list', json.dumps(serializer.data), timeout=CACHE_TTL)
        return serializer.data

    def post(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        serializer = WinerySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class WineryDetail(RetrieveView, UpdateView, DestroyView):
    """
    Retrieve, update or delete a winery instance.
    """
    queryset = Winery.objects.all()
    serializer_class = WinerySerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        if cache.get(f'winery_detail_{kwargs["pk"]}'):
            returned_data = json.loads(cache.get(f'winery_detail_{kwargs["pk"]}'))
            serializer = WinerySerializer(data=returned_data)
            return serializer.data
        serializer = WinerySerializer(request.winery)
        cache.set(f'winery_detail_{kwargs["pk"]}', json.dumps(serializer.data), timeout=CACHE_TTL)
        return serializer.data

    def put(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        serializer = WinerySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        request.winery.delete()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class WineryFilter(ListView):
    """
    Filter wineries by parameters.
    """
    serializer_class = FilterWinerySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        winery_name = self.request.query_params.get('winery_name', None)
        website = self.request.query_params.get('website', None)
        data = {
            "winery_name": winery_name,
            "website": website
        }
        list_wineries = Winery.objects.filter_wineries(**data)
        return list_wineries