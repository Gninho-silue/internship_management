# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import os


class InternshipPresentation(models.Model):
    _name = 'internship.presentation'
    _description = 'Internship Defense Presentation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # BASIC FIELDS
    name = fields.Char(
        string='Presentation Name',
        required=True,
        tracking=True,
        help="Name of the presentation file"
    )
    
    stage_id = fields.Many2one(
        'internship.stage',
        string='Internship Stage',
        required=True,
        ondelete='cascade',
        tracking=True,
        help="Related internship stage"
    )
    
    student_id = fields.Many2one(
        'internship.student',
        string='Student',
        related='stage_id.student_id',
        store=True,
        help="Student who submitted the presentation"
    )
    
    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Supervisor',
        related='stage_id.supervisor_id',
        store=True,

        help="Supervisor of the internship"
    )

    # FILE MANAGEMENT
    presentation_file = fields.Binary(
        string='Presentation File',
        required=True,
        help="Upload the presentation file (PDF, PPT, PPTX)"
    )
    
    filename = fields.Char(
        string='Filename',
        help="Original filename of the uploaded file"
    )
    
    file_size = fields.Float(
        string='File Size (MB)',
        compute='_compute_file_size',
        store=True,
        help="Size of the uploaded file in MB"
    )
    
    file_type = fields.Selection([
        ('pdf', 'PDF'),
        ('ppt', 'PowerPoint (.ppt)'),
        ('pptx', 'PowerPoint (.pptx)'),
        ('other', 'Other Format')
    ], string='File Type', compute='_compute_file_type', store=True)

    # STATUS AND VERSIONING
    version = fields.Char(
        string='Version',
        default='1.0',
        tracking=True,
        help="Version number of the presentation"
    )
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('revision_required', 'Revision Required'),
        ('final', 'Final Version')
    ], string='Status', default='draft', tracking=True)
    
    is_final_version = fields.Boolean(
        string='Final Version',
        default=False,
        help="Mark as the final version for defense"
    )

    # REVIEW AND FEEDBACK
    review_notes = fields.Text(
        string='Review Notes',
        help="Notes from supervisor review"
    )
    
    reviewer_id = fields.Many2one(
        'res.users',
        string='Reviewed By',
        help="User who reviewed the presentation"
    )
    
    review_date = fields.Datetime(
        string='Review Date',
        help="Date when the presentation was reviewed"
    )
    
    feedback_ids = fields.One2many(
        'internship.document.feedback',
        'presentation_id',
        string='Feedback',
        help="Feedback related to this presentation"
    )

    # DATES
    submission_date = fields.Datetime(
        string='Submission Date',
        default=fields.Datetime.now,
        tracking=True,
        help="Date when the presentation was submitted"
    )
    
    deadline_date = fields.Datetime(
        string='Deadline',
        related='stage_id.defense_date',
        store=True,
        help="Deadline for presentation submission"
    )
    
    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_overdue_status',
        store=True,
        help="Whether the submission is overdue"
    )

    # COMPUTED FIELDS
    @api.depends('presentation_file')
    def _compute_file_size(self):
        """Calculate file size in MB."""
        for presentation in self:
            if presentation.presentation_file:
                # Approximate calculation (base64 encoded file)
                file_size_bytes = len(presentation.presentation_file) * 3 / 4
                presentation.file_size = round(file_size_bytes / (1024 * 1024), 2)
            else:
                presentation.file_size = 0.0

    @api.depends('filename')
    def _compute_file_type(self):
        """Determine file type from filename."""
        for presentation in self:
            if presentation.filename:
                ext = presentation.filename.lower().split('.')[-1]
                if ext == 'pdf':
                    presentation.file_type = 'pdf'
                elif ext == 'ppt':
                    presentation.file_type = 'ppt'
                elif ext == 'pptx':
                    presentation.file_type = 'pptx'
                else:
                    presentation.file_type = 'other'
            else:
                presentation.file_type = 'other'

    @api.depends('submission_date', 'deadline_date')
    def _compute_overdue_status(self):
        """Check if submission is overdue."""
        for presentation in self:
            if presentation.deadline_date and presentation.submission_date:
                presentation.is_overdue = presentation.submission_date > presentation.deadline_date
            else:
                presentation.is_overdue = False

    # CONSTRAINTS
    @api.constrains('presentation_file', 'file_size')
    def _check_file_constraints(self):
        """Validate file constraints."""
        for presentation in self:
            # Check file size (max 50MB)
            if presentation.file_size > 50:
                raise ValidationError(_("Presentation file size cannot exceed 50MB."))
            
            # Check file type
            if presentation.file_type == 'other':
                raise ValidationError(_("Only PDF, PPT, and PPTX files are allowed for presentations."))

    @api.constrains('version')
    def _check_version_format(self):
        """Validate version format."""
        for presentation in self:
            if presentation.version and not presentation.version.replace('.', '').isdigit():
                raise ValidationError(_("Version must be in format X.Y (e.g., 1.0, 2.1)"))

    # ACTIONS
    def action_submit(self):
        """Submit presentation for review."""
        self.ensure_one()
        if self.status != 'draft':
            raise ValidationError(_("Only draft presentations can be submitted."))
        
        if not self.presentation_file:
            raise ValidationError(_("Please upload a presentation file before submitting."))
        
        # Update status
        self.write({
            'status': 'submitted',
            'submission_date': fields.Datetime.now()
        })
        
        # Create communication notification
        self.env['internship.communication'].create({
            'subject': f'New Presentation Submitted: {self.name}',
            'content': f'''
                <p><strong>New Presentation Submitted</strong></p>
                <p>Student {self.student_id.full_name if self.student_id else 'N/A'} has submitted a new presentation:</p>
                <ul>
                    <li><strong>Presentation:</strong> {self.name}</li>
                    <li><strong>Version:</strong> {self.version}</li>
                    <li><strong>File Type:</strong> {dict(self._fields['file_type'].selection)[self.file_type]}</li>
                    <li><strong>File Size:</strong> {self.file_size} MB</li>
                </ul>
                <p>Please review the presentation and provide feedback.</p>
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
                'title': _('Presentation Submitted'),
                'message': _('Your presentation has been submitted for review.'),
                'type': 'success',
            }
        }

    def action_approve(self):
        """Approve presentation."""
        self.ensure_one()
        if self.status not in ['submitted', 'revision_required']:
            raise ValidationError(_("Only submitted or revision-required presentations can be approved."))
        
        self.write({
            'status': 'approved',
            'reviewer_id': self.env.user.id,
            'review_date': fields.Datetime.now()
        })
        
        # Create communication notification
        self.env['internship.communication'].create({
            'subject': f'Presentation Approved: {self.name}',
            'content': f'''
                <p><strong>Presentation Approved</strong></p>
                <p>Your presentation "{self.name}" has been approved by {self.env.user.name}.</p>
                <p>You can now proceed with your defense preparation.</p>
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

    def action_request_revision(self):
        """Request revision of presentation."""
        self.ensure_one()
        if self.status != 'submitted':
            raise ValidationError(_("Only submitted presentations can be requested for revision."))
        
        self.write({
            'status': 'revision_required',
            'reviewer_id': self.env.user.id,
            'review_date': fields.Datetime.now()
        })
        
        # Create communication notification
        self.env['internship.communication'].create({
            'subject': f'Presentation Revision Required: {self.name}',
            'content': f'''
                <p><strong>Presentation Revision Required</strong></p>
                <p>Your presentation "{self.name}" requires revision.</p>
                <p><strong>Review Notes:</strong></p>
                <p>{self.review_notes or 'Please contact your supervisor for detailed feedback.'}</p>
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

    def action_mark_final(self):
        """Mark presentation as final version."""
        self.ensure_one()
        if self.status != 'approved':
            raise ValidationError(_("Only approved presentations can be marked as final."))
        
        # Unmark other final versions for this stage
        self.stage_id.presentation_ids.filtered(lambda p: p.is_final_version and p.id != self.id).write({
            'is_final_version': False
        })
        
        self.write({
            'is_final_version': True,
            'status': 'final'
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Final Version'),
                'message': _('This presentation has been marked as the final version.'),
                'type': 'success',
            }
        }

    def action_download(self):
        """Download presentation file."""
        self.ensure_one()
        if not self.presentation_file:
            raise ValidationError(_("No file to download."))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=internship.presentation&id={self.id}&field=presentation_file&filename_field=filename&download=true',
            'target': 'new',
        }

    # OVERRIDE CREATE METHOD
    @api.model
    def create(self, vals):
        """Override create to set default values."""
        # Set filename if not provided
        if 'filename' not in vals and 'presentation_file' in vals:
            vals['filename'] = f"presentation_{vals.get('name', 'unknown')}.pdf"
        
        presentation = super().create(vals)
        
        # Create communication for new presentation
        if presentation.stage_id and presentation.stage_id.supervisor_id and presentation.stage_id.supervisor_id.user_id:
            self.env['internship.communication'].create({
                'subject': f'New Presentation Created: {presentation.name}',
                'content': f'''
                    <p><strong>New Presentation Created</strong></p>
                    <p>Student {presentation.student_id.full_name if presentation.student_id else 'N/A'} has created a new presentation:</p>
                    <p><strong>Presentation:</strong> {presentation.name}</p>
                    <p><strong>Version:</strong> {presentation.version}</p>
                ''',
                'communication_type': 'internal_message',
                'stage_id': presentation.stage_id.id,
                'sender_id': self.env.user.id,
                'recipient_ids': [(6, 0, [presentation.stage_id.supervisor_id.user_id.id])],
                'priority': '3',
                'state': 'sent'
            })
        
        return presentation
