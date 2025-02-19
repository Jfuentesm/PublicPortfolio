# core/urls.py
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

def home(request):
    return HttpResponse("Welcome to the IRO Platform!")

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
]