from django.urls import path
from django.http import HttpResponse

app_name = 'notifications'

def temp_view(request):
    return HttpResponse("<h1>📱 Notifications</h1><p>Module en construction...</p>")

urlpatterns = [
    path('', temp_view, name='list'),
    path('templates/', temp_view, name='templates'),
]