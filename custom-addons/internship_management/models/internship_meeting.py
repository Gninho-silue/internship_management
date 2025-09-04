# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


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
    email_sent = fields.Boolean(string='Email envoyé', default=False)
    
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

    @api.model_create_multi
    def create(self, vals_list):
        """Créer des réunions et envoyer des notifications"""
        meetings = super().create(vals_list)
        
        for meeting in meetings:
            # Ajouter automatiquement les participants principaux
            if meeting.stage_id:
                participants = []
                if meeting.stage_id.student_id.user_id:
                    participants.append(meeting.stage_id.student_id.user_id.id)
                if meeting.stage_id.supervisor_id.user_id:
                    participants.append(meeting.stage_id.supervisor_id.user_id.id)
                
                if participants:
                    meeting.participant_ids = [(6, 0, participants)]
            
            # Envoyer un email de notification
            meeting._send_meeting_notification_email()
        
        return meetings

    def action_confirm(self):
        """Confirmer la réunion"""
        self.write({'state': 'confirmed'})
        # Envoyer un email de confirmation
        self._send_meeting_confirmation_email()
        return True

    def action_start(self):
        """Démarrer la réunion"""
        self.write({'state': 'in_progress'})
        return True

    def action_complete(self):
        """Terminer la réunion"""
        self.write({'state': 'completed'})
        # Envoyer un email de résumé
        self._send_meeting_summary_email()
        return True

    def action_cancel(self):
        """Annuler la réunion"""
        self.write({'state': 'cancelled'})
        # Envoyer un email d'annulation
        self._send_meeting_cancellation_email()
        return True

    def action_send_reminder(self):
        """Envoyer un rappel aux participants"""
        for meeting in self:
            meeting._send_meeting_reminder_email()
            meeting.reminder_sent = True
            meeting.reminder_date = datetime.now()
        return True

    def _send_meeting_notification_email(self):
        """Envoyer un email de notification de nouvelle réunion"""
        for meeting in self:
            if not meeting.email_sent and meeting.participant_ids:
                subject = f"Nouvelle réunion planifiée : {meeting.name}"
                body = self._get_meeting_email_template('notification', meeting)
                
                # Envoyer l'email à tous les participants
                for participant in meeting.participant_ids:
                    if participant.email:
                        self.env['mail.mail'].create({
                            'subject': subject,
                            'body_html': body,
                            'email_from': self.env.user.email,
                            'email_to': participant.email,
                            'auto_delete': True,
                        }).send()
                
                meeting.email_sent = True

    def _send_meeting_confirmation_email(self):
        """Envoyer un email de confirmation de réunion"""
        for meeting in self:
            if meeting.participant_ids:
                subject = f"Réunion confirmée : {meeting.name}"
                body = self._get_meeting_email_template('confirmation', meeting)
                
                for participant in meeting.participant_ids:
                    if participant.email:
                        self.env['mail.mail'].create({
                            'subject': subject,
                            'body_html': body,
                            'email_from': self.env.user.email,
                            'email_to': participant.email,
                            'auto_delete': True,
                        }).send()

    def _send_meeting_reminder_email(self):
        """Envoyer un email de rappel de réunion"""
        for meeting in self:
            if meeting.participant_ids:
                subject = f"Rappel : Réunion {meeting.name} - {meeting.date.strftime('%d/%m/%Y à %H:%M')}"
                body = self._get_meeting_email_template('reminder', meeting)
                
                for participant in meeting.participant_ids:
                    if participant.email:
                        self.env['mail.mail'].create({
                            'subject': subject,
                            'body_html': body,
                            'email_from': self.env.user.email,
                            'email_to': participant.email,
                            'auto_delete': True,
                        }).send()

    def _send_meeting_summary_email(self):
        """Envoyer un email de résumé de réunion"""
        for meeting in self:
            if meeting.participant_ids:
                subject = f"Résumé de la réunion : {meeting.name}"
                body = self._get_meeting_email_template('summary', meeting)
                
                for participant in meeting.participant_ids:
                    if participant.email:
                        self.env['mail.mail'].create({
                            'subject': subject,
                            'body_html': body,
                            'email_from': self.env.user.email,
                            'email_to': participant.email,
                            'auto_delete': True,
                        }).send()

    def _send_meeting_cancellation_email(self):
        """Envoyer un email d'annulation de réunion"""
        for meeting in self:
            if meeting.participant_ids:
                subject = f"Réunion annulée : {meeting.name}"
                body = self._get_meeting_email_template('cancellation', meeting)
                
                for participant in meeting.participant_ids:
                    if participant.email:
                        self.env['mail.mail'].create({
                            'subject': subject,
                            'body_html': body,
                            'email_from': self.env.user.email,
                            'email_to': participant.email,
                            'auto_delete': True,
                        }).send()

    def _get_meeting_email_template(self, template_type, meeting):
        """Générer le contenu de l'email selon le type"""
        base_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">Gestion des Stages - Techpal</h2>
        """
        
        if template_type == 'notification':
            base_html += f"""
                <h3 style="color: #3498db;">Nouvelle réunion planifiée</h3>
                <p>Bonjour,</p>
                <p>Une nouvelle réunion a été planifiée :</p>
                <ul>
                    <li><strong>Titre :</strong> {meeting.name}</li>
                    <li><strong>Date :</strong> {meeting.date.strftime('%d/%m/%Y à %H:%M')}</li>
                    <li><strong>Durée :</strong> {meeting.duration} heure(s)</li>
                    <li><strong>Type :</strong> {dict(meeting._fields['type'].selection).get(meeting.type)}</li>
                    <li><strong>Modalité :</strong> {dict(meeting._fields['meeting_type'].selection).get(meeting.meeting_type)}</li>
                </ul>
                <p>Vous recevrez une confirmation une fois la réunion validée.</p>
            """
        elif template_type == 'confirmation':
            base_html += f"""
                <h3 style="color: #27ae60;">Réunion confirmée</h3>
                <p>Bonjour,</p>
                <p>La réunion suivante a été confirmée :</p>
                <ul>
                    <li><strong>Titre :</strong> {meeting.name}</li>
                    <li><strong>Date :</strong> {meeting.date.strftime('%d/%m/%Y à %H:%M')}</li>
                    <li><strong>Durée :</strong> {meeting.duration} heure(s)</li>
                    <li><strong>Lieu :</strong> {meeting.location or 'À définir'}</li>
                </ul>
                <p>Merci de confirmer votre présence.</p>
            """
        elif template_type == 'reminder':
            base_html += f"""
                <h3 style="color: #e74c3c;">Rappel de réunion</h3>
                <p>Bonjour,</p>
                <p>Rappel : Vous avez une réunion prévue :</p>
                <ul>
                    <li><strong>Titre :</strong> {meeting.name}</li>
                    <li><strong>Date :</strong> {meeting.date.strftime('%d/%m/%Y à %H:%M')}</li>
                    <li><strong>Lieu :</strong> {meeting.location or 'À définir'}</li>
                </ul>
                <p>N'oubliez pas de vous préparer !</p>
            """
        elif template_type == 'summary':
            base_html += f"""
                <h3 style="color: #9b59b6;">Résumé de la réunion</h3>
                <p>Bonjour,</p>
                <p>La réunion "{meeting.name}" s'est terminée.</p>
                <p><strong>Compte-rendu :</strong></p>
                <div style="background-color: white; padding: 15px; border-radius: 3px; margin: 10px 0;">
                    {meeting.summary or 'Aucun compte-rendu disponible'}
                </div>
                <p><strong>Actions à suivre :</strong></p>
                <div style="background-color: white; padding: 15px; border-radius: 3px; margin: 10px 0;">
                    {meeting.next_actions or 'Aucune action définie'}
                </div>
            """
        elif template_type == 'cancellation':
            base_html += f"""
                <h3 style="color: #e74c3c;">Réunion annulée</h3>
                <p>Bonjour,</p>
                <p>La réunion "{meeting.name}" prévue le {meeting.date.strftime('%d/%m/%Y à %H:%M')} a été annulée.</p>
                <p>Une nouvelle date sera proposée prochainement.</p>
            """
        
        base_html += """
            </div>
            <div style="text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 12px;">
                <p>Cet email a été envoyé automatiquement par le système de gestion des stages Techpal</p>
            </div>
        </div>
        """
        
        return base_html

    def action_generate_report(self):
        """Générer un rapport de réunion"""
        # Logique de génération de rapport
        return True
