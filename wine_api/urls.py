"""wine_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import re_path, path, include
from .views import protected_serve, swagger_schema_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/v1/wines/', include('wine.urls'), name='wine'),
    path('api/v1/wineries/', include('winery.urls'), name='winery'),
    path('api/v1/regions/', include('region.urls'), name='region'),
    path('api/v1/predict/', include('predict.urls'), name='predict'),

    re_path(r'^doc(?P<format>\.json|\.yaml)$',
            swagger_schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('doc/', swagger_schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path('redoc/', swagger_schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),
]
