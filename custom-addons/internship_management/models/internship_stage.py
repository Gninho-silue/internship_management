# -*- coding: utf-8 -*-
"""
Modèle pour la gestion des stages (Internship Stage).
Ce modèle gère le cycle de vie complet d'un stage, de la candidature
à l'évaluation finale, en incluant le suivi de la progression,
les évaluations et la gestion documentaire.
"""

import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipStage(models.Model):
    """
    Définit un stage, ses acteurs, son calendrier et son état d'avancement.
    Hérite de 'mail.thread' et 'mail.activity.mixin' pour intégrer le Chatter
    et les activités, qui sont les outils standards d'Odoo pour la communication
    et le suivi des tâches.
    """
    _name = 'internship.stage'
    _description = 'Gestion de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, title'
    _rec_name = 'title'

    # ===============================
    # CHAMPS D'IDENTIFICATION
    # ===============================

    title = fields.Char(
        string='Titre du Stage',
        required=True,
        tracking=True,
        help="Sujet principal ou titre du projet de stage."
    )

    reference_number = fields.Char(
        string='Numéro de Référence',
        readonly=True,
        copy=False,
        default='Nouveau',
        help="Numéro de référence unique pour ce stage."
    )

    # ===============================
    # CLASSIFICATION
    # ===============================

    internship_type = fields.Selection([
        ('final_project', 'Projet de Fin d\'Études (PFE)'),
        ('summer_internship', 'Stage d\'été'),
        ('observation_internship', 'Stage d\'observation'),
        ('professional_internship', 'Stage professionnel')
    ], string='Type de Stage', tracking=True)

    # ===============================
    # CHAMPS RELATIONNELS
    # ===============================

    student_id = fields.Many2one(
        'internship.student',
        string='Étudiant(e)',
        tracking=True,
        ondelete='restrict',
        help="Étudiant(e) assigné(e) à ce stage."
    )

    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Encadrant(e)',
        tracking=True,
        ondelete='restrict',
        help="Encadrant(e) académique ou professionnel."
    )

    area_id = fields.Many2one(
        'internship.area',
        string='Domaine d\'Expertise',
        help="Domaine d'expertise de ce stage."
    )

    company_id = fields.Many2one(
        'res.company',
        string='Entreprise',
        default=lambda self: self.env.company,
        readonly=True,
        help="Entreprise où se déroule le stage."
    )

    # ===============================
    # GESTION DU TEMPS
    # ===============================

    start_date = fields.Date(
        string='Date de Début',
        tracking=True,
        help="Date de début officielle du stage."
    )

    end_date = fields.Date(
        string='Date de Fin',
        tracking=True,
        help="Date de fin officielle du stage."
    )

    @api.depends('start_date', 'end_date')
    def _compute_duration_days(self):
        """Calcule la durée du stage en jours."""
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
        string='Durée (Jours)',
        compute='_compute_duration_days',
        store=True,
        help="Durée totale du stage en jours."
    )

    # ===============================
    # PROPOSITION DE SUJET
    # ===============================

    subject_proposal = fields.Html(
        string='Proposition de Sujet',
        help="Proposition de l'entreprise pour le sujet de stage (format HTML)."
    )

    proposal_status = fields.Selection([
        ('draft', 'Brouillon'),
        ('proposed', 'Proposé'),
        ('accepted', 'Accepté'),
        ('modifications_requested', 'Modifications Demandées'),
        ('rejected', 'Rejeté')
    ], string='Statut de la Proposition', default='draft', tracking=True,
        help="Statut de la proposition de sujet.")

    proposal_feedback = fields.Html(
        string='Feedback sur la Proposition',
        help="Feedback sur la proposition de sujet."
    )

    proposal_date = fields.Datetime(
        string='Date de Proposition',
        help="Date à laquelle le sujet a été proposé."
    )

    proposal_accepted_date = fields.Datetime(
        string='Date d\'Acceptation',
        help="Date à laquelle la proposition a été acceptée."
    )

    # ===============================
    # CONTENU DU STAGE
    # ===============================

    project_description = fields.Html(
        string='Description du Projet',
        help="Description détaillée du projet de stage et de son contexte."
    )

    learning_objectives = fields.Html(
        string='Objectifs Pédagogiques',
        help="Objectifs pédagogiques et professionnels à atteindre."
    )

    # ===============================
    # SUIVI DE LA PROGRESSION
    # ===============================

    @api.depends('task_ids.state', 'start_date', 'end_date', 'state')
    def _compute_completion_percentage(self):
        """
        Calcule le pourcentage d'achèvement.
        - Si le stage est terminé ou évalué, le pourcentage est de 100%.
        - Si des tâches existent, le calcul se base sur le ratio de tâches terminées.
        - Sinon, il se base sur le temps écoulé par rapport à la durée totale.
        """
        for stage in self:
            if stage.state in ('completed', 'evaluated'):
                stage.completion_percentage = 100.0
                continue
            elif stage.state == 'cancelled':
                stage.completion_percentage = 0.0
                continue

            progress_value = 0.0
            total_tasks = len(stage.task_ids)
            if total_tasks > 0:
                completed_tasks = len(stage.task_ids.filtered(lambda t: t.state == 'done'))
                progress_value = (completed_tasks / total_tasks) * 100.0
            else:
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

            stage.completion_percentage = max(0.0, min(100.0, round(progress_value, 2)))

    completion_percentage = fields.Float(
        string='Achèvement %',
        compute='_compute_completion_percentage',
        store=True,
        tracking=True,
        help="Pourcentage global d'achèvement du stage."
    )

    # ===============================
    # GESTION D'ÉTAT (WORKFLOW)
    # ===============================

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('in_progress', 'En Cours'),
        ('completed', 'Terminé'),
        ('evaluated', 'Évalué'),
        ('cancelled', 'Annulé')
    ], string='Statut', default='draft', tracking=True)

    # ===============================
    # CHAMPS RELATIONNELS (One2many)
    # ===============================

    document_ids = fields.One2many(
        'internship.document', 'stage_id', string='Documents',
        help="Tous les documents liés à ce stage."
    )

    meeting_ids = fields.One2many(
        'internship.meeting', 'stage_id', string='Réunions',
        help="Réunions planifiées pour ce stage."
    )

    task_ids = fields.One2many(
        'internship.todo', 'stage_id', string='Tâches',
        help="Tâches et livrables pour ce stage."
    )

    presentation_ids = fields.One2many(
        'internship.presentation', 'stage_id', string='Présentations',
        help="Présentations de l'étudiant pour la soutenance."
    )

    # ===============================
    # STATISTIQUES (CHAMPS CALCULÉS)
    # ===============================

    @api.depends('task_ids', 'task_ids.state')
    def _compute_task_stats(self):
        """Calcule les statistiques sur les tâches."""
        for stage in self:
            stage.task_count = len(stage.task_ids)
            stage.completed_task_count = len(stage.task_ids.filtered(lambda t: t.state == 'done'))
            stage.pending_task_count = len(stage.task_ids.filtered(lambda t: t.state in ['todo', 'in_progress']))

    task_count = fields.Integer(string='Tâches Totales', compute='_compute_task_stats', store=True)
    completed_task_count = fields.Integer(string='Tâches Terminées', compute='_compute_task_stats', store=True)
    pending_task_count = fields.Integer(string='Tâches en Attente', compute='_compute_task_stats', store=True)

    @api.depends('presentation_ids', 'presentation_ids.status')
    def _compute_presentation_stats(self):
        """Calcule les statistiques sur les présentations."""
        for stage in self:
            stage.presentation_count = len(stage.presentation_ids)
            stage.pending_presentation_count = len(
                stage.presentation_ids.filtered(lambda p: p.status in ['submitted', 'revision_required']))

    presentation_count = fields.Integer(string='Nb Présentations', compute='_compute_presentation_stats', store=True)
    pending_presentation_count = fields.Integer(string='Présentations en Attente',
                                                compute='_compute_presentation_stats', store=True)

    @api.depends('presentation_ids.status')
    def _compute_final_presentation(self):
        """Détermine la présentation finale approuvée."""
        for stage in self:
            approved_presentation = stage.presentation_ids.filtered(lambda p: p.status == 'approved')
            stage.final_presentation_id = approved_presentation[0] if approved_presentation else False

    final_presentation_id = fields.Many2one(
        'internship.presentation', string="Présentation Finale Approuvée",
        compute='_compute_final_presentation', store=True,
        help="La dernière présentation approuvée pour la soutenance."
    )

    @api.depends('meeting_ids', 'meeting_ids.date')
    def _compute_meeting_stats(self):
        """Calcule les statistiques sur les réunions."""
        for stage in self:
            stage.meeting_count = len(stage.meeting_ids)
            stage.upcoming_meeting_count = len(stage.meeting_ids.filtered(
                lambda m: m.date and m.date > fields.Datetime.now()
            ))

    meeting_count = fields.Integer(string='Nb Réunions', compute='_compute_meeting_stats', store=True)
    upcoming_meeting_count = fields.Integer(string='Réunions à Venir', compute='_compute_meeting_stats', store=True)

    # ===============================
    # ÉVALUATION
    # ===============================

    final_grade = fields.Float(string='Note Finale', digits=(4, 2), help="Note finale du stage (sur 20).")
    defense_grade = fields.Float(string='Note de Soutenance', digits=(4, 2), help="Note de la soutenance (sur 20).")
    evaluation_feedback = fields.Html(string='Feedback d\'Évaluation', help="Feedback détaillé de l'encadrant(e).")

    # ===============================
    # GESTION DE LA SOUTENANCE
    # ===============================

    defense_date = fields.Datetime(string='Date de Soutenance', help="Date planifiée pour la soutenance.")
    defense_location = fields.Char(string='Lieu de la Soutenance', help="Lieu où se déroulera la soutenance.")
    defense_status = fields.Selection([
        ('scheduled', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée')
    ], string='Statut Soutenance', default='scheduled', tracking=True)
    jury_member_ids = fields.Many2many('internship.supervisor', string='Membres du Jury',
                                       help="Encadrants assignés comme membres du jury.")

    # ===============================
    # SIGNATURES
    # ===============================

    supervisor_signature = fields.Binary(string='Signature Encadrant(e)',
                                         help='Signature numérique de l\'encadrant(e).')
    student_signature = fields.Binary(string='Signature Étudiant(e)', help='Signature numérique de l\'étudiant(e).')
    jury_signature = fields.Binary(string='Signature Jury', help='Signature numérique du président du jury.')

    # ===============================
    # CHAMP TECHNIQUE
    # ===============================

    active = fields.Boolean(default=True, string='Actif', help="Indique si cet enregistrement de stage est actif.")

    # ===============================
    # CONTRAINTES DE VALIDATION
    # ===============================

    @api.constrains('start_date', 'end_date')
    def _check_date_consistency(self):
        """Vérifie que la date de fin est postérieure à la date de début."""
        for stage in self:
            if stage.start_date and stage.end_date and stage.start_date > stage.end_date:
                raise ValidationError(_("La date de fin doit être après la date de début."))

    @api.constrains('final_grade', 'defense_grade')
    def _check_grade_range(self):
        """Vérifie que les notes sont dans une plage valide (0-20)."""
        for stage in self:
            if stage.final_grade and not (0 <= stage.final_grade <= 20):
                raise ValidationError(_("La note finale doit être entre 0 et 20."))
            if stage.defense_grade and not (0 <= stage.defense_grade <= 20):
                raise ValidationError(_("La note de soutenance doit être entre 0 et 20."))

    # ===============================
    # MÉTHODES CRUD
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode create pour générer les numéros de référence."""
        for vals in vals_list:
            if vals.get('reference_number', 'Nouveau') == 'Nouveau':
                vals['reference_number'] = self.env['ir.sequence'].next_by_code('internship.stage') or 'STG-N/A'

        stages = super().create(vals_list)

        for stage in stages:
            _logger.info(f"Stage créé : {stage.reference_number} - {stage.title}")
            # Notifier l'étudiant via le Chatter
            if stage.student_id.user_id:
                stage.message_post(
                    body=_(
                        "Bienvenue ! Vous avez été assigné(e) au stage "
                        "\"<strong>%s</strong>\". Veuillez consulter les détails.",
                        stage.title
                    ),
                    partner_ids=[stage.student_id.user_id.partner_id.id],
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
        return stages

    # ===============================
    # MÉTHODES MÉTIER (ACTIONS DES BOUTONS)
    # ===============================

    def action_submit(self):
        """Soumet le stage pour approbation."""
        self.write({'state': 'submitted'})

    def action_approve(self):
        """Approuve le stage."""
        self.write({'state': 'approved'})

    def action_start(self):
        """Démarre le stage."""
        self.write({'state': 'in_progress'})

    def action_complete(self):
        """Marque le stage comme terminé."""
        self.write({'state': 'completed'})

    def action_schedule_defense(self):
        """
        Crée une activité pour l'encadrant afin qu'il planifie la soutenance.
        """
        self.ensure_one()
        if self.state != 'completed':
            raise ValidationError(_("Seuls les stages terminés peuvent avoir une soutenance planifiée."))

        if self.supervisor_id.user_id:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("Planifier la soutenance pour %s", self.title),
                note=_(
                    "Le stage est terminé. Veuillez configurer la date, "
                    "le lieu et les membres du jury dans l'onglet 'Soutenance & Évaluation'."
                ),
                user_id=self.supervisor_id.user_id.id,
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Planification de la Soutenance'),
                'message': _('Une activité a été créée pour que l\'encadrant(e) configure la soutenance.'),
                'type': 'info',
            }
        }

    def action_evaluate(self):
        """Marque le stage comme évalué après vérifications."""
        self.ensure_one()
        if self.state != 'completed':
            raise ValidationError(_("Seuls les stages terminés peuvent être évalués."))

        if not all([self.defense_date, self.jury_member_ids, self.defense_grade, self.final_grade]):
            raise ValidationError(
                _("Date de soutenance, membres du jury et notes doivent être renseignés avant d'évaluer."))

        self.write({'state': 'evaluated', 'defense_status': 'completed'})

        # Notifier les parties prenantes via le Chatter
        partner_ids = []
        if self.student_id.user_id:
            partner_ids.append(self.student_id.user_id.partner_id.id)
        if self.supervisor_id.user_id:
            partner_ids.append(self.supervisor_id.user_id.partner_id.id)

        self.message_post(
            body=_(
                "<strong>Évaluation du Stage Terminée</strong><br/>"
                "Note de Soutenance: <strong>%s/20</strong><br/>"
                "Note Finale: <strong>%s/20</strong>",
                self.defense_grade, self.final_grade
            ),
            partner_ids=partner_ids,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

    def action_cancel(self):
        """Annule le stage."""
        if self.state == 'evaluated':
            raise ValidationError(_("Un stage évalué ne peut pas être annulé."))
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """Réinitialise le stage à l'état brouillon."""
        if self.state == 'evaluated':
            raise ValidationError(_("Un stage évalué ne peut pas être réinitialisé."))
        self.write({'state': 'draft'})

    # ===============================
    # PROPOSITION DE SUJET
    # ===============================

    def action_propose_subject(self):
        """Propose le sujet à l'étudiant."""
        self.ensure_one()
        if not self.subject_proposal:
            raise ValidationError(_("Veuillez renseigner une proposition de sujet avant de soumettre."))

        self.write({
            'proposal_status': 'proposed',
            'proposal_date': fields.Datetime.now(),
            'state': 'submitted'
        })

        if self.student_id.user_id:
            self.message_post(
                body=_(
                    "<strong>Nouvelle Proposition de Sujet</strong><br/>"
                    "Veuillez examiner la proposition dans l'onglet 'Proposition de Sujet' et y répondre."
                ),
                partner_ids=[self.student_id.user_id.partner_id.id],
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )

    def action_accept_proposal(self):
        """Accepte la proposition de sujet."""
        self.ensure_one()
        self.write({
            'proposal_status': 'accepted',
            'proposal_accepted_date': fields.Datetime.now(),
            'state': 'approved'
        })
        self.action_start()  # Démarre automatiquement le stage

        if self.supervisor_id.user_id:
            self.message_post(
                body=_("La proposition de sujet a été <strong>acceptée</strong> par l'étudiant(e)."),
                partner_ids=[self.supervisor_id.user_id.partner_id.id]
            )

    def action_request_modifications(self):
        """Demande des modifications sur la proposition."""
        self.ensure_one()
        if not self.proposal_feedback:
            raise ValidationError(_("Veuillez fournir un feedback expliquant les modifications demandées."))

        self.write({'proposal_status': 'modifications_requested', 'state': 'draft'})

        if self.supervisor_id.user_id:
            self.message_post(
                body=_(
                    "<strong>Modifications Demandées</strong><br/>"
                    "L'étudiant(e) a demandé des modifications sur la proposition de sujet. "
                    "Veuillez consulter son feedback dans l'onglet dédié."
                ),
                partner_ids=[self.supervisor_id.user_id.partner_id.id]
            )

    def action_reject_proposal(self):
        """Rejette la proposition de sujet."""
        self.ensure_one()
        self.write({'proposal_status': 'rejected'})

        if self.supervisor_id.user_id:
            self.message_post(
                body=_("La proposition de sujet a été <strong>rejetée</strong>."),
                partner_ids=[self.supervisor_id.user_id.partner_id.id]
            )

    # ===============================
    # ACTIONS D'OUVERTURE DE VUES
    # ===============================

    def action_create_presentation(self):
        """Ouvre le formulaire pour créer une nouvelle présentation."""
        self.ensure_one()
        return {
            'name': _('Téléverser une Présentation - %s', self.title),
            'type': 'ir.actions.act_window',
            'res_model': 'internship.presentation',
            'view_mode': 'form',
            'context': {
                'default_stage_id': self.id,
                'default_student_id': self.student_id.id,
                'default_supervisor_id': self.supervisor_id.id,
            },
            'target': 'new',
        }

    def action_create_task(self):
        """Ouvre le formulaire pour créer une nouvelle tâche."""
        self.ensure_one()
        return {
            'name': _('Créer une Tâche - %s', self.title),
            'type': 'ir.actions.act_window',
            'res_model': 'internship.todo',
            'view_mode': 'form',
            'view_id': self.env.ref('internship_management.view_internship_todo_form').id,
            'context': {
                'default_stage_id': self.id,
                'default_assigned_to': self.student_id.id,
            },
            'target': 'new',
        }

    def action_open_tasks(self):
        """Ouvre la liste des tâches de ce stage."""
        self.ensure_one()
        return {
            'name': _('Tâches - %s', self.title),
            'type': 'ir.actions.act_window',
            'res_model': 'internship.todo',
            'view_mode': 'kanban,tree,form',
            'domain': [('stage_id', '=', self.id)],
            'target': 'current',
        }

    def action_schedule_meeting(self):
        """Ouvre le formulaire pour planifier une réunion."""
        self.ensure_one()
        return {
            'name': _('Planifier une Réunion - %s', self.title),
            'type': 'ir.actions.act_window',
            'res_model': 'internship.meeting',
            'view_mode': 'form',
            'context': {
                'default_stage_id': self.id,
                'default_student_id': self.student_id.id,
                'default_supervisor_id': self.supervisor_id.id,
            },
            'target': 'new',
        }

    # ===============================
    # TÂCHE AUTOMATISÉE (CRON)
    # ===============================

    @api.model
    def _cron_internship_monitoring(self):
        """
        Méthode principale appelée par le Cron pour lancer toutes les détections
        et transformer les problèmes trouvés en Activités.
        """
        _logger.info("CRON: Démarrage du suivi des stages...")

        # 1. Détection des tâches en retard (appel de la méthode dédiée)
        self.env['internship.todo']._cron_detect_overdue_tasks()

        # 2. Détection des stages inactifs
        fourteen_days_ago = fields.Datetime.now() - timedelta(days=14)
        inactive_stages = self.search([
            ('state', '=', 'in_progress'),
            ('write_date', '<', fourteen_days_ago),
            ('activity_ids', '=', False)
        ])

        for stage in inactive_stages:
            if stage.supervisor_id.user_id:
                stage.activity_schedule(
                    'internship_management.activity_type_internship_alert',
                    summary=_("Stage potentiellement inactif : %s", stage.title),
                    note=_(
                        "Aucune modification sur ce stage depuis plus de 14 jours. "
                        "Un suivi est peut-être nécessaire."
                    ),
                    user_id=stage.supervisor_id.user_id.id
                )

        _logger.info("CRON: Suivi des stages terminé.")

    # ===============================
    # MÉTHODES UTILITAIRES
    # ===============================

    def name_get(self):
        """Affichage personnalisé du nom : [Référence] - Titre."""
        result = []
        for stage in self:
            name = f"[{stage.reference_number}] {stage.title}"
            result.append((stage.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        """Recherche personnalisée sur la référence, le titre ou le nom de l'étudiant."""
        args = args or []
        domain = []
        if name:
            domain = ['|', '|',
                      ('title', operator, name),
                      ('reference_number', operator, name),
                      ('student_id.full_name', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid, order=order)
