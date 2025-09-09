# -*- coding: utf-8 -*-
"""Internship Message Model"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipMessage(models.Model):
    """Message model for internship management system.

    This model handles internal communication between users in the
    internship management system, providing a structured messaging
    system with threading, priorities, and integration with other
    internship-related objects.

    Key Features:
    - Internal messaging system
    - Message threading and replies
    - Priority and urgency levels
    - Integration with internships, documents, and meetings
    - Read status tracking
    - Message archiving and organization
    """
    _name = 'internship.message'
    _description = 'Internship Internal Messaging'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'subject'

    # ===============================
    # CORE MESSAGE FIELDS
    # ===============================

    subject = fields.Char(
        string='Subject',
        required=True,
        tracking=True,
        size=200,
        help="Subject line of the message"
    )

    body = fields.Html(
        string='Message Content',
        required=True,
        tracking=True,
        help="Main content of the message"
    )

    # ===============================
    # PARTICIPANT FIELDS
    # ===============================

    sender_id = fields.Many2one(
        'res.users',
        string='Sender',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help="User who sent this message"
    )

    recipient_ids = fields.Many2many(
        'res.users',
        string='Recipients',
        required=True,
        help="Users who should receive this message"
    )

    cc_ids = fields.Many2many(
        'res.users',
        'message_cc_rel',
        string='CC',
        help="Users who should receive a copy of this message"
    )

    # ===============================
    # MESSAGE CLASSIFICATION
    # ===============================

    message_type = fields.Selection([
        ('internal', 'Internal Communication'),
        ('notification', 'System Notification'),
        ('reminder', 'Reminder'),
        ('announcement', 'Announcement'),
        ('urgent', 'Urgent Message')
    ], string='Message Type', default='internal', tracking=True,
        help="Type of message being sent")

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True,
        help="Priority level of the message")

    # ===============================
    # WORKFLOW AND STATUS FIELDS
    # ===============================

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived')
    ], string='Status', default='draft', tracking=True, required=True,
        help="Current status of the message")

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    stage_id = fields.Many2one(
        'internship.stage',
        string='Related Internship',
        help="Internship this message is related to"
    )

    document_id = fields.Many2one(
        'internship.document',
        string='Related Document',
        help="Document this message is related to"
    )

    meeting_id = fields.Many2one(
        'internship.meeting',
        string='Related Meeting',
        help="Meeting this message is related to"
    )

    parent_id = fields.Many2one(
        'internship.message',
        string='Parent Message',
        help="Original message this is replying to"
    )

    child_ids = fields.One2many(
        'internship.message',
        'parent_id',
        string='Replies',
        help="Replies to this message"
    )

    # ===============================
    # COMPUTED FIELDS
    # ===============================

    @api.depends('recipient_ids')
    def _compute_is_read(self):
        """Check if current user has read this message."""
        for message in self:
            message.is_read = self.env.user in message.recipient_ids

    @api.depends('recipient_ids')
    def _compute_read_count(self):
        """Calculate number of recipients."""
        for message in self:
            message.read_count = len(message.recipient_ids)

    @api.depends('child_ids')
    def _compute_reply_count(self):
        """Calculate number of replies."""
        for message in self:
            message.reply_count = len(message.child_ids)

    @api.depends('create_date')
    def _compute_is_recent(self):
        """Check if message was created recently (within 24 hours)."""
        for message in self:
            if message.create_date:
                delta = fields.Datetime.now() - message.create_date
                message.is_recent = delta.total_seconds() < 86400  # 24 hours
            else:
                message.is_recent = False

    is_read = fields.Boolean(
        string='Read by Me',
        compute='_compute_is_read',
        store=True,
        help="Whether current user has read this message"
    )

    read_count = fields.Integer(
        string='Recipient Count',
        compute='_compute_read_count',
        store=True,
        help="Number of recipients"
    )

    reply_count = fields.Integer(
        string='Reply Count',
        compute='_compute_reply_count',
        store=True,
        help="Number of replies to this message"
    )

    is_recent = fields.Boolean(
        string='Recent Message',
        compute='_compute_is_recent',
        store=True,
        help="Whether this message was created recently"
    )

    # ===============================
    # TECHNICAL FIELDS
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Whether this message is active"
    )

    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================

    @api.constrains('recipient_ids')
    def _check_recipients(self):
        """Ensure message has at least one recipient."""
        for message in self:
            if not message.recipient_ids:
                raise ValidationError(_("Message must have at least one recipient."))

    @api.constrains('sender_id', 'recipient_ids')
    def _check_sender_not_recipient(self):
        """Ensure sender is not in recipients list."""
        for message in self:
            if message.sender_id in message.recipient_ids:
                raise ValidationError(_("Sender cannot be a recipient of their own message."))

    # ===============================
    # CRUD METHODS
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create method with proper message handling."""
        _logger.info(f"Creating {len(vals_list)} message record(s)")

        for vals in vals_list:
            # Auto-set sender if not provided
            if not vals.get('sender_id'):
                vals['sender_id'] = self.env.user.id

            # Auto-generate subject if not provided
            if not vals.get('subject') and vals.get('body'):
                # Extract first line as subject
                body_text = vals['body'].replace('<p>', '').replace('</p>', '')
                vals['subject'] = body_text[:50] + '...' if len(body_text) > 50 else body_text

            # Ensure recipients are properly set
            if not vals.get('recipient_ids'):
                _logger.warning("Creating message without recipients!")

        messages = super().create(vals_list)

        for message in messages:
            _logger.info(f"Created message: {message.subject}")
            _logger.info(f"Recipients: {[r.name for r in message.recipient_ids]}")

            # Send email notifications if message is sent
            if message.state == 'sent':
                message._send_email_notifications()
                message._create_notifications()

        return messages

    def write(self, vals):
        """Override write method with logging."""
        if 'state' in vals:
            _logger.info(f"Message {self.subject} status changed to {vals['state']}")

        result = super().write(vals)

        # Send notifications when message is sent
        if 'state' in vals and vals['state'] == 'sent':
            self._send_email_notifications()

        return result

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_send(self):
        """Enhanced send method with better notification handling."""
        for message in self:
            # Validate before sending
            if not message.recipient_ids:
                raise ValidationError(_("Cannot send message without recipients."))

            # Update state
            message.write({'state': 'sent'})

            # Create notifications first
            message._create_notifications()

            # Then send emails
            message._send_email_notifications()

            _logger.info(f"Message '{message.subject}' sent to {len(message.recipient_ids)} recipients")

    def action_mark_as_read(self):
        """Mark message as read by current user."""
        self.write({'state': 'read'})

    def action_reply(self):
        """Create a reply to this message."""
        self.ensure_one()
        return {
            'name': f'Reply to: {self.subject}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.message',
            'view_mode': 'form',
            'context': {
                'default_subject': f'Re: {self.subject}',
                'default_parent_id': self.id,
                'default_recipient_ids': [(6, 0, [self.sender_id.id])],
                'default_stage_id': self.stage_id.id if self.stage_id else False,
                'default_document_id': self.document_id.id if self.document_id else False,
                'default_meeting_id': self.meeting_id.id if self.meeting_id else False,
            },
            'target': 'current',
        }

    def action_archive(self):
        """Archive the message."""
        self.write({'state': 'archived'})

    def action_forward(self):
        """Forward this message to other users."""
        self.ensure_one()
        return {
            'name': f'Forward: {self.subject}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.message',
            'view_mode': 'form',
            'context': {
                'default_subject': f'Fwd: {self.subject}',
                'default_body': f'<p>Forwarded message:</p><hr/>{self.body}',
                'default_stage_id': self.stage_id.id if self.stage_id else False,
                'default_document_id': self.document_id.id if self.document_id else False,
                'default_meeting_id': self.meeting_id.id if self.meeting_id else False,
            },
            'target': 'current',
        }

    # ===============================
    # NOTIFICATION METHODS
    # ===============================
    def _send_email_notifications(self):
        """Enhanced email notification method using proper Odoo practices."""
        for message in self:
            if message.recipient_ids:
                try:
                    # Use message_post for proper email handling
                    message.message_post(
                        body=message._get_email_template(message),
                        subject=f"[Internship Management] {message.subject}",
                        partner_ids=message.recipient_ids.mapped('partner_id').ids,
                        email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                        subtype_xmlid='mail.mt_comment',
                        message_type='email',
                    )

                    _logger.info(f"Email notifications sent for message: {message.subject}")

                except Exception as e:
                    _logger.error(f"Failed to send email notifications via message_post: {str(e)}")

                    # Fallback to sudo method
                    for recipient in message.recipient_ids:
                        if recipient.email:
                            try:
                                self.env['mail.mail'].sudo().create({
                                    'subject': f"[Internship Management] {message.subject}",
                                    'body_html': message._get_email_template(message),
                                    'email_to': recipient.email,
                                    'email_from': self.env.user.email or 'noreply@internship.com',
                                    'auto_delete': True,
                                }).send()

                                _logger.info(f"Fallback email sent to {recipient.email}")

                            except Exception as e2:
                                _logger.error(f"Failed to send fallback email to {recipient.email}: {str(e2)}")

    def _create_notifications(self):
        """Enhanced notification creation with better tracking."""
        for message in self:
            _logger.info(f"Creating notifications for message: {message.subject}")

            notification_vals = []
            for recipient in message.recipient_ids:
                notification_vals.append({
                    'title': f'New Message: {message.subject}',
                    'message': f'You have received a new message from {message.sender_id.name}.',
                    'user_id': recipient.id,
                    'notification_type': 'info',
                    'stage_id': message.stage_id.id if message.stage_id else None,
                    'document_id': message.document_id.id if message.document_id else None,
                    'meeting_id': message.meeting_id.id if message.meeting_id else None,
                    'message_id': message.id,  # Add reference to the message
                })

            if notification_vals:
                notifications = self.env['internship.notification'].create(notification_vals)
                _logger.info(f"Created {len(notifications)} notifications for message {message.id}")

    def _get_email_template(self, message):
        """Generate email template for the message."""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">Internship Management System</h2>
                <h3 style="color: #3498db;">New Message</h3>
                <p><strong>From:</strong> {message.sender_id.name}</p>
                <p><strong>Subject:</strong> {message.subject}</p>
                <p><strong>Priority:</strong> {dict(message._fields['priority'].selection).get(message.priority)}</p>
                <hr/>
                <div style="background-color: white; padding: 15px; border-radius: 3px; margin: 10px 0;">
                    {message.body}
                </div>
                <hr/>
                <p style="color: #7f8c8d; font-size: 12px;">
                    Please log in to the system to reply to this message.
                </p>
            </div>
        </div>
        """

    # ===============================
    # UTILITY METHODS
    # ===============================

    def name_get(self):
        """Enhanced name display with sender info."""
        result = []
        for message in self:
            # Show sender name and subject for better identification
            name = f"{message.sender_id.name}: {message.subject}"
            if message.state:
                state_name = dict(message._fields['state'].selection).get(message.state)
                name = f"{name} ({state_name})"
            result.append((message.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        """Custom search: search by subject, body, or sender."""
        args = args or []
        domain = []

        if name:
            domain = ['|', '|', '|',
                      ('subject', operator, name),
                      ('body', operator, name),
                      ('sender_id.name', operator, name),
                      ('recipient_ids.name', operator, name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid, order=order)

    def get_message_statistics(self):
        """Return statistical data for this message."""
        self.ensure_one()
        return {
            'recipient_count': self.read_count,
            'reply_count': self.reply_count,
            'is_recent': self.is_recent,
            'days_since_created': (fields.Datetime.now() - self.create_date).days if self.create_date else 0,
            'has_attachments': bool(self.stage_id or self.document_id or self.meeting_id),
        }