# apps/properties/templatetags/custom_filters.py

from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère un item d'un dictionnaire par sa clé"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def jsonify(obj):
    """Convertit un objet Python en JSON pour JavaScript"""
    return mark_safe(json.dumps(obj))

@register.filter
def percentage(value, total):
    """Calcule un pourcentage"""
    if total and total > 0:
        return round((value / total) * 100, 1)
    return 0

@register.filter
def currency(value):
    """Formate un nombre en devise FCFA"""
    if value:
        return f"{value:,.0f} FCFA".replace(',', ' ')
    return "0 FCFA"

@register.filter
def status_color(status):
    """Retourne une classe CSS selon le statut"""
    colors = {
        'libre': 'text-green-600 bg-green-100',
        'available': 'text-green-600 bg-green-100',
        'occupe': 'text-red-600 bg-red-100', 
        'occupied': 'text-red-600 bg-red-100',
        'maintenance': 'text-orange-600 bg-orange-100',
        'signale': 'text-blue-600 bg-blue-100',
        'assigne': 'text-purple-600 bg-purple-100',
        'en_cours': 'text-yellow-600 bg-yellow-100',
        'complete': 'text-green-600 bg-green-100',
        'annule': 'text-gray-600 bg-gray-100',
    }
    return colors.get(status, 'text-gray-600 bg-gray-100')

@register.filter
def priority_color(priority):
    """Retourne une classe CSS selon la priorité"""
    colors = {
        'urgent': 'text-red-600 bg-red-100',
        'haute': 'text-orange-600 bg-orange-100',
        'normale': 'text-blue-600 bg-blue-100',
        'basse': 'text-gray-600 bg-gray-100',
    }
    return colors.get(priority, 'text-gray-600 bg-gray-100')