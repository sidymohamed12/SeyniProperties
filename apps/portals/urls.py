# apps/portals/urls.py
from django.urls import path
from django.http import HttpResponse

app_name = 'portals'

def temp_view(request):
    return HttpResponse("<h1>🌐 Portails Utilisateurs</h1><p>Module en construction...</p>")

urlpatterns = [
    path('tenant/', temp_view, name='tenant_portal'),  # Changé de 'tenant' à 'tenant_portal'
    path('landlord/', temp_view, name='landlord_portal'),  # Changé de 'landlord' à 'landlord_portal'
    path('employee/', temp_view, name='employee'),
]