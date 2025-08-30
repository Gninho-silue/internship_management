# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InternshipConversation(models.Model):
    _name = 'internship.conversation'
    _description = 'Conversation entre acteurs'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'last_message_date desc'

    # Champs de base
    name = fields.Char(string='Sujet de la conversation', required=True, tracking=True)
    description = fields.Text(string='Description')

    # Participants
    participant_ids = fields.Many2many('res.users', string='Participants', required=True)
    creator_id = fields.Many2one('res.users', string='Créateur', required=True,
                                 default=lambda self: self.env.user)

    # Relations
    stage_id = fields.Many2one('internship.stage', string='Stage lié')
    company_id = fields.Many2one('internship.company', string='Entreprise liée')

    # Messages
    message_ids = fields.One2many('internship.message', 'conversation_id', string='Messages')
    message_count = fields.Integer(string='Nombre de messages', compute='_compute_message_count')

    # Métadonnées
    conversation_type = fields.Selection([
        ('general', 'Général'),
        ('stage', 'Stage'),
        ('document', 'Document'),
        ('meeting', 'Réunion')
    ], string='Type', default='general', tracking=True)

    state = fields.Selection([
        ('active', 'Active'),
        ('archived', 'Archivée'),
        ('closed', 'Fermée')
    ], string='État', default='active', tracking=True)

    # Champs calculés
    last_message_date = fields.Datetime(string='Dernier message',
                                        compute='_compute_last_message_date', store=True)

    # Champs techniques
    active = fields.Boolean(default=True, string='Actif')

    @api.depends('message_ids')
    def _compute_message_count(self):
        for conversation in self:
            conversation.message_count = len(conversation.message_ids)

    @api.depends('message_ids.create_date')
    def _compute_last_message_date(self):
        for conversation in self:
            if conversation.message_ids:
                conversation.last_message_date = max(conversation.message_ids.mapped('create_date'))
            else:
                conversation.last_message_count = conversation.create_date

    def action_archive(self):
        """Archiver la conversation"""
        self.write({'state': 'archived'})
        return True

    def action_close(self):
        """Fermer la conversation"""
        self.write({'state': 'closed'})
        return True