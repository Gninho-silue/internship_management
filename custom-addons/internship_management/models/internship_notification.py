# -*- coding: utf-8 -*-
"""Internship Notification Model"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipNotification(models.Model):
    """Notification model for internship management system.

    This model handles system notifications, alerts, and reminders
    for users in the internship management system, providing a
    centralized notification system with different types and priorities.

    Key Features:
    - System notifications and alerts
    - Priority-based notification handling
    - Integration with all internship-related objects
    - Email and in-app notification support
    - Notification scheduling and reminders
    - User notification preferences
    """
    _name = 'internship.notification'
    _description = 'Internship Notification System'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, priority desc'
    _rec_name = 'title'

    # ===============================
    # CORE NOTIFICATION FIELDS
    # ===============================

    title = fields.Char(
        string='Notification Title',
        required=True,
        tracking=True,
        size=200,
        help="Title or subject of the notification"
    )

    message = fields.Text(
        string='Notification Message',
        required=True,
        tracking=True,
        help="Detailed message content of the notification"
    )

    # ===============================
    # RECIPIENT AND SENDER FIELDS
    # ===============================

    user_id = fields.Many2one(
        'res.users',
        string='Recipient',
        required=True,
        tracking=True,
        help="User who should receive this notification"
    )

    sender_id = fields.Many2one(
        'res.users',
        string='Sender',
        default=lambda self: self.env.user,
        help="User who created this notification"
    )

    # ===============================
    # NOTIFICATION CLASSIFICATION
    # ===============================

    notification_type = fields.Selection([
        ('deadline', 'Deadline Reminder'),
        ('reminder', 'General Reminder'),
        ('approval', 'Approval Required'),
        ('alert', 'System Alert'),
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error')
    ], string='Notification Type', default='info', tracking=True,
        help="Type of notification being sent")

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True,
        help="Priority level of the notification")

    # ===============================
    # WORKFLOW AND STATUS FIELDS
    # ===============================

    state = fields.Selection([
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
        ('dismissed', 'Dismissed')
    ], string='Status', default='unread', tracking=True, required=True,
        help="Current status of the notification")

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    stage_id = fields.Many2one(
        'internship.stage',
        string='Related Internship',
        help="Internship this notification is related to"
    )

    document_id = fields.Many2one(
        'internship.document',
        string='Related Document',
        help="Document this notification is related to"
    )

    meeting_id = fields.Many2one(
        'internship.meeting',
        string='Related Meeting',
        help="Meeting this notification is related to"
    )

    message_id = fields.Many2one(
        'internship.message',
        string='Related Message',
        help="Message this notification is related to"
    )

    # ===============================
    # SCHEDULING AND TIMING FIELDS
    # ===============================

    due_date = fields.Datetime(
        string='Due Date',
        help="When this notification should be processed or when the related action is due"
    )

    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        help="When this notification should be sent (for scheduled notifications)"
    )

    read_date = fields.Datetime(
        string='Read Date',
        readonly=True,
        help="When this notification was read by the user"
    )

    # ===============================
    # ACTION FIELDS
    # ===============================

    action_url = fields.Char(
        string='Action URL',
        help="URL to navigate to when notification is clicked"
    )

    action_text = fields.Char(
        string='Action Text',
        help="Text for the action button (e.g., 'View Document', 'Approve')"
    )

    action_model = fields.Char(
        string='Action Model',
        help="Model name for the action"
    )

    action_res_id = fields.Integer(
        string='Action Record ID',
        help="Record ID for the action"
    )

    # ===============================
    # COMPUTED FIELDS
    # ===============================

    @api.depends('user_id')
    def _compute_is_recipient(self):
        """Check if current user is the recipient."""
        for notification in self:
            notification.is_recipient = notification.user_id == self.env.user

    @api.depends('due_date')
    def _compute_is_overdue(self):
        """Check if notification is overdue."""
        for notification in self:
            notification.is_overdue = (
                    notification.due_date and
                    notification.due_date < fields.Datetime.now() and
                    notification.state == 'unread'
            )

    @api.depends('create_date')
    def _compute_is_recent(self):
        """Check if notification was created recently (within 24 hours)."""
        for notification in self:
            if notification.create_date:
                delta = fields.Datetime.now() - notification.create_date
                notification.is_recent = delta.total_seconds() < 86400  # 24 hours
            else:
                notification.is_recent = False

    is_recipient = fields.Boolean(
        string='My Notification',
        compute='_compute_is_recipient',
        store=True,
        help="Whether current user is the recipient"
    )

    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_is_overdue',
        store=True,
        help="Whether this notification is overdue"
    )

    is_recent = fields.Boolean(
        string='Recent',
        compute='_compute_is_recent',
        store=True,
        help="Whether this notification was created recently"
    )

    # ===============================
    # TECHNICAL FIELDS
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Whether this notification is active"
    )

    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================

    @api.constrains('due_date')
    def _check_due_date(self):
        """Ensure due date is in the future for new notifications."""
        for notification in self:
            if notification.due_date and notification.due_date < fields.Datetime.now():
                raise ValidationError(_("Due date must be in the future."))

    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        """Ensure scheduled date is in the future."""
        for notification in self:
            if notification.scheduled_date and notification.scheduled_date < fields.Datetime.now():
                raise ValidationError(_("Scheduled date must be in the future."))

    # ===============================
    # CRUD METHODS
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method with logging and validation."""
        _logger.info(f"Creating {len(vals_list)} notification record(s)")

        for vals in vals_list:
            # Auto-set sender if not provided
            if not vals.get('sender_id'):
                vals['sender_id'] = self.env.user.id

            # Auto-generate title if not provided
            if not vals.get('title') and vals.get('message'):
                message_text = vals['message'][:50]
                vals['title'] = message_text + '...' if len(vals['message']) > 50 else message_text

        notifications = super().create(vals_list)

        for notification in notifications:
            _logger.info(f"Created notification: {notification.title} for {notification.user_id.name}")

            # Send email notification if user has email
            if notification.user_id.email:
                notification._send_email_notification()

        return notifications

    def write(self, vals):
        """Override write method with logging."""
        if 'state' in vals:
            _logger.info(f"Notification {self.title} status changed to {vals['state']}")

            # Set read_date when marked as read
            if vals['state'] == 'read' and not self.read_date:
                vals['read_date'] = fields.Datetime.now()

        return super().write(vals)

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_mark_as_read(self):
        """Mark notification as read."""
        self.write({
            'state': 'read',
            'read_date': fields.Datetime.now()
        })

    def action_archive(self):
        """Archive the notification."""
        self.write({'state': 'archived'})

    def action_dismiss(self):
        """Dismiss the notification."""
        self.write({'state': 'dismissed'})

    def action_view_related(self):
        """Navigate to the related object."""
        self.ensure_one()

        if self.stage_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'internship.stage',
                'res_id': self.stage_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        elif self.document_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'internship.document',
                'res_id': self.document_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        elif self.meeting_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'internship.meeting',
                'res_id': self.meeting_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        elif self.message_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'internship.message',
                'res_id': self.message_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        elif self.action_model and self.action_res_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.action_model,
                'res_id': self.action_res_id,
                'view_mode': 'form',
                'target': 'current',
            }

        return True

    def action_execute_action(self):
        """Execute the action associated with this notification."""
        self.ensure_one()

        if self.action_model and self.action_res_id:
            record = self.env[self.action_model].browse(self.action_res_id)
            if record.exists():
                return self.action_view_related()

        return True

    # ===============================
    # NOTIFICATION METHODS
    # ===============================

    def _send_email_notification(self):
        """Send email notification to the recipient."""
        for notification in self:
            if notification.user_id.email:
                subject = f"[Internship Management] {notification.title}"
                body = self._get_email_template(notification)

                self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body,
                    'email_from': notification.sender_id.email or self.env.user.email,
                    'email_to': notification.user_id.email,
                    'auto_delete': True,
                }).send()

    def _get_email_template(self, notification):
        """Generate email template for the notification."""
        priority_colors = {
            '0': '#95a5a6',  # Low - Gray
            '1': '#3498db',  # Normal - Blue
            '2': '#f39c12',  # High - Orange
            '3': '#e74c3c',  # Urgent - Red
        }

        type_colors = {
            'deadline': '#e74c3c',
            'reminder': '#f39c12',
            'approval': '#3498db',
            'alert': '#e74c3c',
            'info': '#3498db',
            'warning': '#f39c12',
            'success': '#27ae60',
            'error': '#e74c3c',
        }

        priority_color = priority_colors.get(notification.priority, '#3498db')
        type_color = type_colors.get(notification.notification_type, '#3498db')

        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">Internship Management System</h2>
                <div style="background-color: {type_color}; color: white; padding: 10px; border-radius: 3px; margin-bottom: 20px;">
                    <h3 style="margin: 0;">{notification.title}</h3>
                </div>
                <div style="background-color: white; padding: 15px; border-radius: 3px; margin: 10px 0;">
                    {notification.message}
                </div>
                <div style="margin-top: 20px;">
                    <p><strong>Priority:</strong> <span style="color: {priority_color};">{dict(notification._fields['priority'].selection).get(notification.priority)}</strong></p>
                    <p><strong>Type:</strong> {dict(notification._fields['notification_type'].selection).get(notification.notification_type)}</p>
                    {f'<p><strong>Due Date:</strong> {notification.due_date.strftime("%Y-%m-%d %H:%M")}</p>' if notification.due_date else ''}
                </div>
                <hr/>
                <p style="color: #7f8c8d; font-size: 12px;">
                    Please log in to the system to view more details and take action.
                </p>
            </div>
        </div>
        """

    # ===============================
    # UTILITY METHODS
    # ===============================

    def name_get(self):
        """Custom name display: Title (Type)."""
        result = []
        for notification in self:
            name = notification.title
            if notification.notification_type:
                type_name = dict(notification._fields['notification_type'].selection).get(
                    notification.notification_type)
                name = f"{name} ({type_name})"
            result.append((notification.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Custom search: search by title or message."""
        args = args or []
        domain = []

        if name:
            domain = ['|', '|',
                      ('title', operator, name),
                      ('message', operator, name),
                      ('user_id.name', operator, name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def create_notification(self, title, message, user_id, notification_type='info',
                            priority='1', stage_id=None, document_id=None, meeting_id=None,
                            message_id=None, due_date=None, action_url=None):
        """Create a notification programmatically."""
        return self.create({
            'title': title,
            'message': message,
            'user_id': user_id,
            'notification_type': notification_type,
            'priority': priority,
            'stage_id': stage_id,
            'document_id': document_id,
            'meeting_id': meeting_id,
            'message_id': message_id,
            'due_date': due_date,
            'action_url': action_url,
        })

    def get_notification_statistics(self):
        """Return statistical data for this notification."""
        self.ensure_one()
        return {
            'days_since_created': (fields.Datetime.now() - self.create_date).days if self.create_date else 0,
            'is_overdue': self.is_overdue,
            'is_recent': self.is_recent,
            'has_action': bool(self.action_url or (self.action_model and self.action_res_id)),
            'days_to_due': (self.due_date - fields.Datetime.now()).days if self.due_date else None,
        }