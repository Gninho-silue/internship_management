# -*- coding: utf-8 -*-
"""Internship Meeting Model"""

import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class InternshipMeeting(models.Model):
    """Meeting model for internship management system.

    This model handles meeting scheduling, management, and tracking
    for internships, providing a comprehensive meeting management
    system with different types, participants, and follow-up tracking.

    Key Features:
    - Meeting scheduling and management
    - Different meeting types (kickoff, follow-up, evaluation, defense)
    - Participant management and attendance tracking
    - Meeting minutes and action items
    - Email notifications and reminders
    - Integration with internships and documents
    - Virtual and physical meeting support
    """
    _name = 'internship.meeting'
    _description = 'Internship Meeting Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name'
    _rec_name = 'name'

    # ===============================
    # CORE MEETING FIELDS
    # ===============================

    name = fields.Char(
        string='Meeting Title',
        required=True,
        tracking=True,
        size=200,
        help="Title or subject of the meeting"
    )

    meeting_type = fields.Selection([
        ('kickoff', 'Kick-off Meeting'),
        ('follow_up', 'Follow-up Meeting'),
        ('milestone', 'Milestone Review'),
        ('defense', 'Defense Meeting'),
        ('evaluation', 'Evaluation Meeting'),
        ('emergency', 'Emergency Meeting'),
        ('other', 'Other')
    ], string='Meeting Type', default='follow_up', tracking=True, required=False,
        help="Type of meeting being scheduled")

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    stage_id = fields.Many2one(
        'internship.stage',
        string='Related Internship',
        required=False,
        tracking=True,
        ondelete='cascade',
        help="Internship this meeting is related to"
    )

    student_id = fields.Many2one(
        'internship.student',
        string='Student',
        related='stage_id.student_id',
        store=True,
        readonly=True,
        help="Student involved in this meeting"
    )

    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Supervisor',
        related='stage_id.supervisor_id',
        store=True,
        readonly=True,
        help="Supervisor involved in this meeting"
    )

    organizer_id = fields.Many2one(
        'res.users',
        string='Organizer',
        default=lambda self: self.env.user,
        tracking=True,
        help="User who organized this meeting"
    )

    participant_ids = fields.Many2many(
        'res.users',
        string='Participants',
        help="Users who should attend this meeting"
    )

    # ===============================
    # SCHEDULING FIELDS
    # ===============================

    date = fields.Datetime(
        string='Meeting Date & Time',
        required=False,
        tracking=True,
        help="Scheduled date and time for the meeting"
    )

    duration = fields.Float(
        string='Duration (Hours)',
        default=1.0,
        tracking=True,
        help="Expected duration of the meeting in hours"
    )

    @api.depends('date', 'duration')
    def _compute_end_date(self):
        """Calculate meeting end time."""
        for meeting in self:
            if meeting.date and meeting.duration:
                meeting.end_date = meeting.date + timedelta(hours=meeting.duration)
            else:
                meeting.end_date = False

    end_date = fields.Datetime(
        string='End Time',
        compute='_compute_end_date',
        store=True,
        help="Calculated end time of the meeting"
    )

    # ===============================
    # LOCATION AND MODALITY FIELDS
    # ===============================

    location = fields.Char(
        string='Location',
        tracking=True,
        help="Physical location of the meeting"
    )

    meeting_url = fields.Char(
        string='Meeting URL',
        help="URL for virtual meetings (Zoom, Teams, etc.)"
    )

    meeting_type_modality = fields.Selection([
        ('physical', 'Physical Meeting'),
        ('virtual', 'Virtual Meeting'),
        ('hybrid', 'Hybrid Meeting')
    ], string='Meeting Modality', default='virtual', tracking=True,
        help="How the meeting will be conducted")

    # ===============================
    # CONTENT AND TRACKING FIELDS
    # ===============================

    agenda = fields.Html(
        string='Agenda',
        help="Meeting agenda and topics to be discussed"
    )

    summary = fields.Html(
        string='Meeting Summary',
        help="Summary of what was discussed in the meeting"
    )

    next_actions = fields.Html(
        string='Action Items',
        help="Action items and follow-up tasks from the meeting"
    )

    decisions = fields.Html(
        string='Decisions Made',
        help="Key decisions made during the meeting"
    )

    # ===============================
    # WORKFLOW AND STATUS FIELDS
    # ===============================

    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed')
    ], string='Status', default='draft', tracking=True, required=False,
        help="Current status of the meeting")

    # ===============================
    # ATTENDANCE TRACKING FIELDS
    # ===============================

    attendee_ids = fields.One2many(
        'internship.meeting.attendee',
        'meeting_id',
        string='Attendees',
        help="List of attendees and their attendance status"
    )

    attendance_confirmed = fields.Boolean(
        string='Attendance Confirmed',
        default=False,
        help="Whether attendance has been confirmed"
    )

    # ===============================
    # NOTIFICATION FIELDS
    # ===============================

    reminder_sent = fields.Boolean(
        string='Reminder Sent',
        default=False,
        help="Whether reminder has been sent"
    )

    reminder_date = fields.Datetime(
        string='Reminder Date',
        help="When the reminder was sent"
    )

    email_sent = fields.Boolean(
        string='Email Sent',
        default=False,
        help="Whether invitation email has been sent"
    )

    # ===============================
    # COMPUTED FIELDS
    # ===============================

    @api.depends('date')
    def _compute_is_past(self):
        """Check if meeting is in the past."""
        for meeting in self:
            meeting.is_past = meeting.date and meeting.date < fields.Datetime.now()

    @api.depends('date')
    def _compute_is_today(self):
        """Check if meeting is today."""
        for meeting in self:
            if meeting.date:
                meeting.is_today = meeting.date.date() == fields.Date.today()
            else:
                meeting.is_today = False

    @api.depends('date')
    def _compute_is_upcoming(self):
        """Check if meeting is upcoming (within next 7 days)."""
        for meeting in self:
            if meeting.date:
                now = fields.Datetime.now()
                week_from_now = now + timedelta(days=7)
                meeting.is_upcoming = now <= meeting.date <= week_from_now
            else:
                meeting.is_upcoming = False

    @api.depends('attendee_ids.attendance_status')
    def _compute_attendance_stats(self):
        """Calculate attendance statistics."""
        for meeting in self:
            total_attendees = len(meeting.attendee_ids)
            confirmed_attendees = len(meeting.attendee_ids.filtered(lambda a: a.attendance_status == 'confirmed'))
            meeting.attendance_count = total_attendees
            meeting.confirmed_count = confirmed_attendees

    is_past = fields.Boolean(
        string='Past Meeting',
        compute='_compute_is_past',
        store=True,
        help="Whether this meeting is in the past"
    )

    is_today = fields.Boolean(
        string='Today',
        compute='_compute_is_today',
        store=True,
        help="Whether this meeting is today"
    )

    is_upcoming = fields.Boolean(
        string='Upcoming',
        compute='_compute_is_upcoming',
        store=True,
        help="Whether this meeting is upcoming (within 7 days)"
    )

    attendance_count = fields.Integer(
        string='Total Attendees',
        compute='_compute_attendance_stats',
        store=True,
        help="Total number of attendees"
    )

    confirmed_count = fields.Integer(
        string='Confirmed Attendees',
        compute='_compute_attendance_stats',
        store=True,
        help="Number of confirmed attendees"
    )

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    document_ids = fields.One2many(
        'internship.document',
        'meeting_id',
        string='Related Documents',
        help="Documents related to this meeting"
    )

    communication_ids = fields.One2many(
        'internship.communication',
        'meeting_id',
        string='Related Communications',
        help="Communications related to this meeting"
    )

    # ===============================
    # TECHNICAL FIELDS
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Whether this meeting is active"
    )

    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================

    @api.constrains('date')
    def _check_meeting_date(self):
        """Ensure meeting date is in the future for new meetings."""
        for meeting in self:
            if meeting.date and meeting.state in ['draft', 'scheduled'] and meeting.date < fields.Datetime.now():
                raise ValidationError(_("Meeting date must be in the future."))

    @api.constrains('duration')
    def _check_duration(self):
        """Ensure duration is positive."""
        for meeting in self:
            if meeting.duration <= 0:
                raise ValidationError(_("Meeting duration must be positive."))

    @api.constrains('participant_ids')
    def _check_participants(self):
        """Ensure meeting has at least one participant."""
        for meeting in self:
            if not meeting.participant_ids:
                raise ValidationError(_("Meeting must have at least one participant."))

    # ===============================
    # CRUD METHODS
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method with logging and validation."""
        _logger.info(f"Creating {len(vals_list)} meeting record(s)")

        for vals in vals_list:
            participants = []

            # Auto-add organizer as participant (FIX FOR ISSUE 1)
            organizer_id = vals.get('organizer_id', self.env.user.id)
            if organizer_id:
                participants.append(organizer_id)

            # Auto-add main participants if not specified and stage exists
            if vals.get('stage_id'):
                stage = self.env['internship.stage'].browse(vals['stage_id'])

                # Add student if exists and not already in participants
                if stage.student_id and stage.student_id.user_id:
                    if stage.student_id.user_id.id not in participants:
                        participants.append(stage.student_id.user_id.id)

                # Add supervisor if exists and not already in participants
                if stage.supervisor_id and stage.supervisor_id.user_id:
                    if stage.supervisor_id.user_id.id not in participants:
                        participants.append(stage.supervisor_id.user_id.id)

            # Add any existing participants from vals
            if vals.get('participant_ids'):
                for participant_command in vals['participant_ids']:
                    if participant_command[0] == 6:  # Command (6, 0, ids)
                        existing_participants = participant_command[2]
                        for pid in existing_participants:
                            if pid not in participants:
                                participants.append(pid)
                    elif participant_command[0] == 4:  # Command (4, id)
                        if participant_command[1] not in participants:
                            participants.append(participant_command[1])

            # Set the final participant list
            if participants:
                vals['participant_ids'] = [(6, 0, participants)]

        meetings = super().create(vals_list)

        for meeting in meetings:
            _logger.info(
                f"Created meeting: {meeting.name} for {meeting.stage_id.title if meeting.stage_id else 'No Stage'}")
            _logger.info(f"Participants: {[p.name for p in meeting.participant_ids]}")

            # Create attendee records
            meeting._create_attendee_records()

            # Send invitation emails (will be fixed in Fix 2)
            meeting._send_meeting_invitation_email()

        return meetings

    def write(self, vals):
        """Override write method with logging."""
        if 'state' in vals:
            _logger.info(f"Meeting {self.name} status changed to {vals['state']}")

        result = super().write(vals)

        # Update attendee records if participants changed
        if 'participant_ids' in vals:
            for meeting in self:
                meeting._create_attendee_records()

        return result

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_schedule(self):
        """Schedule the meeting."""
        self.write({'state': 'scheduled'})
        self._send_meeting_invitation_email()

    def action_confirm(self):
        """Confirm the meeting."""
        self.write({'state': 'confirmed'})
        self._send_meeting_confirmation_email()

    def action_start(self):
        """Start the meeting."""
        self.write({'state': 'in_progress'})

    def action_complete(self):
        """Complete the meeting."""
        self.write({'state': 'completed'})
        self._send_meeting_summary_email()

    def action_cancel(self):
        """Cancel the meeting."""
        self.write({'state': 'cancelled'})
        self._send_meeting_cancellation_email()

    def action_postpone(self):
        """Postpone the meeting."""
        self.write({'state': 'postponed'})
        self._send_meeting_postponement_email()

    def action_open_meeting_communications(self):
        """Open communications for this meeting."""
        self.ensure_one()
        return {
            'name': f'Meeting Communications - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.communication',
            'view_mode': 'tree,form',
            'domain': [('meeting_id', '=', self.id)],
            'context': {
                'default_meeting_id': self.id,
                'default_stage_id': self.stage_id.id,
                'default_sender_id': self.env.user.id,
            },
            'target': 'current',
        }

    def action_generate_minutes(self):
        """Generate meeting minutes document."""
        self.ensure_one()
        if not self.summary:
            raise UserError(_("Please add a meeting summary before generating minutes."))

        # Create document record for meeting minutes
        document = self.env['internship.document'].create({
            'name': f'Meeting Minutes - {self.name}',
            'document_type': 'other',
            'stage_id': self.stage_id.id,
            'meeting_id': self.id,
            'description': self.summary,
            'state': 'draft',
        })

        return {
            'name': 'Meeting Minutes Generated',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.document',
            'res_id': document.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ===============================
    # ATTENDEE MANAGEMENT METHODS
    # ===============================

    def _create_attendee_records(self):
        """Create attendee records for all participants."""
        for meeting in self:
            # Remove existing attendee records
            meeting.attendee_ids.unlink()

            # Create new attendee records
            attendee_vals = []
            for participant in meeting.participant_ids:
                attendee_vals.append({
                    'meeting_id': meeting.id,
                    'user_id': participant.id,
                    'attendance_status': 'pending',
                })

            if attendee_vals:
                self.env['internship.meeting.attendee'].create(attendee_vals)

    # ===============================
    # EMAIL NOTIFICATION METHODS
    # ===============================

    def _send_meeting_invitation_email(self):
        """Send meeting invitation email to participants using proper Odoo methods."""
        for meeting in self:
            if meeting.participant_ids and not meeting.email_sent:
                try:
                    # Use message_post instead of direct mail.mail creation
                    meeting.message_post(
                        body=meeting._get_email_template('invitation', meeting),
                        subject=f"Meeting Invitation: {meeting.name}",
                        partner_ids=meeting.participant_ids.mapped('partner_id').ids,
                        email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                        subtype_xmlid='mail.mt_comment',
                        message_type='email',
                    )

                    meeting.email_sent = True
                    _logger.info(f"Meeting invitation sent for: {meeting.name}")

                except Exception as e:
                    _logger.error(f"Failed to send meeting invitation for {meeting.name}: {str(e)}")
                    # Fallback: use sudo() for mail creation
                    meeting._send_email_with_sudo('invitation')

    def _send_meeting_confirmation_email(self):
        """Send meeting confirmation email using proper methods."""
        for meeting in self:
            if meeting.participant_ids:
                try:
                    meeting.message_post(
                        body=meeting._get_email_template('confirmation', meeting),
                        subject=f"Meeting Confirmed: {meeting.name}",
                        partner_ids=meeting.participant_ids.mapped('partner_id').ids,
                        email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                        subtype_xmlid='mail.mt_comment',
                        message_type='email',
                    )
                except Exception as e:
                    _logger.error(f"Failed to send meeting confirmation: {str(e)}")
                    meeting._send_email_with_sudo('confirmation')

    def _send_email_with_sudo(self, template_type):
        """Fallback method using sudo() for email creation."""
        for meeting in self:
            if meeting.participant_ids:
                subject = f"Meeting {template_type.title()}: {meeting.name}"
                body = meeting._get_email_template(template_type, meeting)

                for participant in meeting.participant_ids:
                    if participant.email:
                        try:
                            # Use sudo() for mail creation as fallback
                            self.env['mail.mail'].sudo().create({
                                'subject': subject,
                                'body_html': body,
                                'email_from': meeting.organizer_id.email or self.env.user.email,
                                'email_to': participant.email,
                                'auto_delete': True,
                            }).send()

                            _logger.info(f"Email sent via sudo to {participant.email}")

                        except Exception as e:
                            _logger.error(f"Failed to send email to {participant.email}: {str(e)}")

    def _send_meeting_reminder_email(self):
        """Send meeting reminder email."""
        for meeting in self:
            try:
                meeting.message_post(
                    body=meeting._get_email_template('reminder', meeting),
                    subject=f"Meeting Reminder: {meeting.name} - {meeting.date.strftime('%d/%m/%Y at %H:%M') if meeting.date else 'TBD'}",
                    partner_ids=meeting.participant_ids.mapped('partner_id').ids,
                    subtype_xmlid='mail.mt_comment',
                )
            except Exception as e:
                _logger.error(f"Failed to send reminder: {str(e)}")
                meeting._send_email_with_sudo('reminder')

    def _send_meeting_summary_email(self):
        """Send meeting summary email."""
        for meeting in self:
            if meeting.participant_ids:
                subject = f"Meeting Summary: {meeting.name}"
                body = self._get_email_template('summary', meeting)

                for participant in meeting.participant_ids:
                    if participant.email:
                        try:
                            # Use sudo() for mail creation
                            self.env['mail.mail'].sudo().create({
                                'subject': subject,
                                'body_html': body,
                                'email_from': meeting.organizer_id.email or self.env.user.email,
                                'email_to': participant.email,
                                'auto_delete': True,
                            }).send()

                            _logger.info(f"Meeting summary sent to {participant.email}")
                        except Exception as e:
                            _logger.error(f"Failed to send summary to {participant.email}: {str(e)}")

    def _send_meeting_postponement_email(self):
        """Send meeting postponement email."""
        for meeting in self:
            if meeting.participant_ids:
                subject = f"Meeting Postponed: {meeting.name}"
                body = self._get_email_template('postponement', meeting)

                for participant in meeting.participant_ids:
                    if participant.email:
                        try:
                            # Use sudo() for mail creation
                            self.env['mail.mail'].sudo().create({
                                'subject': subject,
                                'body_html': body,
                                'email_from': meeting.organizer_id.email or self.env.user.email,
                                'email_to': participant.email,
                                'auto_delete': True,
                            }).send()

                            _logger.info(f"Meeting postponement sent to {participant.email}")
                        except Exception as e:
                            _logger.error(f"Failed to send postponement to {participant.email}: {str(e)}")

    def _send_meeting_cancellation_email(self):
        """Send meeting cancellation email."""
        for meeting in self:
            try:
                meeting.message_post(
                    body=meeting._get_email_template('cancellation', meeting),
                    subject=f"Meeting Cancelled: {meeting.name}",
                    partner_ids=meeting.participant_ids.mapped('partner_id').ids,
                    subtype_xmlid='mail.mt_comment',
                )
            except Exception as e:
                _logger.error(f"Failed to send cancellation: {str(e)}")
                meeting._send_email_with_sudo('cancellation')

    def _get_email_template(self, template_type, meeting):
        """Generate email template based on type."""
        base_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #2c3e50; margin-bottom: 20px;">Internship Management System</h2>
        """

        if template_type == 'invitation':
            base_html += f"""
                <h3 style="color: #3498db;">Meeting Invitation</h3>
                <p>You are invited to attend the following meeting:</p>
                <div style="background-color: white; padding: 15px; border-radius: 3px; margin: 10px 0;">
                    <p><strong>Title:</strong> {meeting.name}</p>
                    <p><strong>Date:</strong> {meeting.date.strftime('%A, %B %d, %Y at %H:%M')}</p>
                    <p><strong>Duration:</strong> {meeting.duration} hour(s)</p>
                    <p><strong>Type:</strong> {dict(meeting._fields['meeting_type'].selection).get(meeting.meeting_type)}</p>
                    <p><strong>Modality:</strong> {dict(meeting._fields['meeting_type_modality'].selection).get(meeting.meeting_type_modality)}</p>
                    {f'<p><strong>Location:</strong> {meeting.location}</p>' if meeting.location else ''}
                    {f'<p><strong>Meeting URL:</strong> <a href="{meeting.meeting_url}">{meeting.meeting_url}</a></p>' if meeting.meeting_url else ''}
                </div>
                {f'<div style="background-color: #e8f4fd; padding: 15px; border-radius: 3px; margin: 10px 0;"><h4>Agenda:</h4>{meeting.agenda or "No agenda provided"}</div>' if meeting.agenda else ''}
            """
        elif template_type == 'confirmation':
            base_html += f"""
                <h3 style="color: #27ae60;">Meeting Confirmed</h3>
                <p>The following meeting has been confirmed:</p>
                <div style="background-color: white; padding: 15px; border-radius: 3px; margin: 10px 0;">
                    <p><strong>Title:</strong> {meeting.name}</p>
                    <p><strong>Date:</strong> {meeting.date.strftime('%A, %B %d, %Y at %H:%M')}</p>
                    <p><strong>Duration:</strong> {meeting.duration} hour(s)</p>
                    {f'<p><strong>Location:</strong> {meeting.location}</p>' if meeting.location else ''}
                    {f'<p><strong>Meeting URL:</strong> <a href="{meeting.meeting_url}">{meeting.meeting_url}</a></p>' if meeting.meeting_url else ''}
                </div>
                <p>Please confirm your attendance.</p>
            """
        elif template_type == 'reminder':
            base_html += f"""
                <h3 style="color: #f39c12;">Meeting Reminder</h3>
                <p>This is a reminder for your upcoming meeting:</p>
                <div style="background-color: white; padding: 15px; border-radius: 3px; margin: 10px 0;">
                    <p><strong>Title:</strong> {meeting.name}</p>
                    <p><strong>Date:</strong> {meeting.date.strftime('%A, %B %d, %Y at %H:%M')}</p>
                    <p><strong>Duration:</strong> {meeting.duration} hour(s)</p>
                    {f'<p><strong>Location:</strong> {meeting.location}</p>' if meeting.location else ''}
                    {f'<p><strong>Meeting URL:</strong> <a href="{meeting.meeting_url}">{meeting.meeting_url}</a></p>' if meeting.meeting_url else ''}
                </div>
                <p>Please prepare for the meeting!</p>
            """
        elif template_type == 'summary':
            base_html += f"""
                <h3 style="color: #9b59b6;">Meeting Summary</h3>
                <p>The meeting "{meeting.name}" has been completed.</p>
                {f'<div style="background-color: white; padding: 15px; border-radius: 3px; margin: 10px 0;"><h4>Summary:</h4>{meeting.summary or "No summary provided"}</div>' if meeting.summary else ''}
                {f'<div style="background-color: #f0f8ff; padding: 15px; border-radius: 3px; margin: 10px 0;"><h4>Action Items:</h4>{meeting.next_actions or "No action items"}</div>' if meeting.next_actions else ''}
                {f'<div style="background-color: #f0fff0; padding: 15px; border-radius: 3px; margin: 10px 0;"><h4>Decisions Made:</h4>{meeting.decisions or "No decisions recorded"}</div>' if meeting.decisions else ''}
            """
        elif template_type == 'cancellation':
            base_html += f"""
                <h3 style="color: #e74c3c;">Meeting Cancelled</h3>
                <p>The meeting "{meeting.name}" scheduled for {meeting.date.strftime('%A, %B %d, %Y at %H:%M')} has been cancelled.</p>
                <p>A new meeting will be scheduled soon.</p>
            """
        elif template_type == 'postponement':
            base_html += f"""
                <h3 style="color: #f39c12;">Meeting Postponed</h3>
                <p>The meeting "{meeting.name}" scheduled for {meeting.date.strftime('%A, %B %d, %Y at %H:%M')} has been postponed.</p>
                <p>A new date will be communicated soon.</p>
            """

        base_html += """
            </div>
            <div style="text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 12px;">
                <p>This email was sent automatically by the Internship Management System</p>
            </div>
        </div>
        """

        return base_html

    # ===============================
    # UTILITY METHODS
    # ===============================

    def name_get(self):
        """Custom name display: Name (Date)."""
        result = []
        for meeting in self:
            name = meeting.name
            if meeting.date:
                date_str = meeting.date.strftime('%Y-%m-%d %H:%M')
                name = f"{name} ({date_str})"
            result.append((meeting.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        """Custom search: search by name, type, or participants."""
        args = args or []
        domain = []

        if name:
            domain = ['|', '|', '|',
                      ('name', operator, name),
                      ('meeting_type', operator, name),
                      ('participant_ids.name', operator, name),
                      ('agenda', operator, name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid, order=order)

    def get_meeting_statistics(self):
        """Return statistical data for this meeting."""
        self.ensure_one()
        return {
            'days_to_meeting': (self.date - fields.Datetime.now()).days if self.date else None,
            'is_past': self.is_past,
            'is_today': self.is_today,
            'is_upcoming': self.is_upcoming,
            'attendance_rate': (self.confirmed_count / self.attendance_count * 100) if self.attendance_count > 0 else 0,
            'has_documents': len(self.document_ids) > 0,
            'has_summary': bool(self.summary),
            'has_action_items': bool(self.next_actions),
        }


class InternshipMeetingAttendee(models.Model):
    """Meeting attendee model for tracking attendance."""
    _name = 'internship.meeting.attendee'
    _description = 'Meeting Attendee'
    _rec_name = 'user_id'

    meeting_id = fields.Many2one(
        'internship.meeting',
        string='Meeting',
        required=False,
        ondelete='cascade'
    )

    user_id = fields.Many2one(
        'res.users',
        string='Attendee',
        required=False
    )

    attendance_status = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('absent', 'Absent'),
        ('excused', 'Excused')
    ], string='Attendance Status', default='pending')

    attendance_confirmed = fields.Boolean(
        string='Attendance Confirmed',
        default=False
    )

    notes = fields.Text(
        string='Notes',
        help="Additional notes about attendance"
    )

    _sql_constraints = [
        ('unique_attendee_per_meeting', 'UNIQUE(meeting_id, user_id)',
         'Each user can only be listed once per meeting.'),
    ]
