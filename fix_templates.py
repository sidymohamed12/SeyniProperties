#!/usr/bin/env python
"""
Script de Correction Automatique des Templates
Phase 3 : Correction automatique de l'architecture Tiers
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class TemplateFixer:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.backup_dir = f'templates_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        self.corrections = defaultdict(list)
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'total_replacements': 0,
            'by_pattern': {}
        }

        # Définir les patterns de remplacement
        self.replacement_patterns = [
            # Pattern 1: bailleur → proprietaire (dans les variables Django)
            {
                'name': 'bailleur_to_proprietaire_variable',
                'pattern': r'\{\{\s*(\w+\.)*bailleur\.',
                'replacement': lambda m: m.group(0).replace('bailleur', 'proprietaire'),
                'description': 'Variable bailleur → proprietaire',
                'priority': 1
            },
            # Pattern 2: bailleurs → proprietaires (dans les boucles)
            {
                'name': 'bailleurs_to_proprietaires_loop',
                'pattern': r'\{%\s*for\s+(\w+)\s+in\s+bailleurs\s*%\}',
                'replacement': r'{% for \1 in proprietaires %}',
                'description': 'Boucle bailleurs → proprietaires',
                'priority': 1
            },
            # Pattern 3: bailleur_id → proprietaire_id
            {
                'name': 'bailleur_id_to_proprietaire_id',
                'pattern': r'\bbailleur_id\b',
                'replacement': 'proprietaire_id',
                'description': 'bailleur_id → proprietaire_id',
                'priority': 1
            },
            # Pattern 4: locataire.user.get_full_name → locataire.nom_complet
            {
                'name': 'locataire_user_get_full_name',
                'pattern': r'(\w+\.)*locataire\.user\.get_full_name',
                'replacement': lambda m: m.group(0).replace('.user.get_full_name', '.nom_complet'),
                'description': 'locataire.user.get_full_name → locataire.nom_complet',
                'priority': 1
            },
            # Pattern 5: locataire.user.email → locataire.email
            {
                'name': 'locataire_user_email',
                'pattern': r'(\w+\.)*locataire\.user\.email',
                'replacement': lambda m: m.group(0).replace('.user.email', '.email'),
                'description': 'locataire.user.email → locataire.email',
                'priority': 1
            },
            # Pattern 6: locataire.user.phone → locataire.telephone
            {
                'name': 'locataire_user_phone',
                'pattern': r'(\w+\.)*locataire\.user\.phone',
                'replacement': lambda m: m.group(0).replace('.user.phone', '.telephone'),
                'description': 'locataire.user.phone → locataire.telephone',
                'priority': 1
            },
            # Pattern 7: locataire.user.first_name → locataire.prenom
            {
                'name': 'locataire_user_first_name',
                'pattern': r'(\w+\.)*locataire\.user\.first_name',
                'replacement': lambda m: m.group(0).replace('.user.first_name', '.prenom'),
                'description': 'locataire.user.first_name → locataire.prenom',
                'priority': 1
            },
            # Pattern 8: locataire.user.last_name → locataire.nom
            {
                'name': 'locataire_user_last_name',
                'pattern': r'(\w+\.)*locataire\.user\.last_name',
                'replacement': lambda m: m.group(0).replace('.user.last_name', '.nom'),
                'description': 'locataire.user.last_name → locataire.nom',
                'priority': 1
            },
            # Pattern 9: bailleur.user.get_full_name → proprietaire.nom_complet
            {
                'name': 'bailleur_user_get_full_name',
                'pattern': r'(\w+\.)*bailleur\.user\.get_full_name',
                'replacement': lambda m: m.group(0).replace('bailleur.user.get_full_name', 'proprietaire.nom_complet'),
                'description': 'bailleur.user.get_full_name → proprietaire.nom_complet',
                'priority': 1
            },
            # Pattern 10: proprietaire.user.get_full_name → proprietaire.nom_complet
            {
                'name': 'proprietaire_user_get_full_name',
                'pattern': r'(\w+\.)*proprietaire\.user\.get_full_name',
                'replacement': lambda m: m.group(0).replace('.user.get_full_name', '.nom_complet'),
                'description': 'proprietaire.user.get_full_name → proprietaire.nom_complet',
                'priority': 1
            },
            # Pattern 11: proprietaire.user.email → proprietaire.email
            {
                'name': 'proprietaire_user_email',
                'pattern': r'(\w+\.)*proprietaire\.user\.email',
                'replacement': lambda m: m.group(0).replace('.user.email', '.email'),
                'description': 'proprietaire.user.email → proprietaire.email',
                'priority': 1
            },
            # Pattern 12: "bailleur" dans les chaînes de texte visibles
            {
                'name': 'bailleur_text_singular',
                'pattern': r'\bbailleur\b(?![_\w])',
                'replacement': 'proprietaire',
                'description': 'Texte "bailleur" → "proprietaire"',
                'priority': 2,
                'case_sensitive': False
            },
            # Pattern 13: "Bailleur" avec majuscule
            {
                'name': 'bailleur_text_capitalized',
                'pattern': r'\bBailleur\b(?![_\w])',
                'replacement': 'Propriétaire',
                'description': 'Texte "Bailleur" → "Propriétaire"',
                'priority': 2
            },
            # Pattern 14: "BAILLEUR" en majuscules
            {
                'name': 'bailleur_text_uppercase',
                'pattern': r'\bBAILLEUR\b',
                'replacement': 'PROPRIÉTAIRE',
                'description': 'Texte "BAILLEUR" → "PROPRIÉTAIRE"',
                'priority': 2
            },
            # Pattern 15: "bailleurs" pluriel
            {
                'name': 'bailleurs_text_plural',
                'pattern': r'\bbailleurs\b(?![_\w])',
                'replacement': 'proprietaires',
                'description': 'Texte "bailleurs" → "proprietaires"',
                'priority': 2
            },
            # Pattern 16: tenant → locataire (terme anglais)
            {
                'name': 'tenant_to_locataire',
                'pattern': r'\.tenant\.',
                'replacement': '.locataire.',
                'description': 'tenant → locataire',
                'priority': 3
            },
        ]

    def find_template_files(self):
        """Trouve tous les fichiers template HTML"""
        template_files = []

        # Templates principaux
        if os.path.exists('templates'):
            for root, dirs, files in os.walk('templates'):
                for file in files:
                    if file.endswith('.html'):
                        template_files.append(os.path.join(root, file))

        # Templates dans les apps
        if os.path.exists('apps'):
            for app in os.listdir('apps'):
                app_templates = os.path.join('apps', app, 'templates')
                if os.path.exists(app_templates):
                    for root, dirs, files in os.walk(app_templates):
                        for file in files:
                            if file.endswith('.html'):
                                template_files.append(os.path.join(root, file))

        return template_files

    def create_backup(self, filepath):
        """Crée un backup du fichier"""
        if not self.dry_run:
            backup_path = os.path.join(self.backup_dir, filepath)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(filepath, backup_path)

    def apply_pattern(self, content, pattern_info):
        """Applique un pattern de remplacement"""
        pattern = pattern_info['pattern']
        replacement = pattern_info['replacement']

        # Compiler le pattern avec ou sans case sensitivity
        flags = 0 if pattern_info.get('case_sensitive', True) else re.IGNORECASE
        regex = re.compile(pattern, flags)

        # Compter les correspondances
        matches = list(regex.finditer(content))
        if not matches:
            return content, 0

        # Appliquer le remplacement
        if callable(replacement):
            new_content = regex.sub(replacement, content)
        else:
            new_content = regex.sub(replacement, content)

        return new_content, len(matches)

    def fix_file(self, filepath):
        """Corrige un fichier template"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

            content = original_content
            file_changes = []
            total_changes = 0

            # Appliquer tous les patterns par ordre de priorité
            sorted_patterns = sorted(self.replacement_patterns, key=lambda x: x.get('priority', 999))

            for pattern_info in sorted_patterns:
                new_content, count = self.apply_pattern(content, pattern_info)

                if count > 0:
                    file_changes.append({
                        'pattern': pattern_info['name'],
                        'description': pattern_info['description'],
                        'count': count
                    })
                    total_changes += count
                    content = new_content

                    # Mettre à jour les statistiques
                    if pattern_info['name'] not in self.stats['by_pattern']:
                        self.stats['by_pattern'][pattern_info['name']] = 0
                    self.stats['by_pattern'][pattern_info['name']] += count

            # Si des changements ont été faits
            if total_changes > 0:
                self.stats['files_modified'] += 1
                self.stats['total_replacements'] += total_changes
                self.corrections[filepath] = file_changes

                # Créer backup et écrire le nouveau contenu
                if not self.dry_run:
                    self.create_backup(filepath)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)

            self.stats['files_processed'] += 1
            return total_changes > 0

        except Exception as e:
            print(f"❌ Erreur lors du traitement de {filepath}: {str(e)}")
            return False

    def generate_report(self):
        """Génère un rapport des modifications"""
        print("\n" + "="*80)
        print(" "*20 + "RAPPORT DE CORRECTION AUTOMATIQUE")
        print("="*80)

        mode_str = "🔍 MODE SIMULATION (DRY-RUN)" if self.dry_run else "✍️  MODE ÉCRITURE (MODIFICATIONS APPLIQUÉES)"
        print(f"\n{mode_str}")

        print(f"\n📊 STATISTIQUES GLOBALES:")
        print(f"   Fichiers traités : {self.stats['files_processed']}")
        print(f"   Fichiers modifiés : {self.stats['files_modified']}")
        print(f"   Total remplacements : {self.stats['total_replacements']}")

        if self.stats['by_pattern']:
            print(f"\n📝 REMPLACEMENTS PAR PATTERN:")
            sorted_patterns = sorted(self.stats['by_pattern'].items(), key=lambda x: x[1], reverse=True)
            for pattern_name, count in sorted_patterns:
                # Trouver la description
                desc = next((p['description'] for p in self.replacement_patterns if p['name'] == pattern_name), pattern_name)
                print(f"   {count:3d} × {desc}")

        if self.corrections:
            print(f"\n📄 FICHIERS MODIFIÉS ({len(self.corrections)} fichiers):")

            sorted_files = sorted(self.corrections.items(), key=lambda x: sum(c['count'] for c in x[1]), reverse=True)

            for filepath, changes in sorted_files:
                total_file_changes = sum(c['count'] for c in changes)
                print(f"\n   {filepath} ({total_file_changes} modifications)")
                for change in changes:
                    print(f"      {change['count']:2d} × {change['description']}")

        if not self.dry_run and self.stats['files_modified'] > 0:
            print(f"\n💾 BACKUP:")
            print(f"   Emplacement : {self.backup_dir}/")
            print(f"   Fichiers sauvegardés : {self.stats['files_modified']}")

    def generate_markdown_report(self, output_file='CORRECTIONS_REPORT.md'):
        """Génère un rapport Markdown"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Rapport de Corrections Automatiques - Templates\n\n")
            f.write(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            mode = "Simulation (Dry-Run)" if self.dry_run else "Modifications Appliquées"
            f.write(f"**Mode** : {mode}\n\n")

            f.write("## 📊 Statistiques\n\n")
            f.write(f"- **Fichiers traités** : {self.stats['files_processed']}\n")
            f.write(f"- **Fichiers modifiés** : {self.stats['files_modified']}\n")
            f.write(f"- **Total remplacements** : {self.stats['total_replacements']}\n\n")

            if self.stats['by_pattern']:
                f.write("## 📝 Remplacements par Pattern\n\n")
                f.write("| Pattern | Description | Occurrences |\n")
                f.write("|---------|-------------|-------------|\n")

                sorted_patterns = sorted(self.stats['by_pattern'].items(), key=lambda x: x[1], reverse=True)
                for pattern_name, count in sorted_patterns:
                    desc = next((p['description'] for p in self.replacement_patterns if p['name'] == pattern_name), pattern_name)
                    f.write(f"| `{pattern_name}` | {desc} | {count} |\n")
                f.write("\n")

            if self.corrections:
                f.write("## 📄 Fichiers Modifiés\n\n")

                sorted_files = sorted(self.corrections.items(), key=lambda x: sum(c['count'] for c in x[1]), reverse=True)

                for filepath, changes in sorted_files:
                    total_file_changes = sum(c['count'] for c in changes)
                    f.write(f"\n### `{filepath}` ({total_file_changes} modifications)\n\n")

                    for change in changes:
                        f.write(f"- **{change['description']}** : {change['count']} remplacement(s)\n")

            if not self.dry_run and self.stats['files_modified'] > 0:
                f.write(f"\n## 💾 Backup\n\n")
                f.write(f"Les fichiers originaux ont été sauvegardés dans : `{self.backup_dir}/`\n\n")
                f.write("Pour restaurer un fichier :\n")
                f.write("```bash\n")
                f.write(f"cp {self.backup_dir}/path/to/file.html path/to/file.html\n")
                f.write("```\n")

        print(f"\n✅ Rapport Markdown généré : {output_file}")

    def run(self):
        """Exécute la correction"""
        if not self.dry_run:
            os.makedirs(self.backup_dir, exist_ok=True)
            print(f"📁 Dossier de backup créé : {self.backup_dir}/")

        print("🔍 Recherche des fichiers templates...")
        template_files = self.find_template_files()
        print(f"📄 {len(template_files)} fichiers template trouvés\n")

        if self.dry_run:
            print("🔍 MODE SIMULATION - Aucune modification ne sera appliquée\n")
        else:
            print("✍️  MODE ÉCRITURE - Les modifications seront appliquées\n")

        print("🔧 Traitement en cours...\n")

        for filepath in template_files:
            self.fix_file(filepath)

        self.generate_report()

        report_name = 'CORRECTIONS_REPORT_DRYRUN.md' if self.dry_run else 'CORRECTIONS_REPORT.md'
        self.generate_markdown_report(report_name)


def main():
    import sys

    # Vérifier les arguments
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        dry_run = False
        print("\n⚠️  MODE ÉCRITURE ACTIVÉ - Les fichiers seront modifiés !")
        response = input("Voulez-vous continuer ? (oui/non) : ")
        if response.lower() not in ['oui', 'yes', 'y', 'o']:
            print("❌ Opération annulée.")
            return

    fixer = TemplateFixer(dry_run=dry_run)
    fixer.run()

    print("\n" + "="*80)
    if dry_run:
        print("✅ Simulation terminée !")
        print("\n💡 Pour appliquer les modifications, exécutez :")
        print("   python fix_templates.py --apply")
    else:
        print("✅ Corrections appliquées !")
        print(f"\n💾 Backup disponible dans : {fixer.backup_dir}/")
        print("\n💡 Prochaines étapes :")
        print("   1. Vérifier les modifications")
        print("   2. Tester l'application")
        print("   3. Commiter si tout fonctionne")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
