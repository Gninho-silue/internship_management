# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class InternshipDashboard(models.TransientModel):

    """
    Internship Dashboard Model

    This model handles the dashboard for the internship management system.
    It provides a summary of the internship data for the current user.
    """

    _name = 'internship.dashboard'
    _description = 'Internship Dashboard'

    # Dashboard Type
    dashboard_type = fields.Selection([
        ('admin', 'Administrator Dashboard'),
        ('supervisor', 'Supervisor Dashboard'),
        ('student', 'Student Dashboard')
    ], string='Dashboard Type', required=True, default='admin')

    # Date Range
    date_from = fields.Date(string='From Date', default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='To Date', default=fields.Date.today)

    # Statistics Fields
    total_internships = fields.Integer(string='Total Internships', compute='_compute_statistics')
    active_internships = fields.Integer(string='Active Internships', compute='_compute_statistics')
    completed_internships = fields.Integer(string='Completed Internships', compute='_compute_statistics')
    pending_internships = fields.Integer(string='Pending Internships', compute='_compute_statistics')

    # Student Statistics
    total_students = fields.Integer(string='Total Students', compute='_compute_statistics')
    active_students = fields.Integer(string='Active Students', compute='_compute_statistics')

    # Supervisor Statistics
    total_supervisors = fields.Integer(string='Total Supervisors', compute='_compute_statistics')
    active_supervisors = fields.Integer(string='Active Supervisors', compute='_compute_statistics')

    # Document Statistics
    total_documents = fields.Integer(string='Total Documents', compute='_compute_statistics')
    pending_reviews = fields.Integer(string='Pending Reviews', compute='_compute_statistics')
    total_presentations = fields.Integer(string='Total Presentations', compute='_compute_statistics')
    pending_presentations = fields.Integer(string='Pending Presentations', compute='_compute_statistics')

    # Task Statistics
    total_tasks = fields.Integer(string='Total Tasks', compute='_compute_statistics')
    overdue_tasks = fields.Integer(string='Overdue Tasks', compute='_compute_statistics')
    completed_tasks = fields.Integer(string='Completed Tasks', compute='_compute_statistics')

    # Meeting Statistics
    total_meetings = fields.Integer(string='Total Meetings', compute='_compute_statistics')
    upcoming_meetings = fields.Integer(string='Upcoming Meetings', compute='_compute_statistics')
    
    # Alert Statistics
    total_alerts = fields.Integer(string='Total Alerts', compute='_compute_statistics')
    active_alerts = fields.Integer(string='Active Alerts', compute='_compute_statistics')
    high_priority_alerts = fields.Integer(string='High Priority Alerts', compute='_compute_statistics')
    overdue_tasks_alerts = fields.Integer(string='Overdue Tasks Alerts', compute='_compute_statistics')

    # Communication Statistics
    total_communications = fields.Integer(string='Total Communications', compute='_compute_statistics')
    unread_communications = fields.Integer(string='Unread Communications', compute='_compute_statistics')

   
    @api.depends('dashboard_type', 'date_from', 'date_to')
    def _compute_statistics(self):
        """Compute dashboard statistics based on user role and date range."""
        for dashboard in self:
            domain = self._get_base_domain()
            
            # Internship Statistics
            dashboard.total_internships = self.env['internship.stage'].search_count(domain)
            dashboard.active_internships = self.env['internship.stage'].search_count(
                domain + [('state', '=', 'in_progress')]
            )
            dashboard.completed_internships = self.env['internship.stage'].search_count(
                domain + [('state', '=', 'completed')]
            )
            dashboard.pending_internships = self.env['internship.stage'].search_count(
                domain + [('state', 'in', ['draft', 'submitted', 'approved'])]
            )

            # Student Statistics
            student_domain = self._get_student_domain()
            dashboard.total_students = self.env['internship.student'].search_count(student_domain)
            dashboard.active_students = self.env['internship.student'].search_count(
                student_domain + [('internship_ids.state', '=', 'in_progress')]
            )

            # Supervisor Statistics
            supervisor_domain = self._get_supervisor_domain()
            dashboard.total_supervisors = self.env['internship.supervisor'].search_count(supervisor_domain)
            dashboard.active_supervisors = self.env['internship.supervisor'].search_count(
                supervisor_domain + [('stage_ids.state', '=', 'in_progress')]
            )

            # Document Statistics
            doc_domain = self._get_document_domain()
            dashboard.total_documents = self.env['internship.document'].search_count(doc_domain)
            dashboard.pending_reviews = self.env['internship.document'].search_count(
                doc_domain + [('state', '=', 'submitted')]
            )

            # Presentation Statistics
            pres_domain = self._get_presentation_domain()
            dashboard.total_presentations = self.env['internship.presentation'].search_count(pres_domain)
            dashboard.pending_presentations = self.env['internship.presentation'].search_count(
                pres_domain + [('status', '=', 'submitted')]
            )

            # Task Statistics
            task_domain = self._get_task_domain()
            dashboard.total_tasks = self.env['internship.todo'].search_count(task_domain)
            dashboard.overdue_tasks = self.env['internship.todo'].search_count(
                task_domain + [('deadline', '<', fields.Date.today()), ('state', '!=', 'completed')]
            )
            dashboard.completed_tasks = self.env['internship.todo'].search_count(
                task_domain + [('state', '=', 'completed')]
            )

            # Meeting Statistics
            meeting_domain = self._get_meeting_domain()
            dashboard.total_meetings = self.env['internship.meeting'].search_count(meeting_domain)
            dashboard.upcoming_meetings = self.env['internship.meeting'].search_count(
                meeting_domain + [('date', '>', fields.Datetime.now())]
            )
            
            # Alert Statistics
            alert_domain = self._get_alert_domain()
            dashboard.total_alerts = self.env['internship.alert'].search_count(alert_domain)
            dashboard.active_alerts = self.env['internship.alert'].search_count(
                alert_domain + [('state', '=', 'active')]
            )
            dashboard.high_priority_alerts = self.env['internship.alert'].search_count(
                alert_domain + [('priority', '=', '1')]
            )
            dashboard.overdue_tasks_alerts = self.env['internship.alert'].search_count(
                alert_domain + [('alert_type', '=', 'task_overdue')]
            )

            # Communication Statistics
            comm_domain = self._get_communication_domain()
            dashboard.total_communications = self.env['internship.communication'].search_count(comm_domain)
            dashboard.unread_communications = self.env['internship.communication'].search_count(
                comm_domain + [('state', '=', 'sent')]
            )

    def _get_base_domain(self):
        """Get base domain based on dashboard type and user role."""
        domain = []
        
        if self.dashboard_type == 'supervisor':
            # Supervisor sees only supervised internships
            domain = [('supervisor_id.user_id', '=', self.env.user.id)]
        elif self.dashboard_type == 'student':
            # Student sees only their internships
            student = self.env['internship.student'].search([('user_id', '=', self.env.user.id)], limit=1)
            if student:
                domain = [('student_id', '=', student.id)]
            else:
                domain = [('id', '=', False)]  # No internships if no student record
        
        # Add date filter
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
            
        return domain

    def _get_student_domain(self):
        """Get student domain based on dashboard type."""
        domain = []
        
        if self.dashboard_type == 'supervisor':
            # Supervisor sees students from supervised internships
            supervised_stages = self.env['internship.stage'].search([
                ('supervisor_id.user_id', '=', self.env.user.id)
            ])
            student_ids = supervised_stages.mapped('student_id.id')
            domain = [('id', 'in', student_ids)]
        elif self.dashboard_type == 'student':
            # Student sees only themselves
            domain = [('user_id', '=', self.env.user.id)]
        
        return domain

    def _get_supervisor_domain(self):
        """Get supervisor domain based on dashboard type."""
        domain = []
        
        if self.dashboard_type == 'supervisor':
            # Supervisor sees only themselves
            domain = [('user_id', '=', self.env.user.id)]
        elif self.dashboard_type == 'student':
            # Student sees their supervisors
            student = self.env['internship.student'].search([('user_id', '=', self.env.user.id)], limit=1)
            if student:
                supervisor_ids = student.internship_ids.mapped('supervisor_id.id')
                domain = [('id', 'in', supervisor_ids)]
            else:
                domain = [('id', '=', False)]
        
        return domain

    def _get_document_domain(self):
        """Get document domain based on dashboard type."""
        domain = []
        
        if self.dashboard_type == 'supervisor':
            # Supervisor sees documents from supervised internships
            supervised_stages = self.env['internship.stage'].search([
                ('supervisor_id.user_id', '=', self.env.user.id)
            ])
            stage_ids = supervised_stages.ids
            domain = [('stage_id', 'in', stage_ids)]
        elif self.dashboard_type == 'student':
            # Student sees their documents
            student = self.env['internship.student'].search([('user_id', '=', self.env.user.id)], limit=1)
            if student:
                stage_ids = student.internship_ids.ids
                domain = [('stage_id', 'in', stage_ids)]
            else:
                domain = [('id', '=', False)]
        
        return domain

    def _get_presentation_domain(self):
        """Get presentation domain based on dashboard type."""
        domain = []
        
        if self.dashboard_type == 'supervisor':
            # Supervisor sees presentations from supervised internships
            supervised_stages = self.env['internship.stage'].search([
                ('supervisor_id.user_id', '=', self.env.user.id)
            ])
            stage_ids = supervised_stages.ids
            domain = [('stage_id', 'in', stage_ids)]
        elif self.dashboard_type == 'student':
            # Student sees their presentations
            student = self.env['internship.student'].search([('user_id', '=', self.env.user.id)], limit=1)
            if student:
                stage_ids = student.internship_ids.ids
                domain = [('stage_id', 'in', stage_ids)]
            else:
                domain = [('id', '=', False)]
        
        return domain

    def _get_task_domain(self):
        """Get task domain based on dashboard type."""
        domain = []
        
        if self.dashboard_type == 'supervisor':
            # Supervisor sees tasks from supervised internships
            supervised_stages = self.env['internship.stage'].search([
                ('supervisor_id.user_id', '=', self.env.user.id)
            ])
            stage_ids = supervised_stages.ids
            domain = [('stage_id', 'in', stage_ids)]
        elif self.dashboard_type == 'student':
            # Student sees their tasks
            student = self.env['internship.student'].search([('user_id', '=', self.env.user.id)], limit=1)
            if student:
                stage_ids = student.internship_ids.ids
                domain = [('stage_id', 'in', stage_ids)]
            else:
                domain = [('id', '=', False)]
        
        return domain

    def _get_meeting_domain(self):
        """Get meeting domain based on dashboard type."""
        domain = []
        
        if self.dashboard_type == 'supervisor':
            # Supervisor sees meetings they organize or participate in
            domain = ['|', ('organizer_id', '=', self.env.user.id), ('participant_ids', 'in', self.env.user.id)]
        elif self.dashboard_type == 'student':
            # Student sees meetings they organize or participate in
            domain = ['|', ('organizer_id', '=', self.env.user.id), ('participant_ids', 'in', self.env.user.id)]
        
        return domain

    def _get_alert_domain(self):
        """Get alert domain based on dashboard type."""
        domain = []
        
        if self.dashboard_type == 'supervisor':
            # Supervisor sees alerts for their supervised internships
            supervised_stages = self.env['internship.stage'].search([
                ('supervisor_id.user_id', '=', self.env.user.id)
            ])
            stage_ids = supervised_stages.ids
            domain = [('stage_id', 'in', stage_ids)]
        elif self.dashboard_type == 'student':
            # Student sees alerts for their internships
            student = self.env['internship.student'].search([('user_id', '=', self.env.user.id)], limit=1)
            if student:
                stage_ids = student.internship_ids.ids
                domain = [('stage_id', 'in', stage_ids)]
            else:
                domain = [('id', '=', False)]
        
        return domain

    def _get_communication_domain(self):
        """Get communication domain based on dashboard type."""
        domain = []
        
        if self.dashboard_type == 'supervisor':
            # Supervisor sees communications they sent or received
            domain = ['|', ('sender_id', '=', self.env.user.id), ('recipient_ids', 'in', self.env.user.id)]
        elif self.dashboard_type == 'student':
            # Student sees communications they sent or received
            domain = ['|', ('sender_id', '=', self.env.user.id), ('recipient_ids', 'in', self.env.user.id)]
        
        return domain


    def action_refresh_dashboard(self):
        """Refresh dashboard data."""
        self._compute_statistics()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'internship.dashboard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def get_dashboard_data(self, dashboard_type='admin'):
        """Get dashboard data for current user."""
        dashboard = self.create({
            'dashboard_type': dashboard_type,
            'date_from': fields.Date.today() - timedelta(days=30),
            'date_to': fields.Date.today()
        })
        dashboard._compute_statistics()
        return dashboard
