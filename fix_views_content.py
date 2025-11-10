#!/usr/bin/env python
"""
Script pour mettre à jour le contenu des vues maintenance
Remplace les références à Intervention par Travail dans les fonctions renommées
"""

import re

# Lire le fichier
with open('apps/maintenance/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Liste des fonctions que nous avons renommées (ne pas toucher aux *_simple)
renamed_functions = [
    'travail_detail_view',
    'travail_assign_view',
    'travail_start_view',
    'travail_complete_view',
    'travail_delete_view',
    'travail_upload_media_view',
    'travaux_stats_api',
    'travail_calendar_api',
    'travail_checklist_view',
    'mes_travaux_view',
    'travaux_bulk_action',
    'travaux_search',
    'travaux_export',
]

# Remplacements globaux à faire
replacements = [
    # URLs et redirects
    (r"'maintenance:intervention_detail'", "'maintenance:travail_detail'"),
    (r'intervention_id=intervention\.id', 'travail_id=travail.id'),
    (r'intervention_id=travail\.id', 'travail_id=travail.id'),
    (r"'intervention_id': intervention\.id", "'travail_id': travail.id"),
    (r"'intervention_id': travail\.id", "'travail_id': travail.id"),
    (r"kwargs=\{'intervention_id': intervention\.id\}", "kwargs={'travail_id': travail.id}"),
    (r"kwargs=\{'intervention_id': travail\.id\}", "kwargs={'travail_id': travail.id}"),

    # Variables dans les fonctions renommées (mais pas dans *_simple)
    # Ces remplacements seront faits de manière ciblée
]

# Appliquer les remplacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Remplacements spécifiques pour les variables 'intervention' → 'travail'
# dans les fonctions que nous avons renommées
for func_name in renamed_functions:
    # Trouver la fonction
    func_pattern = rf'(def {func_name}\([^)]+\):.*?)(?=\n@|\ndef\s|\nclass\s|\Z)'

    def replace_in_function(match):
        func_code = match.group(1)
        # Ne pas toucher aux commentaires
        # Remplacer 'intervention = ' par 'travail = '
        func_code = re.sub(r'\bintervention\s*=\s*', 'travail = ', func_code)
        # Remplacer 'intervention.' par 'travail.'
        func_code = re.sub(r'\bintervention\.', 'travail.', func_code)
        # Remplacer '"intervention"' et "'intervention'" par "travail"
        func_code = re.sub(r"'intervention'", "'travail'", func_code)
        func_code = re.sub(r'"intervention"', '"travail"', func_code)
        # Messages
        func_code = re.sub(r'intervention assignée', 'travail assigné', func_code)
        func_code = re.sub(r"Intervention assignée", "Travail assigné", func_code)
        func_code = re.sub(r'd\'assigner cette intervention', 'd\'assigner ce travail', func_code)

        return func_code

    content = re.sub(func_pattern, replace_in_function, content, flags=re.DOTALL)

# Remplacements dans les stats API
content = re.sub(r'Intervention\.objects', 'Travail.objects', content)
content = re.sub(r'Intervention\.PRIORITE_CHOICES', 'Travail.PRIORITE_CHOICES', content)
content = re.sub(r'Intervention\.TYPE_INTERVENTION_CHOICES', 'Travail.TYPE_TRAVAIL_CHOICES', content)
content = re.sub(r'Intervention\.STATUT_CHOICES', 'Travail.STATUT_CHOICES', content)

# Ne pas remplacer dans les fonctions *_simple qui doivent rester avec Intervention
# et dans les commentaires de forme/configuration

# Écrire le fichier
with open('apps/maintenance/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Fichier mis a jour avec succes!")
print("Verifiez le resultat avant de tester.")
