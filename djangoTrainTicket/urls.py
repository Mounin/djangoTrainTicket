"""djangoTrainTicket URL Configuration

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
from django.urls import path, re_path, include
from pyTrainTicket import views
# drf_yasg2 从这里开始
from rest_framework import permissions, serializers, viewsets, routers
from drf_yasg2.views import get_schema_view
from drf_yasg2 import openapi
schema_view = get_schema_view(
      openapi.Info(
          title="MSMonitor API",
          default_version='v1.0',
          description="To monitor microservice performance metrics and request paths.",
          # 服务条款
          # terms_of_service="http://localhost:5173/",
          # email
          contact=openapi.Contact(email="honvinzhou@163.com"),
          license=openapi.License(name="BSD License"),
      ),
      public=True,
      permission_classes=(permissions.AllowAny,),
   )
# 这里结束

MSMonitor = routers.DefaultRouter()

urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', include(MSMonitor.urls)),
    path('test/', views.test),
    path("admin/", admin.site.urls),
    path('show_single_mss/', views.PromSingleViewSet.as_view({'get': 'list'})),
    path('single_monitor/', views.PromSingleViewSet.as_view({'get': 'single_monitor'})),
    path('show_continue_mss/', views.PromContinueViewSet.as_view({'get': 'show_continue_mss'})),
    path('show_graph_continue_mss/', views.PromContinueViewSet.as_view({'get': 'show_graph_continue_mss'})),
    path('get_traces_and_spans/', views.get_traces_and_spans),
    path('get_traces/', views.TraceViewSet.as_view({'get': 'get_traces'})),
    path('get_spans/', views.SpanViewSet.as_view({'get': 'get_spans'})),
    path('draw_path/', views.JaegerMonitorViewSet.as_view({'get': 'draw_path'})),
    path('get_monitor/', views.JaegerMonitorViewSet.as_view({'get': 'get_monitor'})),
    path('get_resource/', views.JaegerMonitorViewSet.as_view({'get': 'get_resource'})),
    path('get_hot_ms/', views.JaegerHotMSViewSet.as_view({'get': 'get_hot_ms'})),
    path('login/', views.UserViewSet.as_view({'post': 'check_login'})),
]
