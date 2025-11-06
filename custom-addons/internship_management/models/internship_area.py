# -*- coding: utf-8 -*-
"""
Modèle pour la gestion des Domaines d'Expertise de stage.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InternshipArea(models.Model):
    """Modèle Domaine d'expertise pour la gestion des stages.

    Ce modèle gère les différents domaines d'expertise dans lesquels les stages
    peuvent être menés, aidant à catégoriser et organiser les opportunités de stage.

    Fonctionnalités clés :
    - Structure hiérarchique des domaines (relations parent/enfant)
    - Association avec les compétences requises
    - Cartographie de l'expertise des encadrants
    - Catégorisation des stages
    """
    _name = 'internship.area'
    _description = 'Domaine d\'Expertise de Stage'
    _order = 'parent_id, sequence, name'
    _rec_name = 'name'

    # ===============================
    # CHAMPS D'IDENTIFICATION PRINCIPAUX
    # ===============================

    name = fields.Char(
        string='Nom du domaine',
        required=True,
        help="Nom du domaine d'expertise (ex: Développement Logiciel, Marketing)."
    )

    code = fields.Char(
        string='Code du domaine',
        size=20,
        help="Code court pour le domaine (ex: DEVLOG, MKTG)."
    )

    # ===============================
    # STRUCTURE HIÉRARCHIQUE
    # ===============================

    parent_id = fields.Many2one(
        'internship.area',
        string='Domaine parent',
        ondelete='cascade',
        help="Domaine parent dans la hiérarchie."
    )

    child_ids = fields.One2many(
        'internship.area',
        'parent_id',
        string='Sous-domaines',
        help="Sous-domaines appartenant à celui-ci."
    )

    level = fields.Integer(
        string='Niveau',
        compute='_compute_level',
        store=True,
        recursive=True,
        help="Niveau dans la hiérarchie (0 pour les domaines racines)."
    )

    @api.depends('parent_id.level')
    def _compute_level(self):
        """Calcule le niveau hiérarchique."""
        for area in self:
            area.level = area.parent_id.level + 1 if area.parent_id else 0

    # ===============================
    # DESCRIPTION ET MÉTADONNÉES
    # ===============================

    description = fields.Text(
        string='Description',
        help="Description détaillée de ce domaine d'expertise."
    )

    # ===============================
    # CHAMPS RELATIONNELS
    # ===============================

    skill_ids = fields.Many2many(
        'internship.skill',
        string='Compétences requises',
        help="Compétences généralement nécessaires dans ce domaine."
    )

    supervisor_ids = fields.Many2many(
        'internship.supervisor',
        'supervisor_area_rel', 'area_id', 'supervisor_id',
        string='Encadrants experts',
        help="Encadrants ayant une expertise dans ce domaine."
    )

    internship_ids = fields.One2many(
        'internship.stage',
        'area_id',
        string='Stages',
        help="Stages menés dans ce domaine."
    )

    # ===============================
    # CHAMPS CALCULÉS
    # ===============================

    internship_count = fields.Integer(
        string='Nombre de stages',
        compute='_compute_internship_count',
        store=True,
        help="Nombre de stages dans ce domaine."
    )

    @api.depends('internship_ids')
    def _compute_internship_count(self):
        """Calcule le nombre de stages dans ce domaine."""
        for area in self:
            area.internship_count = len(area.internship_ids)

    # ===============================
    # CHAMPS TECHNIQUES
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Actif',
        help="Indique si ce domaine est actuellement disponible."
    )

    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre d'affichage des domaines dans les listes."
    )

    color = fields.Integer(string='Couleur')

    # ===============================
    # CONTRAINTES ET VALIDATIONS
    # ===============================

    @api.constrains('parent_id')
    def _check_no_circular_hierarchy(self):
        """Empêche les relations hiérarchiques circulaires."""
        if not self._check_recursion():
            raise ValidationError(_('Erreur ! Vous ne pouvez pas créer de hiérarchie circulaire.'))

    _sql_constraints = [
        ('unique_area_name', 'UNIQUE(name)',
         'Un domaine avec ce nom existe déjà.'),
        ('unique_area_code', 'UNIQUE(code)',
         'Un domaine avec ce code existe déjà.'),
    ]
