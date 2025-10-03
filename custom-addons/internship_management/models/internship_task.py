# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipTodo(models.Model):
    """
    Gestion des Tâches et Livrables de Stage.

    Ce modèle a pour but de gérer toutes les tâches, missions ou livrables
    associés à un stage. Il permet un suivi structuré de l'avancement,
    des responsabilités et des échéances.

    Fonctionnalités Clés :
    - Assignation et suivi des tâches.
    - Gestion des priorités et des dates limites.
    - Suivi du pourcentage de progression.
    - Intégration directe avec le modèle de stage.
    - Notifications automatiques pour les tâches en retard.
    """
    _name = 'internship.todo'
    _description = 'Gestion des Tâches de Stage'
    # Héritage pour la messagerie, le suivi et les activités
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # Ordre d'affichage par défaut : séquence, date limite, puis priorité.
    _order = 'sequence, deadline, priority desc, id'
    _rec_name = 'name'

    # ===================================================
    # CHAMPS PRINCIPAUX
    # ===================================================

    name = fields.Char(
        string='Nom de la Tâche',
        required=True,  # Bonne pratique : une tâche doit toujours avoir un nom.
        tracking=True,
        help="Titre ou nom de la tâche à réaliser."
    )

    description = fields.Html(
        string='Description',
        help="Description détaillée de la tâche, des exigences et des livrables attendus."
    )

    # ===================================================
    # CHAMPS RELATIONNELS
    # ===================================================

    stage_id = fields.Many2one(
        'internship.stage',
        string='Stage Associé',
        required=True,  # Une tâche devrait toujours être liée à un stage pour le contexte.
        ondelete='cascade',
        help="Stage auquel cette tâche est rattachée."
    )

    assigned_to = fields.Many2one(
        'res.users',
        string='Assignée à',
        tracking=True,
        help="Utilisateur responsable de la réalisation de cette tâche (généralement l'étudiant)."
    )

    # ===================================================
    # CHAMPS DE GESTION DE LA TÂCHE
    # ===================================================

    state = fields.Selection([
        ('todo', 'À Faire'),
        ('in_progress', 'En Cours'),
        ('done', 'Terminée'),
        ('cancelled', 'Annulée')
    ], string='Statut', default='todo', tracking=True, required=True,
        help="Statut actuel de la tâche.")

    priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Très Haute')
    ], string='Priorité', default='1', tracking=True,
        help="Niveau de priorité de la tâche.")

    deadline = fields.Datetime(
        string='Date Limite',
        tracking=True,
        help="Date et heure auxquelles cette tâche doit être terminée."
    )

    completion_date = fields.Datetime(
        string='Date de Finalisation',
        readonly=True,
        copy=False,  # Ne pas copier la date de finalisation lors de la duplication.
        help="Date et heure réelles de finalisation de la tâche."
    )

    estimated_hours = fields.Float(
        string='Heures Estimées',
        help="Temps estimé pour accomplir cette tâche."
    )

    actual_hours = fields.Float(
        string='Heures Réelles',
        help="Temps réel passé sur cette tâche."
    )

    progress_percentage = fields.Float(
        string='Progression (%)',
        default=0.0,
        help="Pourcentage de complétion de la tâche (de 0 à 100)."
    )

    # ===================================================
    # CHAMPS DE SUIVI ET ALERTES
    # ===================================================

    is_overdue = fields.Boolean(
        string='En Retard',
        compute='_compute_overdue_status',
        store=True,
        help="Coché si la tâche a dépassé sa date limite."
    )

    days_overdue = fields.Integer(
        string='Jours de Retard',
        compute='_compute_overdue_status',
        store=True,
        help="Nombre de jours de retard de la tâche."
    )

    # ===================================================
    # CHAMPS TECHNIQUES
    # ===================================================

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Indique si l'enregistrement est actif ou archivé."
    )

    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Définit l'ordre d'affichage des tâches dans la vue liste."
    )

    # ===================================================
    # CONTRAINTES
    # ===================================================

    @api.constrains('progress_percentage')
    def _check_progress_percentage(self):
        """Vérifie que le pourcentage de progression est entre 0 et 100."""
        for task in self:
            if not (0 <= task.progress_percentage <= 100):
                raise ValidationError(_("Le pourcentage de progression doit être compris entre 0 et 100."))

    @api.constrains('deadline', 'create_date')
    def _check_deadline(self):
        """Vérifie que la date limite n'est pas antérieure à la date de création."""
        for task in self:
            if task.deadline and task.create_date and task.deadline < task.create_date:
                raise ValidationError(
                    _("La date limite ne peut pas être antérieure à la date de création de la tâche."))

    # ===================================================
    # MÉTHODES DE CALCUL (COMPUTE)
    # ===================================================

    @api.depends('deadline', 'state')
    def _compute_overdue_status(self):
        """Calcule le statut 'en retard' et le nombre de jours de retard."""
        now = fields.Datetime.now()
        for task in self:
            task.is_overdue = False
            task.days_overdue = 0
            if task.deadline and task.state in ['todo', 'in_progress']:
                if task.deadline < now:
                    task.is_overdue = True
                    # Calcul de la différence en jours
                    delta = now - task.deadline
                    task.days_overdue = delta.days

    @api.model
    def _cron_detect_overdue_tasks(self):
        """
        CRON: Détecte les tâches en retard et planifie une activité pour l'encadrant.
        """
        overdue_tasks = self.search([
            ('deadline', '<', fields.Date.today()),
            ('state', 'in', ['todo', 'in_progress']),
            ('activity_ids', '=', False)  # Pour ne pas créer de doublons
        ])

        for task in overdue_tasks:
            if task.stage_id.supervisor_id.user_id:
                task.activity_schedule(
                    'internship_management.activity_type_internship_alert',
                    summary=_("Tâche en retard: %s", task.name),
                    note=_(
                        "La date limite du %s est dépassée. Veuillez vérifier avec l'étudiant(e).",
                        task.deadline.strftime('%d/%m/%Y')
                    ),
                    user_id=task.stage_id.supervisor_id.user_id.id
                )

    # ===================================================
    # ACTIONS DES BOUTONS (WORKFLOW)
    # ===================================================

    def action_start(self):
        """Passe la tâche au statut 'En Cours'."""
        self.ensure_one()
        self.write({'state': 'in_progress'})

    def action_complete(self):
        """Marque la tâche comme 'Terminée'."""
        self.ensure_one()
        self.write({
            'state': 'done',
            'completion_date': fields.Datetime.now(),
            'progress_percentage': 100.0
        })

    def action_cancel(self):
        """Passe la tâche au statut 'Annulée'."""
        self.ensure_one()
        self.write({'state': 'cancelled'})

    def action_reset_to_todo(self):
        """Réinitialise la tâche au statut 'À Faire'."""
        self.ensure_one()
        self.write({
            'state': 'todo',
            'progress_percentage': 0.0,
            'completion_date': False
        })

    # ===================================================
    # LOGIQUE MÉTIER (OVERRIDE)
    # ===================================================

    @api.model_create_multi
    def create(self, vals_list):
        """
        Surcharge de la méthode de création pour assigner automatiquement
        la tâche à l'étudiant du stage si elle est créée par un encadrant.
        """
        for vals in vals_list:
            # Si un stage est défini et que personne n'est assigné manuellement
            if vals.get('stage_id') and not vals.get('assigned_to'):
                # On vérifie si le créateur est un encadrant
                is_supervisor = self.env.user.has_group('internship_management.group_internship_supervisor')

                if is_supervisor:
                    stage = self.env['internship.stage'].browse(vals['stage_id'])
                    if stage.student_id and stage.student_id.user_id:
                        vals['assigned_to'] = stage.student_id.user_id.id
                        _logger.info(
                            f"Tâche auto-assignée à l'étudiant {stage.student_id.user_id.name} "
                            f"par l'encadrant {self.env.user.name}."
                        )
                    else:
                        _logger.warning(
                            f"L'encadrant {self.env.user.name} a créé une tâche pour le stage "
                            f"'{stage.title}', mais aucun étudiant (ou utilisateur lié) n'a été trouvé."
                        )

        return super().create(vals_list)

    # ===================================================
    # Méthodes pour l'affichage (non modifiées, déjà bonnes)
    # ===================================================

    def name_get(self):
        """Affichage personnalisé du nom : Nom (Statut)."""
        result = []
        # Traduction des statuts pour un affichage propre
        status_translations = dict(self._fields['state'].selection)

        for todo in self:
            name = todo.name or ''
            state_name = status_translations.get(todo.state, '')
            result.append((todo.id, f"{name} ({state_name})"))
        return result
