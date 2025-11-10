# apps/employees/templatetags/mobile_extras.py
from django import template
from django.utils import timezone
from datetime import timedelta
import json

register = template.Library()

@register.filter
def mobile_date(value):
    """Formatage de date optimisé pour mobile"""
    if not value:
        return ''
    
    now = timezone.now()
    today = now.date()
    
    if value.date() == today:
        return f"Aujourd'hui {value.strftime('%H:%M')}"
    elif value.date() == today - timedelta(days=1):
        return f"Hier {value.strftime('%H:%M')}"
    elif value.date() == today + timedelta(days=1):
        return f"Demain {value.strftime('%H:%M')}"
    elif value.year == today.year:
        return value.strftime('%d/%m %H:%M')
    else:
        return value.strftime('%d/%m/%Y %H:%M')

@register.filter
def status_color(status):
    """Retourne la couleur selon le statut"""
    colors = {
        'planifie': 'blue',
        'en_cours': 'orange',
        'complete': 'green',
        'annule': 'gray',
        'signale': 'yellow',
        'assigne': 'blue'
    }
    return colors.get(status, 'gray')

@register.filter
def priority_icon(priority):
    """Retourne l'icône selon la priorité"""
    icons = {
        'basse': 'fa-flag text-green-500',
        'normale': 'fa-flag text-blue-500',
        'haute': 'fa-flag text-orange-500',
        'urgente': 'fa-exclamation-triangle text-red-500'
    }
    return icons.get(priority, 'fa-flag text-gray-500')

@register.filter
def task_type_icon(task_type):
    """Retourne l'icône selon le type de tâche"""
    icons = {
        'menage': 'fa-broom',
        'maintenance_preventive': 'fa-tools',
        'visite': 'fa-eye',
        'etat_lieux': 'fa-clipboard-list',
        'livraison': 'fa-truck',
        'administrative': 'fa-file-alt',
        'autres': 'fa-ellipsis-h'
    }
    return icons.get(task_type, 'fa-tasks')

@register.filter
def intervention_type_icon(intervention_type):
    """Retourne l'icône selon le type d'intervention"""
    icons = {
        'plomberie': 'fa-faucet',
        'electricite': 'fa-bolt',
        'menage': 'fa-broom',
        'reparation': 'fa-hammer',
        'peinture': 'fa-paint-roller',
        'serrurerie': 'fa-key',
        'climatisation': 'fa-snowflake',
        'jardinage': 'fa-leaf',
        'autres': 'fa-tools'
    }
    return icons.get(intervention_type, 'fa-wrench')

@register.filter
def duration_human(minutes):
    """Convertit les minutes en format lisible"""
    if not minutes:
        return ''
    
    if minutes < 60:
        return f"{minutes}min"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h{remaining_minutes:02d}"

@register.filter
def truncate_smart(text, length=30):
    """Tronque intelligemment le texte"""
    if len(text) <= length:
        return text
    
    # Trouver le dernier espace avant la limite
    truncated = text[:length]
    last_space = truncated.rfind(' ')
    
    if last_space > length * 0.7:  # Si l'espace est pas trop loin
        return text[:last_space] + '...'
    else:
        return text[:length-3] + '...'

@register.simple_tag
def get_notification_count(user):
    """Compte les notifications non lues"""
    if not user.is_authenticated:
        return 0
    
    # Ici vous pourriez implémenter la logique de comptage des notifications
    # Pour l'instant, retourner 0
    return 0

@register.simple_tag
def json_script_safe(value, element_id):
    """Version sécurisée de json_script pour mobile"""
    try:
        json_str = json.dumps(value, ensure_ascii=False)
        return f'<script id="{element_id}" type="application/json">{json_str}</script>'
    except (TypeError, ValueError):
        return f'<script id="{element_id}" type="application/json">{{}}</script>'

@register.inclusion_tag('employees/mobile/components/status_badge.html')
def status_badge(status, size='sm'):
    """Affiche un badge de statut"""
    return {
        'status': status,
        'size': size,
        'color': status_color(status)
    }

@register.inclusion_tag('employees/mobile/components/priority_badge.html')
def priority_badge(priority, size='sm'):
    """Affiche un badge de priorité"""
    return {
        'priority': priority,
        'size': size,
        'icon': priority_icon(priority)
    }

@register.inclusion_tag('employees/mobile/components/progress_bar.html')
def progress_bar(value, max_value=100, color='blue'):
    """Affiche une barre de progression"""
    percentage = (value / max_value * 100) if max_value > 0 else 0
    return {
        'percentage': min(percentage, 100),
        'value': value,
        'max_value': max_value,
        'color': color
    }

