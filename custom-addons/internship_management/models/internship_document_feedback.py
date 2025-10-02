# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipDocumentFeedback(models.Model):
    """
    Gestion des Retours (Feedback) sur les Documents de Stage.

    Ce modèle permet aux utilisateurs (principalement les encadrants) de fournir
    des commentaires structurés, des demandes de révision ou des approbations
    sur les documents soumis par les étudiants.
    """
    _name = 'internship.document.feedback'
    _description = 'Retour sur Document de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    # Le nom affiché sera une combinaison du document et du résumé
    _rec_name = 'display_name'

    # ===================================================
    # CHAMPS PRINCIPAUX
    # ===================================================

    document_id = fields.Many2one(
        'internship.document',
        string='Document',
        required=True,  # Un retour doit toujours être lié à un document.
        ondelete='cascade',
        tracking=True,
        help="Document concerné par ce retour."
    )

    reviewer_id = fields.Many2one(
        'res.users',
        string='Auteur du Retour',
        default=lambda self: self.env.user,
        readonly=True,  # L'auteur est toujours l'utilisateur connecté.
        tracking=True,
        help="Utilisateur qui fournit le retour."
    )

    feedback_type = fields.Selection([
        ('comment', 'Commentaire'),
        ('revision_required', 'Révision Requise'),
        ('question', 'Question'),
        ('suggestion', 'Suggestion'),
        ('approval', 'Approbation')
    ], string='Type de Retour', default='comment', required=True, tracking=True,
        help="La nature du retour fourni.")

    feedback_summary = fields.Char(
        string='Résumé',
        required=True,
        help="Un titre ou un résumé concis du retour."
    )

    detailed_feedback = fields.Html(
        string='Détails du Retour',
        help="Contenu détaillé du commentaire ou de la demande de révision."
    )

    # ===================================================
    # STATUT ET PRIORITÉ
    # ===================================================

    status = fields.Selection([
        ('open', 'Ouvert'),
        ('resolved', 'Résolu'),
        ('dismissed', 'Rejeté')
    ], string='Statut', default='open', tracking=True,
        help="Le statut du retour. Est-il encore à traiter ?")

    priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute')
    ], string='Priorité', default='1', tracking=True,
        help="Niveau de priorité du retour.")

    # ===================================================
    # CHAMPS 'RELATED' ET 'COMPUTE'
    # ===================================================

    stage_id = fields.Many2one(
        'internship.stage',
        related='document_id.stage_id',
        string='Stage Associé',
        store=True,
        help="Stage auquel ce retour est indirectement lié."
    )

    display_name = fields.Char(
        string="Nom Affiché",
        compute='_compute_display_name',
        store=True
    )

    @api.depends('document_id.name', 'feedback_summary')
    def _compute_display_name(self):
        """Construit un nom affiché plus informatif."""
        for feedback in self:
            if feedback.document_id and feedback.feedback_summary:
                feedback.display_name = f"{feedback.document_id.name}: {feedback.feedback_summary}"
            else:
                feedback.display_name = feedback.feedback_summary or _("Nouveau Retour")

    # ===================================================
    # LOGIQUE MÉTIER
    # ===================================================

    @api.model_create_multi
    def create(self, vals_list):
        """
        Surcharge de la création pour notifier les bonnes personnes
        et potentiellement changer le statut du document lié.
        """
        feedbacks = super().create(vals_list)
        for feedback in feedbacks:
            # Notifier l'étudiant via le chatter du document
            student_user = feedback.stage_id.student_id.user_id
            if student_user:
                feedback.document_id.message_post(
                    body=_("Nouveau retour de <strong>%s</strong> : <em>%s</em>",
                           feedback.reviewer_id.name, feedback.feedback_summary),
                    partner_ids=[student_user.partner_id.id],
                    subtype_xmlid='mail.mt_comment'
                )

            # Si le retour demande une révision, changer le statut du document
            if feedback.feedback_type == 'revision_required':
                feedback.document_id.write({'state': 'rejected'})
            elif feedback.feedback_type == 'approval':
                feedback.document_id.write({'state': 'approved'})

        return feedbacks

    # ===================================================
    # ACTIONS DES BOUTONS
    # ===================================================

    def action_resolve(self):
        """Marque le retour comme résolu."""
        self.write({'status': 'resolved'})

    def action_reopen(self):
        """Ré-ouvre un retour qui a été résolu ou rejeté."""
        self.write({'status': 'open'})

    def action_dismiss(self):
        """Marque le retour comme rejeté (non pertinent)."""
        self.write({'status': 'dismissed'})