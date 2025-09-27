# -*- coding: utf-8 -*-

import os

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InternshipPresentation(models.Model):
    """
    Modèle de Présentation de Soutenance de Stage

    Gère les présentations soumises par les étudiants pour leur soutenance,
    incluant le workflow d'approbation et les révisions.
    """
    _name = 'internship.presentation'
    _description = 'Présentation de Soutenance de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ===============================
    # CHAMPS DE BASE
    # ===============================

    name = fields.Char(
        string='Nom de la Présentation',
        required=True,
        tracking=True,
        help="Nom du fichier de présentation"
    )

    stage_id = fields.Many2one(
        'internship.stage',
        string='Stage',
        required=False,
        ondelete='cascade',
        tracking=True,
        help="Stage associé à cette présentation"
    )

    student_id = fields.Many2one(
        'internship.student',
        string='Étudiant',
        related='stage_id.student_id',
        store=True,
        help="Étudiant ayant soumis la présentation"
    )

    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Encadrant',
        related='stage_id.supervisor_id',
        store=True,
        help="Encadrant du stage"
    )

    # ===============================
    # GESTION DES FICHIERS
    # ===============================

    presentation_file = fields.Binary(
        string='Fichier de Présentation',
        required=False,
        help="Télécharger le fichier de présentation (PDF, PPT, PPTX)"
    )

    filename = fields.Char(
        string='Nom du Fichier',
        help="Nom original du fichier téléchargé"
    )

    file_size = fields.Float(
        string='Taille du Fichier (MB)',
        compute='_compute_file_size',
        store=True,
        help="Taille du fichier téléchargé en MB"
    )

    file_type = fields.Selection([
        ('pdf', 'PDF'),
        ('ppt', 'PowerPoint (.ppt)'),
        ('pptx', 'PowerPoint (.pptx)'),
        ('other', 'Autre Format')
    ], string='Type de Fichier', compute='_compute_file_type', store=True)

    # ===============================
    # STATUT ET VERSIONING
    # ===============================

    version = fields.Char(
        string='Version',
        default='1.0',
        tracking=True,
        help="Numéro de version de la présentation"
    )

    status = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('revision_required', 'Révision Requise'),
        ('final', 'Version Finale')
    ], string='Statut', default='draft', tracking=True, required=False)

    is_final_version = fields.Boolean(
        string='Version Finale',
        default=False,
        help="Marquer comme version finale pour la soutenance"
    )

    # ===============================
    # RÉVISION ET FEEDBACK
    # ===============================

    review_notes = fields.Html(
        string='Notes de Révision',
        help="Notes et commentaires du superviseur"
    )

    reviewer_id = fields.Many2one(
        'res.users',
        string='Révisé par',
        help="Utilisateur ayant révisé la présentation"
    )

    review_date = fields.Datetime(
        string='Date de Révision',
        help="Date de la révision"
    )

    reviewed_date = fields.Datetime(
        string='Date de Validation Finale',
        readonly=True,
        help="Date de validation finale (auto-renseignée)"
    )

    # ===============================
    # DATES
    # ===============================

    submission_date = fields.Datetime(
        string='Date de Soumission',
        help="Date de soumission pour révision"
    )

    due_date = fields.Date(
        string='Date Limite',
        help="Date limite pour soumettre la présentation"
    )

    is_overdue = fields.Boolean(
        string='En Retard',
        compute='_compute_is_overdue',
        store=True,
        help="Indique si la présentation est en retard"
    )

    # ===============================
    # COMPUTED FIELDS
    # ===============================

    @api.depends('presentation_file')
    def _compute_file_size(self):
        """Calculer la taille du fichier en MB."""
        for record in self:
            if record.presentation_file:
                # Taille approximative en MB
                record.file_size = len(record.presentation_file) / 1048576
            else:
                record.file_size = 0.0

    @api.depends('filename')
    def _compute_file_type(self):
        """Déterminer le type de fichier basé sur l'extension."""
        for record in self:
            if record.filename:
                ext = os.path.splitext(record.filename)[1].lower()
                if ext == '.pdf':
                    record.file_type = 'pdf'
                elif ext == '.ppt':
                    record.file_type = 'ppt'
                elif ext == '.pptx':
                    record.file_type = 'pptx'
                else:
                    record.file_type = 'other'
            else:
                record.file_type = 'other'

    @api.depends('due_date', 'submission_date', 'status')
    def _compute_is_overdue(self):
        """Vérifier si la présentation est en retard."""
        today = fields.Date.today()
        for record in self:
            if record.due_date and record.status in ['draft', 'revision_required']:
                record.is_overdue = record.due_date < today
            else:
                record.is_overdue = False

    # ===============================
    # CONTRAINTES
    # ===============================

    @api.constrains('version')
    def _check_version_format(self):
        """Valider le format de version."""
        for record in self:
            if record.version and not record.version.replace('.', '').isdigit():
                raise ValidationError(_("La version doit être au format X.Y (ex: 1.0, 2.1)"))

    # ===============================
    # ACTIONS
    # ===============================

    def action_submit(self):
        """Soumettre la présentation pour révision."""
        self.ensure_one()
        if self.status != 'draft':
            raise ValidationError(_("Seules les présentations en brouillon peuvent être soumises."))

        if not self.presentation_file:
            raise ValidationError(_("Veuillez télécharger un fichier de présentation avant de soumettre."))

        self.write({
            'status': 'submitted',
            'submission_date': fields.Datetime.now()
        })

        # Créer notification
        self.env['internship.communication'].create({
            'subject': f'Nouvelle Présentation Soumise : {self.name}',
            'content': f'''
                <p><strong>Nouvelle Présentation Soumise</strong></p>
                <p>L'étudiant {self.student_id.full_name if self.student_id else 'N/A'} a soumis une nouvelle présentation :</p>
                <ul>
                    <li><strong>Présentation :</strong> {self.name}</li>
                    <li><strong>Version :</strong> {self.version}</li>
                    <li><strong>Type :</strong> {dict(self._fields['file_type'].selection).get(self.file_type, 'N/A')}</li>
                    <li><strong>Taille :</strong> {self.file_size:.2f} MB</li>
                </ul>
                <p>Veuillez réviser la présentation et fournir un retour.</p>
            ''',
            'communication_type': 'approval_request',
            'stage_id': self.stage_id.id,
            'sender_id': self.env.user.id,
            'recipient_ids': [(6, 0, [
                user_id for user_id in [
                    self.supervisor_id.user_id.id if self.supervisor_id and self.supervisor_id.user_id else None
                ] if user_id
            ])],
            'priority': '2',
            'state': 'sent'
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Présentation Soumise'),
                'message': _('Votre présentation a été soumise pour révision.'),
                'type': 'success',
            }
        }

    def action_approve(self):
        """
        Approuver la présentation.
        Si l'utilisateur est admin/coordinator, passer automatiquement à 'final'.
        """
        self.ensure_one()
        if self.status not in ['submitted', 'revision_required']:
            raise ValidationError(_("Seules les présentations soumises ou en révision peuvent être approuvées."))

        # Déterminer le statut selon le rôle
        values = {
            'status': 'approved',
            'reviewer_id': self.env.user.id,
            'review_date': fields.Datetime.now()
        }

        # Si admin/coordinator approuve → passer automatiquement à 'final'
        if self.env.user.has_group('internship_management.group_internship_admin') or \
                self.env.user.has_group('internship_management.group_internship_coordinator'):
            values['status'] = 'final'
            values['reviewed_date'] = fields.Datetime.now()  # AUTO-RENSEIGNÉ
            values['is_final_version'] = True

        self.write(values)

        # Notification
        status_text = "approuvée et finalisée" if values['status'] == 'final' else "approuvée"
        self.env['internship.communication'].create({
            'subject': f'Présentation {status_text.capitalize()} : {self.name}',
            'content': f'''
                <p><strong>Présentation {status_text.capitalize()}</strong></p>
                <p>Votre présentation "{self.name}" a été {status_text} par {self.env.user.name}.</p>
                {'<p>Il s\'agit maintenant de la version finale pour votre soutenance.</p>' if values['status'] == 'final' else '<p>Vous pouvez maintenant préparer votre soutenance.</p>'}
            ''',
            'communication_type': 'approval_request',
            'stage_id': self.stage_id.id,
            'sender_id': self.env.user.id,
            'recipient_ids': [(6, 0, [
                user_id for user_id in [
                    self.student_id.user_id.id if self.student_id and self.student_id.user_id else None
                ] if user_id
            ])],
            'priority': '3',
            'state': 'sent'
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Présentation Approuvée'),
                'message': _('La présentation a été approuvée avec succès.'),
                'type': 'success',
            }
        }

    def action_request_revision(self):
        """Demander une révision de la présentation."""
        self.ensure_one()
        if self.status != 'submitted':
            raise ValidationError(_("Seules les présentations soumises peuvent nécessiter une révision."))

        self.write({
            'status': 'revision_required',
            'reviewer_id': self.env.user.id,
            'review_date': fields.Datetime.now()
        })

        # Notification
        self.env['internship.communication'].create({
            'subject': f'Révision Requise : {self.name}',
            'content': f'''
                <p><strong>Révision de Présentation Requise</strong></p>
                <p>Votre présentation "{self.name}" nécessite une révision.</p>
                <p><strong>Notes de Révision :</strong></p>
                <p>{self.review_notes or 'Veuillez contacter votre encadrant pour plus de détails.'}</p>
            ''',
            'communication_type': 'approval_request',
            'stage_id': self.stage_id.id,
            'sender_id': self.env.user.id,
            'recipient_ids': [(6, 0, [
                user_id for user_id in [
                    self.student_id.user_id.id if self.student_id and self.student_id.user_id else None
                ] if user_id
            ])],
            'priority': '1',
            'state': 'sent'
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Révision Demandée'),
                'message': _('Une révision a été demandée pour cette présentation.'),
                'type': 'warning',
            }
        }

    def action_mark_final(self):
        """Marquer la présentation comme version finale."""
        self.ensure_one()
        if self.status != 'approved':
            raise ValidationError(_("Seules les présentations approuvées peuvent être marquées comme finales."))

        self.write({
            'status': 'final',
            'is_final_version': True,
            'reviewed_date': fields.Datetime.now()
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Version Finale'),
                'message': _('Cette présentation est maintenant la version finale.'),
                'type': 'success',
            }
        }

    def action_download(self):
        """Télécharger le fichier de présentation."""
        self.ensure_one()
        if not self.presentation_file:
            raise ValidationError(_("Aucun fichier disponible pour le téléchargement."))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=internship.presentation&id={self.id}&field=presentation_file&filename_field=filename&download=true',
            'target': 'new',
        }
