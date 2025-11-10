from django.urls import path
from django.http import JsonResponse

app_name = 'api'

def temp_api_view(request):
    return JsonResponse({'message': 'API en construction', 'status': 'development'})

urlpatterns = [
    path('v1/', temp_api_view, name='v1'),
    path('auth/', temp_api_view, name='auth'),
]