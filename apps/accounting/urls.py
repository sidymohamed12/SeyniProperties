from django.urls import path
from django.http import HttpResponse

app_name = 'accounting'

def temp_view(request):
    return HttpResponse("<h1>📊 Comptabilité</h1><p>Module en construction...</p>")

urlpatterns = [
    path('', temp_view, name='dashboard'),
    path('expenses/', temp_view, name='expenses'),
]