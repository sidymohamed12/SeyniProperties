# apps/accounts/views.py - Correction de la redirection employés

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect


def logout_view(request):
    """Vue pour déconnecter l'utilisateur"""
    # Ajouter le message AVANT de détruire la session
    # Mais ne pas l'ajouter car il sera perdu de toute façon
    # À la place, on passe un paramètre URL
    logout(request)
    # Rediriger avec paramètre pour afficher message sur la page home
    return redirect('home')

def custom_login_post_view(request):
    """Vue pour traiter la connexion depuis la page d'accueil"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember')

        # Nettoyer les messages résiduels avant le login
        storage = messages.get_messages(request)
        storage.used = True

        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Gestion "Se souvenir de moi"
                    if not remember_me:
                        request.session.set_expiry(0)
                    
                    # ✅ CORRECTION: Types d'employés unifiés
                    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
                    
                    # Redirection basée sur le type d'utilisateur
                    if user.user_type == 'manager':
                        messages.success(request, f"Bienvenue {user.get_full_name()} ! Voici votre tableau de bord manager.")
                        return redirect('dashboard:manager_dashboard')
                    elif user.user_type == 'accountant':
                        messages.success(request, f"Bienvenue {user.get_full_name()} ! Voici votre tableau de bord comptable.")
                        return redirect('dashboard:accountant_dashboard')
                    elif user.user_type in employee_types:
                        messages.success(request, f"Bienvenue {user.get_full_name()} ! Voici vos tâches du jour.")
                        # ✅ CORRECTION: Utiliser l'URL qui existe vraiment
                        return redirect('employees:index')
                    elif user.user_type == 'tenant':
                        messages.success(request, f"Bienvenue {user.get_full_name()} ! Accédez à votre espace locataire.")
                        return redirect('portals:tenant_portal')
                    elif user.user_type == 'landlord':
                        messages.success(request, f"Bienvenue {user.get_full_name()} ! Accédez à votre espace bailleur.")
                        return redirect('portals:landlord_portal')
                    elif user.is_superuser or user.is_staff:
                        messages.success(request, f"Bienvenue {user.get_full_name()} ! Accès administrateur.")
                        return redirect('admin:index')
                    else:
                        messages.success(request, f"Bienvenue {user.get_full_name()} !")
                        return redirect('dashboard:index')
                else:
                    messages.error(request, "Votre compte est désactivé. Contactez l'administrateur.")
            else:
                messages.error(request, "Identifiants incorrects. Veuillez vérifier votre nom d'utilisateur et mot de passe.")
        else:
            messages.error(request, "Veuillez saisir vos identifiants.")
    
    return redirect('home')


class CustomLoginView(LoginView):
    """Vue de connexion personnalisée avec redirection basée sur le type d'utilisateur"""
    template_name = 'home.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirection basée sur le type d'utilisateur"""
        user = self.request.user
        
        if not user.is_authenticated:
            return reverse_lazy('home')
        
        # ✅ CORRECTION: Types d'employés unifiés
        employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
        
        # Redirection selon le type d'utilisateur
        if user.user_type == 'manager':
            return reverse_lazy('dashboard:manager_dashboard')
        elif user.user_type == 'accountant':
            return reverse_lazy('dashboard:accountant_dashboard')
        elif user.user_type in employee_types:
            # ✅ CORRECTION: Utiliser l'URL qui existe vraiment
            return reverse_lazy('employees:index')
        elif user.user_type == 'tenant':
            return reverse_lazy('portals:tenant_portal')
        elif user.user_type == 'landlord':
            return reverse_lazy('portals:landlord_portal')
        elif user.is_superuser or user.is_staff:
            return reverse_lazy('admin:index')
        else:
            return reverse_lazy('dashboard:index')
    
    def form_valid(self, form):
        """Traitement après connexion réussie"""
        # Nettoyer les messages résiduels AVANT le login
        storage = messages.get_messages(self.request)
        storage.used = True

        response = super().form_valid(form)

        # Message personnalisé pour tous les types d'employés
        user = self.request.user
        employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']

        if user.user_type in employee_types:
            messages.success(self.request, f"Bienvenue {user.get_full_name()} ! Voici vos tâches du jour.")
        elif user.user_type == 'manager':
            messages.success(self.request, f"Bienvenue {user.get_full_name()} ! Voici votre tableau de bord manager.")
        else:
            messages.success(self.request, f"Bienvenue {user.get_full_name()} !")

        return response
    
    def form_invalid(self, form):
        """Traitement en cas d'erreur de connexion"""
        messages.error(self.request, "Identifiants incorrects. Veuillez réessayer.")
        return super().form_invalid(form)


@login_required
def employee_dashboard_redirect(request):
    """Redirection pour les employés vers leur dashboard approprié"""
    user = request.user

    # Vérifier que l'utilisateur est bien un employé
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']

    if user.user_type not in employee_types:
        messages.error(request, "Accès non autorisé pour ce type d'utilisateur.")
        return redirect('accounts:login')

    # Rediriger vers le dashboard employé
    try:
        return redirect('employees:index')
    except:
        # Si l'URL n'existe pas, rediriger vers l'index employé
        messages.info(request, "Dashboard employé en cours de développement.")
        return redirect('dashboard:index')


@login_required
def profile_view(request):
    """Page de profil utilisateur - Gestion du compte"""
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash

    if request.method == 'POST':
        action = request.POST.get('action')

        # Changement de mot de passe
        if action == 'change_password':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Garder connecté
                messages.success(request, 'Votre mot de passe a été changé avec succès.')
                return redirect('accounts:profile')
            else:
                for error in password_form.errors.values():
                    messages.error(request, error)

        # Mise à jour des informations personnelles
        elif action == 'update_info':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()

            if first_name and last_name and email:
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.save()
                messages.success(request, 'Vos informations ont été mises à jour avec succès.')
                return redirect('accounts:profile')
            else:
                messages.error(request, 'Tous les champs sont requis.')

        # Upload photo de profil
        elif action == 'upload_photo':
            photo = request.FILES.get('profile_photo')
            if photo:
                request.user.profile_picture = photo
                request.user.save()
                messages.success(request, 'Votre photo de profil a été mise à jour.')
                return redirect('accounts:profile')

    password_form = PasswordChangeForm(request.user)

    context = {
        'password_form': password_form,
    }

    return render(request, 'accounts/profile.html', context)