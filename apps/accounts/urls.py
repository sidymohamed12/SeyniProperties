# apps/accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Connexion personnalisée
    path('login/', views.custom_login_post_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profil utilisateur
    path('profile/', views.profile_view, name='profile'),

    # Réinitialisation de mot de passe
    path('password/reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset_form.html',
             email_template_name='accounts/password_reset_email.html',
             success_url='/accounts/password/reset/done/'
         ), 
         name='password_reset'),
    
    path('password/reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password/reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password/reset/complete/'
         ), 
         name='password_reset_confirm'),
    
    path('password/reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Changement de mot de passe
    path('password/change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='accounts/password_change_form.html',
             success_url='/accounts/password/change/done/'
         ), 
         name='password_change'),
    
    path('password/change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html'
         ), 
         name='password_change_done'),
]