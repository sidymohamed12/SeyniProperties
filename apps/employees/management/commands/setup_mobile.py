# apps/employees/management/commands/setup_mobile.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import apps.employees.models.employee as Employee
from apps.employees.models.task import Task
from apps.maintenance.models import Intervention
import random
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Configure l\'environnement mobile avec des données de test'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-demo-data',
            action='store_true',
            help='Crée des données de démonstration',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Configuration de l\'environnement mobile...')
        
        # Créer un technicien de test
        technicien, created = User.objects.get_or_create(
            username='tech_mobile',
            defaults={
                'first_name': 'Jean',
                'last_name': 'Dupont',
                'email': 'jean.dupont@seyniproperties.com',
                'user_type': 'technicien',
                'phone': '+221771234567',
                'is_active': True
            }
        )
        
        if created:
            technicien.set_password('mobile123')
            technicien.save()
            self.stdout.write(f'Technicien créé: {technicien.username}')
        
        # Créer le profil employé
        employee, created = Employee.objects.get_or_create(
            user=technicien,
            defaults={
                'specialite': 'polyvalent',
                'date_embauche': timezone.now().date(),
                'statut': 'actif',
                'is_available': True,
                'telephone_professionnel': '+221771234567'
            }
        )
        
        # Créer un agent de terrain
        agent, created = User.objects.get_or_create(
            username='agent_mobile',
            defaults={
                'first_name': 'Marie',
                'last_name': 'Fall',
                'email': 'marie.fall@seyniproperties.com',
                'user_type': 'agent_terrain',
                'phone': '+221775555555',
                'is_active': True
            }
        )
        
        if created:
            agent.set_password('mobile123')
            agent.save()
            self.stdout.write(f'Agent créé: {agent.username}')
        
        # Créer le profil employé pour l'agent
        agent_employee, created = Employee.objects.get_or_create(
            user=agent,
            defaults={
                'specialite': 'menage',
                'date_embauche': timezone.now().date(),
                'statut': 'actif',
                'is_available': True,
                'telephone_professionnel': '+221775555555'
            }
        )
        
        if options['create_demo_data']:
            self.create_demo_data(technicien, agent)
        
        self.stdout.write(
            self.style.SUCCESS('Configuration mobile terminée!')
        )
        self.stdout.write('Comptes de test:')
        self.stdout.write(f'  - Technicien: tech_mobile / mobile123')
        self.stdout.write(f'  - Agent: agent_mobile / mobile123')
    
    def create_demo_data(self, technicien, agent):
        """Crée des données de démonstration"""
        self.stdout.write('Création des données de démonstration...')
        
        # Créer des tâches pour l'agent
        task_types = ['menage', 'visite', 'maintenance_preventive', 'etat_lieux']
        priorities = ['basse', 'normale', 'haute', 'urgente']
        statuses = ['planifie', 'en_cours', 'complete']
        
        for i in range(10):
            date_prevue = timezone.now() + timedelta(
                days=random.randint(-3, 7),
                hours=random.randint(8, 18)
            )
            
            Task.objects.create(
                titre=f'Tâche démo {i+1}',
                description=f'Description détaillée de la tâche {i+1}',
                type_tache=random.choice(task_types),
                priorite=random.choice(priorities),
                assigne_a=agent,
                cree_par=technicien,
                date_prevue=date_prevue,
                statut=random.choice(statuses),
                duree_estimee=random.randint(30, 240)
            )
        
        self.stdout.write('Données de démonstration créées!')
