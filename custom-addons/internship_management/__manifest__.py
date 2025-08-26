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
            
            **Suivi & Communication :**
            * Messagerie interne entre tous les acteurs
            * Système de commentaires et feedback
            * Notifications automatiques (email + in-app)
            * Agenda partagé pour réunions et soutenances
            
            **Tableau de Bord & Statistiques :**
            * Tableaux de bord personnalisés selon le rôle
            * Statistiques détaillées : répartition, progression, taux de réussite
            * Alertes automatiques en cas de retard ou blocage
            
            **Gestion des Soutenances :**
            * Planification automatique des soutenances
            * Attribution de jury et génération de procès-verbaux
            * Dépôt et gestion des présentations
            
            Développé dans le cadre d'un stage chez Techpal Casablanca.
    """,
    'author': 'SILUE - Stagiaire Techpal',
    'website': 'https://techpal.ma',
    'license': 'LGPL-3',

    # Dépendances : modules Odoo requis
    'depends': [
        'base',  # Module de base Odoo (obligatoire)
        'mail',  # Système de messagerie et notifications
        'portal',  # Accès portail pour entreprises
        'hr',  # Ressources humaines (pour les employés/encadrants)
        'contacts',  # Gestion des contacts (entreprises)
        'document',  # Gestion de documents
        'calendar',  # Gestion d'agenda
    ],

    # Fichiers de données à charger
    'data': [
        # Sécurité (ordre important !)
        'security/internship_security.xml',
        'security/ir.model.access.csv',

        # Données de base
        'data/internship_sequence.xml',
        'data/internship_data.xml',

        # Vues (ordre important !)
        'views/internship_student_views.xml',
        'views/internship_supervisor_views.xml',
        'views/internship_company_views.xml',
        'views/internship_stage_views.xml',
        'views/internship_document_views.xml',

        # Menus (en dernier)
        'views/internship_menus.xml',

        # Rapports
        'reports/internship_reports.xml',
        'reports/convention_report_template.xml',
    ],

    # Fichiers de démonstration (optionnel)
    'demo': [
        'demo/internship_demo.xml',
    ],

    # Assets (CSS/JS) - pour l'interface web
    'assets': {
        'web.assets_backend': [
            'internship_management/static/src/css/internship.css',
            'internship_management/static/src/js/internship_dashboard.js',
        ],
        'web.assets_frontend': [
            'internship_management/static/src/css/portal_internship.css',
        ],
    },

    # Configuration du module
    'installable': True,  # Le module peut être installé
    'application': True,  # C'est une application principale (apparaît dans le menu Apps)
    'auto_install': False,  # Ne s'installe pas automatiquement
    'sequence': 10,  # Ordre d'apparition dans la liste des apps

    # Images du module
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],

    # Version minimum d'Odoo supportée
    'odoo_version': '17.0',
}