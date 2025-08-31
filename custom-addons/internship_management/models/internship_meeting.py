# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta


class InternshipMeeting(models.Model):
    _name = 'internship.meeting'
    _description = 'Réunion de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    # Champs de base
    name = fields.Char(string='Titre', required=True, tracking=True)
    stage_id = fields.Many2one('internship.stage', string='Stage', required=True, tracking=True)
    date = fields.Datetime(string='Date et heure', required=True, tracking=True)
    duration = fields.Float(string='Durée (heures)', default=1.0, tracking=True)
    
    # Type de réunion
    type = fields.Selection([
        ('kickoff', 'Réunion de lancement'),
        ('followup', 'Suivi hebdomadaire'),
        ('milestone', 'Point d\'étape'),
        ('defense', 'Soutenance'),
        ('evaluation', 'Évaluation'),
        ('other', 'Autre')
    ], string='Type', default='followup', tracking=True)

    # Participants
    organizer_id = fields.Many2one('res.users', string='Organisateur', 
                                   default=lambda self: self.env.user, tracking=True)
    participant_ids = fields.Many2many('res.users', string='Participants', tracking=True)
    
    # Lieu et modalité
    location = fields.Char(string='Lieu', tracking=True)
    meeting_type = fields.Selection([
        ('physical', 'Présentiel'),
        ('virtual', 'Virtuel'),
        ('hybrid', 'Hybride')
    ], string='Modalité', default='virtual', tracking=True)
    
    # Contenu et suivi
    agenda = fields.Html(string='Ordre du jour', tracking=True)
    summary = fields.Html(string='Compte-rendu', tracking=True)
    next_actions = fields.Html(string='Actions à suivre', tracking=True)
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
    # Notifications
    reminder_sent = fields.Boolean(string='Rappel envoyé', default=False)
    reminder_date = fields.Datetime(string='Date de rappel')
    
    # Champs calculés
    end_date = fields.Datetime(string='Fin', compute='_compute_end_date', store=True)
    is_past = fields.Boolean(string='Passé', compute='_compute_is_past', store=True)
    is_today = fields.Boolean(string='Aujourd\'hui', compute='_compute_is_today', store=True)
    
    # Relations
    document_ids = fields.One2many('internship.document', 'meeting_id', string='Documents')
    
    # Champs techniques
    active = fields.Boolean(default=True, string='Actif')

    @api.depends('date', 'duration')
    def _compute_end_date(self):
        for meeting in self:
            if meeting.date and meeting.duration:
                meeting.end_date = meeting.date + timedelta(hours=meeting.duration)
            else:
                meeting.end_date = False

    @api.depends('date')
    def _compute_is_past(self):
        for meeting in self:
            meeting.is_past = meeting.date and meeting.date < datetime.now()

    @api.depends('date')
    def _compute_is_today(self):
        for meeting in self:
            if meeting.date:
                meeting.is_today = meeting.date.date() == datetime.now().date()
            else:
                meeting.is_today = False

    @api.model
    def create(self, vals):
        """Créer une réunion et envoyer des notifications"""
        meeting = super().create(vals)
        
        # Ajouter automatiquement les participants principaux
        if meeting.stage_id:
            participants = []
            if meeting.stage_id.student_id.user_id:
                participants.append(meeting.stage_id.student_id.user_id.id)
            if meeting.stage_id.supervisor_id.user_id:
                participants.append(meeting.stage_id.supervisor_id.user_id.id)
            
            if participants:
                meeting.participant_ids = [(6, 0, participants)]
        
        return meeting

    def action_confirm(self):
        """Confirmer la réunion"""
        self.write({'state': 'confirmed'})
        return True

    def action_start(self):
        """Démarrer la réunion"""
        self.write({'state': 'in_progress'})
        return True

    def action_complete(self):
        """Terminer la réunion"""
        self.write({'state': 'completed'})
        return True

    def action_cancel(self):
        """Annuler la réunion"""
        self.write({'state': 'cancelled'})
        return True

    def action_send_reminder(self):
        """Envoyer un rappel aux participants"""
        for meeting in self:
            # Logique d'envoi de rappel
            meeting.reminder_sent = True
            meeting.reminder_date = datetime.now()
        return True

    def action_generate_report(self):
        """Générer un rapport de réunion"""
        # Logique de génération de rapport
        return True
