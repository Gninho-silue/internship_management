# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipDocument(models.Model):
    """
    Gestion des Documents de Stage.

    Ce modèle gère tous les documents liés à un stage, y compris le téléversement,
    le suivi des versions, et un processus de validation.

    Fonctionnalités Clés :
    - Suivi du cycle de vie du document (brouillon, soumis, approuvé, etc.).
    - Intégration avec les stages, étudiants et encadrants.
    - Champs 'related' pour assurer la cohérence des données.
    - Notifications via le chatter lors de la soumission.
    """
    _name = 'internship.document'
    _description = 'Gestion des Documents de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_upload desc, name'
    _rec_name = 'name'

    # ===================================================
    # CHAMPS PRINCIPAUX
    # ===================================================

    name = fields.Char(
        string='Titre du Document',
        required=True,
        tracking=True,
        help="Titre ou nom du document."
    )

    document_type = fields.Selection([
        ('convention', 'Convention de Stage'),
        ('progress_report', 'Rapport d\'Avancement'),
        ('final_report', 'Rapport Final'),
        ('presentation', 'Présentation'),
        ('evaluation', 'Fiche d\'Évaluation'),
        ('attestation', 'Attestation de Stage'),
        ('other', 'Autre')
    ], string='Type de Document', required=True, tracking=True,
        help="Type de document téléversé.")

    # ===================================================
    # CHAMPS RELATIONNELS
    # ===================================================

    stage_id = fields.Many2one(
        'internship.stage',
        string='Stage Associé',
        required=True,
        tracking=True,
        ondelete='cascade',
        help="Stage auquel ce document est rattaché."
    )


    meeting_id = fields.Many2one(
        'internship.meeting',
        string='Réunion Associée',
        help="Réunion à laquelle ce document est lié (ex: support de présentation)."
    )

    student_id = fields.Many2one(
        'internship.student',
        string='Étudiant',
        domain="[('id', 'in', stage_id.student_ids)]",
        required=True,
        tracking=True,
        help="Étudiant propriétaire de ce document."
    )

    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Encadrant',
        related='stage_id.supervisor_id',
        store=True,
        readonly=True
    )

    uploaded_by = fields.Many2one(
        'res.users',
        string='Téléversé par',
        default=lambda self: self.env.user,
        readonly=True,
        help="Utilisateur qui a téléversé ce document."
    )

    feedback_ids = fields.One2many(
        'internship.document.feedback',
        'document_id',
        string='Commentaires',
        help="Ensemble des commentaires reçus pour ce document."
    )

    # ===================================================
    # GESTION DU FICHIER
    # ===================================================

    file = fields.Binary(
        string='Fichier',
        attachment=True,
        required=True,
        help="Le fichier du document."
    )

    filename = fields.Char(
        string='Nom du Fichier',
        help="Nom original du fichier téléversé."
    )

    file_size = fields.Integer(
        string="Taille du Fichier (octets)",
        compute='_compute_file_metadata',
        store=True,
        help="Taille du fichier en octets."
    )

    file_type = fields.Char(
        string="Type de Fichier",
        compute='_compute_file_metadata',
        store=True,
        help="Extension ou type MIME du fichier."
    )

    version = fields.Char(
        string='Version',
        default='1.0',
        tracking=True,
        help="Numéro de version du document."
    )

    # ===================================================
    # WORKFLOW ET STATUT
    # ===================================================

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis pour Révision'),
        ('under_review', 'En Cours de Révision'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('archived', 'Archivé')
    ], string='Statut', default='draft', tracking=True, required=True,
        help="Statut actuel du document dans le processus de révision.")

    review_required = fields.Boolean(
        string='Révision Requise',
        default=True,
        help="Cochez si ce document nécessite une révision par l'encadrant."
    )

    review_date = fields.Datetime(
        string='Date de Révision',
        readonly=True,
        copy=False,
        help="Date à laquelle le document a été révisé."
    )

    reviewed_by = fields.Many2one(
        'res.users',
        string='Révisé par',
        readonly=True,
        copy=False,
        help="Utilisateur qui a révisé le document."
    )

    review_comments = fields.Html(
        string='Commentaires de Révision',
        help="Commentaires et remarques de l'encadrant."
    )

    # ===================================================
    # CHAMPS DE SUIVI
    # ===================================================

    date_upload = fields.Datetime(
        string='Date de Téléversement',
        default=fields.Datetime.now,
        readonly=True,
        help="Date et heure du téléversement du document."
    )

    description = fields.Text(
        string='Description',
        help="Description détaillée du contenu du document."
    )

    active = fields.Boolean(default=True, string='Actif')

    # ===================================================
    # CONTRAINTES
    # ===================================================

    _sql_constraints = [
        ('unique_name_per_stage',
         'UNIQUE(stage_id, name, version)',
         'Un document avec ce nom et cette version existe déjà pour ce stage.')
    ]

    @api.constrains('file_size')
    def _check_file_size(self):
        """Vérifie que la taille du fichier ne dépasse pas la limite (ex: 50MB)."""
        max_size_mb = 50
        max_size = max_size_mb * 1024 * 1024
        for doc in self:
            if doc.file_size and doc.file_size > max_size:
                raise ValidationError(_(
                    "La taille du fichier ne peut pas dépasser %s MB.", max_size_mb
                ))

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """Mettre à jour le domaine de student_id et auto-remplir si l'utilisateur est un étudiant"""
        if self.stage_id:
            # Si l'utilisateur est un étudiant et appartient au stage, l'auto-remplir
            student = self.env['internship.student'].search([
                ('user_id', '=', self.env.user.id)
            ], limit=1)
            if student and student in self.stage_id.student_ids:
                self.student_id = student
            elif self.student_id and self.student_id not in self.stage_id.student_ids:
                # Si l'étudiant sélectionné n'appartient pas au nouveau stage, le vider
                self.student_id = False
            return {
                'domain': {
                    'student_id': [('id', 'in', self.stage_id.student_ids.ids)]
                }
            }
        else:
            self.student_id = False
            return {
                'domain': {
                    'student_id': [('id', '=', False)]
                }
            }

    @api.constrains('student_id', 'stage_id')
    def _check_student_in_stage(self):
        for record in self:
            if record.student_id and record.stage_id:
                if record.student_id not in record.stage_id.student_ids:
                    raise ValidationError(
                        "L'étudiant sélectionné doit être assigné au stage correspondant."
                    )

    # ===================================================
    # MÉTHODES DE CALCUL (COMPUTE)
    # ===================================================

    @api.depends('file', 'filename')
    def _compute_file_metadata(self):
        """Calcule la taille et le type du fichier."""
        for doc in self:
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', doc.id),
                ('res_field', '=', 'file')
            ], limit=1)
            if attachment:
                doc.file_size = attachment.file_size
                doc.file_type = attachment.mimetype
            else:
                doc.file_size = 0
                doc.file_type = 'inconnu'

    # ===================================================
    # MÉTHODES CRUD (CREATE, WRITE)
    # ===================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode de création pour remplir automatiquement student_id."""
        # Remplir automatiquement student_id si l'utilisateur est un étudiant
        for vals in vals_list:
            if not vals.get('student_id') and vals.get('stage_id'):
                # Vérifier si l'utilisateur actuel est un étudiant
                student = self.env['internship.student'].search([
                    ('user_id', '=', self.env.user.id)
                ], limit=1)
                if student:
                    # Vérifier que l'étudiant appartient au stage
                    stage = self.env['internship.stage'].browse(vals['stage_id'])
                    if student in stage.student_ids:
                        vals['student_id'] = student.id
            # Vérifier que si student_id est fourni, il appartient bien au stage
            elif vals.get('student_id') and vals.get('stage_id'):
                stage = self.env['internship.stage'].browse(vals['stage_id'])
                student = self.env['internship.student'].browse(vals['student_id'])
                if student not in stage.student_ids:
                    raise ValidationError(_(
                        "L'étudiant sélectionné doit être assigné au stage correspondant."
                    ))
        
        docs = super().create(vals_list)
        for doc in docs:
            doc.message_post(body=_("Document '%s' créé.", doc.name))
        return docs

    # ===================================================
    # ACTIONS DES BOUTONS (WORKFLOW)
    # ===================================================

    def action_submit_for_review(self):
        """Soumet le document pour révision."""
        for doc in self:
            doc.state = 'submitted'
            if doc.supervisor_id and doc.supervisor_id.user_id:
                supervisor_partner = doc.supervisor_id.user_id.partner_id
                if supervisor_partner:
                    doc.message_post(
                        body=_("Le document '%s' a été soumis pour votre révision.", doc.name),
                        partner_ids=[supervisor_partner.id],
                        subtype_xmlid='mail.mt_comment',
                    )
                    self.activity_schedule(
                        'mail.activity_data_todo',
                        user_id=doc.supervisor_id.user_id.id,
                        summary=_("Réviser le document : %s", doc.name)
                    )

    def action_start_review(self):
        """Démarre la révision du document."""
        self.write({
            'state': 'under_review',
            'reviewed_by': self.env.user.id
        })

    def action_approve(self):
        """Approuve le document."""
        self.write({
            'state': 'approved',
            'review_date': fields.Datetime.now(),
            'reviewed_by': self.env.user.id
        })

    def action_reject(self):
        """Ouvre un wizard pour justifier le rejet."""
        self.ensure_one()
        # Note : ce wizard 'internship.document.reject.wizard' doit être créé.
        # S'il n'existe pas encore, cette action provoquera une erreur.
        return {
            'name': _("Motif du Rejet"),
            'type': 'ir.actions.act_window',
            'res_model': 'internship.document.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_document_id': self.id},
        }

    def action_archive(self):
        """Archive le document."""
        self.active = False
