# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InternshipSupervisor(models.Model):
    _name = 'internship.supervisor'
    _description = 'Encadrant de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nom complet', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Utilisateur associé', ondelete='restrict')
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Téléphone')

    # Informations professionnelles
    company_id = fields.Many2one(
        'res.company',
        string='Entreprise',
        required=True,
        default=lambda self: self.env.company,
    )
    department = fields.Char(string='Département', required=True)
    position = fields.Char(string='Poste', required=True)
    # CORRIGÉ: Utiliser internship.area au lieu de internship.expertise
    expertise = fields.Many2many('internship.area', string='Domaines d\'expertise')

    # Gestion des stages
    stage_ids = fields.One2many('internship.stage', 'supervisor_id', string='Stages encadrés')
    max_students = fields.Integer(string='Nombre max de stagiaires', default=3)
    current_students_count = fields.Integer(compute='_compute_current_students')
    availability = fields.Selection([
        ('available', 'Disponible'),
        ('busy', 'Occupé'),
        ('unavailable', 'Indisponible')
    ], string='Disponibilité', default='available', tracking=True)

    # Photo et statut
    image = fields.Binary(string='Photo', attachment=True)
    active = fields.Boolean(default=True, string='Actif')

    # Champs calculés
    stage_count = fields.Integer(compute='_compute_stage_count', string='Nombre de stages encadrés')

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for supervisor in self:
            supervisor.stage_count = len(supervisor.stage_ids)

    @api.depends('stage_ids')
    def _compute_current_students(self):
        for supervisor in self:
            supervisor.current_students_count = len(
                supervisor.stage_ids.filtered(
                    lambda s: s.state in ['approved', 'in_progress']
                )
            )

    @api.onchange('current_students_count', 'max_students')
    def _onchange_students_count(self):
        if self.current_students_count >= self.max_students:
            self.availability = 'busy'