# -*- coding: utf-8 -*-
"""Internship Communication Model - Unified messaging system"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipCommunication(models.Model):
    """Unified communication model for internship management system.
    
    This model handles ALL communication within internship stages:
    - Internal messaging between participants
    - Comments and feedback on deliverables
    - System notifications and reminders
    - Meeting notes and agenda items
    
    Replaces both internship.message and internship.notification
    """
    _name = 'internship.communication'
    _description = 'Internship Communication System'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'subject'

    # ===============================
    # CORE COMMUNICATION FIELDS
    # ===============================
    
    subject = fields.Char(
        string='Subject',
        required=True,
        tracking=True,
        size=200,
        help="Subject line of the communication"
    )
    
    content = fields.Html(
        string='Content',
        required=True,
        tracking=True,
        help="Main content of the communication"
    )
    
    # ===============================
    # COMMUNICATION CLASSIFICATION
    # ===============================
    
    communication_type = fields.Selection([
        ('internal_message', 'Internal Message'),
        ('document_feedback', 'Document Feedback'),
        ('meeting_note', 'Meeting Note'),
        ('system_notification', 'System Notification'),
        ('approval_request', 'Approval Request'),
        ('deadline_reminder', 'Deadline Reminder'),
        ('stage_update', 'Stage Update'),
        ('general_announcement', 'General Announcement')
    ], string='Communication Type', default='internal_message', tracking=True,
        help="Type of communication being sent")
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True,
        help="Priority level of the communication")
    
    # ===============================
    # PARTICIPANTS AND CONTEXT
    # ===============================
    
    stage_id = fields.Many2one(
        'internship.stage',
        string='Related Internship',
        required=True,
        tracking=True,
        help="Internship this communication is related to"
    )
    
    sender_id = fields.Many2one(
        'res.users',
        string='Sender',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help="User who sent this communication"
    )
    
    recipient_ids = fields.Many2many(
        'res.users',
        string='Recipients',
        help="Users who should receive this communication"
    )
    
    # ===============================
    # INTEGRATION WITH BUSINESS OBJECTS
    # ===============================
    
    document_id = fields.Many2one(
        'internship.document',
        string='Related Document',
        help="Document this communication is related to"
    )
    
    meeting_id = fields.Many2one(
        'internship.meeting',
        string='Related Meeting',
        help="Meeting this communication is related to"
    )
    
    # ===============================
    # WORKFLOW AND STATUS
    # ===============================
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived')
    ], string='Status', default='draft', tracking=True, required=True,
        help="Current status of the communication")
    
    # ===============================
    # THREADING AND RELATIONSHIPS
    # ===============================
    
    parent_id = fields.Many2one(
        'internship.communication',
        string='Parent Communication',
        help="Original communication this is replying to"
    )
    
    child_ids = fields.One2many(
        'internship.communication',
        'parent_id',
        string='Replies',
        help="Replies to this communication"
    )
    
    # ===============================
    # COMPUTED FIELDS
    # ===============================
    
    @api.depends('recipient_ids')
    def _compute_recipient_count(self):
        for comm in self:
            comm.recipient_count = len(comm.recipient_ids)
    
    @api.depends('child_ids')
    def _compute_reply_count(self):
        for comm in self:
            comm.reply_count = len(comm.child_ids)
    
    @api.depends('create_date')
    def _compute_is_recent(self):
        for comm in self:
            if comm.create_date:
                delta = fields.Datetime.now() - comm.create_date
                comm.is_recent = delta.total_seconds() < 86400  # 24 hours
            else:
                comm.is_recent = False
    
    recipient_count = fields.Integer(
        string='Recipient Count',
        compute='_compute_recipient_count',
        store=True
    )
    
    reply_count = fields.Integer(
        string='Reply Count',
        compute='_compute_reply_count',
        store=True
    )
    
    is_recent = fields.Boolean(
        string='Recent',
        compute='_compute_is_recent',
        store=True
    )
    
    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================
    
    @api.constrains('stage_id', 'communication_type')
    def _check_communication_context(self):
        """Ensure communication has proper context based on type."""
        for comm in self:
            if comm.communication_type == 'document_feedback' and not comm.document_id:
                raise ValidationError(_("Document feedback must be related to a document."))
            if comm.communication_type == 'meeting_note' and not comm.meeting_id:
                raise ValidationError(_("Meeting note must be related to a meeting."))
    
    # ===============================
    # BUSINESS METHODS
    # ===============================
    
    def action_send(self):
        """Send the communication."""
        for comm in self:
            if not comm.recipient_ids and comm.communication_type != 'system_notification':
                raise ValidationError(_("Cannot send communication without recipients."))
            
            comm.write({'state': 'sent'})
            comm._send_notifications()
            _logger.info(f"Communication '{comm.subject}' sent")
    
    def action_reply(self):
        """Create a reply to this communication."""
        self.ensure_one()
        return {
            'name': f'Reply to: {self.subject}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.communication',
            'view_mode': 'form',
            'context': {
                'default_subject': f'Re: {self.subject}',
                'default_parent_id': self.id,
                'default_stage_id': self.stage_id.id,
                'default_document_id': self.document_id.id if self.document_id else False,
                'default_meeting_id': self.meeting_id.id if self.meeting_id else False,
                'default_recipient_ids': [(6, 0, [self.sender_id.id])],
            },
            'target': 'current',
        }
    
    def _send_notifications(self):
        """Send email notifications for this communication."""
        for comm in self:
            if comm.recipient_ids:
                try:
                    comm.message_post(
                        body=comm._get_email_template(),
                        subject=f"[Internship] {comm.subject}",
                        partner_ids=comm.recipient_ids.mapped('partner_id').ids,
                        subtype_xmlid='mail.mt_comment',
                        message_type='email',
                    )
                except Exception as e:
                    _logger.error(f"Failed to send email notification: {str(e)}")
    
    def _get_email_template(self):
        """Generate email template for the communication."""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #2c3e50;">Internship Management System</h2>
                <h3 style="color: #3498db;">{self.subject}</h3>
                <p><strong>From:</strong> {self.sender_id.name}</p>
                <p><strong>Type:</strong> {dict(self._fields['communication_type'].selection).get(self.communication_type)}</p>
                <p><strong>Priority:</strong> {dict(self._fields['priority'].selection).get(self.priority)}</p>
                <hr/>
                <div style="background-color: white; padding: 15px; border-radius: 3px;">
                    {self.content}
                </div>
                <hr/>
                <p style="color: #7f8c8d; font-size: 12px;">
                    Please log in to the system to reply to this communication.
                </p>
            </div>
        </div>
        """
        