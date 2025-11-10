import string
import random
from datetime import datetime
from django.utils import timezone


def generate_reference(prefix='REF', length=6):
    """
    Génère une référence unique avec un préfixe
    
    Args:
        prefix (str): Préfixe de la référence (ex: 'FAC', 'CTR', 'INT')
        length (int): Longueur de la partie numérique
    
    Returns:
        str: Référence unique (ex: 'FAC-2025-001234')
    """
    current_year = timezone.now().year
    
    # Générer un nombre aléatoire
    random_number = ''.join(random.choices(string.digits, k=length))
    
    return f"{prefix}-{current_year}-{random_number}"


def generate_unique_reference(prefix='REF', length=6):
    """Alias pour generate_reference pour compatibilité"""
    return generate_reference(prefix, length)


def format_currency(amount, currency='FCFA'):
    """
    Formate un montant en devise
    
    Args:
        amount (Decimal/float): Montant à formater
        currency (str): Devise
    
    Returns:
        str: Montant formaté
    """
    if amount is None:
        return f"0 {currency}"
    
    # Formater avec des espaces comme séparateurs de milliers
    formatted = f"{amount:,.0f}".replace(',', ' ')
    
    return f"{formatted} {currency}"


def format_money(amount, currency='FCFA'):
    """Alias pour format_currency pour compatibilité"""
    return format_currency(amount, currency)


def validate_phone_number(phone):
    """
    Valide et formate un numéro de téléphone sénégalais
    
    Args:
        phone (str): Numéro de téléphone
    
    Returns:
        str: Numéro formaté ou None si invalide
    """
    import re
    
    if not phone:
        return None
    
    # Supprimer tous les caractères non numériques
    clean_phone = re.sub(r'[^\d]', '', phone)
    
    # Patterns pour les numéros sénégalais
    patterns = [
        r'^221(7[0-9]{8})$',  # +221 7X XXX XX XX
        r'^(7[0-9]{8})$',     # 7X XXX XX XX
        r'^221(3[0-9]{8})$',  # +221 3X XXX XX XX (fixe)
        r'^(3[0-9]{8})$',     # 3X XXX XX XX (fixe)
    ]
    
    for pattern in patterns:
        match = re.match(pattern, clean_phone)
        if match:
            if clean_phone.startswith('221'):
                return f"+{clean_phone}"
            else:
                return f"+221{clean_phone}"
    
    return None


def validate_phone(phone):
    """Alias pour validate_phone_number pour compatibilité"""
    return validate_phone_number(phone)


def get_user_display_name(user):
    """
    Retourne le nom d'affichage d'un utilisateur
    
    Args:
        user: Instance User
    
    Returns:
        str: Nom d'affichage
    """
    if not user:
        return "Utilisateur inconnu"
    
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.last_name:
        return user.last_name
    else:
        return user.username


def generate_password(length=12):
    """
    Génère un mot de passe aléatoire
    
    Args:
        length (int): Longueur du mot de passe
    
    Returns:
        str: Mot de passe généré
    """
    import secrets
    
    # Caractères autorisés (éviter les caractères ambigus)
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    
    # S'assurer d'avoir au moins un caractère de chaque type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase), 
        secrets.choice(string.digits),
        secrets.choice("!@#$%&*")
    ]
    
    # Compléter avec des caractères aléatoires
    for _ in range(length - 4):
        password.append(secrets.choice(chars))
    
    # Mélanger la liste
    random.shuffle(password)
    
    return ''.join(password)