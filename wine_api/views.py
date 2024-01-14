import os

from django.conf import settings
from django.http import HttpResponse
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from wine_api.paginators import CustomPagination
from django.http import JsonResponse, HttpResponseNotFound
from django.views.static import serve

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

swagger_schema_view = get_schema_view(
    openapi.Info(
        title="Wine API",
        default_version='v1'
    ),
    public=True,
    permission_classes=(permissions.AllowAny,)
)


class CreateView(mixins.CreateModelMixin, GenericViewSet):
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ListView(mixins.ListModelMixin, GenericViewSet):
    pagination_class = CustomPagination

    def get_queryset(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RetrieveView(mixins.RetrieveModelMixin, GenericViewSet):
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class DestroyView(mixins.DestroyModelMixin, GenericViewSet):
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UpdateView(mixins.UpdateModelMixin, GenericViewSet):
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


def protected_serve(request, path, document_root=None, show_indexes=False):
    if path.startswith('public/') or request.user.is_authenticated:
        if os.getenv('ENV') not in ['prod', 'prep', 'staging']:
            return serve(request, path, document_root, show_indexes)
        else:
            response = HttpResponse(status=200)
            response['Content-Type'] = ''
            response['X-Accel-Redirect'] = (settings.WEB_SERVER_MEDIA_URL + path).encode('utf-8')
            return response
    return HttpResponseNotFound()
