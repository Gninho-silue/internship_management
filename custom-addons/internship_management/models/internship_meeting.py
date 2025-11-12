# -*- coding: utf-8 -*-
"""
Modèle pour la gestion des réunions de stage.
Ce modèle centralise la planification, le suivi et la gestion des réunions
liées aux stages (lancement, suivi, soutenance, etc.).
"""

import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class InternshipMeeting(models.Model):
    """
    Modèle de Réunion pour le système de gestion des stages.

    Ce modèle gère la planification, la gestion et le suivi des réunions
    pour les stages.

    Optimisations principales :
    - Remplacement de la gestion manuelle des participants (via internship.meeting.attendee)
      par un champ standard `partner_ids` (res.partner) pour une meilleure intégration.
    - Suppression des champs de suivi d'e-mail (`email_sent`, `reminder_sent`) au profit
      du Chatter et des Activités Odoo.
    - Utilisation des modèles d'e-mail (`mail.template`) pour les notifications,
      au lieu de générer du HTML manuellement dans le code Python.
    - Simplification de la logique de création avec un onchange pour suggérer les participants.
    """
    _name = 'internship.meeting'
    _description = 'Gestion des Réunions de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name'
    _rec_name = 'name'

    # ===============================
    # CHAMPS PRINCIPAUX
    # ===============================

    name = fields.Char(
        string='Titre de la réunion',
        required=True,
        tracking=True,
        help="Titre ou sujet de la réunion."
    )

    meeting_type = fields.Selection([
        ('kickoff', 'Lancement'),
        ('follow_up', 'Suivi'),
        ('milestone', 'Revue d\'étape'),
        ('defense', 'Soutenance'),
        ('evaluation', 'Évaluation'),
        ('emergency', 'Urgence'),
        ('other', 'Autre')
    ], string='Type de réunion', default='follow_up', tracking=True, required=True,
        help="Type de réunion planifiée.")

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('scheduled', 'Planifiée'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
    ], string='Statut', default='draft', tracking=True, required=True, copy=False,
        help="Statut actuel de la réunion.")

    # ===============================
    # CHAMPS DE RELATION
    # ===============================

    stage_id = fields.Many2one(
        'internship.stage',
        string='Stage Associé',
        required=True,  # OPTIMISATION: Une réunion doit toujours être liée à un stage
        tracking=True,
        ondelete='cascade',
        help="Stage auquel cette réunion est liée."
    )

    student_ids = fields.Many2many(
        'internship.student',
        related='stage_id.student_ids',
        readonly=True,
        string="ÉtudiantS"
    )

    supervisor_id = fields.Many2one(
        related='stage_id.supervisor_id',
        store=True,
        readonly=True,
        string="Encadrant(e)"
    )

    organizer_id = fields.Many2one(
        'res.users',
        string='Organisateur',
        default=lambda self: self.env.user,
        tracking=True,
        required=True,
        help="Utilisateur qui a organisé cette réunion."
    )

    # OPTIMISATION: Remplacement de 'participant_ids' et 'attendee_ids' par un seul champ standard
    # pointant vers 'res.partner' pour une intégration parfaite avec le calendrier et les e-mails d'Odoo.
    partner_ids = fields.Many2many(
        'res.partner',
        'internship_meeting_partner_rel',  # relation (table intermédiaire)
        'meeting_id',                      # column1
        'partner_id',                      # column2
        string='Participants',
        tracking=True,
        help="Personnes qui doivent assister à cette réunion."
    )

    # ===============================
    # CHAMPS DE PLANIFICATION
    # ===============================

    date = fields.Datetime(
        string='Date et Heure',
        required=True,
        tracking=True,
        help="Date et heure prévues pour la réunion."
    )

    duration = fields.Float(
        string='Durée (Heures)',
        default=1.0,
        tracking=True,
        help="Durée prévue de la réunion en heures."
    )

    # OPTIMISATION: Renommé de 'end_date' à 'stop_date' pour correspondre aux conventions du calendrier Odoo
    @api.depends('date', 'duration')
    def _compute_stop_date(self):
        """Calcule l'heure de fin de la réunion."""
        for meeting in self:
            if meeting.date and meeting.duration:
                meeting.stop_date = meeting.date + timedelta(hours=meeting.duration)
            else:
                meeting.stop_date = meeting.date

    stop_date = fields.Datetime(
        string='Heure de fin',
        compute='_compute_stop_date',
        store=True,
        help="Heure de fin calculée de la réunion."
    )

    # ===============================
    # CHAMPS DE MODALITÉ
    # ===============================

    location = fields.Char(
        string='Lieu',
        tracking=True,
        help="Lieu physique de la réunion."
    )

    meeting_url = fields.Char(
        string='URL de la réunion',
        help="URL pour les réunions virtuelles (Zoom, Teams, etc.)."
    )

    # NOTE: Ce champ n'est pas strictement nécessaire si location/meeting_url est utilisé,
    # mais conservé pour le filtrage.
    meeting_modality = fields.Selection([
        ('physical', 'En Présentiel'),
        ('virtual', 'En Ligne'),
    ], string='Modalité', default='virtual', tracking=True,
        help="Comment la réunion se déroulera.")

    # ===============================
    # CHAMPS DE CONTENU
    # ===============================

    agenda = fields.Html(
        string='Ordre du jour',
        help="Ordre du jour et sujets à discuter."
    )

    summary = fields.Html(
        string='Compte-rendu',
        help="Résumé de ce qui a été discuté lors de la réunion."
    )

    # ===============================
    # CHAMPS TECHNIQUES
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Actif',
        help="Indique si cet enregistrement est actif."
    )

    # ===============================
    # CONTRAINTES
    # ===============================

    @api.constrains('date')
    def _check_meeting_date(self):
        """Vérifie que la date de la réunion est dans le futur pour les brouillons."""
        for meeting in self:
            if meeting.state == 'draft' and meeting.date and meeting.date < fields.Datetime.now():
                raise ValidationError(_("La date de la réunion doit être dans le futur."))

    @api.constrains('duration')
    def _check_duration(self):
        """Vérifie que la durée est positive."""
        for meeting in self:
            if meeting.duration <= 0:
                raise ValidationError(_("La durée de la réunion doit être positive."))

    @api.constrains('student_ids')
    def _check_students(self):
        for meeting in self:
            if not meeting.student_ids:
                raise ValidationError("Une réunion doit avoir au moins un étudiant participant.")

    # ===============================
    # ONCHANGE
    # ===============================

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """
        OPTIMISATION: Suggère automatiquement les participants (étudiant, encadrant)
        et l'organisateur lors de la sélection d'un stage.
        """
        if not self.stage_id:
            self.partner_ids = False
            return

        partners = self.env['res.partner']

        # Récupération des partenaires des étudiants
        student_partners = self.stage_id.student_ids.mapped('user_id.partner_id')
        if student_partners:
            partners |= student_partners

        # Récupération du partenaire de l'encadrant
        supervisor_partner = self.stage_id.supervisor_id.user_id.partner_id
        if supervisor_partner:
            partners |= supervisor_partner

        # Ajout de l'organisateur s'il existe déjà
        if self.organizer_id.partner_id:
            partners |= self.organizer_id.partner_id

        self.partner_ids = partners

    # ===============================
    # MÉTHODES D'ACTION (WORKFLOW)
    # ===============================

    def action_schedule(self):
        """Passe la réunion à l'état 'Planifiée' et envoie les invitations."""
        self.ensure_one()
        if not self.partner_ids:
            raise UserError(_("Veuillez ajouter au moins un participant avant de planifier la réunion."))

        self.write({'state': 'scheduled'})
        # OPTIMISATION: Utilise un modèle d'e-mail pour l'invitation
        template = self.env.ref('internship_management.mail_template_meeting_invitation', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def action_complete(self):
        """Passe la réunion à l'état 'Terminée'."""
        self.write({'state': 'completed'})

    def action_cancel(self):
        """Passe la réunion à l'état 'Annulée' et envoie une notification."""
        self.write({'state': 'cancelled'})
        # OPTIMISATION: Utilise un modèle d'e-mail pour l'annulation
        template = self.env.ref('internship_management.mail_template_meeting_cancellation', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def action_reset_to_draft(self):
        """Réinitialise la réunion à l'état 'Brouillon'."""
        self.write({'state': 'draft'})

    # ===============================
    # MÉTHODES D'AFFICHAGE
    # ===============================

    def name_get(self):
        result = []
        for record in self:
            date_str = fields.Date.to_string(record.date)
            students = ', '.join(record.student_ids.mapped('name'))
            name = f"{date_str} - {students}"
            if record.name:
                name = f"{name} ({record.name})"
            result.append((record.id, name))
        return result

