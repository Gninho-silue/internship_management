# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InternshipMessage(models.Model):
    _name = 'internship.message'
    _description = 'Message interne'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Champs de base
    subject = fields.Char(string='Sujet', required=True, tracking=True)
    body = fields.Html(string='Contenu', required=True, tracking=True)
    sender_id = fields.Many2one('res.users', string='Expéditeur', required=True,
                                default=lambda self: self.env.user)
    recipient_ids = fields.Many2many('res.users', string='Destinataires', required=True)

    # Relations (optionnelles)
    stage_id = fields.Many2one('internship.stage', string='Stage lié', required=False)
    document_id = fields.Many2one('internship.document', string='Document lié', required=False)

    # Métadonnées
    message_type = fields.Selection([
        ('internal', 'Interne'),
        ('notification', 'Notification'),
        ('reminder', 'Rappel')
    ], string='Type', default='internal', tracking=True)

    priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Urgente')
    ], string='Priorité', default='1', tracking=True)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('read', 'Lu'),
        ('archived', 'Archivé')
    ], string='État', default='draft', tracking=True)

    # Champs calculés
    is_read = fields.Boolean(string='Lu', compute='_compute_is_read', store=True)
    read_count = fields.Integer(string='Nombre de lecteurs', compute='_compute_read_count')

    # Champs techniques
    active = fields.Boolean(default=True, string='Actif')

    @api.depends('recipient_ids')
    def _compute_is_read(self):
        for message in self:
            message.is_read = self.env.user in message.recipient_ids

    @api.depends('recipient_ids')
    def _compute_read_count(self):
        for message in self:
            message.read_count = len(message.recipient_ids)

    def action_send(self):
        """Envoyer le message"""
        self.write({'state': 'sent'})
        return True

    def action_mark_as_read(self):
        """Marquer comme lu"""
        self.write({'state': 'read'})
        return True

    def action_archive(self):
        """Archiver le message"""
        self.write({'state': 'archived'})
        return True