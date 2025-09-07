# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InternshipStage(models.Model):
    _name = 'internship.stage'
    _description = 'Internship'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, name'

    # ===============================
    # CORE IDENTIFICATION FIELDS
    # ===============================

    title = fields.Char(
        string='Internship Title',
        required=True,
        tracking=True,
        help="Main subject or title of the internship project"
    )

    reference_number = fields.Char(
        string='Reference Number',
        readonly=True,
        copy=False,
        default='New',
        help="Unique reference number for this internship"
    )

    # ===============================
    # TYPE AND CLASSIFICATION
    # ===============================

    internship_type = fields.Selection([
        ('final_project', 'Final Year Project (PFE)'),
        ('summer_internship', 'Summer Internship'),
        ('observation_internship', 'Observation Internship'),
        ('professional_internship', 'Professional Internship')
    ], string='Internship Type', required=True, tracking=True)

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    student_id = fields.Many2one(
        'internship.student',
        string='Student',
        tracking=True,
        ondelete='restrict',
        help="Student assigned to this internship"
    )

    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Supervisor',
        tracking=True,
        ondelete='restrict',
        help="Academic or professional supervisor"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Host Organization',
        required=True,
        tracking=True,
        default=lambda self: self.env.company,
        help="Organization hosting the internship"
    )

    # ===============================
    # TIMELINE FIELDS
    # ===============================

    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True,
        help="Official start date of the internship"
    )

    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True,
        help="Official end date of the internship"
    )

    @api.depends('start_date', 'end_date')
    def _compute_duration_days(self):
        """Calculate internship duration in days."""
        for stage in self:
            if stage.start_date and stage.end_date:
                if stage.end_date >= stage.start_date:
                    delta = stage.end_date - stage.start_date
                    stage.duration_days = delta.days + 1
                else:
                    stage.duration_days = 0
            else:
                stage.duration_days = 0

    duration_days = fields.Integer(
        string='Duration (Days)',
        compute='_compute_duration_days',
        store=True,
        help="Total duration of internship in days"
    )

    # ===============================
    # CONTENT FIELDS
    # ===============================

    project_description = fields.Html(
        string='Project Description',
        required=True,
        help="Detailed description of the internship project and context"
    )

    learning_objectives = fields.Html(
        string='Learning Objectives',
        help="Educational and professional objectives to be achieved"
    )

    # ===============================
    # PROGRESS TRACKING
    # ===============================

    @api.depends('task_ids.state', 'start_date', 'end_date', 'current_state')
    def _compute_completion_percentage(self):
        """Calculate completion percentage based on tasks and timeline."""
        for stage in self:
            if stage.current_state in ('completed', 'evaluated'):
                stage.completion_percentage = 100.0
                continue
            elif stage.current_state == 'cancelled':
                stage.completion_percentage = 0.0
                continue

            progress_value = 0.0

            # Calculate based on completed tasks if available
            total_tasks = len(stage.task_ids)
            if total_tasks > 0:
                completed_tasks = len(stage.task_ids.filtered(lambda t: t.state == 'completed'))
                progress_value = (completed_tasks / total_tasks) * 100.0
            else:
                # Fallback: time-based calculation
                if stage.start_date and stage.end_date and stage.end_date >= stage.start_date:
                    total_duration = (stage.end_date - stage.start_date).days + 1
                    if total_duration > 0:
                        today = fields.Date.context_today(stage)
                        if today <= stage.start_date:
                            elapsed_days = 0
                        elif today >= stage.end_date:
                            elapsed_days = total_duration
                        else:
                            elapsed_days = (today - stage.start_date).days
                        progress_value = (elapsed_days / total_duration) * 100.0

            # Ensure progress is within 0-100 range
            stage.completion_percentage = max(0.0, min(100.0, round(progress_value, 2)))

    completion_percentage = fields.Float(
        string='Completion %',
        compute='_compute_completion_percentage',
        store=True,
        tracking=True,
        help="Overall completion percentage of the internship"
    )

    # État du stage
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('evaluated', 'Évalué'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)

    # Documents et soutenance
    document_ids = fields.One2many('internship.document', 'stage_id', string='Documents')
    message_ids = fields.One2many('internship.message', 'stage_id', string='Messages liés')
    notification_ids = fields.One2many('internship.notification', 'stage_id', string='Notifications liées')
    meeting_ids = fields.One2many('internship.meeting', 'stage_id', string='Réunions')
    convention_generated = fields.Boolean(string='Convention générée', default=False)
    defense_date = fields.Datetime(string='Date soutenance')
    jury_ids = fields.Many2many('internship.supervisor', string='Jury')
    defense_room = fields.Char(string='Salle soutenance')
    presentation_uploaded = fields.Boolean(string='Présentation déposée')
    presentation_document_id = fields.Many2one('internship.document', string='Document de présentation',
                                              domain="[('type', '=', 'presentation'), ('stage_id', '=', id)]")
    
    # Soutenance avancée
    defense_report = fields.Text(string='Procès-verbal de soutenance')
    defense_attendance = fields.Many2many('res.users', string='Présents à la soutenance')
    defense_notes = fields.Text(string='Notes du jury')
    defense_duration = fields.Float(string='Durée soutenance (heures)', default=1.5)
    defense_status = fields.Selection([
        ('scheduled', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée')
    ], string='Statut soutenance', default='scheduled', tracking=True)

    # Évaluation
    grade = fields.Float(string='Note finale', digits=(4, 2))
    defense_grade = fields.Float(string='Note soutenance')
    feedback = fields.Text(string='Commentaire d\'évaluation')
    
    # Documents générés
    convention_generated = fields.Boolean(string='Convention générée', default=False)
    attestation_generated = fields.Boolean(string='Attestation générée', default=False)
    defense_report_generated = fields.Boolean(string='PV généré', default=False)
    evaluation_report_generated = fields.Boolean(string='Rapport d\'évaluation généré', default=False)
    
    # Notes d'évaluation
    evaluation_notes = fields.Html(string='Notes d\'évaluation')

    # Champs techniques
    active = fields.Boolean(default=True, string='Actif')

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for stage in self:
            if stage.start_date and stage.end_date:
                if stage.end_date >= stage.start_date:
                    delta = stage.end_date - stage.start_date
                    stage.duration = delta.days + 1
                else:
                    stage.duration = 0
            else:
                stage.duration = 0

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for stage in self:
            if stage.start_date and stage.end_date and stage.start_date > stage.end_date:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début."))

    @api.constrains('jury_ids', 'defense_status')
    def _check_jury_for_defense(self):
        for stage in self:
            if stage.defense_status in ['in_progress', 'completed'] and len(stage.jury_ids) < 2:
                raise ValidationError(_("Au moins 2 membres du jury sont requis pour démarrer une soutenance."))

    @api.constrains('presentation_document_id', 'defense_status')
    def _check_presentation_for_defense(self):
        for stage in self:
            if stage.defense_status == 'completed' and not stage.presentation_document_id:
                raise ValidationError(_("Un document de présentation est obligatoire pour terminer la soutenance."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('internship.stage') or 'Nouveau'
        return super(InternshipStage, self).create(vals_list)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_evaluate(self):
        self.write({'state': 'evaluated'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        """Remettre en brouillon - impossible après évaluation"""
        for stage in self:
            if stage.state == 'evaluated':
                raise ValidationError(_("Impossible de remettre en brouillon un stage déjà évalué."))
        self.write({'state': 'draft'})

    def action_generate_convention(self):
        """Générer la convention et la marquer comme générée"""
        self.write({'convention_generated': True})
        return {
            'type': 'ir.actions.report',
            'report_name': 'internship_management.convention_report_document',
            'report_type': 'qweb-pdf',
            'data': {'doc_ids': self.ids},
        }

    def action_generate_attestation(self):
        """Générer l'attestation et la marquer comme générée"""
        self.write({'attestation_generated': True})
        return {
            'type': 'ir.actions.report',
            'report_name': 'internship_management.attestation_report_document',
            'report_type': 'qweb-pdf',
            'data': {'doc_ids': self.ids},
        }

    def action_generate_defense_report(self):
        """Générer le PV et le marquer comme généré"""
        self.write({'defense_report_generated': True})
        return {
            'type': 'ir.actions.report',
            'report_name': 'internship_management.defense_report_document',
            'report_type': 'qweb-pdf',
            'data': {'doc_ids': self.ids},
        }

    def action_generate_evaluation_report(self):
        """Générer le rapport d'évaluation et le marquer comme généré"""
        self.write({'evaluation_report_generated': True})
        return {
            'type': 'ir.actions.report',
            'report_name': 'internship_management.evaluation_report_document',
            'report_type': 'qweb-pdf',
            'data': {'doc_ids': self.ids},
        }

    # Méthodes d'alertes automatiques
    @api.model
    def _check_delays_and_stagnation(self):
        """Vérifier les retards et blocages - appelé par cron"""
        today = fields.Date.today()
        
        # Alertes de retard (fin de stage dépassée)
        delayed_stages = self.search([
            ('end_date', '<', today),
            ('state', 'in', ['draft', 'submitted', 'approved', 'in_progress']),
            ('active', '=', True)
        ])
        
        for stage in delayed_stages:
            self._create_delay_alert(stage)
        
        # Alertes de blocage (progression stagnante)
        active_stages = self.search([
            ('state', '=', 'in_progress'),
            ('active', '=', True)
        ])
        
        for stage in active_stages:
            self._check_progress_stagnation(stage)
        
        # Alertes de réunions manquées
        self._check_missing_meetings()
    
    def _create_delay_alert(self, stage):
        """Créer une alerte de retard"""
        if stage.student_id.user_id:
            self.env['internship.notification'].create({
                'title': f'⚠️ Retard détecté - {stage.name}',
                'message': f'Votre stage a dépassé la date de fin prévue ({stage.end_date}). Contactez votre encadrant.',
                'user_id': stage.student_id.user_id.id,
                'notification_type': 'alert',
                'stage_id': stage.id,
            })
        
        if stage.supervisor_id.user_id:
            self.env['internship.notification'].create({
                'title': f'⚠️ Retard détecté - {stage.name}',
                'message': f'Le stage de {stage.student_id.name} a dépassé la date de fin. Action requise.',
                'user_id': stage.supervisor_id.user_id.id,
                'notification_type': 'alert',
                'stage_id': stage.id,
            })
    
    def _check_progress_stagnation(self, stage):
        """Vérifier la stagnation de progression"""
        # Vérifier si la progression n'a pas bougé depuis 7 jours
        last_activity = self.env['mail.message'].search([
            ('model', '=', 'internship.stage'),
            ('res_id', '=', stage.id)
        ], order='create_date desc', limit=1)
        
        if last_activity:
            days_since_activity = (fields.Date.today() - last_activity.create_date.date()).days
            if days_since_activity > 7 and stage.progress < 50:
                self._create_stagnation_alert(stage, days_since_activity)
    
    def _create_stagnation_alert(self, stage, days):
        """Créer une alerte de stagnation"""
        if stage.supervisor_id.user_id:
            self.env['internship.notification'].create({
                'title': f'📊 Progression stagnante - {stage.name}',
                'message': f'Aucune activité depuis {days} jours sur le stage de {stage.student_id.name}. Progression: {stage.progress}%',
                'user_id': stage.supervisor_id.user_id.id,
                'notification_type': 'warning',
                'stage_id': stage.id,
            })
    
    def _check_missing_meetings(self):
        """Vérifier les réunions manquées"""
        # Stages en cours sans réunion depuis 14 jours
        active_stages = self.search([
            ('state', '=', 'in_progress'),
            ('active', '=', True)
        ])
        
        for stage in active_stages:
            last_meeting = self.env['internship.meeting'].search([
                ('stage_id', '=', stage.id),
                ('state', 'in', ['confirmed', 'completed'])
            ], order='date desc', limit=1)
            
            if last_meeting:
                days_since_meeting = (fields.Date.today() - last_meeting.date.date()).days
                if days_since_meeting > 14:
                    self._create_missing_meeting_alert(stage, days_since_meeting)
            else:
                # Pas de réunion du tout
                if stage.start_date and (fields.Date.today() - stage.start_date).days > 14:
                    self._create_missing_meeting_alert(stage, 0)
    
    def _create_missing_meeting_alert(self, stage, days):
        """Créer une alerte de réunion manquée"""
        if stage.supervisor_id.user_id:
            message = f'Réunion de suivi nécessaire pour le stage de {stage.student_id.name}.'
            if days > 0:
                message += f' Dernière réunion il y a {days} jours.'
            else:
                message += ' Aucune réunion programmée depuis le début du stage.'
            
            self.env['internship.notification'].create({
                'title': f'📅 Réunion de suivi nécessaire - {stage.name}',
                'message': message,
                'user_id': stage.supervisor_id.user_id.id,
                'notification_type': 'info',
                'stage_id': stage.id,
            })

    # Méthodes pour les soutenances
    def action_schedule_defense(self):
        """Planifier une soutenance"""
        return {
            'name': 'Planifier Soutenance',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.stage',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_defense_status': 'scheduled'}
        }

    def action_start_defense(self):
        """Démarrer la soutenance"""
        self.write({
            'defense_status': 'in_progress',
            'defense_date': fields.Datetime.now()
        })
        # Envoyer notification aux membres du jury
        self._notify_jury_defense_started()

    def action_complete_defense(self):
        """Terminer la soutenance"""
        self.write({'defense_status': 'completed'})
        # Envoyer notification de fin de soutenance
        self._notify_defense_completed()

    def action_cancel_defense(self):
        """Annuler la soutenance"""
        self.write({'defense_status': 'cancelled'})
        # Envoyer notification d'annulation
        self._notify_defense_cancelled()

    def _notify_jury_defense_started(self):
        """Notifier le jury que la soutenance commence"""
        for jury_member in self.jury_ids:
            if jury_member.user_id:
                self.env['internship.notification'].create({
                    'title': f'Soutenance démarrée - {self.name}',
                    'message': f'La soutenance de {self.student_id.name} a commencé.',
                    'user_id': jury_member.user_id.id,
                    'notification_type': 'info',
                    'stage_id': self.id,
                })

    def _notify_defense_completed(self):
        """Notifier la fin de soutenance"""
        if self.student_id.user_id:
            self.env['internship.notification'].create({
                'title': f'Soutenance terminée - {self.name}',
                'message': f'Votre soutenance est terminée. Note: {self.defense_grade or "Non notée"}',
                'user_id': self.student_id.user_id.id,
                'notification_type': 'info',
                'stage_id': self.id,
            })

    def _notify_defense_cancelled(self):
        """Notifier l'annulation de soutenance"""
        if self.student_id.user_id:
            self.env['internship.notification'].create({
                'title': f'Soutenance annulée - {self.name}',
                'message': 'Votre soutenance a été annulée. Une nouvelle date sera fixée.',
                'user_id': self.student_id.user_id.id,
                'notification_type': 'alert',
                'stage_id': self.id,
            })

    # Méthodes de statistiques
    @api.model
    def get_stage_statistics(self):
        """Retourne les statistiques globales des stages"""
        stages = self.search([])
        total_stages = len(stages)
        
        if total_stages == 0:
            return {
                'total': 0,
                'in_progress': 0,
                'completed': 0,
                'average_grade': 0,
                'completion_rate': 0,
                'defense_scheduled': 0
            }
        
        in_progress = len(stages.filtered(lambda s: s.state == 'in_progress'))
        completed = len(stages.filtered(lambda s: s.state in ['completed', 'evaluated']))
        defense_scheduled = len(stages.filtered(lambda s: s.defense_status == 'scheduled'))
        
        # Calcul de la note moyenne
        graded_stages = stages.filtered(lambda s: s.grade > 0)
        average_grade = sum(graded_stages.mapped('grade')) / len(graded_stages) if graded_stages else 0
        
        # Taux de complétion
        completion_rate = (completed / total_stages) * 100 if total_stages > 0 else 0
        
        return {
            'total': total_stages,
            'in_progress': in_progress,
            'completed': completed,
            'average_grade': round(average_grade, 2),
            'completion_rate': round(completion_rate, 1),
            'defense_scheduled': defense_scheduled
        }

    @api.model
    def get_student_statistics(self, student_id):
        """Retourne les statistiques d'un étudiant"""
        student_stages = self.search([('student_id', '=', student_id)])
        
        if not student_stages:
            return {
                'total_stages': 0,
                'current_stage': None,
                'average_grade': 0,
                'total_progress': 0
            }
        
        current_stage = student_stages.filtered(lambda s: s.state == 'in_progress')
        completed_stages = student_stages.filtered(lambda s: s.state in ['completed', 'evaluated'])
        
        average_grade = sum(completed_stages.mapped('grade')) / len(completed_stages) if completed_stages else 0
        total_progress = sum(student_stages.mapped('progress')) / len(student_stages) if student_stages else 0
        
        return {
            'total_stages': len(student_stages),
            'current_stage': current_stage[0] if current_stage else None,
            'average_grade': round(average_grade, 2),
            'total_progress': round(total_progress, 1)
        }

    @api.model
    def get_supervisor_statistics(self, supervisor_id):
        """Retourne les statistiques d'un encadrant"""
        supervisor_stages = self.search([('supervisor_id', '=', supervisor_id)])
        
        if not supervisor_stages:
            return {
                'total_stages': 0,
                'active_stages': 0,
                'average_grade': 0,
                'student_count': 0
            }
        
        active_stages = supervisor_stages.filtered(lambda s: s.state == 'in_progress')
        completed_stages = supervisor_stages.filtered(lambda s: s.state in ['completed', 'evaluated'])
        unique_students = len(supervisor_stages.mapped('student_id'))
        
        average_grade = sum(completed_stages.mapped('grade')) / len(completed_stages) if completed_stages else 0
        
        return {
            'total_stages': len(supervisor_stages),
            'active_stages': len(active_stages),
            'average_grade': round(average_grade, 2),
            'student_count': unique_students
        }