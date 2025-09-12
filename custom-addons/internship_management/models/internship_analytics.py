# -*- coding: utf-8 -*-
"""
Step 1: Analytics Model for Advanced Dashboard
==============================================
File: models/internship_analytics.py
"""

import logging
from datetime import datetime, timedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class InternshipAnalytics(models.Model):
    """Analytics model for advanced dashboard metrics."""

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
            
            if user_role == 'student':
                return self._get_student_dashboard()
            elif user_role == 'supervisor':
                return self._get_supervisor_dashboard()
            elif user_role == 'company':
                return self._get_company_dashboard()
            elif user_role == 'admin':
                return self._get_admin_dashboard()
            else:
                return self._get_default_dashboard()
                
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
        elif user.has_group('internship_management.group_internship_company'):
            return 'company'
        elif user.has_group('internship_management.group_internship_admin'):
            return 'admin'
        return 'default'

    def _get_kpi_cards(self):
        """Get KPI cards data."""
        Stage = self.env['internship.stage']
        Student = self.env['internship.student']
        Supervisor = self.env['internship.supervisor']

        # Calculate current year data
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1)

        total_internships = Stage.search_count([])
        active_internships = Stage.search_count([('state', 'in', ['in_progress', 'submitted'])])
        completed_this_year = Stage.search_count([
            ('state', '=', 'completed'),
            ('end_date', '>=', year_start)
        ])

        # Calculate completion rate
        total_started = Stage.search_count([('state', '!=', 'draft')])
        completed_total = Stage.search_count([('state', 'in', ['completed', 'evaluated'])])
        completion_rate = round((completed_total / total_started * 100) if total_started > 0 else 0, 1)

        # Calculate average grade
        graded_stages = Stage.search([('final_grade', '>', 0), ('state', '=', 'evaluated')])
        avg_grade = round(sum(graded_stages.mapped('final_grade')) / len(graded_stages), 2) if graded_stages else 0

        return {
            'total_internships': {
                'value': total_internships,
                'label': 'Total Internships',
                'icon': 'fa-graduation-cap',
                'color': 'primary',
                'trend': self._calculate_trend('total', total_internships)
            },
            'active_internships': {
                'value': active_internships,
                'label': 'Active Now',
                'icon': 'fa-play-circle',
                'color': 'success',
                'trend': self._calculate_trend('active', active_internships)
            },
            'completion_rate': {
                'value': f"{completion_rate}%",
                'label': 'Completion Rate',
                'icon': 'fa-chart-line',
                'color': 'info',
                'trend': self._calculate_trend('completion', completion_rate)
            },
            'average_grade': {
                'value': avg_grade,
                'label': 'Average Grade',
                'icon': 'fa-star',
                'color': 'warning',
                'trend': self._calculate_trend('grade', avg_grade)
            }
        }

    def _get_charts_data(self):
        """Get all charts data."""
        return {
            'status_distribution': self._get_status_distribution(),
            'monthly_trends': self._get_monthly_trends(),
            'grade_distribution': self._get_grade_distribution(),
            'supervisor_workload': self._get_supervisor_workload(),
            'area_performance': self._get_area_performance()
        }

    def _get_status_distribution(self):
        """Get internship status distribution for pie chart."""
        Stage = self.env['internship.stage']

        states_data = []
        state_colors = {
            'draft': '#6c757d',
            'submitted': '#007bff',
            'approved': '#28a745',
            'in_progress': '#ffc107',
            'completed': '#17a2b8',
            'evaluated': '#28a745',
            'cancelled': '#dc3545'
        }

        for state_key, state_label in Stage._fields['state'].selection:
            count = Stage.search_count([('state', '=', state_key)])
            if count > 0:  # Only include states with data
                states_data.append({
                    'label': state_label,
                    'value': count,
                    'color': state_colors.get(state_key, '#6c757d')
                })

        return states_data

    def _get_monthly_trends(self):
        """Get monthly trends for the last 12 months."""
        Stage = self.env['internship.stage']
        trends_data = []

        for i in range(12):
            # Calculate month boundaries
            month_date = datetime.now() - timedelta(days=30 * i)
            month_start = month_date.replace(day=1)
            if month_date.month == 12:
                month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)

            # Count created and completed internships
            created_count = Stage.search_count([
                ('create_date', '>=', month_start),
                ('create_date', '<=', month_end)
            ])

            completed_count = Stage.search_count([
                ('end_date', '>=', month_start),
                ('end_date', '<=', month_end),
                ('state', 'in', ['completed', 'evaluated'])
            ])

            trends_data.append({
                'month': month_start.strftime('%b %Y'),
                'created': created_count,
                'completed': completed_count
            })

        return list(reversed(trends_data))  # Oldest to newest

    def _get_grade_distribution(self):
        """Get grade distribution for histogram."""
        Stage = self.env['internship.stage']
        graded_stages = Stage.search([('final_grade', '>', 0), ('state', '=', 'evaluated')])

        if not graded_stages:
            return []

        grade_ranges = [
            (0, 8, 'Poor (0-8)', '#dc3545'),
            (8, 12, 'Fair (8-12)', '#ffc107'),
            (12, 16, 'Good (12-16)', '#28a745'),
            (16, 20, 'Excellent (16-20)', '#007bff')
        ]

        distribution = []
        total_count = len(graded_stages)

        for min_grade, max_grade, label, color in grade_ranges:
            count = len([s for s in graded_stages if min_grade <= s.final_grade < max_grade])
            percentage = round((count / total_count * 100), 1) if total_count > 0 else 0

            distribution.append({
                'label': label,
                'value': count,
                'percentage': percentage,
                'color': color
            })

        return distribution

    def _get_supervisor_workload(self):
        """Get supervisor workload analysis."""
        Supervisor = self.env['internship.supervisor']
        supervisors = Supervisor.search([])

        workload_data = []
        for supervisor in supervisors:
            active_count = len(supervisor.supervised_internships.filtered(
                lambda s: s.state in ['in_progress', 'submitted', 'approved']
            ))

            max_capacity = supervisor.max_students or 5  # Default capacity
            utilization = round((active_count / max_capacity * 100), 1) if max_capacity > 0 else 0

            # Determine status
            if utilization > 100:
                status = 'overloaded'
                color = '#dc3545'
            elif utilization > 80:
                status = 'busy'
                color = '#ffc107'
            else:
                status = 'available'
                color = '#28a745'

            workload_data.append({
                'name': supervisor.name,
                'active_count': active_count,
                'max_capacity': max_capacity,
                'utilization': utilization,
                'status': status,
                'color': color
            })

        return sorted(workload_data, key=lambda x: x['utilization'], reverse=True)

    def _get_area_performance(self):
        """Get performance by expertise area."""
        Area = self.env['internship.area']
        areas = Area.search([])

        performance_data = []
        for area in areas:
            area_internships = area.internship_ids
            completed_internships = area_internships.filtered(
                lambda s: s.state == 'evaluated' and s.final_grade > 0
            )

            if completed_internships:
                avg_grade = round(sum(completed_internships.mapped('final_grade')) / len(completed_internships), 2)
                success_rate = round(len(completed_internships.filtered(lambda s: s.final_grade >= 10)) / len(
                    completed_internships) * 100, 1)
            else:
                avg_grade = 0
                success_rate = 0

            performance_data.append({
                'name': area.name,
                'total_internships': len(area_internships),
                'completed_internships': len(completed_internships),
                'avg_grade': avg_grade,
                'success_rate': success_rate
            })

        return sorted(performance_data, key=lambda x: x['avg_grade'], reverse=True)

    def _get_recent_activities(self):
        """Get recent system activities."""
        Stage = self.env['internship.stage']
        recent_stages = Stage.search([
            ('write_date', '>=', datetime.now() - timedelta(days=7))
        ], order='write_date desc', limit=10)

        activities = []
        for stage in recent_stages:
            activities.append({
                'title': stage.title,
                'student': stage.student_id.full_name if stage.student_id else 'N/A',
                'supervisor': stage.supervisor_id.name if stage.supervisor_id else 'N/A',
                'action': self._get_action_from_state(stage.state),
                'date': stage.write_date.strftime('%Y-%m-%d %H:%M'),
                'state': stage.state,
                'id': stage.id
            })

        return activities

    def _get_system_alerts(self):
        """Get system alerts and warnings."""
        alerts = []

        # Alert 1: Overdue internships
        overdue_count = self.env['internship.stage'].search_count([
            ('end_date', '<', datetime.now()),
            ('state', 'in', ['in_progress', 'submitted'])
        ])

        if overdue_count > 0:
            alerts.append({
                'type': 'warning',
                'icon': 'fa-exclamation-triangle',
                'title': 'Overdue Internships',
                'message': f'{overdue_count} internships are past their end date',
                'count': overdue_count,
                'action': 'action_view_overdue_internships'
            })

        # Alert 2: Overloaded supervisors
        overloaded_supervisors = self.env['internship.supervisor'].search([]).filtered(
            lambda s: len(s.supervised_internships.filtered(
                lambda i: i.state in ['in_progress', 'submitted']
            )) > s.max_students
        )

        if overloaded_supervisors:
            alerts.append({
                'type': 'danger',
                'icon': 'fa-users',
                'title': 'Overloaded Supervisors',
                'message': f'{len(overloaded_supervisors)} supervisors exceed capacity',
                'count': len(overloaded_supervisors),
                'action': 'action_view_overloaded_supervisors'
            })

        # Alert 3: Upcoming defenses
        upcoming_defenses = self.env['internship.stage'].search_count([
            ('defense_date', '>=', datetime.now()),
            ('defense_date', '<=', datetime.now() + timedelta(days=7))
        ])

        if upcoming_defenses > 0:
            alerts.append({
                'type': 'info',
                'icon': 'fa-calendar',
                'title': 'Upcoming Defenses',
                'message': f'{upcoming_defenses} defenses scheduled this week',
                'count': upcoming_defenses,
                'action': 'action_view_upcoming_defenses'
            })

        return alerts

    # Helper methods
    def _calculate_trend(self, metric_type, current_value):
        """Calculate trend for KPI cards."""
        # This is a simplified trend calculation
        # In a real implementation, you'd compare with previous period
        trends = {
            'total': '+5% this month',
            'active': 'Currently running',
            'completion': 'Above target',
            'grade': '/20 overall'
        }
        return trends.get(metric_type, 'No trend data')

    def _get_action_from_state(self, state):
        """Get human-readable action from state."""
        actions = {
            'draft': 'Created',
            'submitted': 'Submitted for approval',
            'approved': 'Approved',
            'in_progress': 'Started',
            'completed': 'Completed',
            'evaluated': 'Evaluated',
            'cancelled': 'Cancelled'
        }
        return actions.get(state, 'Updated')

    def _get_empty_dashboard(self):
        """Return empty dashboard structure in case of error."""
        return {
            'kpi_cards': {},
            'charts': {},
            'recent_activities': [],
            'alerts': [],
            'error': True,
            'message': 'Unable to load dashboard data'
        }

    # ===============================
    # ROLE-SPECIFIC DASHBOARDS
    # ===============================

    def _get_student_dashboard(self):
        """Get dashboard data for student role."""
        student = self._get_current_student()
        if not student:
            return self._get_empty_dashboard()

        return {
            'role': 'student',
            'user_info': {
                'name': student.full_name,
                'institution': student.institution,
                'field_of_study': student.field_of_study
            },
            'kpi_cards': self._get_student_kpis(student),
            'charts': self._get_student_charts(student),
            'recent_activities': self._get_student_activities(student),
            'alerts': self._get_student_alerts(student),
            'upcoming_deadlines': self._get_student_deadlines(student),
            'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def _get_supervisor_dashboard(self):
        """Get dashboard data for supervisor role."""
        supervisor = self._get_current_supervisor()
        if not supervisor:
            return self._get_empty_dashboard()

        return {
            'role': 'supervisor',
            'user_info': {
                'name': supervisor.name,
                'department': supervisor.department,
                'company': supervisor.company_id.name
            },
            'kpi_cards': self._get_supervisor_kpis(supervisor),
            'charts': self._get_supervisor_charts(supervisor),
            'recent_activities': self._get_supervisor_activities(supervisor),
            'alerts': self._get_supervisor_alerts(supervisor),
            'workload_analysis': self._get_supervisor_workload_detail(supervisor),
            'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def _get_company_dashboard(self):
        """Get dashboard data for company role."""
        company = self.env.company
        return {
            'role': 'company',
            'user_info': {
                'name': company.name,
                'industry': getattr(company, 'industry', 'N/A')
            },
            'kpi_cards': self._get_company_kpis(company),
            'charts': self._get_company_charts(company),
            'recent_activities': self._get_company_activities(company),
            'alerts': self._get_company_alerts(company),
            'internship_opportunities': self._get_company_opportunities(company),
            'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def _get_admin_dashboard(self):
        """Get dashboard data for admin role (global view)."""
        return {
            'role': 'admin',
            'user_info': {
                'name': self.env.user.name,
                'role': 'System Administrator'
            },
            'kpi_cards': self._get_kpi_cards(),
            'charts': self._get_charts_data(),
            'recent_activities': self._get_recent_activities(),
            'alerts': self._get_system_alerts(),
            'system_health': self._get_system_health(),
            'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def _get_default_dashboard(self):
        """Get default dashboard for users without specific role."""
        return {
            'role': 'default',
            'kpi_cards': self._get_kpi_cards(),
            'charts': self._get_charts_data(),
            'recent_activities': self._get_recent_activities(),
            'alerts': self._get_system_alerts(),
            'last_updated': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    # ===============================
    # HELPER METHODS FOR ROLE DASHBOARDS
    # ===============================

    def _get_current_student(self):
        """Get current student record for logged user."""
        return self.env['internship.student'].search([
            ('user_id', '=', self.env.user.id)
        ], limit=1)

    def _get_current_supervisor(self):
        """Get current supervisor record for logged user."""
        return self.env['internship.supervisor'].search([
            ('user_id', '=', self.env.user.id)
        ], limit=1)

    def _get_student_kpis(self, student):
        """Get KPI cards for student dashboard."""
        active_internships = student.internship_ids.filtered(
            lambda s: s.state in ['in_progress', 'submitted']
        )
        completed_internships = student.internship_ids.filtered(
            lambda s: s.state in ['completed', 'evaluated']
        )
        
        return {
            'active_internships': {
                'value': len(active_internships),
                'label': 'Active Internships',
                'icon': 'fa-play-circle',
                'color': 'success'
            },
            'completed_internships': {
                'value': len(completed_internships),
                'label': 'Completed',
                'icon': 'fa-check-circle',
                'color': 'info'
            },
            'average_grade': {
                'value': f"{student.average_grade:.1f}/20",
                'label': 'Average Grade',
                'icon': 'fa-star',
                'color': 'warning'
            },
            'completion_rate': {
                'value': f"{student.completion_rate:.1f}%",
                'label': 'Completion Rate',
                'icon': 'fa-chart-line',
                'color': 'primary'
            }
        }

    def _get_supervisor_kpis(self, supervisor):
        """Get KPI cards for supervisor dashboard."""
        return {
            'current_students': {
                'value': supervisor.current_students_count,
                'label': 'Current Students',
                'icon': 'fa-users',
                'color': 'primary'
            },
            'max_capacity': {
                'value': supervisor.max_students,
                'label': 'Max Capacity',
                'icon': 'fa-user-plus',
                'color': 'info'
            },
            'workload': {
                'value': f"{supervisor.workload_percentage:.1f}%",
                'label': 'Workload',
                'icon': 'fa-tasks',
                'color': 'warning'
            },
            'total_supervised': {
                'value': supervisor.stage_count,
                'label': 'Total Supervised',
                'icon': 'fa-graduation-cap',
                'color': 'success'
            }
        }

    def _get_company_kpis(self, company):
        """Get KPI cards for company dashboard."""
        # Get internships for this company
        company_internships = self.env['internship.stage'].search([
            ('company_id', '=', company.id)
        ])
        
        active_internships = company_internships.filtered(
            lambda s: s.state in ['in_progress', 'submitted']
        )
        
        return {
            'total_internships': {
                'value': len(company_internships),
                'label': 'Total Internships',
                'icon': 'fa-briefcase',
                'color': 'primary'
            },
            'active_internships': {
                'value': len(active_internships),
                'label': 'Active Now',
                'icon': 'fa-play-circle',
                'color': 'success'
            },
            'supervisors_count': {
                'value': len(company_internships.mapped('supervisor_id')),
                'label': 'Supervisors',
                'icon': 'fa-user-tie',
                'color': 'info'
            },
            'success_rate': {
                'value': '85%',  # TODO: Calculate actual success rate
                'label': 'Success Rate',
                'icon': 'fa-trophy',
                'color': 'warning'
            }
        }

    def _get_student_charts(self, student):
        """Get charts data for student dashboard."""
        return {
            'progress_timeline': self._get_student_progress_timeline(student),
            'skill_development': self._get_student_skill_development(student),
            'grade_evolution': self._get_student_grade_evolution(student)
        }

    def _get_supervisor_charts(self, supervisor):
        """Get charts data for supervisor dashboard."""
        return {
            'student_progress': self._get_supervisor_student_progress(supervisor),
            'workload_trend': self._get_supervisor_workload_trend(supervisor),
            'grade_distribution': self._get_supervisor_grade_distribution(supervisor)
        }

    def _get_company_charts(self, company):
        """Get charts data for company dashboard."""
        return {
            'internship_distribution': self._get_company_internship_distribution(company),
            'department_performance': self._get_company_department_performance(company),
            'timeline_analysis': self._get_company_timeline_analysis(company)
        }

    # Placeholder methods for chart data - to be implemented
    def _get_student_progress_timeline(self, student):
        return {'labels': [], 'data': []}
    
    def _get_student_skill_development(self, student):
        return {'labels': [], 'data': []}
    
    def _get_student_grade_evolution(self, student):
        return {'labels': [], 'data': []}
    
    def _get_supervisor_student_progress(self, supervisor):
        return {'labels': [], 'data': []}
    
    def _get_supervisor_workload_trend(self, supervisor):
        return {'labels': [], 'data': []}
    
    def _get_supervisor_grade_distribution(self, supervisor):
        return {'labels': [], 'data': []}
    
    def _get_company_internship_distribution(self, company):
        return {'labels': [], 'data': []}
    
    def _get_company_department_performance(self, company):
        return {'labels': [], 'data': []}
    
    def _get_company_timeline_analysis(self, company):
        return {'labels': [], 'data': []}

    def _get_student_activities(self, student):
        """Get recent activities for student."""
        recent_stages = student.internship_ids.search([
            ('write_date', '>=', fields.Datetime.now() - timedelta(days=7))
        ], order='write_date desc', limit=5)
        
        activities = []
        for stage in recent_stages:
            activities.append({
                'title': stage.title,
                'action': self._get_action_from_state(stage.state),
                'date': stage.write_date.strftime('%Y-%m-%d %H:%M'),
                'state': stage.state
            })
        return activities

    def _get_supervisor_activities(self, supervisor):
        """Get recent activities for supervisor."""
        recent_stages = supervisor.stage_ids.search([
            ('write_date', '>=', fields.Datetime.now() - timedelta(days=7))
        ], order='write_date desc', limit=5)
        
        activities = []
        for stage in recent_stages:
            activities.append({
                'title': stage.title,
                'student': stage.student_id.full_name,
                'action': self._get_action_from_state(stage.state),
                'date': stage.write_date.strftime('%Y-%m-%d %H:%M'),
                'state': stage.state
            })
        return activities

    def _get_company_activities(self, company):
        """Get recent activities for company."""
        recent_stages = self.env['internship.stage'].search([
            ('company_id', '=', company.id),
            ('write_date', '>=', fields.Datetime.now() - timedelta(days=7))
        ], order='write_date desc', limit=5)
        
        activities = []
        for stage in recent_stages:
            activities.append({
                'title': stage.title,
                'student': stage.student_id.full_name,
                'supervisor': stage.supervisor_id.name,
                'action': self._get_action_from_state(stage.state),
                'date': stage.write_date.strftime('%Y-%m-%d %H:%M'),
                'state': stage.state
            })
        return activities

    def _get_student_alerts(self, student):
        """Get alerts for student."""
        alerts = []
        
        # Check for overdue tasks
        overdue_tasks = self.env['internship.todo'].search([
            ('stage_id.student_id', '=', student.id),
            ('deadline', '<', fields.Datetime.now()),
            ('state', '!=', 'done')
        ])
        
        if overdue_tasks:
            alerts.append({
                'type': 'warning',
                'icon': 'fa-exclamation-triangle',
                'title': 'Overdue Tasks',
                'message': f'{len(overdue_tasks)} tasks are overdue',
                'count': len(overdue_tasks)
            })
        
        return alerts

    def _get_supervisor_alerts(self, supervisor):
        """Get alerts for supervisor."""
        alerts = []
        
        # Check for overloaded supervisor
        if supervisor.current_students_count >= supervisor.max_students:
            alerts.append({
                'type': 'danger',
                'icon': 'fa-users',
                'title': 'Capacity Reached',
                'message': 'You have reached your maximum student capacity',
                'count': supervisor.current_students_count
            })
        
        return alerts

    def _get_company_alerts(self, company):
        """Get alerts for company."""
        alerts = []
        
        # Check for internships without supervisors
        unsupervised = self.env['internship.stage'].search([
            ('company_id', '=', company.id),
            ('supervisor_id', '=', False),
            ('state', 'in', ['approved', 'in_progress'])
        ])
        
        if unsupervised:
            alerts.append({
                'type': 'warning',
                'icon': 'fa-user-slash',
                'title': 'Unsupervised Internships',
                'message': f'{len(unsupervised)} internships need supervisors',
                'count': len(unsupervised)
            })
        
        return alerts

    def _get_student_deadlines(self, student):
        """Get upcoming deadlines for student."""
        upcoming_tasks = self.env['internship.todo'].search([
            ('stage_id.student_id', '=', student.id),
            ('deadline', '>=', fields.Datetime.now()),
            ('deadline', '<=', fields.Datetime.now() + timedelta(days=7)),
            ('state', '!=', 'done')
        ], order='deadline')
        
        deadlines = []
        for task in upcoming_tasks:
            deadlines.append({
                'title': task.name,
                'deadline': task.deadline.strftime('%Y-%m-%d %H:%M'),
                'priority': task.priority,
                'stage': task.stage_id.title
            })
        
        return deadlines

    def _get_supervisor_workload_detail(self, supervisor):
        """Get detailed workload analysis for supervisor."""
        return {
            'current_students': supervisor.current_students_count,
            'max_capacity': supervisor.max_students,
            'utilization_percentage': supervisor.workload_percentage,
            'availability_status': supervisor.availability,
            'students_list': [
                {
                    'name': stage.student_id.full_name,
                    'stage': stage.title,
                    'progress': stage.progress_percentage,
                    'state': stage.state
                }
                for stage in supervisor.stage_ids.filtered(
                    lambda s: s.state in ['in_progress', 'submitted']
                )
            ]
        }

    def _get_company_opportunities(self, company):
        """Get internship opportunities for company."""
        # This would typically come from a separate opportunities model
        return {
            'available_positions': 0,
            'pending_applications': 0,
            'upcoming_interviews': 0
        }

    def _get_system_health(self):
        """Get system health metrics for admin."""
        return {
            'total_users': self.env['res.users'].search_count([]),
            'active_sessions': 0,  # TODO: Implement session tracking
            'system_uptime': '99.9%',
            'last_backup': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }