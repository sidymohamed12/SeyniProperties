#!/usr/bin/env python
"""
Script d'analyse des templates pour la migration vers l'architecture Tiers
Phase 3 : Détection des templates à mettre à jour
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Patterns à détecter dans les templates
PATTERNS = {
    'bailleur_reference': {
        'pattern': r'\b(bailleur|Bailleur)\b',
        'description': 'Référence à bailleur (devrait être proprietaire)',
        'suggestion': 'Remplacer par proprietaire',
        'severity': 'HIGH'
    },
    'locataire_user_access': {
        'pattern': r'locataire\.user\.(get_full_name|first_name|last_name|email|phone)',
        'description': 'Accès via locataire.user (devrait être direct)',
        'suggestion': 'Utiliser locataire.nom_complet, locataire.email, etc.',
        'severity': 'HIGH'
    },
    'bailleur_user_access': {
        'pattern': r'bailleur\.user\.(get_full_name|first_name|last_name|email|phone)',
        'description': 'Accès via bailleur.user (devrait être direct)',
        'suggestion': 'Utiliser proprietaire.nom_complet, proprietaire.email, etc.',
        'severity': 'HIGH'
    },
    'proprietaire_user_access': {
        'pattern': r'proprietaire\.user\.(get_full_name|first_name|last_name|email|phone)',
        'description': 'Accès via proprietaire.user (devrait être direct)',
        'suggestion': 'Utiliser proprietaire.nom_complet, proprietaire.email, etc.',
        'severity': 'MEDIUM'
    },
    'landlord_reference': {
        'pattern': r'\blandlord\b',
        'description': 'Référence à landlord (terme anglais)',
        'suggestion': 'Remplacer par proprietaire',
        'severity': 'MEDIUM'
    },
    'tenant_reference': {
        'pattern': r'\btenant\b',
        'description': 'Référence à tenant (terme anglais)',
        'suggestion': 'Remplacer par locataire',
        'severity': 'LOW'
    },
    'user_filter_locataire': {
        'pattern': r'filter\(user__is_active=True\)',
        'description': 'Filtre sur user__is_active (vieux pattern)',
        'suggestion': 'Remplacer par filter(statut="actif")',
        'severity': 'MEDIUM'
    },
    'for_loop_bailleurs': {
        'pattern': r'{%\s*for\s+\w+\s+in\s+bailleurs',
        'description': 'Boucle sur bailleurs',
        'suggestion': 'Renommer la variable en proprietaires',
        'severity': 'HIGH'
    },
}

class TemplateAnalyzer:
    def __init__(self, templates_dir='templates'):
        self.templates_dir = templates_dir
        self.issues = defaultdict(list)
        self.stats = {
            'total_files': 0,
            'files_with_issues': 0,
            'total_issues': 0,
            'by_severity': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        }

    def find_template_files(self):
        """Trouve tous les fichiers template HTML"""
        template_files = []

        # Chercher dans le dossier templates
        if os.path.exists(self.templates_dir):
            for root, dirs, files in os.walk(self.templates_dir):
                for file in files:
                    if file.endswith('.html'):
                        template_files.append(os.path.join(root, file))

        # Chercher dans les apps (dossier templates de chaque app)
        apps_dir = 'apps'
        if os.path.exists(apps_dir):
            for app in os.listdir(apps_dir):
                app_templates = os.path.join(apps_dir, app, 'templates')
                if os.path.exists(app_templates):
                    for root, dirs, files in os.walk(app_templates):
                        for file in files:
                            if file.endswith('.html'):
                                template_files.append(os.path.join(root, file))

        return template_files

    def analyze_file(self, filepath):
        """Analyse un fichier template"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            file_issues = []

            for line_num, line in enumerate(lines, 1):
                for pattern_name, pattern_info in PATTERNS.items():
                    matches = re.finditer(pattern_info['pattern'], line, re.IGNORECASE)
                    for match in matches:
                        issue = {
                            'file': filepath,
                            'line': line_num,
                            'content': line.strip(),
                            'match': match.group(0),
                            'pattern': pattern_name,
                            'description': pattern_info['description'],
                            'suggestion': pattern_info['suggestion'],
                            'severity': pattern_info['severity'],
                            'column': match.start()
                        }
                        file_issues.append(issue)
                        self.stats['total_issues'] += 1
                        self.stats['by_severity'][pattern_info['severity']] += 1

            if file_issues:
                self.issues[filepath] = file_issues
                self.stats['files_with_issues'] += 1

            return file_issues

        except Exception as e:
            print(f"❌ Erreur lors de l'analyse de {filepath}: {str(e)}")
            return []

    def generate_report(self):
        """Génère un rapport détaillé"""
        print("\n" + "="*80)
        print(" "*20 + "RAPPORT D'ANALYSE DES TEMPLATES")
        print("="*80)

        print(f"\n📊 STATISTIQUES GLOBALES:")
        print(f"   Total fichiers analysés : {self.stats['total_files']}")
        print(f"   Fichiers avec problèmes : {self.stats['files_with_issues']}")
        print(f"   Total problèmes détectés : {self.stats['total_issues']}")
        print(f"\n   Par sévérité:")
        print(f"      🔴 HIGH   : {self.stats['by_severity']['HIGH']} problèmes")
        print(f"      🟡 MEDIUM : {self.stats['by_severity']['MEDIUM']} problèmes")
        print(f"      🟢 LOW    : {self.stats['by_severity']['LOW']} problèmes")

        if not self.issues:
            print("\n✅ Aucun problème détecté ! Tous les templates sont conformes.")
            return

        # Grouper par sévérité
        by_severity = {'HIGH': [], 'MEDIUM': [], 'LOW': []}
        for filepath, file_issues in self.issues.items():
            for issue in file_issues:
                by_severity[issue['severity']].append(issue)

        # Afficher par sévérité
        severity_symbols = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
        severity_order = ['HIGH', 'MEDIUM', 'LOW']

        for severity in severity_order:
            issues = by_severity[severity]
            if not issues:
                continue

            print(f"\n\n{severity_symbols[severity]} PROBLÈMES DE SÉVÉRITÉ {severity} ({len(issues)} problèmes)")
            print("="*80)

            # Grouper par fichier
            by_file = defaultdict(list)
            for issue in issues:
                by_file[issue['file']].append(issue)

            for filepath in sorted(by_file.keys()):
                file_issues = by_file[filepath]
                print(f"\n📄 {filepath} ({len(file_issues)} problème(s))")

                for issue in file_issues:
                    print(f"\n   Ligne {issue['line']}, Col {issue['column']}")
                    print(f"   Pattern  : {issue['pattern']}")
                    print(f"   Trouvé   : {issue['match']}")
                    print(f"   Contexte : {issue['content'][:100]}...")
                    print(f"   ℹ️  {issue['description']}")
                    print(f"   💡 {issue['suggestion']}")

        # Résumé par fichier
        print("\n\n" + "="*80)
        print("📋 RÉSUMÉ PAR FICHIER")
        print("="*80)

        sorted_files = sorted(self.issues.items(), key=lambda x: len(x[1]), reverse=True)

        for filepath, file_issues in sorted_files:
            severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            for issue in file_issues:
                severity_counts[issue['severity']] += 1

            severity_str = f"🔴{severity_counts['HIGH']} 🟡{severity_counts['MEDIUM']} 🟢{severity_counts['LOW']}"
            print(f"\n{len(file_issues):3d} problèmes - {severity_str} - {filepath}")

    def generate_markdown_report(self, output_file='TEMPLATES_MIGRATION.md'):
        """Génère un rapport en Markdown"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Rapport de Migration des Templates - Architecture Tiers\n\n")
            f.write(f"Date d'analyse : {os.popen('date').read().strip()}\n\n")

            f.write("## 📊 Statistiques Globales\n\n")
            f.write(f"- **Total fichiers analysés** : {self.stats['total_files']}\n")
            f.write(f"- **Fichiers avec problèmes** : {self.stats['files_with_issues']}\n")
            f.write(f"- **Total problèmes détectés** : {self.stats['total_issues']}\n\n")

            f.write("### Par sévérité\n\n")
            f.write(f"- 🔴 **HIGH** : {self.stats['by_severity']['HIGH']} problèmes\n")
            f.write(f"- 🟡 **MEDIUM** : {self.stats['by_severity']['MEDIUM']} problèmes\n")
            f.write(f"- 🟢 **LOW** : {self.stats['by_severity']['LOW']} problèmes\n\n")

            if not self.issues:
                f.write("✅ **Aucun problème détecté !** Tous les templates sont conformes.\n")
                return

            # Tableau récapitulatif
            f.write("## 📋 Fichiers à Mettre à Jour\n\n")
            f.write("| Fichier | Total | 🔴 HIGH | 🟡 MEDIUM | 🟢 LOW |\n")
            f.write("|---------|-------|---------|-----------|--------|\n")

            sorted_files = sorted(self.issues.items(), key=lambda x: len(x[1]), reverse=True)
            for filepath, file_issues in sorted_files:
                severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
                for issue in file_issues:
                    severity_counts[issue['severity']] += 1

                f.write(f"| `{filepath}` | {len(file_issues)} | {severity_counts['HIGH']} | "
                       f"{severity_counts['MEDIUM']} | {severity_counts['LOW']} |\n")

            # Détails par fichier
            f.write("\n## 🔍 Détails par Fichier\n\n")

            for filepath, file_issues in sorted_files:
                f.write(f"\n### 📄 `{filepath}`\n\n")
                f.write(f"**{len(file_issues)} problème(s) détecté(s)**\n\n")

                for i, issue in enumerate(file_issues, 1):
                    severity_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}[issue['severity']]
                    f.write(f"#### {severity_icon} Problème {i} (Ligne {issue['line']})\n\n")
                    f.write(f"- **Pattern détecté** : `{issue['match']}`\n")
                    f.write(f"- **Type** : {issue['pattern']}\n")
                    f.write(f"- **Description** : {issue['description']}\n")
                    f.write(f"- **Suggestion** : {issue['suggestion']}\n")
                    f.write(f"- **Contexte** :\n")
                    f.write(f"  ```django\n")
                    f.write(f"  {issue['content']}\n")
                    f.write(f"  ```\n\n")

            # Guide de migration
            f.write("\n## 📖 Guide de Migration\n\n")
            f.write("### Patterns de Remplacement\n\n")

            f.write("#### 1. Bailleur → Propriétaire\n\n")
            f.write("```django\n")
            f.write("<!-- AVANT -->\n")
            f.write("{{ residence.bailleur.user.get_full_name }}\n")
            f.write("{{ residence.bailleur.user.email }}\n\n")
            f.write("<!-- APRÈS -->\n")
            f.write("{{ residence.proprietaire.nom_complet }}\n")
            f.write("{{ residence.proprietaire.email }}\n")
            f.write("```\n\n")

            f.write("#### 2. Locataire - Accès Direct\n\n")
            f.write("```django\n")
            f.write("<!-- AVANT -->\n")
            f.write("{{ contrat.locataire.user.get_full_name }}\n")
            f.write("{{ contrat.locataire.user.email }}\n")
            f.write("{{ contrat.locataire.user.phone }}\n\n")
            f.write("<!-- APRÈS -->\n")
            f.write("{{ contrat.locataire.nom_complet }}\n")
            f.write("{{ contrat.locataire.email }}\n")
            f.write("{{ contrat.locataire.telephone }}\n")
            f.write("```\n\n")

            f.write("#### 3. Boucles et Filtres\n\n")
            f.write("```django\n")
            f.write("<!-- AVANT -->\n")
            f.write("{% for bailleur in bailleurs %}\n")
            f.write("  {{ bailleur.user.get_full_name }}\n")
            f.write("{% endfor %}\n\n")
            f.write("<!-- APRÈS -->\n")
            f.write("{% for proprietaire in proprietaires %}\n")
            f.write("  {{ proprietaire.nom_complet }}\n")
            f.write("{% endfor %}\n")
            f.write("```\n\n")

            f.write("#### 4. Initiales (Avatars)\n\n")
            f.write("```django\n")
            f.write("<!-- AVANT -->\n")
            f.write("{{ locataire.user.first_name.0 }}{{ locataire.user.last_name.0 }}\n\n")
            f.write("<!-- APRÈS -->\n")
            f.write("{{ locataire.prenom.0 }}{{ locataire.nom.0 }}\n")
            f.write("```\n\n")

        print(f"\n✅ Rapport Markdown généré : {output_file}")

    def run(self):
        """Exécute l'analyse complète"""
        print("🔍 Recherche des fichiers templates...")
        template_files = self.find_template_files()
        self.stats['total_files'] = len(template_files)

        print(f"📄 {len(template_files)} fichiers template trouvés\n")
        print("🔎 Analyse en cours...\n")

        for filepath in template_files:
            self.analyze_file(filepath)

        self.generate_report()
        self.generate_markdown_report()

        return self.issues


def main():
    analyzer = TemplateAnalyzer()
    analyzer.run()

    print("\n" + "="*80)
    print("✅ Analyse terminée !")
    print("="*80)
    print("\n📝 Un rapport détaillé a été généré : TEMPLATES_MIGRATION.md")
    print("\n💡 Prochaines étapes :")
    print("   1. Consulter le rapport TEMPLATES_MIGRATION.md")
    print("   2. Prioriser les fichiers avec sévérité HIGH")
    print("   3. Mettre à jour les templates un par un")
    print("   4. Tester après chaque mise à jour\n")


if __name__ == '__main__':
    main()
