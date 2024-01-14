from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound


class CustomPagination(PageNumberPagination):
    def paginate_queryset(self, queryset, request, view=None):
        page_size = request.query_params.get('page_size', 10)
        if page_size == 'all':
            page_size = queryset.count()
        self.page_size = page_size
        page_num = request.query_params.get('page', 1)
        self.page_number = page_num
        try:
            return super().paginate_queryset(queryset, request, view=view)
        except NotFound:
            return []

    def get_paginated_response(self, data):
        return Response(data)
