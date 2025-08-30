# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class InternshipNotification(models.Model):
    _name = 'internship.notification'
    _description = 'Notification de stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Champs de base
    title = fields.Char(string='Titre', required=True, tracking=True)
    message = fields.Text(string='Message', required=True, tracking=True)
    
    # Destinataire
    user_id = fields.Many2one('res.users', string='Destinataire', required=True, tracking=True)
    
    # Type de notification
    notification_type = fields.Selection([
        ('deadline', 'Échéance'),
        ('reminder', 'Rappel'),
        ('approval', 'Approbation'),
        ('alert', 'Alerte'),
        ('info', 'Information')
    ], string='Type', default='info', tracking=True)
    
    # Priorité
    priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Urgente')
    ], string='Priorité', default='1', tracking=True)
    
    # État
    state = fields.Selection([
        ('unread', 'Non lu'),
        ('read', 'Lu'),
        ('archived', 'Archivé')
    ], string='État', default='unread', tracking=True)
    
    # Relations
    stage_id = fields.Many2one('internship.stage', string='Stage lié')
    document_id = fields.Many2one('internship.document', string='Document lié')
    message_id = fields.Many2one('internship.message', string='Message lié')
    
    # Métadonnées
    action_url = fields.Char(string='URL d\'action')
    due_date = fields.Datetime(string='Date d\'échéance')
    
    # Champs calculés
    is_recipient = fields.Boolean(string='Mon notification', compute='_compute_is_recipient')
    
    # Champs techniques
    active = fields.Boolean(default=True, string='Actif')

    @api.depends('user_id')
    def _compute_is_recipient(self):
        for notification in self:
            notification.is_recipient = notification.user_id == self.env.user

    def action_mark_as_read(self):
        """Marquer comme lu"""
        self.write({'state': 'read'})
        return True

    def action_archive(self):
        """Archiver la notification"""
        self.write({'state': 'archived'})
        return True

    def action_view_related(self):
        """Voir l'objet lié"""
        if self.stage_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'internship.stage',
                'res_id': self.stage_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        elif self.document_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'internship.document',
                'res_id': self.document_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return True

    @api.model
    def create_notification(self, title, message, user_id, notification_type='info', 
                          priority='1', stage_id=None, document_id=None, message_id=None):
        """Créer une notification programmatiquement"""
        return self.create({
            'title': title,
            'message': message,
            'user_id': user_id,
            'notification_type': notification_type,
            'priority': priority,
            'stage_id': stage_id,
            'document_id': document_id,
            'message_id': message_id,
        })
