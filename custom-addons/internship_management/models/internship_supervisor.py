# -*- coding: utf-8 -*-
"""
Modèle pour la gestion des Encadrants de Stage.

Ce module gère les informations des encadrants pour le système de gestion des stages,
y compris la gestion de leur capacité, leurs domaines d'expertise et le suivi
de leur charge de travail.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InternshipSupervisor(models.Model):
    """Modèle Encadrant pour la gestion des stages.

    Ce modèle gère les encadrants qui guident les étudiants durant leurs stages.
    Il inclut leurs informations professionnelles, leurs domaines d'expertise,
    leur disponibilité et le suivi de leur charge de travail actuelle.

    Fonctionnalités clés :
    - Gestion de la capacité d'encadrement (nombre max d'étudiants)
    - Suivi des domaines d'expertise
    - Calcul automatique de la disponibilité
    - Suivi de la charge de travail
    - Intégration avec les comptes utilisateurs
    """
    _name = 'internship.supervisor'
    _description = 'Gestion des Encadrants de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ===============================
    # CHAMPS D'IDENTIFICATION PRINCIPAUX
    # ===============================

    name = fields.Char(
        string='Nom complet',
        required=True,
        tracking=True,
        help="Nom complet de l'encadrant."
    )

    user_id = fields.Many2one(
        'res.users',
        string='Compte utilisateur',
        ondelete='restrict',
        help="Compte utilisateur associé pour l'accès au système."
    )

    # AMÉLIORATION: Utilisation de champs 'related' pour la cohérence des données.
    email = fields.Char(
        related='user_id.login',
        string='Adresse e-mail',
        readonly=True,
        store=True,
        help="Adresse e-mail principale, liée au compte utilisateur."
    )

    phone = fields.Char(
        related='user_id.phone',
        string='Numéro de téléphone',
        readonly=False,  # Permet la modification depuis cette vue
        help="Numéro de téléphone principal, lié au compte utilisateur."
    )

    # ===============================
    # INFORMATIONS PROFESSIONNELLES
    # ===============================

    company_id = fields.Many2one(
        'res.company',
        string='Entreprise',
        default=lambda self: self.env.company,
        readonly=True,
        help="Entreprise de l'encadrant (par défaut, la société actuelle)."
    )

    department = fields.Char(
        string='Département',
        help="Département ou division au sein de l'organisation."
    )

    position = fields.Char(
        string='Poste',
        help="Titre du poste ou fonction professionnelle."
    )

    expertise_area_ids = fields.Many2many(
        'internship.area',
        string="Domaines d'expertise",
        help="Domaines professionnels où l'encadrant peut offrir son expertise."
    )

    # ===============================
    # GESTION DES STAGES
    # ===============================

    stage_ids = fields.One2many(
        'internship.stage',
        'supervisor_id',
        string='Stages encadrés',
        help="Tous les stages supervisés par cette personne."
    )

    max_students = fields.Integer(
        string='Capacité d\'accueil (étudiants)',
        default=3,
        help="Nombre maximum d'étudiants que cet encadrant peut superviser simultanément."
    )

    current_students_count = fields.Integer(
        string='Étudiants actuels',
        compute='_compute_current_students_count',
        store=True,
        help="Nombre d'étudiants actuellement en cours d'encadrement."
    )

    @api.depends('stage_ids.state')
    def _compute_current_students_count(self):
        """Calcule le nombre d'étudiants activement supervisés."""
        for supervisor in self:
            active_stages = supervisor.stage_ids.filtered(
                lambda s: s.state in ['approved', 'in_progress']
            )
            supervisor.current_students_count = len(active_stages)

    # BONNE PRATIQUE: Remplacer l'@api.onchange par un champ calculé pour la robustesse.
    # L'inverse permet de modifier manuellement la valeur si nécessaire.
    availability = fields.Selection([
        ('available', 'Disponible'),
        ('busy', 'Occupé'),
        ('unavailable', 'Indisponible')
    ], string='Statut de disponibilité',
        default='available',
        compute='_compute_availability',
        inverse='_inverse_availability',
        store=True,
        tracking=True,
        help="Disponibilité actuelle pour de nouvelles affectations de stage.")

    @api.depends('current_students_count', 'max_students')
    def _compute_availability(self):
        """Met à jour automatiquement la disponibilité en fonction de la charge de travail."""
        for supervisor in self:
            if supervisor.current_students_count >= supervisor.max_students:
                supervisor.availability = 'busy'
            else:
                supervisor.availability = 'available'

    def _inverse_availability(self):
        """Méthode inverse pour permettre la modification manuelle du statut de disponibilité."""
        # Cette méthode est intentionnellement vide. Elle permet au champ 'compute'
        # d'être modifiable manuellement par l'utilisateur. La valeur sera recalculée
        # au prochain changement de dépendances.
        return

    # ===============================
    # PROFIL ET STATUT
    # ===============================

    # AMÉLIORATION: Utilisation de fields.Image pour une meilleure gestion des images.
    profile_image = fields.Image(
        string='Photo de profil',
        max_width=1920,
        max_height=1920,
        help="Photo de profil de l'encadrant."
    )

    active = fields.Boolean(
        default=True,
        string='Actif',
        help="Indique si cet enregistrement d'encadrant est actif."
    )

    # ===============================
    # CHAMPS CALCULÉS
    # ===============================

    stage_count = fields.Integer(
        string='Total des stages encadrés',
        compute='_compute_stage_count',
        store=True,
        help="Nombre total de stages (passés et présents) supervisés par cette personne."
    )

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        """Calcule le nombre total de stages supervisés."""
        for supervisor in self:
            supervisor.stage_count = len(supervisor.stage_ids)

    workload_percentage = fields.Float(
        string='Taux de charge',
        compute='_compute_workload_percentage',
        help="Charge de travail actuelle en pourcentage de la capacité maximale."
    )

    @api.depends('current_students_count', 'max_students')
    def _compute_workload_percentage(self):
        """Calcule le pourcentage de la charge de travail de l'encadrant."""
        for supervisor in self:
            if supervisor.max_students > 0:
                workload = (supervisor.current_students_count / supervisor.max_students) * 100
                supervisor.workload_percentage = min(workload, 100.0)
            else:
                supervisor.workload_percentage = 0.0

    # ===============================
    # CONTRAINTES ET VALIDATIONS
    # ===============================

    @api.constrains('max_students')
    def _check_max_students(self):
        """Vérifie que la capacité maximale d'accueil est un nombre positif."""
        for supervisor in self:
            if supervisor.max_students < 1:
                raise ValidationError(_("La capacité d'accueil doit être d'au moins 1."))

    # NOTE: La contrainte sur l'email est retirée car le champ est maintenant lié à res.users.

    # ===============================
    # MÉTHODES MÉTIER
    # ===============================

    def action_view_supervised_internships(self):
        """Ouvre la liste des stages supervisés dans une vue dédiée."""
        self.ensure_one()
        return {
            'name': _('Stages encadrés par %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'internship.stage',
            'view_mode': 'tree,form,kanban',
            'domain': [('supervisor_id', '=', self.id)],
            'context': {'default_supervisor_id': self.id},
        }

    # ===============================
    # MÉTHODES UTILITAIRES
    # ===============================

    def name_get(self):
        """Affichage personnalisé du nom : Nom (Département)."""
        result = []
        for supervisor in self:
            name = supervisor.name
            if supervisor.department:
                name = f"{name} ({supervisor.department})"
            result.append((supervisor.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        """Recherche personnalisée : par nom, e-mail, département ou poste."""
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|',
                      ('name', operator, name),
                      ('email', operator, name),
                      ('department', operator, name),
                      ('position', operator, name)]
        return self._search(domain + args, limit=limit, order=order)
