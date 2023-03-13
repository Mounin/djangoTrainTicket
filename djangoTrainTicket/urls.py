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
from django.urls import path

from pyTrainTicket import views

urlpatterns = [
    path('test/', views.test),
    path("admin/", admin.site.urls),
    path('show_single_mss/', views.show_single_mss),
    path('single_monitor/', views.single_monitor),
    path('show_continue_mss/', views.show_continue_mss),
    path('show_graph_continue_mss/', views.show_graph_continue_mss),
    path('get_traces_and_spans/', views.get_traces_and_spans),
    path('get_traces/', views.get_traces),
    path('get_spans/', views.get_spans),
    path('draw_path/', views.draw_path),
    path('get_monitor/', views.get_monitor),
    path('get_resource/', views.get_resource),
    path('get_hot_ms/', views.get_hot_ms),
]
