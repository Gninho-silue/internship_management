# -*- coding: utf-8 -*-
"""Internship Document Feedback Model"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipDocumentFeedback(models.Model):
    """Document feedback model for internship management system.
    
    This model handles comments and feedback on deliverables,
    as specified in the requirements document.
    """
    _name = 'internship.document.feedback'
    _description = 'Document Feedback and Comments'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'feedback_summary'

    # ===============================
    # CORE FEEDBACK FIELDS
    # ===============================
    
    document_id = fields.Many2one(
        'internship.document',
        string='Document',
        tracking=True,
        help="Document this feedback is about"
    )
    
    presentation_id = fields.Many2one(
        'internship.presentation',
        string='Presentation',
        tracking=True,
        help="Presentation this feedback is about"
    )
    
    reviewer_id = fields.Many2one(
        'res.users',
        string='Reviewer',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help="User providing the feedback"
    )
    
    feedback_type = fields.Selection([
        ('approval', 'Approval'),
        ('revision_required', 'Revision Required'),
        ('comment', 'Comment'),
        ('question', 'Question'),
        ('suggestion', 'Suggestion'),
        ('praise', 'Praise')
    ], string='Feedback Type', default='comment', tracking=True,
        help="Type of feedback being provided")
    
    feedback_summary = fields.Char(
        string='Feedback Summary',
        required=True,
        size=200,
        help="Brief summary of the feedback"
    )
    
    detailed_feedback = fields.Html(
        string='Detailed Feedback',
        required=True,
        help="Detailed feedback content"
    )
    
    # ===============================
    # FEEDBACK STATUS AND WORKFLOW
    # ===============================
    
    status = fields.Selection([
        ('pending', 'Pending Review'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed')
    ], string='Status', default='pending', tracking=True,
        help="Current status of the feedback")
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical')
    ], string='Priority', default='1', tracking=True,
        help="Priority level of the feedback")
    
    # ===============================
    # INTEGRATION FIELDS
    # ===============================
    
    stage_id = fields.Many2one(
        'internship.stage',
        related='document_id.stage_id',
        string='Related Internship',
        store=True,
        help="Internship this feedback is related to"
    )
    
    communication_id = fields.Many2one(
        'internship.communication',
        string='Related Communication',
        help="Communication record created for this feedback"
    )
    
    # ===============================
    # RESPONSE AND FOLLOW-UP
    # ===============================
    
    response_date = fields.Datetime(
        string='Response Date',
        readonly=True,
        help="When the feedback was responded to"
    )
    
    response_content = fields.Html(
        string='Response',
        help="Response to the feedback"
    )
    
    response_by = fields.Many2one(
        'res.users',
        string='Responded By',
        readonly=True,
        help="User who responded to the feedback"
    )
    
    # ===============================
    # COMPUTED FIELDS
    # ===============================
    
    @api.depends('create_date', 'response_date')
    def _compute_response_time(self):
        for feedback in self:
            if feedback.response_date and feedback.create_date:
                delta = feedback.response_date - feedback.create_date
                feedback.response_time_hours = delta.total_seconds() / 3600
            else:
                feedback.response_time_hours = 0
    
    @api.depends('status')
    def _compute_is_resolved(self):
        for feedback in self:
            feedback.is_resolved = feedback.status in ['resolved', 'dismissed']
    
    response_time_hours = fields.Float(
        string='Response Time (Hours)',
        compute='_compute_response_time',
        store=True,
        help="Time taken to respond to feedback"
    )
    
    is_resolved = fields.Boolean(
        string='Is Resolved',
        compute='_compute_is_resolved',
        store=True,
        help="Whether this feedback has been resolved"
    )
    
    # ===============================
    # BUSINESS METHODS
    # ===============================
    
    def action_acknowledge(self):
        """Acknowledge the feedback."""
        self.write({'status': 'acknowledged'})
        self._create_communication_record()
    
    def action_resolve(self):
        """Mark feedback as resolved."""
        self.write({
            'status': 'resolved',
            'response_date': fields.Datetime.now(),
            'response_by': self.env.user.id
        })
        self._create_communication_record()
    
    def action_dismiss(self):
        """Dismiss the feedback."""
        self.write({
            'status': 'dismissed',
            'response_date': fields.Datetime.now(),
            'response_by': self.env.user.id
        })
    
    def action_respond(self):
        """Create a response to the feedback."""
        self.ensure_one()
        return {
            'name': f'Respond to Feedback: {self.feedback_summary}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.document.feedback',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _create_communication_record(self):
        """Create a communication record for this feedback."""
        if not self.communication_id:
            comm_vals = {
                'subject': f'Feedback on {self.document_id.name}',
                'content': f'<p><strong>Feedback Type:</strong> {dict(self._fields["feedback_type"].selection).get(self.feedback_type)}</p><p><strong>Summary:</strong> {self.feedback_summary}</p><p><strong>Details:</strong></p>{self.detailed_feedback}',
                'communication_type': 'document_feedback',
                'stage_id': self.stage_id.id,
                'document_id': self.document_id.id,
                'sender_id': self.reviewer_id.id,
                'priority': self.priority,
                'state': 'sent'
            }
            
            # Add recipients based on document ownership
            recipients = []
            if self.document_id.stage_id.student_id:
                recipients.append(self.document_id.stage_id.student_id.user_id.id)
            if self.document_id.stage_id.supervisor_id:
                recipients.append(self.document_id.stage_id.supervisor_id.user_id.id)
            
            if recipients:
                comm_vals['recipient_ids'] = [(6, 0, recipients)]
            
            communication = self.env['internship.communication'].create(comm_vals)
            self.write({'communication_id': communication.id})
    
    # ===============================
    # CONSTRAINTS
    # ===============================
    
    @api.constrains('document_id', 'presentation_id')
    def _check_feedback_target(self):
        """Ensure either document or presentation is specified, but not both."""
        for feedback in self:
            if not feedback.document_id and not feedback.presentation_id:
                raise ValidationError(_("Either a document or presentation must be specified."))
            if feedback.document_id and feedback.presentation_id:
                raise ValidationError(_("Cannot specify both document and presentation."))

    @api.constrains('document_id', 'presentation_id', 'reviewer_id')
    def _check_reviewer_access(self):
        """Ensure reviewer has access to the document or presentation."""
        for feedback in self:
            target_stage = None
            if feedback.document_id:
                target_stage = feedback.document_id.stage_id
            elif feedback.presentation_id:
                target_stage = feedback.presentation_id.stage_id
            
            if target_stage and target_stage.student_id.user_id == feedback.reviewer_id:
                raise ValidationError(_("Students cannot provide feedback on their own documents or presentations."))