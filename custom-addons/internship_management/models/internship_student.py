# -*- coding: utf-8 -*-
"""
Modèle pour la gestion des Étudiants Stagiaires.
"""

import logging

from psycopg2 import errors

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipStudent(models.Model):
    """Modèle Étudiant pour le système de gestion des stages.

    Ce modèle gère toutes les informations relatives à un étudiant, y compris
    ses détails personnels, son parcours académique et son historique de stages.
    """
    _name = 'internship.student'
    _description = 'Étudiant Stagiaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'full_name'
    _rec_name = 'full_name'

    # ===============================
    # CHAMPS D'INFORMATIONS PERSONNELLES
    # ===============================

    full_name = fields.Char(
        string='Nom complet',
        required=True,
        tracking=True,
        size=100,
        help="Nom complet de l'étudiant."
    )

    # AMÉLIORATION: Utilisation de champs 'related' pour garantir la cohérence
    # des données entre l'étudiant et son compte utilisateur.
    user_id = fields.Many2one(
        'res.users',
        string='Compte utilisateur',
        ondelete='restrict',  # Bonne pratique: empêche la suppression d'un utilisateur lié à un étudiant
        help="Compte utilisateur associé pour l'accès au système."
    )

    email_from_user = fields.Char(
        related='user_id.login',
        string='Adresse e-mail',
        readonly=True,
        store=True,
        help="Adresse e-mail principale pour la communication, liée au compte utilisateur."
    )

    phone = fields.Char(
        related='user_id.phone',
        string='Numéro de téléphone',
        readonly=False,  # Permet de modifier le tel de l'étudiant et que ca modifie celui de l'user
        size=20,
        help="Numéro de téléphone principal, lié au compte utilisateur."
    )

    # Champ technique pour la création initiale
    email = fields.Char(
        string='Email (pour création)',
        help="Utilisé uniquement pour créer le compte utilisateur initial."
    )

    birth_date = fields.Date(
        string='Date de naissance',
        help="Date de naissance de l'étudiant."
    )

    linkedin_profile = fields.Char(
        string='Profil LinkedIn',
        help="URL du profil LinkedIn de l'étudiant."
    )

    cv_document = fields.Binary(
        string='CV',
        attachment=True,
        help="Téléverser le curriculum vitae de l'étudiant."
    )
    # AMÉLIORATION: Ajout du champ pour le nom du fichier, nécessaire pour la vue.
    cv_document_filename = fields.Char(string="Nom du fichier CV")

    profile_image = fields.Image(
        string='Photo de profil',
        max_width=1920,
        max_height=1920,
        help="Photo de profil de l'étudiant."
    )

    # ===============================
    # CHAMPS D'INFORMATIONS ACADÉMIQUES
    # ===============================

    institution = fields.Char(
        string='Établissement d\'enseignement',
        required=False,
        size=100,
        help="Nom de l'école, de l'université ou du collège."
    )

    education_level = fields.Selection([
        ('bachelor_1', 'Licence 1'),
        ('bachelor_2', 'Licence 2'),
        ('bachelor_3', 'Licence 3'),
        ('engineer', 'Cycle Ingénieur'),
        ('master_1', 'Master 1'),
        ('master_2', 'Master 2'),
        ('phd', 'Doctorat')
    ], string='Niveau d\'études')

    field_of_study = fields.Char(
        string='Domaine d\'études',
        required=False,
        size=100,
        help="Matière principale ou spécialisation."
    )

    student_id_number = fields.Char(
        string='Numéro d\'étudiant',
        size=20,
        help="Numéro d'identification officiel de l'étudiant."
    )

    expected_graduation_date = fields.Date(
        string='Date de diplomation prévue',
        help="Date prévue pour l'obtention du diplôme."
    )

    # ===============================
    # CHAMPS RELATIONNELS
    # ===============================

    internship_ids = fields.Many2many(
        'internship.stage',
        'internship_student_stage_rel',  # relation (table intermédiaire)
        'student_id',
        'stage_id',

        string='Stages',
        help="Tous les stages associés à cet étudiant."
    )

    skill_ids = fields.Many2many(
        'internship.skill',
        'internship_student_skill_rel',  # relation (table intermédiaire)
        'student_id',                    # column1
        'skill_id',                      # column2
        string='Compétences',
        help="Compétences techniques et générales de l'étudiant."
    )

    interest_area_ids = fields.Many2many(
        'internship.area',
        'internship_student_area_rel',  # relation (table intermédiaire)
        'student_id',                   # column1
        'area_id',                      # column2
        string='Centres d\'intérêt',
        help="Domaines dans lesquels l'étudiant souhaite effectuer un stage."
    )

    document_ids = fields.One2many(
        'internship.document',
        'student_id',
        string='Documents',
        help="Tous les documents téléversés par ou pour cet étudiant."
    )

    presentation_ids = fields.One2many(
        'internship.presentation',
        'student_id',
        string='Présentations',
        help="Toutes les présentations soumises par cet étudiant."
    )
    # ===============================
    # CHAMPS CALCULÉS
    # ===============================

    internship_count = fields.Integer(
        string='Nombre de stages',
        compute='_compute_internship_count',
        store=True,
        help="Nombre total de stages pour cet étudiant."
    )

    presentation_count = fields.Integer(
        string='Nombre de présentations',
        compute='_compute_presentation_count',
        store=True,
        help="Nombre total de présentations soumises."
    )

    average_grade = fields.Float(
        string='Note moyenne',
        compute='_compute_average_grade',
        digits=(4, 2),
        help="Note moyenne de tous les stages terminés."
    )

    completion_rate = fields.Float(
        string='Taux de complétion',
        compute='_compute_completion_rate',
        help="Taux de complétion global de tous les stages."
    )

    @api.depends('internship_ids')
    def _compute_internship_count(self):
        """Calcule le nombre total de stages pour cet étudiant."""
        for student in self:
            student.internship_count = len(student.internship_ids)

    @api.depends('internship_ids.final_grade')
    def _compute_average_grade(self):
        """Calcule la note moyenne de tous les stages terminés."""
        for student in self:
            completed_internships = student.internship_ids.filtered(lambda i: i.final_grade > 0)
            if completed_internships:
                total_grade = sum(completed_internships.mapped('final_grade'))
                student.average_grade = total_grade / len(completed_internships)
            else:
                student.average_grade = 0.0

    @api.depends('internship_ids.completion_percentage')
    def _compute_completion_rate(self):
        """Calcule le taux de complétion moyen de tous les stages."""
        for student in self:
            active_internships = student.internship_ids.filtered(lambda i: i.state != 'cancelled')
            if active_internships:
                total_progress = sum(active_internships.mapped('completion_percentage'))
                student.completion_rate = total_progress / len(active_internships)
            else:
                student.completion_rate = 0.0

    @api.depends('presentation_ids')
    def _compute_presentation_count(self):
        """Calcule le nombre total de présentations soumises par l'étudiant."""
        for student in self:
            student.presentation_count = len(student.presentation_ids)

    # ===============================
    # CHAMPS TECHNIQUES
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Actif',
        help="Indique si cet enregistrement d'étudiant est actif."
    )

    # ===============================
    # CONTRAINTES ET VALIDATIONS
    # ===============================

    @api.constrains('birth_date')
    def _check_birth_date(self):
        """Vérifie que la date de naissance est plausible."""
        for student in self:
            if student.birth_date and student.birth_date > fields.Date.today():
                raise ValidationError(_("La date de naissance ne peut pas être dans le futur."))

    # NOTE: Les contraintes sur l'email et le numéro de téléphone ne sont plus nécessaires ici
    # car ces champs sont maintenant liés au modèle res.users, qui a ses propres validations.

    _sql_constraints = [
        ('unique_user_id', 'UNIQUE(user_id)',
         'Ce compte utilisateur est déjà associé à un autre étudiant.'),
        ('unique_student_id', 'UNIQUE(student_id_number)',
         'Ce numéro d\'étudiant est déjà utilisé.'),
    ]

    # ===============================
    # MÉTHODES CRUD (Create, Read, Update, Delete)
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode 'create' pour la journalisation et la création automatique d'utilisateurs."""
        _logger.info(f"Création de {len(vals_list)} enregistrement(s) étudiant(s)")

        for vals in vals_list:
            # Crée automatiquement un compte utilisateur si un email est fourni et qu'aucun utilisateur n'est lié
            if vals.get('email') and not vals.get('user_id'):
                user_vals = {
                    'name': vals.get('full_name', 'Étudiant'),
                    'login': vals['email'],
                    'email': vals['email'],
                    'groups_id': [(4, self.env.ref('internship_management.group_internship_student').id)]
                }
                try:
                    user = self.env['res.users'].create(user_vals)
                    vals['user_id'] = user.id
                    _logger.info(f"Compte utilisateur créé pour l'étudiant : {vals['email']}")
                except errors.UniqueViolation:
                    _logger.warning(f"Un utilisateur avec l'email {vals['email']} existe déjà.")
                    # Vous pourriez ici rechercher l'utilisateur existant et le lier
                except Exception as e:
                    _logger.error(f"Impossible de créer le compte utilisateur : {e}")

        # On ne veut pas stocker l'email technique
        for vals in vals_list:
            vals.pop('email', None)

        return super().create(vals_list)

    # ===============================
    # MÉTHODES MÉTIER
    # ===============================

    def action_view_internships(self):
        """Ouvre la liste des stages de l'étudiant dans une nouvelle vue."""
        self.ensure_one()
        return {
            'name': _('Stages - %s') % self.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 'internship.stage',
            'view_mode': 'tree,form,kanban',
            'domain': [('student_ids', 'in', [self.id])],
            'context': {},
        }

    # ===============================
    # MÉTHODES UTILITAIRES
    # ===============================

    def name_get(self):
        """Affichage personnalisé du nom : Nom Complet (Établissement)."""
        result = []
        for student in self:
            name = student.full_name
            if student.institution:
                name = f"{name} ({student.institution})"
            result.append((student.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        """Recherche personnalisée : par nom, e-mail ou numéro d'étudiant."""
        args = args or []
        domain = []
        if name:
            domain = ['|', '|',
                      ('full_name', operator, name),
                      ('email_from_user', operator, name),
                      ('student_id_number', operator, name)]
        return self._search(domain + args, limit=limit, order=order)
