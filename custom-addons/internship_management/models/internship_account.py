# -*- coding: utf-8 -*-
"""
Modèle pour la gestion des comptes externes liés aux stages.
Ce modèle gère les comptes/adresses externes (GitHub, GitLab, etc.) associés à un stage.
"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipAccount(models.Model):
    """
    Modèle de Compte Externe pour le système de gestion des stages.
    
    Ce modèle gère les comptes externes (adresses, URLs, etc.) associés
    à un stage, comme les comptes GitHub, GitLab, ou autres services.
    """
    _name = 'internship.account'
    _description = 'Compte Externe de Stage'
    _order = 'name'

    # ===============================
    # CHAMPS PRINCIPAUX
    # ===============================

    name = fields.Char(
        string='Nom du Compte',
        required=True,
        help="Nom ou identifiant du compte (ex: GitHub, GitLab, etc.)."
    )

    stage_id = fields.Many2one(
        'internship.stage',
        string='Stage',
        required=True,
        ondelete='cascade',
        help="Stage associé à ce compte."
    )

    # ===============================
    # INFORMATIONS DU COMPTE
    # ===============================

    address = fields.Char(
        string='Adresse/URL',
        required=True,
        help="Adresse complète ou URL du compte (ex: https://github.com/username/repo)."
    )

    account_type = fields.Selection([
        ('github', 'GitHub'),
        ('gitlab', 'GitLab'),
        ('bitbucket', 'Bitbucket'),
        ('other', 'Autre')
    ], string='Type de Compte', default='other',
        help="Type de compte ou service externe.")

    # ===============================
    # DESCRIPTION
    # ===============================

    description = fields.Text(
        string='Description',
        help="Description ou notes supplémentaires sur ce compte."
    )

    # ===============================
    # STATUT
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Actif',
        help="Indique si ce compte est actif."
    )

