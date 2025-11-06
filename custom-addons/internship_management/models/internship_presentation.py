# -*- coding: utf-8 -*-
"""
Modèle pour la gestion des présentations de soutenance de stage.
Ce modèle permet aux étudiants de soumettre leurs présentations,
aux encadrants de les réviser, et de suivre le cycle de vie
d'approbation via le Chatter et les Activités Odoo.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InternshipPresentation(models.Model):
    """
    Gère les présentations soumises par les étudiants pour leur soutenance.

    Optimisations Clés:
    - Remplacement des champs de feedback manuels (review_notes, etc.) par l'utilisation
      exclusive du Chatter pour une communication centralisée.
    - Remplacement des notifications personnalisées par la création d'Activités Odoo
      pour un suivi clair des tâches (ex: "À réviser").
    - Simplification du workflow en supprimant l'état "Final" redondant.
      L'état "Approuvé" est désormais l'état final.
    """
    _name = 'internship.presentation'
    _description = 'Présentation de Soutenance de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ===============================
    # CHAMPS PRINCIPAUX
    # ===============================
    name = fields.Char(string='Titre de la Présentation', required=True, tracking=True)

    stage_id = fields.Many2one(
        'internship.stage', string='Stage Associé',
        # OPTIMISATION: Une présentation doit obligatoirement être liée à un stage.
        required=True, ondelete='cascade', tracking=True
    )
    student_id = fields.Many2one(related='stage_id.student_id', store=True, string='Étudiant(e)')
    supervisor_id = fields.Many2one(related='stage_id.supervisor_id', store=True, string='Encadrant(e)')

    # ===============================
    # GESTION DU FICHIER
    # ===============================
    presentation_file = fields.Binary(string='Fichier de Présentation', required=True, attachment=True)
    filename = fields.Char(string='Nom du Fichier')
    file_size = fields.Float(string='Taille (Mo)', compute='_compute_file_size', store=True,
                             help="Taille du fichier en mégaoctets.")

    # ===============================
    # WORKFLOW ET STATUT
    # ===============================
    status = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis pour révision'),
        ('revision_required', 'En Révision'),
        ('approved', 'Approuvé'),
    ], string='Statut', default='draft', tracking=True, required=True, copy=False)

    version = fields.Char(string='Version', default='1.0', tracking=True, help="Ex: 1.0, 1.1, 2.0")

    submission_date = fields.Datetime(string='Date de Soumission', readonly=True)
    approval_date = fields.Datetime(string='Date d\'Approbation', readonly=True)
    due_date = fields.Date(string='Date Limite')

    is_overdue = fields.Boolean(string='En Retard',
                                compute='_compute_is_overdue',
                                store=True,
                                help="Indique si la date limite est dépassée.")

    # ===============================
    # CHAMPS CALCULÉS
    # ===============================
    @api.depends('presentation_file')
    def _compute_file_size(self):
        """Calcule la taille du fichier en Mo."""
        for record in self:
            if record.presentation_file:
                record.file_size = len(record.presentation_file) / (1024 * 1024)
            else:
                record.file_size = 0.0

    @api.depends('due_date', 'status')
    def _compute_is_overdue(self):
        """Vérifie si la présentation est en retard."""
        for record in self:
            record.is_overdue = (
                    record.due_date and record.due_date < fields.Date.today() and
                    record.status in ['draft', 'revision_required']
            )

    # ===============================
    # ACTIONS DU WORKFLOW
    # ===============================
    def action_submit(self):
        """Soumet la présentation pour révision et crée une activité pour l'encadrant."""
        self.ensure_one()
        if not self.presentation_file:
            raise UserError(_("Veuillez téléverser un fichier avant de soumettre la présentation."))

        self.write({'status': 'submitted', 'submission_date': fields.Datetime.now()})

        # OPTIMISATION: Utilisation du Chatter et des Activités au lieu d'un modèle custom
        self.message_post(body=_("La présentation a été soumise pour révision."))

        if self.supervisor_id.user_id:
            self.activity_schedule(
                'mail.activity_data_todo',
                summary=_("Réviser la présentation de %s", self.student_id.full_name),
                note=_("Veuillez réviser la présentation '%s' et l'approuver ou demander des modifications.",
                       self.name),
                user_id=self.supervisor_id.user_id.id
            )

    def action_approve(self):
        """Approuve la présentation, clôture l'activité de révision et notifie l'étudiant."""
        self.ensure_one()

        # OPTIMISATION: Clôture de l'activité existante
        activity = self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id)
        ], limit=1)
        if activity:
            activity.action_feedback(feedback=_("Présentation approuvée."))

        self.write({'status': 'approved', 'approval_date': fields.Datetime.now()})
        self.message_post(
            body=_("La présentation a été approuvée par %s.", self.env.user.name),
            partner_ids=self.student_id.user_id.partner_id.ids
        )

    def action_request_revision(self):
        """
        Demande une révision. L'encadrant doit d'abord poster son feedback dans le chatter.
        Une activité est ensuite créée pour l'étudiant.
        """
        self.ensure_one()

        # Clôture de l'activité de l'encadrant
        activity = self.env['mail.activity'].search([
            ('res_model', '=', self._name), ('res_id', '=', self.id),
            ('user_id', '=', self.env.user.id)], limit=1)
        if activity:
            activity.action_feedback(feedback=_("Demande de révision envoyée."))

        self.write({'status': 'revision_required'})

        body = _(
            "Une révision est demandée par %s. "
            "Veuillez consulter les commentaires dans le fil de discussion et soumettre une nouvelle version.",
            self.env.user.name
        )
        self.message_post(body=body, partner_ids=self.student_id.user_id.partner_id.ids)

        # Création d'une nouvelle activité pour l'étudiant
        if self.student_id.user_id:
            self.activity_schedule(
                'mail.activity_data_todo',
                summary=_("Mettre à jour votre présentation '%s'", self.name),
                note=_("Votre encadrant a demandé des modifications. Veuillez téléverser une nouvelle version."),
                user_id=self.student_id.user_id.id
            )
