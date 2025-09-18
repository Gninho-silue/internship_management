# -*- coding: utf-8 -*-
"""Internship Alert Model"""

import logging
from datetime import timedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class InternshipAlert(models.Model):
    """Intelligent alert system for internship management.
    
    This model handles automatic detection of issues, delays, and blocks
    in the internship process with configurable rules and escalation.
    """
    _name = 'internship.alert'
    _description = 'Internship Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'title'

    # ===============================
    # CORE IDENTIFICATION FIELDS
    # ===============================

    title = fields.Char(
        string='Alert Title',
        required=True,
        tracking=True,
        help="Brief description of the alert"
    )

    alert_type = fields.Selection([
        ('task_overdue', 'Task Overdue'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('internship_blocked', 'Internship Blocked'),
        ('document_missing', 'Document Missing'),
        ('defense_pending', 'Defense Pending'),
        ('supervisor_overload', 'Supervisor Overload'),
        ('student_inactive', 'Student Inactive')
    ], string='Alert Type', required=True, tracking=True)

    priority = fields.Selection([
        ('1', 'High'),
        ('2', 'Medium'),
        ('3', 'Low')
    ], string='Priority', default='2', tracking=True)

    # ===============================
    # STATUS AND STATE MANAGEMENT
    # ===============================

    state = fields.Selection([
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed')
    ], string='Status', default='active', tracking=True)

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    stage_id = fields.Many2one(
        'internship.stage',
        string='Internship',
        tracking=True,
        help="Related internship stage"
    )

    student_id = fields.Many2one(
        'internship.student',
        string='Student',
        related='stage_id.student_id',
        store=True,
        help="Student related to this alert"
    )

    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Supervisor',
        related='stage_id.supervisor_id',
        store=True,
        help="Supervisor related to this alert"
    )

    task_id = fields.Many2one(
        'internship.todo',
        string='Task',
        help="Related task if applicable"
    )

    document_id = fields.Many2one(
        'internship.document',
        string='Document',
        help="Related document if applicable"
    )

    # ===============================
    # ALERT CONTENT AND DETAILS
    # ===============================

    description = fields.Html(
        string='Description',
        help="Detailed description of the alert"
    )

    suggested_action = fields.Html(
        string='Suggested Action',
        help="Recommended action to resolve the alert"
    )

    # ===============================
    # TIMING AND ESCALATION
    # ===============================

    detected_date = fields.Datetime(
        string='Detected Date',
        default=fields.Datetime.now,
        tracking=True,
        help="When this alert was first detected"
    )

    acknowledged_date = fields.Datetime(
        string='Acknowledged Date',
        help="When this alert was acknowledged"
    )

    resolved_date = fields.Datetime(
        string='Resolved Date',
        help="When this alert was resolved"
    )

    escalation_level = fields.Integer(
        string='Escalation Level',
        default=0,
        tracking=True,
        help="Current escalation level (0=initial, 1=supervisor, 2=admin)"
    )

    # ===============================
    # NOTIFICATION FIELDS
    # ===============================

    notification_sent = fields.Boolean(
        string='Notification Sent',
        default=False,
        help="Whether notification has been sent"
    )

    notification_date = fields.Datetime(
        string='Notification Date',
        help="When notification was sent"
    )

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_acknowledge(self):
        """Acknowledge the alert."""
        self.write({
            'state': 'acknowledged',
            'acknowledged_date': fields.Datetime.now()
        })

    def action_resolve(self):
        """Mark alert as resolved."""
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Datetime.now()
        })

    def action_dismiss(self):
        """Dismiss the alert."""
        self.write({'state': 'dismissed'})

    def action_escalate(self):
        """Escalate the alert to next level."""
        self.ensure_one()
        if self.escalation_level < 2:
            self.write({'escalation_level': self.escalation_level + 1})
            # Send notification to next level
            self._send_escalation_notification()

    def _send_escalation_notification(self):
        """Send escalation notification."""
        self.ensure_one()

        # Determine recipients based on escalation level
        if self.escalation_level == 1:
            # Escalate to supervisor
            recipients = [self.supervisor_id.user_id.email] if self.supervisor_id.user_id.email else []
        elif self.escalation_level == 2:
            # Escalate to admin
            admin_users = self.env['res.users'].search(
                [('groups_id', 'in', self.env.ref('internship_management.group_internship_admin').id)])
            recipients = [user.email for user in admin_users if user.email]

        if recipients:
            self._send_email_notification(recipients, 'escalation')

    def _send_email_notification(self, recipients, notification_type='alert'):
        """Send email notification to recipients."""
        self.ensure_one()

        if not recipients:
            return

        # Email template context
        template_context = {
            'alert': self,
            'student': self.student_id,
            'supervisor': self.supervisor_id,
            'stage': self.stage_id,
        }

        # Send email to each recipient
        for recipient_email in recipients:
            if recipient_email:
                self._send_single_email(recipient_email, template_context, notification_type)

    def _send_single_email(self, recipient_email, context, notification_type):
        """Send single email notification."""
        self.ensure_one()

        # Email subject based on notification type
        if notification_type == 'escalation':
            subject = f"🚨 ESCALATED ALERT: {self.title}"
        else:
            subject = f"🚨 ALERT: {self.title}"

        # Email body
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                <h2 style="margin: 0; text-align: center;">🚨 Internship Alert</h2>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px;">
                <h3 style="color: #495057; margin-top: 0;">{self.title}</h3>
                
                <div style="background: white; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p><strong>Alert Type:</strong> {self.alert_type.replace('_', ' ').title()}</p>
                    <p><strong>Priority:</strong> {dict(self._fields['priority'].selection)[self.priority]}</p>
                    <p><strong>Student:</strong> {self.student_id.name if self.student_id else 'N/A'}</p>
                    <p><strong>Supervisor:</strong> {self.supervisor_id.name if self.supervisor_id else 'N/A'}</p>
                    <p><strong>Detected:</strong> {self.detected_date.strftime('%Y-%m-%d %H:%M') if self.detected_date else 'N/A'}</p>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h4 style="color: #495057; margin-top: 0;">Description:</h4>
                    {self.description or 'No description available'}
                </div>
                
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h4 style="color: #1976d2; margin-top: 0;">Suggested Actions:</h4>
                    {self.suggested_action or 'No suggested actions available'}
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <a href="{self.get_odoo_url()}" 
                       style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Alert in System
                    </a>
                </div>
            </div>
        </div>
        """

        # Send email
        try:
            self.env['mail.mail'].create({
                'subject': subject,
                'body_html': body,
                'email_to': recipient_email,
                'auto_delete': True,
            }).send()

            # Update notification status
            self.write({
                'notification_sent': True,
                'notification_date': fields.Datetime.now()
            })

        except Exception as e:
            _logger.error(f"Failed to send email notification: {str(e)}")

    def get_odoo_url(self):
        """Get Odoo URL for the alert."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web#id={self.id}&model=internship.alert&view_type=form"

    def _send_initial_notification(self):
        """Send initial notification when alert is created."""
        self.ensure_one()

        # Determine recipients based on alert type and priority
        recipients = []

        if self.priority == '1':  # High priority
            # Send to supervisor and admin
            if self.supervisor_id.user_id.email:
                recipients.append(self.supervisor_id.user_id.email)
            admin_users = self.env['res.users'].search(
                [('groups_id', 'in', self.env.ref('internship_management.group_internship_admin').id)])
            recipients.extend([user.email for user in admin_users if user.email])
        elif self.priority == '2':  # Medium priority
            # Send to supervisor
            if self.supervisor_id.user_id.email:
                recipients.append(self.supervisor_id.user_id.email)
        elif self.priority == '3':  # Low priority
            # Send to supervisor only
            if self.supervisor_id.user_id.email:
                recipients.append(self.supervisor_id.user_id.email)

        # Remove duplicates
        recipients = list(set(recipients))

        if recipients:
            self._send_email_notification(recipients, 'alert')

    # ===============================
    # STATIC METHODS FOR ALERT DETECTION
    # ===============================

    @api.model
    def detect_task_overdue_alerts(self):
        """Detect overdue tasks and create alerts."""
        overdue_tasks = self.env['internship.todo'].search([
            ('deadline', '<', fields.Date.today()),
            ('state', 'in', ['todo', 'in_progress'])
        ])

        for task in overdue_tasks:
            self._create_task_overdue_alert(task)

    @api.model
    def detect_deadline_approaching_alerts(self):
        """Detect approaching deadlines and create alerts."""
        three_days_from_now = fields.Date.today() + timedelta(days=3)
        approaching_tasks = self.env['internship.todo'].search([
            ('deadline', '<=', three_days_from_now),
            ('deadline', '>=', fields.Date.today()),
            ('state', 'in', ['todo', 'in_progress'])
        ])

        for task in approaching_tasks:
            self._create_deadline_approaching_alert(task)

    @api.model
    def detect_internship_blocked_alerts(self):
        """Detect blocked internships and create alerts."""
        # Find internships that have been in the same state for too long
        blocked_stages = self.env['internship.stage'].search([
            ('state', 'in', ['submitted', 'approved']),
            ('write_date', '<', fields.Datetime.now() - timedelta(days=7))
        ])

        for stage in blocked_stages:
            self._create_internship_blocked_alert(stage)

    def _create_task_overdue_alert(self, task):
        """Create overdue task alert."""
        existing_alert = self.search([
            ('alert_type', '=', 'task_overdue'),
            ('task_id', '=', task.id),
            ('state', '=', 'active')
        ])

        if not existing_alert:
            alert = self.create({
                'title': f'Task Overdue: {task.title}',
                'alert_type': 'task_overdue',
                'priority': '1',
                'stage_id': task.stage_id.id,
                'task_id': task.id,
                'description': f'''
                    <p><strong>Overdue Task Alert</strong></p>
                    <p>Task "{task.title}" is overdue.</p>
                    <p><strong>Deadline:</strong> {task.deadline}</p>
                    <p><strong>Days Overdue:</strong> {(fields.Date.today() - task.deadline).days}</p>
                ''',
                'suggested_action': f'''
                    <p><strong>Suggested Actions:</strong></p>
                    <ul>
                        <li>Contact student to check progress</li>
                        <li>Review task requirements</li>
                        <li>Consider extending deadline if necessary</li>
                    </ul>
                '''
            })

            # Send email notification
            alert._send_initial_notification()

    def _create_deadline_approaching_alert(self, task):
        """Create deadline approaching alert."""
        existing_alert = self.search([
            ('alert_type', '=', 'deadline_approaching'),
            ('task_id', '=', task.id),
            ('state', '=', 'active')
        ])

        if not existing_alert:
            days_remaining = (task.deadline - fields.Date.today()).days
            self.create({
                'title': f'Deadline Approaching: {task.title}',
                'alert_type': 'deadline_approaching',
                'priority': '2',
                'stage_id': task.stage_id.id,
                'task_id': task.id,
                'description': f'''
                    <p><strong>Deadline Approaching Alert</strong></p>
                    <p>Task "{task.title}" deadline is approaching.</p>
                    <p><strong>Deadline:</strong> {task.deadline}</p>
                    <p><strong>Days Remaining:</strong> {days_remaining}</p>
                ''',
                'suggested_action': f'''
                    <p><strong>Suggested Actions:</strong></p>
                    <ul>
                        <li>Check task progress with student</li>
                        <li>Provide additional support if needed</li>
                        <li>Schedule follow-up meeting</li>
                    </ul>
                '''
            })

    def _create_internship_blocked_alert(self, stage):
        """Create internship blocked alert."""
        existing_alert = self.search([
            ('alert_type', '=', 'internship_blocked'),
            ('stage_id', '=', stage.id),
            ('state', '=', 'active')
        ])

        if not existing_alert:
            days_blocked = (fields.Datetime.now() - stage.write_date).days
            self.create({
                'title': f'Internship Blocked: {stage.title}',
                'alert_type': 'internship_blocked',
                'priority': '1',
                'stage_id': stage.id,
                'description': f'''
                    <p><strong>Internship Blocked Alert</strong></p>
                    <p>Internship "{stage.title}" has been blocked for {days_blocked} days.</p>
                    <p><strong>Current State:</strong> {stage.state}</p>
                    <p><strong>Student:</strong> {stage.student_id.name}</p>
                    <p><strong>Supervisor:</strong> {stage.supervisor_id.name}</p>
                ''',
                'suggested_action': f'''
                    <p><strong>Suggested Actions:</strong></p>
                    <ul>
                        <li>Contact student to check progress</li>
                        <li>Review internship requirements</li>
                        <li>Schedule meeting with supervisor</li>
                        <li>Consider changing internship state</li>
                    </ul>
                '''
            })

    # ===============================
    # GLOBAL ALERT DETECTION METHOD
    # ===============================

    @api.model
    def detect_all_alerts(self):
        """Main method called by cron job to detect all types of alerts."""
        _logger.info("Starting intelligent alerts detection...")

        try:
            # Detect task-related alerts
            self.detect_task_overdue_alerts()
            self.detect_deadline_approaching_alerts()

            # Detect internship-related alerts
            self.detect_internship_blocked_alerts()

            # Detect other types of alerts
            self.detect_document_missing_alerts()
            self.detect_defense_pending_alerts()
            self.detect_supervisor_overload_alerts()
            self.detect_student_inactive_alerts()

            _logger.info("Intelligent alerts detection completed successfully")

        except Exception as e:
            _logger.error(f"Error during alerts detection: {str(e)}")
            raise

    @api.model
    def detect_document_missing_alerts(self):
        """Detect missing required documents."""
        # Find internships that should have documents but don't
        stages_without_docs = self.env['internship.stage'].search([
            ('state', 'in', ['in_progress', 'completed']),
            ('document_ids', '=', False)
        ])

        for stage in stages_without_docs:
            self._create_document_missing_alert(stage)

    @api.model
    def detect_defense_pending_alerts(self):
        """Detect internships ready for defense but not scheduled."""
        ready_for_defense = self.env['internship.stage'].search([
            ('state', '=', 'completed'),
            ('defense_date', '=', False)
        ])

        for stage in ready_for_defense:
            self._create_defense_pending_alert(stage)

    @api.model
    def detect_supervisor_overload_alerts(self):
        """Detect supervisors with too many active internships."""
        supervisors = self.env['internship.supervisor'].search([])

        for supervisor in supervisors:
            active_count = len(supervisor.stage_ids.filtered(lambda s: s.state == 'in_progress'))
            if active_count > 5:  # Threshold for overload
                self._create_supervisor_overload_alert(supervisor, active_count)

    @api.model
    def detect_student_inactive_alerts(self):
        """Detect students who haven't been active recently."""
        inactive_students = self.env['internship.student'].search([
            ('write_date', '<', fields.Datetime.now() - timedelta(days=14))
        ])

        for student in inactive_students:
            if student.internship_ids.filtered(lambda s: s.state == 'in_progress'):
                self._create_student_inactive_alert(student)

    def _create_document_missing_alert(self, stage):
        """Create document missing alert."""
        existing_alert = self.search([
            ('alert_type', '=', 'document_missing'),
            ('stage_id', '=', stage.id),
            ('state', '=', 'active')
        ])

        if not existing_alert:
            self.create({
                'title': f'Missing Documents: {stage.title}',
                'alert_type': 'document_missing',
                'priority': '2',
                'stage_id': stage.id,
                'description': f'''
                    <p><strong>Missing Documents Alert</strong></p>
                    <p>Internship "{stage.title}" is missing required documents.</p>
                    <p><strong>Student:</strong> {stage.student_id.name}</p>
                    <p><strong>Current State:</strong> {stage.state}</p>
                ''',
                'suggested_action': f'''
                    <p><strong>Suggested Actions:</strong></p>
                    <ul>
                        <li>Remind student to upload required documents</li>
                        <li>Check document requirements</li>
                        <li>Provide document templates if needed</li>
                    </ul>
                '''
            })

    def _create_defense_pending_alert(self, stage):
        """Create defense pending alert."""
        existing_alert = self.search([
            ('alert_type', '=', 'defense_pending'),
            ('stage_id', '=', stage.id),
            ('state', '=', 'active')
        ])

        if not existing_alert:
            self.create({
                'title': f'Defense Pending: {stage.title}',
                'alert_type': 'defense_pending',
                'priority': '1',
                'stage_id': stage.id,
                'description': f'''
                    <p><strong>Defense Pending Alert</strong></p>
                    <p>Internship "{stage.title}" is completed but defense is not scheduled.</p>
                    <p><strong>Student:</strong> {stage.student_id.name}</p>
                    <p><strong>Completion Date:</strong> {stage.write_date}</p>
                ''',
                'suggested_action': f'''
                    <p><strong>Suggested Actions:</strong></p>
                    <ul>
                        <li>Schedule defense date</li>
                        <li>Assign jury members</li>
                        <li>Prepare defense materials</li>
                    </ul>
                '''
            })

    def _create_supervisor_overload_alert(self, supervisor, active_count):
        """Create supervisor overload alert."""
        existing_alert = self.search([
            ('alert_type', '=', 'supervisor_overload'),
            ('supervisor_id', '=', supervisor.id),
            ('state', '=', 'active')
        ])

        if not existing_alert:
            self.create({
                'title': f'Supervisor Overload: {supervisor.name}',
                'alert_type': 'supervisor_overload',
                'priority': '2',
                'supervisor_id': supervisor.id,
                'description': f'''
                    <p><strong>Supervisor Overload Alert</strong></p>
                    <p>Supervisor "{supervisor.name}" has {active_count} active internships.</p>
                    <p><strong>Threshold:</strong> 5 active internships</p>
                ''',
                'suggested_action': f'''
                    <p><strong>Suggested Actions:</strong></p>
                    <ul>
                        <li>Consider redistributing some internships</li>
                        <li>Check supervisor capacity</li>
                        <li>Provide additional support</li>
                    </ul>
                '''
            })

    def _create_student_inactive_alert(self, student):
        """Create student inactive alert."""
        existing_alert = self.search([
            ('alert_type', '=', 'student_inactive'),
            ('student_id', '=', student.id),
            ('state', '=', 'active')
        ])

        if not existing_alert:
            self.create({
                'title': f'Student Inactive: {student.name}',
                'alert_type': 'student_inactive',
                'priority': '2',
                'student_id': student.id,
                'description': f'''
                    <p><strong>Student Inactive Alert</strong></p>
                    <p>Student "{student.name}" hasn't been active for 14+ days.</p>
                    <p><strong>Last Activity:</strong> {student.write_date}</p>
                ''',
                'suggested_action': f'''
                    <p><strong>Suggested Actions:</strong></p>
                    <ul>
                        <li>Contact student to check status</li>
                        <li>Verify internship progress</li>
                        <li>Schedule follow-up meeting</li>
                    </ul>
                '''
            })

    # ===============================
    # TEST METHODS
    # ===============================

    @api.model
    def create_test_alerts(self):
        """Create test alerts for demonstration purposes."""
        _logger.info("Creating test alerts...")

        # Create a test overdue task alert
        test_alert = self.create({
            'title': 'Test Alert: Task Overdue',
            'alert_type': 'task_overdue',
            'priority': '1',
            'description': '''
                <p><strong>Test Alert</strong></p>
                <p>This is a test alert to demonstrate the system.</p>
                <p><strong>Created:</strong> {}</p>
            '''.format(fields.Datetime.now().strftime('%Y-%m-%d %H:%M')),
            'suggested_action': '''
                <p><strong>Test Actions:</strong></p>
                <ul>
                    <li>This is a test alert</li>
                    <li>You can acknowledge, resolve, or dismiss it</li>
                    <li>Test the escalation system</li>
                </ul>
            '''
        })

        # Send test notification
        test_alert._send_initial_notification()

        _logger.info(f"Test alert created with ID: {test_alert.id}")
        return test_alert

    @api.model
    def run_alert_detection_test(self):
        """Run alert detection for testing purposes."""
        _logger.info("Running alert detection test...")

        try:
            # Run all detection methods
            self.detect_all_alerts()

            # Count created alerts
            total_alerts = self.search_count([])
            active_alerts = self.search_count([('state', '=', 'active')])

            _logger.info(f"Alert detection completed. Total alerts: {total_alerts}, Active: {active_alerts}")

            return {
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'message': 'Alert detection test completed successfully'
            }

        except Exception as e:
            _logger.error(f"Alert detection test failed: {str(e)}")
            return {
                'error': str(e),
                'message': 'Alert detection test failed'
            }
