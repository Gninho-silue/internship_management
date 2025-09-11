# -*- coding: utf-8 -*-
"""
Internship Dashboard Analytics
==============================
Dashboard with real-time KPIs and analytics
for internship management system.
"""

import logging
from datetime import timedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class InternshipDashboard(models.TransientModel):
    """
    Dashboard Analytics Model

    Provides real-time analytics and KPIs for internship management.
    This is a transient model used only for dashboard calculations.
    """
    _name = 'internship.dashboard'
    _description = 'Internship Analytics Dashboard'

    # ===============================
    # DASHBOARD FILTERS
    # ===============================

    date_from = fields.Date(
        string='From Date',
        default=lambda self: fields.Date.today() - timedelta(days=365),
        help="Start date for analytics period"
    )

    date_to = fields.Date(
        string='To Date',
        default=fields.Date.today,
        help="End date for analytics period"
    )

    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Filter by Supervisor',
        help="Optional: Filter data by specific supervisor"
    )

    area_id = fields.Many2one(
        'internship.area',
        string='Filter by Area',
        help="Optional: Filter data by expertise area"
    )

    # ===============================
    # MAIN DASHBOARD METHODS
    # ===============================

    @api.model
    def get_dashboard_data(self):
        """
        Main method to get all dashboard data
        Returns comprehensive analytics for the dashboard
        """
        _logger.info("Generating dashboard analytics...")

        data = {
            'kpis': self._get_main_kpis(),
            'charts': self._get_chart_data(),
            'recent_activities': self._get_recent_activities(),
            'alerts': self._get_alerts_data(),
            'supervisor_stats': self._get_supervisor_statistics(),
            'area_distribution': self._get_area_distribution(),
        }

        _logger.info(f"Dashboard data generated with {len(data)} sections")
        return data

    def _get_main_kpis(self):
        """Calculate main KPI metrics"""
        domain = self._get_base_domain()

        # Get all stages for calculations
        stages = self.env['internship.stage'].search(domain)
        students = self.env['internship.student'].search([])
        supervisors = self.env['internship.supervisor'].search([])

        # Calculate KPIs
        total_internships = len(stages)
        active_internships = len(stages.filtered(lambda s: s.state == 'in_progress'))
        completed_internships = len(stages.filtered(lambda s: s.state == 'completed'))

        # Success rate calculation
        evaluated_stages = stages.filtered(lambda s: s.state in ['completed', 'evaluated'])
        if evaluated_stages:
            avg_grade = sum(evaluated_stages.mapped('final_grade')) / len(evaluated_stages)
            success_rate = len(evaluated_stages.filtered(lambda s: s.final_grade >= 10)) / len(evaluated_stages) * 100
        else:
            avg_grade = 0
            success_rate = 0

        return {
            'total_internships': total_internships,
            'active_internships': active_internships,
            'completed_internships': completed_internships,
            'total_students': len(students),
            'total_supervisors': len(supervisors),
            'success_rate': round(success_rate, 1),
            'average_grade': round(avg_grade, 2),
            'completion_rate': round((completed_internships / total_internships * 100) if total_internships > 0 else 0,
                                     1)
        }

    def _get_chart_data(self):
        """Get data for dashboard charts"""
        domain = self._get_base_domain()
        stages = self.env['internship.stage'].search(domain)

        return {
            'internship_by_status': self._get_status_distribution(stages),
            'internship_by_type': self._get_type_distribution(stages),
            'progress_timeline': self._get_progress_timeline(stages),
            'grade_distribution': self._get_grade_distribution(stages)
        }

    def _get_status_distribution(self, stages):
        """Get internship distribution by status"""
        status_data = {}
        status_labels = dict(stages._fields['state'].selection)

        for status_key, status_label in status_labels.items():
            count = len(stages.filtered(lambda s: s.state == status_key))
            if count > 0:
                status_data[status_label] = count

        return {
            'labels': list(status_data.keys()),
            'data': list(status_data.values()),
            'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
        }

    def _get_type_distribution(self, stages):
        """Get internship distribution by type"""
        type_data = {}
        type_labels = dict(stages._fields['internship_type'].selection)

        for type_key, type_label in type_labels.items():
            count = len(stages.filtered(lambda s: s.internship_type == type_key))
            if count > 0:
                type_data[type_label] = count

        return {
            'labels': list(type_data.keys()),
            'data': list(type_data.values()),
            'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
        }

    def _get_progress_timeline(self, stages):
        """Get timeline data for progress tracking"""
        # Get last 6 months of data
        timeline_data = []
        current_date = fields.Date.today()

        for i in range(6):
            month_start = current_date.replace(day=1) - timedelta(days=30 * i)
            month_end = month_start + timedelta(days=30)

            month_stages = stages.filtered(
                lambda s: s.start_date and month_start <= s.start_date <= month_end
            )

            timeline_data.append({
                'month': month_start.strftime('%b %Y'),
                'started': len(month_stages),
                'completed': len(month_stages.filtered(lambda s: s.state == 'completed'))
            })

        timeline_data.reverse()  # Order from oldest to newest

        return {
            'labels': [item['month'] for item in timeline_data],
            'datasets': [
                {
                    'label': 'Started',
                    'data': [item['started'] for item in timeline_data],
                    'borderColor': '#36A2EB',
                    'backgroundColor': 'rgba(54, 162, 235, 0.1)'
                },
                {
                    'label': 'Completed',
                    'data': [item['completed'] for item in timeline_data],
                    'borderColor': '#4BC0C0',
                    'backgroundColor': 'rgba(75, 192, 192, 0.1)'
                }
            ]
        }

    def _get_grade_distribution(self, stages):
        """Get grade distribution for completed internships"""
        completed_stages = stages.filtered(lambda s: s.final_grade > 0)

        if not completed_stages:
            return {'labels': [], 'data': []}

        # Grade ranges
        ranges = {
            'Excellent (16-20)': len(completed_stages.filtered(lambda s: s.final_grade >= 16)),
            'Good (14-16)': len(completed_stages.filtered(lambda s: 14 <= s.final_grade < 16)),
            'Average (12-14)': len(completed_stages.filtered(lambda s: 12 <= s.final_grade < 14)),
            'Below Average (10-12)': len(completed_stages.filtered(lambda s: 10 <= s.final_grade < 12)),
            'Fail (<10)': len(completed_stages.filtered(lambda s: s.final_grade < 10))
        }

        # Filter out empty ranges
        filtered_ranges = {k: v for k, v in ranges.items() if v > 0}

        return {
            'labels': list(filtered_ranges.keys()),
            'data': list(filtered_ranges.values()),
            'colors': ['#4BC0C0', '#36A2EB', '#FFCE56', '#FF9F40', '#FF6384']
        }

    def _get_recent_activities(self):
        """Get recent activities for dashboard"""
        recent_stages = self.env['internship.stage'].search([
            ('write_date', '>=', fields.Datetime.now() - timedelta(days=7))
        ], order='write_date desc', limit=10)

        activities = []
        for stage in recent_stages:
            activities.append({
                'id': stage.id,
                'title': stage.title,
                'student_name': stage.student_id.full_name if stage.student_id else 'Unknown',
                'status': stage.state,
                'date': stage.write_date.strftime('%Y-%m-%d %H:%M') if stage.write_date else '',
                'progress': stage.progress_percentage
            })

        return activities

    def _get_alerts_data(self):
        """Get alerts and warnings for dashboard"""
        alerts = []

        # Overdue internships
        overdue_stages = self.env['internship.stage'].search([
            ('end_date', '<', fields.Date.today()),
            ('state', 'in', ['in_progress', 'approved'])
        ])

        if overdue_stages:
            alerts.append({
                'type': 'warning',
                'title': f'{len(overdue_stages)} Overdue Internships',
                'message': 'Some internships have passed their end date',
                'count': len(overdue_stages)
            })

        # Low progress stages
        low_progress = self.env['internship.stage'].search([
            ('state', '=', 'in_progress'),
            ('progress_percentage', '<', 30)
        ])

        if low_progress:
            alerts.append({
                'type': 'info',
                'title': f'{len(low_progress)} Low Progress',
                'message': 'Internships with less than 30% progress',
                'count': len(low_progress)
            })

        # Supervisor overload
        overloaded_supervisors = self.env['internship.supervisor'].search([]).filtered(
            lambda s: s.current_students_count >= s.max_students
        )

        if overloaded_supervisors:
            alerts.append({
                'type': 'warning',
                'title': f'{len(overloaded_supervisors)} Overloaded Supervisors',
                'message': 'Supervisors at maximum capacity',
                'count': len(overloaded_supervisors)
            })

        return alerts

    def _get_supervisor_statistics(self):
        """Get supervisor performance statistics"""
        supervisors = self.env['internship.supervisor'].search([])
        supervisor_stats = []

        for supervisor in supervisors:
            completed_stages = supervisor.stage_ids.filtered(lambda s: s.state == 'completed')
            avg_grade = sum(completed_stages.mapped('final_grade')) / len(completed_stages) if completed_stages else 0

            supervisor_stats.append({
                'id': supervisor.id,
                'name': supervisor.name,
                'department': supervisor.department,
                'current_students': supervisor.current_students_count,
                'max_students': supervisor.max_students,
                'total_supervised': len(supervisor.stage_ids),
                'completed': len(completed_stages),
                'average_grade': round(avg_grade, 2),
                'utilization': round((
                                                 supervisor.current_students_count / supervisor.max_students * 100) if supervisor.max_students > 0 else 0,
                                     1)
            })

        return sorted(supervisor_stats, key=lambda x: x['utilization'], reverse=True)

    def _get_area_distribution(self):
        """Get distribution by expertise areas"""
        areas = self.env['internship.area'].search([])
        area_data = []

        for area in areas:
            internship_count = len(area.internship_ids)
            if internship_count > 0:
                area_data.append({
                    'name': area.name,
                    'count': internship_count,
                    'percentage': round((internship_count / len(self.env['internship.stage'].search([])) * 100), 1)
                })

        return sorted(area_data, key=lambda x: x['count'], reverse=True)

    def _get_base_domain(self):
        """Get base domain for filtering"""
        domain = []

        if hasattr(self, 'date_from') and self.date_from:
            domain.append(('start_date', '>=', self.date_from))

        if hasattr(self, 'date_to') and self.date_to:
            domain.append(('start_date', '<=', self.date_to))

        if hasattr(self, 'supervisor_id') and self.supervisor_id:
            domain.append(('supervisor_id', '=', self.supervisor_id.id))

        if hasattr(self, 'area_id') and self.area_id:
            domain.append(('area_id', '=', self.area_id.id))

        return domain

    # ===============================
    # ACTION METHODS
    # ===============================

    def action_view_internships(self):
        """Action to view filtered internships"""
        domain = self._get_base_domain()

        return {
            'name': 'Filtered Internships',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.stage',
            'view_mode': 'tree,form,kanban',
            'domain': domain,
            'target': 'current',
        }

    def action_refresh_dashboard(self):
        """Refresh dashboard data"""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }