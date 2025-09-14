# -*- coding: utf-8 -*-
"""Internship Document Model"""

import logging
import os

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipDocument(models.Model):
    """Document model for internship management system.

    This model handles all document-related operations including
    file uploads, version control, review workflows, and document
    lifecycle management for internships.

    Key Features:
    - Document version control and history
    - Review workflow with approval/rejection
    - File metadata tracking (size, type, etc.)
    - Integration with internship stages and meetings
    - Automatic notifications for document status changes
    - Access control and security
    """
    _name = 'internship.document'
    _description = 'Internship Document Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_upload desc, name'
    _rec_name = 'name'

    # ===============================
    # CORE IDENTIFICATION FIELDS
    # ===============================

    name = fields.Char(
        string='Document Title',
        required=True,
        tracking=True,
        size=200,
        help="Title or name of the document"
    )

    document_type = fields.Selection([
        ('convention', 'Internship Convention'),
        ('progress_report', 'Progress Report'),
        ('final_report', 'Final Report'),
        ('presentation', 'Presentation'),
        ('evaluation', 'Evaluation Form'),
        ('attestation', 'Attestation'),
        ('other', 'Other')
    ], string='Document Type', required=True, tracking=True,
        help="Type of document being uploaded")

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    stage_id = fields.Many2one(
        'internship.stage',
        string='Internship',
        required=True,
        tracking=True,
        ondelete='cascade',
        help="Internship this document belongs to"
    )

    student_id = fields.Many2one(
        'internship.student',
        string='Student',
        related='stage_id.student_id',
        store=True,
        readonly=True,
        help="Student who uploaded this document"
    )

    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Supervisor',
        related='stage_id.supervisor_id',
        store=True,
        readonly=True,
        help="Supervisor responsible for reviewing this document"
    )

    meeting_id = fields.Many2one(
        'internship.meeting',
        string='Related Meeting',
        help="Meeting this document is related to"
    )

    uploaded_by = fields.Many2one(
        'res.users',
        string='Uploaded By',
        default=lambda self: self.env.user,
        readonly=True,
        help="User who uploaded this document"
    )

    reviewed_by = fields.Many2one(
        'res.users',
        string='Reviewed By',
        readonly=True,
        help="User who reviewed this document"
    )
        # ===============================
    # FEEDBACK INTEGRATION
    # ===============================
    
    feedback_ids = fields.One2many(
        'internship.document.feedback',
        'document_id',
        string='Feedback',
        help="All feedback received on this document"
    )
    
    communication_ids = fields.One2many(
        'internship.communication',
        'document_id',
        string='Related Communications',
        help="Communications related to this document"
    )
    
    # ===============================
    # FEEDBACK STATISTICS
    # ===============================
    
    @api.depends('feedback_ids')
    def _compute_feedback_stats(self):
        for doc in self:
            doc.total_feedback = len(doc.feedback_ids)
            doc.pending_feedback = len(doc.feedback_ids.filtered(
                lambda f: f.status == 'pending'
            ))
            doc.approved_feedback = len(doc.feedback_ids.filtered(
                lambda f: f.feedback_type == 'approval'
            ))
    
    total_feedback = fields.Integer(
        string='Total Feedback',
        compute='_compute_feedback_stats',
        store=True
    )
    
    pending_feedback = fields.Integer(
        string='Pending Feedback',
        compute='_compute_feedback_stats',
        store=True
    )
    
    approved_feedback = fields.Integer(
        string='Approved Feedback',
        compute='_compute_feedback_stats',
        store=True
    )

    # ===============================
    # FILE MANAGEMENT FIELDS
    # ===============================

    file = fields.Binary(
        string='Document File',
        attachment=True,
        required=True,
        help="The actual document file"
    )

    filename = fields.Char(
        string='Original Filename',
        help="Original name of the uploaded file"
    )

    file_size = fields.Integer(
        string='File Size (bytes)',
        compute='_compute_file_size',
        store=True,
        help="Size of the uploaded file in bytes"
    )

    file_type = fields.Char(
        string='File Type',
        compute='_compute_file_type',
        store=True,
        help="MIME type of the uploaded file"
    )

    version = fields.Char(
        string='Version',
        default='1.0',
        help="Document version number"
    )

    # ===============================
    # WORKFLOW AND STATUS FIELDS
    # ===============================

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived')
    ], string='Status', default='draft', tracking=True, required=True,
        help="Current status of the document in the review process")

    review_required = fields.Boolean(
        string='Review Required',
        default=True,
        help="Whether this document requires supervisor review"
    )

    review_deadline = fields.Datetime(
        string='Review Deadline',
        help="Deadline for document review"
    )

    review_date = fields.Datetime(
        string='Review Date',
        readonly=True,
        help="Date when the document was reviewed"
    )

    review_comments = fields.Html(
        string='Review Comments',
        help="Comments from the reviewer"
    )

    # ===============================
    # METADATA FIELDS
    # ===============================

    date_upload = fields.Datetime(
        string='Upload Date',
        default=fields.Datetime.now,
        readonly=True,
        help="Date and time when the document was uploaded"
    )

    last_modified = fields.Datetime(
        string='Last Modified',
        default=fields.Datetime.now,
        help="Date and time when the document was last modified"
    )

    description = fields.Html(
        string='Description',
        help="Detailed description of the document content"
    )

    keywords = fields.Char(
        string='Keywords',
        help="Comma-separated keywords for document search"
    )

    comments = fields.Text(
        string='Internal Comments',
        help="Internal notes and comments about the document"
    )

    # ===============================
    # ACCESS CONTROL FIELDS
    # ===============================

    is_public = fields.Boolean(
        string='Public Document',
        default=False,
        help="Whether this document is publicly accessible"
    )

    access_level = fields.Selection([
        ('private', 'Private'),
        ('internal', 'Internal'),
        ('public', 'Public')
    ], string='Access Level', default='internal',
        help="Access level for this document")

    # ===============================
    # COMPUTED FIELDS
    # ===============================

    @api.depends('file')
    def _compute_file_size(self):
        """Calculate file size from binary data."""
        for doc in self:
            if doc.file:
                # Get file size from attachment
                attachment = self.env['ir.attachment'].search([
                    ('res_model', '=', 'internship.document'),
                    ('res_id', '=', doc.id),
                    ('name', '=', doc.filename or 'document')
                ], limit=1)
                doc.file_size = attachment.file_size if attachment else 0
            else:
                doc.file_size = 0

    @api.depends('filename')
    def _compute_file_type(self):
        """Extract file type from filename extension."""
        for doc in self:
            if doc.filename:
                ext = os.path.splitext(doc.filename)[1].lower()
                doc.file_type = ext if ext else 'unknown'
            else:
                doc.file_type = 'unknown'

    # ===============================
    # TECHNICAL FIELDS
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Whether this document record is active"
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order of documents in lists"
    )

    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================

    @api.constrains('file_size')
    def _check_file_size(self):
        """Ensure file size is within acceptable limits."""
        max_size = 50 * 1024 * 1024  # 50MB
        for doc in self:
            if doc.file_size > max_size:
                raise ValidationError(_("File size cannot exceed 50MB."))

    @api.constrains('review_deadline')
    def _check_review_deadline(self):
        """Ensure review deadline is in the future."""
        for doc in self:
            if doc.review_deadline and doc.review_deadline < fields.Datetime.now():
                raise ValidationError(_("Review deadline must be in the future."))

    _sql_constraints = [
        ('unique_document_per_stage_type',
         'UNIQUE(stage_id, document_type, version)',
         'A document of this type and version already exists for this internship.'),
    ]

    # ===============================
    # CRUD METHODS
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method with logging and validation."""
        _logger.info(f"Creating {len(vals_list)} document record(s)")

        for vals in vals_list:
            # Auto-generate filename if not provided
            if vals.get('file') and not vals.get('filename'):
                doc_type = vals.get('document_type', 'document')
                vals['filename'] = f"{doc_type}_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            # Set upload date
            if not vals.get('date_upload'):
                vals['date_upload'] = fields.Datetime.now()

        documents = super().create(vals_list)

        for doc in documents:
            _logger.info(f"Created document: {doc.name} for internship {doc.stage_id.title}")

            # Create communication for supervisor if review required
            if doc.review_required and doc.supervisor_id and doc.supervisor_id.user_id:
                self.env['internship.communication'].create({
                    'subject': f'New Document for Review: {doc.name}',
                    'content': f'<p>Document "{doc.name}" has been submitted for your review.</p>',
                    'communication_type': 'approval_request',
                    'stage_id': doc.stage_id.id,
                    'document_id': doc.id,
                    'sender_id': self.env.user.id,
                    'recipient_ids': [(6, 0, [doc.supervisor_id.user_id.id])],
                    'priority': '2',
                    'state': 'sent'
                })

        return documents

    def write(self, vals):
        """Override write method with logging and validation."""
        if 'state' in vals:
            _logger.info(f"Document {self.name} status changed to {vals['state']}")

        if 'file' in vals:
            vals['last_modified'] = fields.Datetime.now()

        return super().write(vals)

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_submit_for_review(self):
        """Submit document for supervisor review."""
        self.write({'state': 'submitted'})

    def action_start_review(self):
        """Start reviewing the document."""
        self.write({
            'state': 'under_review',
            'reviewed_by': self.env.user.id
        })

    def action_approve(self):
        """Approve the document."""
        self.write({
            'state': 'approved',
            'review_date': fields.Datetime.now(),
            'reviewed_by': self.env.user.id
        })

    def action_reject(self):
        """Reject the document."""
        self.write({
            'state': 'rejected',
            'review_date': fields.Datetime.now(),
            'reviewed_by': self.env.user.id
        })

    def action_archive(self):
        """Archive the document."""
        self.write({'state': 'archived'})

    def action_download(self):
        """Download the document file."""
        self.ensure_one()
        if not self.file:
            raise ValidationError(_("No file available for download."))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=internship.document&id={self.id}&field=file&filename_field=filename&download=true',
            'target': 'new',
        }
    
    def action_add_feedback(self):
        """Add feedback to this document."""
        self.ensure_one()
        return {
            'name': f'Add Feedback - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.document.feedback',
            'view_mode': 'form',
            'context': {
                'default_document_id': self.id,
                'default_stage_id': self.stage_id.id,
                'default_reviewer_id': self.env.user.id,
            },
            'target': 'current',
        }
    
    def action_view_feedback(self):
        """View all feedback for this document."""
        self.ensure_one()
        return {
            'name': f'Feedback - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.document.feedback',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {
                'default_document_id': self.id,
                'default_stage_id': self.stage_id.id,
            },
            'target': 'current',
        }


    # ===============================
    # UTILITY METHODS
    # ===============================

    # ===============================
    # FEEDBACK STATISTICS
    # ===============================
    
    @api.depends('feedback_ids')
    def _compute_feedback_stats(self):
        for doc in self:
            doc.feedback_count = len(doc.feedback_ids)
            doc.pending_feedback_count = len(doc.feedback_ids.filtered(
                lambda f: f.status == 'pending'
            ))
            if doc.feedback_ids:
                last_feedback = doc.feedback_ids.sorted('create_date', reverse=True)[0]
                doc.last_feedback_date = last_feedback.create_date
                doc.last_reviewer_id = last_feedback.reviewer_id
            else:
                doc.last_feedback_date = False
                doc.last_reviewer_id = False
    
    feedback_count = fields.Integer(
        string='Feedback Count',
        compute='_compute_feedback_stats',
        store=True
    )
    
    pending_feedback_count = fields.Integer(
        string='Pending Feedback Count',
        compute='_compute_feedback_stats',
        store=True
    )
    
    last_feedback_date = fields.Datetime(
        string='Last Feedback Date',
        compute='_compute_feedback_stats',
        store=True
    )
    
    last_reviewer_id = fields.Many2one(
        'res.users',
        string='Last Reviewer',
        compute='_compute_feedback_stats',
        store=True
    )

    def name_get(self):
        """Custom name display: Name (Type)."""
        result = []
        for doc in self:
            name = doc.name
            if doc.document_type:
                type_name = dict(doc._fields['document_type'].selection).get(doc.document_type)
                name = f"{name} ({type_name})"
            result.append((doc.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        """Custom search: search by name, type, or keywords."""
        args = args or []
        domain = []

        if name:
            domain = ['|', '|', '|',
                      ('name', operator, name),
                      ('document_type', operator, name),
                      ('keywords', operator, name),
                      ('description', operator, name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid, order=order)

    def get_document_statistics(self):
        """Return statistical data for this document."""
        self.ensure_one()
        return {
            'file_size_mb': round(self.file_size / (1024 * 1024), 2) if self.file_size else 0,
            'days_since_upload': (fields.Datetime.now() - self.date_upload).days if self.date_upload else 0,
            'review_days': (self.review_date - self.date_upload).days if self.review_date and self.date_upload else 0,
            'is_overdue': self.review_deadline and self.review_deadline < fields.Datetime.now(),
        }