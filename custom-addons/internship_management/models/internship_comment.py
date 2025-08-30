# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class InternshipComment(models.Model):
    _name = 'internship.comment'
    _description = 'Commentaire sur document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Champs de base
    content = fields.Html(string='Commentaire', required=True, tracking=True)
    author_id = fields.Many2one('res.users', string='Auteur', required=True,
                                default=lambda self: self.env.user)

    # Relations
    document_id = fields.Many2one('internship.document', string='Document', required=True)
    stage_id = fields.Many2one('internship.stage', string='Stage lié',
                               related='document_id.stage_id', store=True)

    # Métadonnées
    comment_type = fields.Selection([
        ('feedback', 'Feedback'),
        ('correction', 'Correction'),
        ('approval', 'Approbation'),
        ('rejection', 'Rejet'),
        ('question', 'Question')
    ], string='Type', default='feedback', tracking=True)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('resolved', 'Résolu'),
        ('archived', 'Archivé')
    ], string='État', default='draft', tracking=True)

    # Champs calculés
    is_author = fields.Boolean(string='Mon commentaire', compute='_compute_is_author')

    # Champs techniques
    active = fields.Boolean(default=True, string='Actif')

    @api.depends('author_id')
    def _compute_is_author(self):
        for comment in self:
            comment.is_author = comment.author_id == self.env.user

    def action_send(self):
        """Envoyer le commentaire"""
        self.write({'state': 'sent'})
        return True

    def action_resolve(self):
        """Marquer comme résolu"""
        self.write({'state': 'resolved'})
        return True

    def action_archive(self):
        """Archiver le commentaire"""
        self.write({'state': 'archived'})
        return True