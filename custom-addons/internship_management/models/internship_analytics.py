# -*- coding: utf-8 -*-
"""
Enhanced Analytics Model for Internship Dashboard
==============================================
File: models/internship_analytics.py
"""

import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class InternshipAnalytics(models.Model):
    """Analytics model for internship dashboard metrics."""

    _name = 'internship.analytics'
    _description = 'Internship Analytics & KPIs'
    _auto = False  # No database table needed - this is a computed model

    @api.model
    def get_dashboard_data(self):
        """
        Main method to get all dashboard data based on user role.

        Returns:
            dict: Complete dashboard data structure
        """
        try:
            user_role = self._get_user_role()
            _logger.info(f"Generating dashboard for user role: {user_role}")
            
            base_data = {
                'user_role': user_role,
                'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            if user_role == 'student':
                dashboard_data = self._get_student_dashboard()
            elif user_role == 'supervisor':
                dashboard_data = self._get_supervisor_dashboard()
            elif user_role == 'admin':
                dashboard_data = self._get_admin_dashboard()
            else:
                dashboard_data = self._get_default_dashboard()
            
            # Merge base data with role-specific data
            base_data.update(dashboard_data)
            return base_data
                
        except Exception as e:
            _logger.error(f"Dashboard data error: {e}", exc_info=True)
            return self._get_empty_dashboard()

    def _get_user_role(self):
        """Determine user role from groups."""
        user = self.env.user
        if user.has_group('internship_management.group_internship_student'):
            return 'student'
        elif user.has_group('internship_management.group_internship_supervisor'):
            return 'supervisor'
        elif user.has_group('internship_management.group_internship_admin'):
            return 'admin'
        return 'default'

    def _get_student_dashboard(self):
        """Get dashboard data for students."""
        try:
            # Get student record
            student = self.env['internship.student'].search([
                ('user_id', '=', self.env.user.id)
            ], limit=1)
            
            if not student:
                return self._get_empty_dashboard()
            
            # Get student's internships
            internships = self.env['internship.stage'].search([
                ('student_id', '=', student.id)
            ])
            
            # Calculate KPIs
            kpi_cards = [
                {
                    'id': 'total_internships',
                    'title': 'Total Internships',
                    'value': len(internships),
                    'icon': 'fa-graduation-cap',
                    'color': 'primary'
                },
                {
                    'id': 'active_internships',
                    'title': 'Active Internships',
                    'value': len(internships.filtered(lambda i: i.state == 'in_progress')),
                    'icon': 'fa-play-circle',
                    'color': 'success'
                },
                {
                    'id': 'completed_internships',
                    'title': 'Completed',
                    'value': len(internships.filtered(lambda i: i.state == 'completed')),
                    'icon': 'fa-check-circle',
                    'color': 'info'
                },
                {
                    'id': 'average_grade',
                    'title': 'Average Grade',
                    'value': f"{sum(i.final_grade for i in internships if i.final_grade) / max(len([i for i in internships if i.final_grade]), 1):.1f}" if internships.filtered('final_grade') else 'N/A',
                    'icon': 'fa-star',
                    'color': 'warning'
                }
            ]
            
            # Recent activities
            recent_activities = []
            for internship in internships.sorted('write_date', reverse=True)[:5]:
                recent_activities.append({
                    'id': f'internship_{internship.id}',
                    'message': f'Internship "{internship.title}" - Status: {dict(internship._fields['state'].selection)[internship.state]}',
                    'date': internship.write_date.strftime('%Y-%m-%d %H:%M') if internship.write_date else '',
                    'icon': 'fa-graduation-cap',
                    'type': 'primary'
                })
            
            # Status distribution for charts
            status_data = {}
            for internship in internships:
                status = dict(internship._fields['state'].selection).get(internship.state, internship.state)
                status_data[status] = status_data.get(status, 0) + 1
            
            charts = {
                'status_distribution': {
                    'labels': list(status_data.keys()),
                    'datasets': [{
                        'data': list(status_data.values()),
                        'backgroundColor': ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d']
                    }]
                }
            }
            
            return {
                'kpi_cards': kpi_cards,
                'recent_activities': recent_activities,
                'charts': charts,
                'notifications': self._get_student_notifications(student)
            }
            
        except Exception as e:
            _logger.error(f"Student dashboard error: {e}")
            return self._get_empty_dashboard()

    def _get_supervisor_dashboard(self):
        """Get dashboard data for supervisors."""
        try:
            # Get supervisor record
            supervisor = self.env['internship.supervisor'].search([
                ('user_id', '=', self.env.user.id)
            ], limit=1)
            
            if not supervisor:
                return self._get_empty_dashboard()
            
            # Get supervised internships
            internships = self.env['internship.stage'].search([
                ('supervisor_id', '=', supervisor.id)
            ])
            
            students = internships.mapped('student_id')
            
            # Calculate KPIs
            kpi_cards = [
                {
                    'id': 'total_students',
                    'title': 'Total Students',
                    'value': len(students),
                    'icon': 'fa-users',
                    'color': 'primary'
                },
                {
                    'id': 'active_internships',
                    'title': 'Active Internships',
                    'value': len(internships.filtered(lambda i: i.state == 'in_progress')),
                    'icon': 'fa-play-circle',
                    'color': 'success'
                },
                {
                    'id': 'pending_evaluations',
                    'title': 'Pending Evaluations',
                    'value': len(internships.filtered(lambda i: i.state == 'completed' and not i.final_grade)),
                    'icon': 'fa-clock',
                    'color': 'warning'
                },
                {
                    'id': 'capacity_used',
                    'title': 'Capacity Used',
                    'value': f"{len(internships.filtered(lambda i: i.state == 'in_progress'))}/{supervisor.capacity or 10}",
                    'icon': 'fa-percentage',
                    'color': 'info'
                }
            ]
            
            # Recent activities
            recent_activities = []
            for internship in internships.sorted('write_date', reverse=True)[:5]:
                recent_activities.append({
                    'id': f'internship_{internship.id}',
                    'message': f'Student {internship.student_id.full_name} - {internship.title}',
                    'date': internship.write_date.strftime('%Y-%m-%d %H:%M') if internship.write_date else '',
                    'icon': 'fa-user-graduate',
                    'type': 'primary'
                })
            
            # Status distribution
            status_data = {}
            for internship in internships:
                status = dict(internship._fields['state'].selection).get(internship.state, internship.state)
                status_data[status] = status_data.get(status, 0) + 1
            
            charts = {
                'status_distribution': {
                    'labels': list(status_data.keys()),
                    'datasets': [{
                        'data': list(status_data.values()),
                        'backgroundColor': ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d']
                    }]
                }
            }
            
            return {
                'kpi_cards': kpi_cards,
                'recent_activities': recent_activities,
                'charts': charts,
                'notifications': self._get_supervisor_notifications(supervisor)
            }
            
        except Exception as e:
            _logger.error(f"Supervisor dashboard error: {e}")
            return self._get_empty_dashboard()

    def _get_admin_dashboard(self):
        """Get dashboard data for administrators."""
        try:
            # Get all internships
            all_internships = self.env['internship.stage'].search([])
            all_students = self.env['internship.student'].search([])
            all_supervisors = self.env['internship.supervisor'].search([])
            
            # Calculate KPIs
            kpi_cards = [
                {
                    'id': 'total_internships',
                    'title': 'Total Internships',
                    'value': len(all_internships),
                    'icon': 'fa-graduation-cap',
                    'color': 'primary'
                },
                {
                    'id': 'total_students',
                    'title': 'Total Students',
                    'value': len(all_students),
                    'icon': 'fa-users',
                    'color': 'success'
                },
                {
                    'id': 'total_supervisors',
                    'title': 'Total Supervisors',
                    'value': len(all_supervisors),
                    'icon': 'fa-user-tie',
                    'color': 'info'
                },
                {
                    'id': 'completion_rate',
                    'title': 'Completion Rate',
                    'value': f"{(len(all_internships.filtered(lambda i: i.state == 'completed')) / max(len(all_internships), 1) * 100):.1f}%",
                    'icon': 'fa-chart-line',
                    'color': 'warning'
                }
            ]
            
            # Recent activities (system-wide)
            recent_activities = []
            for internship in all_internships.sorted('write_date', reverse=True)[:5]:
                recent_activities.append({
                    'id': f'internship_{internship.id}',
                    'message': f'Internship "{internship.title}" updated by {internship.student_id.full_name}',
                    'date': internship.write_date.strftime('%Y-%m-%d %H:%M') if internship.write_date else '',
                    'icon': 'fa-edit',
                    'type': 'primary'
                })
            
            # Status distribution
            status_data = {}
            for internship in all_internships:
                status = dict(internship._fields['state'].selection).get(internship.state, internship.state)
                status_data[status] = status_data.get(status, 0) + 1
            
            charts = {
                'status_distribution': {
                    'labels': list(status_data.keys()),
                    'datasets': [{
                        'data': list(status_data.values()),
                        'backgroundColor': ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d']
                    }]
                }
            }
            
            return {
                'kpi_cards': kpi_cards,
                'recent_activities': recent_activities,
                'charts': charts,
                'notifications': self._get_admin_notifications()
            }
            
        except Exception as e:
            _logger.error(f"Admin dashboard error: {e}")
            return self._get_empty_dashboard()

    def _get_default_dashboard(self):
        """Get default dashboard for users without specific roles."""
        return {
            'kpi_cards': [
                {
                    'id': 'welcome',
                    'title': 'Welcome',
                    'value': 'To TechPal',
                    'icon': 'fa-hand-wave',
                    'color': 'primary'
                }
            ],
            'recent_activities': [],
            'charts': {},
            'notifications': []
        }

    def _get_empty_dashboard(self):
        """Return empty dashboard structure."""
        return {
            'user_role': 'default',
            'kpi_cards': [],
            'recent_activities': [],
            'charts': {},
            'notifications': [],
            'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def _get_student_notifications(self, student):
        """Get notifications specific to students."""
        notifications = []
        
        # Check for approaching deadlines
        internships = self.env['internship.stage'].search([
            ('student_id', '=', student.id),
            ('state', '=', 'in_progress'),
            ('end_date', '<=', fields.Date.add(fields.Date.today(), days=7))
        ])
        
        for internship in internships:
            notifications.append({
                'id': f'deadline_{internship.id}',
                'title': 'Deadline Approaching',
                'message': f'Your internship "{internship.title}" ends on {internship.end_date}',
                'type': 'warning'
            })
        
        return notifications

    def _get_supervisor_notifications(self, supervisor):
        """Get notifications specific to supervisors."""
        notifications = []
        
        # Check for students needing evaluation
        internships_to_evaluate = self.env['internship.stage'].search([
            ('supervisor_id', '=', supervisor.id),
            ('state', '=', 'completed'),
            ('final_grade', '=', False)
        ])
        
        if internships_to_evaluate:
            notifications.append({
                'id': 'pending_evaluations',
                'title': 'Pending Evaluations',
                'message': f'You have {len(internships_to_evaluate)} internships waiting for evaluation',
                'type': 'warning'
            })
        
        return notifications

    def _get_admin_notifications(self):
        """Get notifications for administrators."""
        notifications = []
        
        # Check system health
        total_internships = self.env['internship.stage'].search_count([])
        active_internships = self.env['internship.stage'].search_count([('state', '=', 'in_progress')])
        
        if active_internships > 0:
            notifications.append({
                'id': 'system_status',
                'title': 'System Status',
                'message': f'{active_internships} active internships out of {total_internships} total',
                'type': 'info'
            })
        
        return notifications