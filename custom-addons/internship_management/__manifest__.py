{
    'name': 'Gestion des Stages',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Plateforme complète de gestion des stages - Techpal',
    'description': """
Gestion des Stages - Plateforme Complète
=========================================

Cette application permet une gestion complète des stages avec les fonctionnalités suivantes :

**Gestion des Utilisateurs & Rôles :**
* Authentification sécurisée avec rôles : Stagiaire, Encadrant, Entreprise, Administrateur
* Profils utilisateurs détaillés avec informations académiques et professionnelles

**Gestion des Stages :**
* Proposition et validation des sujets de stage
* Affectation d'encadrants et suivi d'avancement
* Gestion complète de documents (conventions, rapports, présentations)
* Génération automatique de documents PDF

Développé dans le cadre d'un stage chez Techpal Casablanca.
    """,
    'author': 'SILUE - Stagiaire Techpal',
    'website': 'https://techpal.ma',
    'license': 'LGPL-3',

    # Dépendances : modules Odoo requis
    'depends': [
        'base',  # Module de base Odoo (obligatoire)
        'mail',  # Système de messagerie et notifications
        'contacts',  # Gestion des contacts (entreprises)
        'portal',        # Accès portail pour entreprises
        'hr',            # Ressources humaines (pour les employés/encadrants)
        'contacts',      # Gestion des contacts (entreprises)
        'calendar',      # Gestion d'agenda
    ],

    # Fichiers de données à charger
    'data': [
        # Sécurité (ordre important !)
        'security/internship_security.xml',
        'security/ir.model.access.csv',

        # Données
        'data/sequences.xml',
        'data/internship_demo_data.xml',
        'data/internship_cron.xml',

        # Vues principales
        'views/internship_stage_views.xml',
        'views/internship_student_views.xml',
        'views/internship_supervisor_views.xml',
        'views/internship_config_views.xml',
        'views/internship_message_views.xml',
        'views/internship_notification_views.xml',
        'views/internship_meeting_views.xml',

        # Dashboard
        'views/dashboard_template.xml',

        # Rapports
        'reports/defense_report_template.xml',
        'reports/internship_reports.xml',

        # Menus (en dernier)
        'views/internship_menus.xml',
    ],

    'demo': [
        #'data/internship_demo_data.xml',
    ],

    # Configuration du module
    'installable': True,  # Le module peut être installé
    'application': True,  # C'est une application principale (apparaît dans le menu Apps)
    'auto_install': False,  # Ne s'installe pas automatiquement
    'sequence': 10,  # Ordre d'apparition dans la liste des apps

}