# -*- coding: utf-8 -*-
"""
Professional Internship Reports
===============================
Enhanced reporting system for internship management with comprehensive
data preparation and professional formatting.
"""

import logging
from odoo import api, models, fields, _
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class InternshipDefenseReport(models.AbstractModel):
    """Defense Proceedings Report"""
    _name = 'report.internship_management.defense_report_document'
    _description = 'Internship Defense Proceedings'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepare defense report data"""
        docs = self.env['internship.stage'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'data': self._prepare_defense_data(docs),
            'company': self.env.company,
        }

    def _prepare_defense_data(self, stages):
        """Prepare defense data for each stage"""
        data = {}
        for stage in stages:
            data[stage.id] = {
                'internship_title': stage.title or stage.name,
                'student_name': stage.student_id.full_name if stage.student_id else 'N/A',
                'student_id': stage.student_id.student_id_number if stage.student_id else 'N/A',
                'supervisor_name': stage.supervisor_id.name if stage.supervisor_id else 'N/A',
                'supervisor_position': stage.supervisor_id.position if stage.supervisor_id else 'Supervisor',
                'company_name': stage.company_id.name or 'TechPal',
                'defense_date': stage.defense_date.strftime(
                    '%B %d, %Y at %H:%M') if stage.defense_date else 'To Be Determined',
                'defense_grade': stage.defense_grade or 0,
                'final_grade': stage.final_grade or 0,
                'duration': self._calculate_duration(stage.start_date, stage.end_date),
                'current_date': datetime.now().strftime('%B %d, %Y'),
                'reference': stage.reference_number or f'INT-{stage.id}',
            }
        return data

    def _calculate_duration(self, start_date, end_date):
        """Calculate internship duration"""
        if start_date and end_date:
            delta = end_date - start_date
            months = delta.days // 30
            return f"{months} month{'s' if months != 1 else ''}"
        return "N/A"


class InternshipConventionReport(models.AbstractModel):
    """Internship Agreement Report"""
    _name = 'report.internship_management.convention_report_document'
    _description = 'Internship Agreement'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepare convention report data"""
        docs = self.env['internship.stage'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'data': self._prepare_convention_data(docs),
            'company': self.env.company,
        }

    def _prepare_convention_data(self, stages):
        """Prepare convention data for each stage"""
        data = {}
        for stage in stages:
            data[stage.id] = {
                'internship_title': stage.title or stage.name,
                'student_name': stage.student_id.full_name if stage.student_id else '',
                'student_email': stage.student_id.email if stage.student_id else '',
                'student_phone': stage.student_id.phone if stage.student_id else '',
                'student_id_number': stage.student_id.student_id_number if stage.student_id else '',
                'institution': stage.student_id.institution if stage.student_id else '',
                'supervisor_name': stage.supervisor_id.name if stage.supervisor_id else '',
                'supervisor_position': stage.supervisor_id.position if stage.supervisor_id else '',
                'supervisor_email': stage.supervisor_id.email if stage.supervisor_id else '',
                'company_name': stage.company_id.name or 'TechPal',
                'start_date': stage.start_date.strftime('%B %d, %Y') if stage.start_date else '',
                'end_date': stage.end_date.strftime('%B %d, %Y') if stage.end_date else '',
                'duration_weeks': self._calculate_weeks(stage.start_date, stage.end_date),
                'current_date': datetime.now().strftime('%B %d, %Y'),
                'reference': stage.reference_number or f'INT-{stage.id}',
                'objectives': stage.project_description or 'Professional development through practical experience',
            }
        return data

    def _calculate_weeks(self, start_date, end_date):
        """Calculate duration in weeks"""
        if start_date and end_date:
            delta = end_date - start_date
            weeks = delta.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''}"
        return "N/A"


class InternshipAttestationReport(models.AbstractModel):
    """Internship Certificate Report"""
    _name = 'report.internship_management.attestation_report_document'
    _description = 'Internship Certificate'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepare attestation report data"""
        docs = self.env['internship.stage'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'data': self._prepare_attestation_data(docs),
            'company': self.env.company,
        }

    def _prepare_attestation_data(self, stages):
        """Prepare attestation data for each stage"""
        data = {}
        for stage in stages:
            data[stage.id] = {
                'student_name': stage.student_id.full_name if stage.student_id else '',
                'student_id_number': stage.student_id.student_id_number if stage.student_id else '',
                'institution': stage.student_id.institution if stage.student_id else '',
                'internship_title': stage.title or stage.name,
                'company_name': stage.company_id.name or 'TechPal',
                'supervisor_name': stage.supervisor_id.name if stage.supervisor_id else '',
                'start_date': stage.start_date.strftime('%B %d, %Y') if stage.start_date else '',
                'end_date': stage.end_date.strftime('%B %d, %Y') if stage.end_date else '',
                'duration_days': (stage.end_date - stage.start_date).days if stage.start_date and stage.end_date else 0,
                'final_grade': stage.final_grade or 0,
                'current_date': datetime.now().strftime('%B %d, %Y'),
                'reference': stage.reference_number or f'INT-{stage.id}',
                'performance': self._get_performance_level(stage.final_grade),
            }
        return data

    def _get_performance_level(self, grade):
        """Get performance level based on grade"""
        if not grade:
            return "Satisfactory"
        elif grade >= 16:
            return "Excellent"
        elif grade >= 14:
            return "Very Good"
        elif grade >= 12:
            return "Good"
        elif grade >= 10:
            return "Satisfactory"
        else:
            return "Needs Improvement"


class InternshipEvaluationReport(models.AbstractModel):
    """Evaluation Report"""
    _name = 'report.internship_management.evaluation_report_document'
    _description = 'Internship Evaluation Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepare evaluation report data"""
        docs = self.env['internship.stage'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'data': self._prepare_evaluation_data(docs),
            'company': self.env.company,
        }

    def _prepare_evaluation_data(self, stages):
        """Prepare evaluation data for each stage"""
        data = {}
        for stage in stages:
            data[stage.id] = {
                'student_name': stage.student_id.full_name if stage.student_id else '',
                'internship_title': stage.title or stage.name,
                'supervisor_name': stage.supervisor_id.name if stage.supervisor_id else '',
                'company_name': stage.company_id.name or 'TechPal',
                'start_date': stage.start_date.strftime('%B %d, %Y') if stage.start_date else '',
                'end_date': stage.end_date.strftime('%B %d, %Y') if stage.end_date else '',
                'final_grade': stage.final_grade or 0,
                'defense_grade': stage.defense_grade or 0,
                'feedback': stage.evaluation_feedback or 'Satisfactory performance throughout the internship period.',
                'current_date': datetime.now().strftime('%B %d, %Y'),
                'reference': stage.reference_number or f'INT-{stage.id}',
                'completion_rate': stage.completion_percentage or 100,
            }
        return data