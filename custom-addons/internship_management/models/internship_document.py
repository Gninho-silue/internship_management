# -*- coding: utf-8 -*-
from odoo import models, fields, api


class InternshipDocument(models.Model):
    _name = 'internship.document'
    _description = 'Document de stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', required=True)
    type = fields.Selection([
        ('convention', 'Convention'),
        ('rapport', 'Rapport'),
        ('presentation', 'Présentation'),
        ('evaluation', 'Évaluation'),
        ('autre', 'Autre')
    ], string='Type', required=True)

    # Relations
    stage_id = fields.Many2one('internship.stage', string='Stage')
    student_id = fields.Many2one('internship.student', string='Étudiant')

    # Document
    file = fields.Binary(string='Fichier', attachment=True, required=True)
    filename = fields.Char(string='Nom du fichier')

    # Métadonnées
    date_upload = fields.Datetime(string='Date d\'upload', default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté')
    ], string='État', default='draft', tracking=True)

    comments = fields.Text(string='Commentaires')
    active = fields.Boolean(default=True)

    @api.onchange('type')
    def _onchange_type(self):
        if self.type and not self.name:
            self.name = dict(self._fields['type'].selection).get(self.type)
