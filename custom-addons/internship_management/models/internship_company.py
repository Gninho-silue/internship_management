# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InternshipCompany(models.Model):
    _name = 'internship.company'
    _description = 'Entreprise d\'Accueil'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nom de l\'entreprise', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Contact associé', ondelete='restrict')

    # Informations de l'entreprise
    industry = fields.Char(string='Secteur d\'activité')
    size = fields.Selection([
        ('small', 'Petite (<50 employés)'),
        ('medium', 'Moyenne (50-250 employés)'),
        ('large', 'Grande (>250 employés)')
    ], string='Taille')
    website = fields.Char(string='Site web')

    # Adresse
    street = fields.Char(string='Rue')
    city = fields.Char(string='Ville')
    zip = fields.Char(string='Code postal')
    country_id = fields.Many2one('res.country', string='Pays')

    # Contact principal
    contact_name = fields.Char(string='Nom du contact')
    contact_email = fields.Char(string='Email du contact')
    contact_phone = fields.Char(string='Téléphone du contact')

    # Relations
    stage_ids = fields.One2many('internship.stage', 'company_id', string='Stages proposés')
    supervisor_ids = fields.One2many('internship.supervisor', 'company_id', string='Encadrants')
    
    # Champs calculés
    stage_count = fields.Integer(compute='_compute_stage_count', string='Nombre de stages')
    rating = fields.Float(string='Note moyenne', compute='_compute_rating')
    
    # Gestion des stages
    internship_capacity = fields.Integer(string='Capacité d\'accueil stagiaires')
    agreement_signed = fields.Boolean(string='Convention signée', tracking=True)

    # Logo et statut
    logo = fields.Binary(string='Logo', attachment=True)
    active = fields.Boolean(default=True, string='Actif')

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for company in self:
            company.stage_count = len(company.stage_ids)

    @api.depends('stage_ids.grade')
    def _compute_rating(self):
        for company in self:
            stages = company.stage_ids.filtered(lambda s: s.grade > 0)
            company.rating = sum(stages.mapped('grade')) / len(stages) if stages else 0.0