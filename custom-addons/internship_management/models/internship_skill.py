# -*- coding: utf-8 -*-
"""
Modèle pour la gestion des Compétences de stage.
"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipSkill(models.Model):
    """Modèle Compétence pour le système de gestion des stages.

    Ce modèle gère les compétences techniques et générales (soft skills) qui peuvent être
    associées aux étudiants, aux encadrants et aux exigences des stages.

    Fonctionnalités clés :
    - Catégorisation des compétences (technique, soft skill, langue, etc.)
    - Gestion du niveau de difficulté
    - Suivi des certifications
    - Relations de prérequis entre compétences
    """
    _name = 'internship.skill'
    _description = 'Gestion des Compétences de Stage'
    _order = 'category, sequence, name'
    _rec_name = 'name'

    # ===============================
    # CHAMPS D'IDENTIFICATION PRINCIPAUX
    # ===============================

    name = fields.Char(
        string='Nom de la compétence',
        required=True,
        help="Nom de la compétence (ex: Python, Communication, Anglais)."
    )

    code = fields.Char(
        string='Code de la compétence',
        size=20,
        help="Code court pour la compétence (ex: PYTHON, COMM, ENG)."
    )

    # ===============================
    # CHAMPS DE CLASSIFICATION
    # ===============================

    category = fields.Selection([
        ('technical', 'Technique'),
        ('soft', 'Soft Skill'),
        ('language', 'Langue'),
        ('certification', 'Certification'),
        ('other', 'Autre')
    ], string='Catégorie', required=True, default='technical',
        help="Catégorie à laquelle cette compétence appartient.")

    level_required = fields.Selection([
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert')
    ], string='Niveau de maîtrise requis', default='intermediate',
        help="Niveau de maîtrise minimum attendu pour cette compétence.")

    difficulty_level = fields.Selection([
        ('1', 'Très Facile'),
        ('2', 'Facile'),
        ('3', 'Moyen'),
        ('4', 'Difficile'),
        ('5', 'Très Difficile')
    ], string='Difficulté d\'apprentissage', default='3',
        help="Niveau de difficulté pour acquérir cette compétence.")

    # ===============================
    # CHAMPS DE CERTIFICATION
    # ===============================

    is_certification = fields.Boolean(
        string='Est une certification',
        default=False,
        help="Cochez si cette compétence est validée par une certification."
    )

    certification_provider = fields.Char(
        string='Organisme de certification',
        help="Organisation qui délivre la certification."
    )

    certification_validity_months = fields.Integer(
        string='Validité de la certification (mois)',
        help="Durée de validité de la certification en mois."
    )

    # ===============================
    # DESCRIPTION ET MÉTADONNÉES
    # ===============================

    description = fields.Text(
        string='Description',
        help="Description détaillée de la compétence et de ses applications."
    )

    prerequisites = fields.Text(
        string='Prérequis (texte libre)',
        help="Compétences ou connaissances requises non listées (ex: 'Bac+3 en informatique')."
    )

    # ===============================
    # CHAMPS RELATIONNELS
    # ===============================

    prerequisite_skill_ids = fields.Many2many(
        'internship.skill',
        'skill_prerequisite_rel',
        'skill_id', 'prerequisite_id',
        string='Compétences prérequises',
        help="Compétences qui doivent être maîtrisées avant celle-ci."
    )

    related_area_ids = fields.Many2many(
        'internship.area',
        string='Domaines liés',
        help="Domaines d'expertise où cette compétence est couramment utilisée."
    )

    # ===============================
    # CHAMPS TECHNIQUES
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Actif',
        help="Indique si cette compétence est actuellement disponible."
    )

    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre d'affichage des compétences dans les listes."
    )

    # ===============================
    # CONTRAINTES ET VALIDATIONS
    # ===============================

    @api.constrains('certification_validity_months')
    def _check_certification_validity(self):
        """S'assure que la durée de validité de la certification est positive."""
        for skill in self:
            if skill.is_certification and skill.certification_validity_months <= 0:
                raise ValidationError(_("La validité de la certification doit être un nombre positif de mois."))

    @api.constrains('prerequisite_skill_ids')
    def _check_no_circular_prerequisites(self):
        """Empêche les relations de prérequis circulaires."""
        for skill in self:
            if skill in skill.prerequisite_skill_ids:
                raise ValidationError(_("Une compétence ne peut pas être un prérequis d'elle-même."))

    _sql_constraints = [
        ('unique_skill_name', 'UNIQUE(name)',
         'Une compétence avec ce nom existe déjà.'),
        ('unique_skill_code', 'UNIQUE(code)',
         'Une compétence avec ce code existe déjà.'),
    ]
