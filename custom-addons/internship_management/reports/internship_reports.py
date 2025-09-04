# -*- coding: utf-8 -*-

from odoo import api, models
from datetime import datetime


class InternshipStageReport(models.AbstractModel):
    _name = 'report.internship_management.defense_report'
    _description = 'Rapport de soutenance'

    @api.model
    def _get_report_values(self, docids):
        """Retourne les valeurs pour le rapport"""
        docs = self.env['internship.stage'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'data': self._get_defense_data(docs),
        }

    def _get_defense_data(self, stages):
        """Prépare les données pour le rapport"""
        data = {}
        for stage in stages:
            data[stage.id] = {
                'stage_name': stage.name,
                'student_name': stage.student_id.name if stage.student_id else '',
                'supervisor_name': stage.supervisor_id.name if stage.supervisor_id else '',
                'defense_date': stage.defense_date.strftime('%d/%m/%Y à %H:%M') if stage.defense_date else '',
                'defense_room': stage.defense_room or '',
                'defense_duration': stage.defense_duration or 1.5,
                'jury_members': [member.name for member in stage.jury_ids],
                'defense_grade': stage.defense_grade or 0,
                'defense_report': stage.defense_report or '',
                'defense_notes': stage.defense_notes or '',
                'attendance': [user.name for user in stage.defense_attendance],
                'company_name': stage.company_id.name if stage.company_id else '',
            }
        return data


class InternshipConventionReport(models.AbstractModel):
    _name = 'report.internship_management.convention_report'
    _description = 'Convention de stage'

    @api.model
    def _get_report_values(self, docids):
        """Retourne les valeurs pour la convention de stage"""
        docs = self.env['internship.stage'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'data': self._get_convention_data(docs),
        }

    def _get_convention_data(self, stages):
        """Prépare les données pour la convention"""
        data = {}
        for stage in stages:
            data[stage.id] = {
                'stage_name': stage.name,
                'student_name': stage.student_id.name if stage.student_id else '',
                'student_email': stage.student_id.email if stage.student_id else '',
                'student_phone': stage.student_id.phone if stage.student_id else '',
                'student_address': stage.student_id.address if stage.student_id else '',
                'supervisor_name': stage.supervisor_id.name if stage.supervisor_id else '',
                'supervisor_email': stage.supervisor_id.email if stage.supervisor_id else '',
                'company_name': stage.company_id.name if stage.company_id else '',
                'company_address': stage.company_id.address if stage.company_id else '',
                'company_phone': stage.company_id.phone if stage.company_id else '',
                'company_email': stage.company_id.email if stage.company_id else '',
                'start_date': stage.start_date.strftime('%d/%m/%Y') if stage.start_date else '',
                'end_date': stage.end_date.strftime('%d/%m/%Y') if stage.end_date else '',
                'stage_type': stage.stage_type,
                'description': stage.description or '',
                'objectives': stage.objectives or '',
                'current_date': datetime.now().strftime('%d/%m/%Y'),
            }
        return data


class InternshipAttestationReport(models.AbstractModel):
    _name = 'report.internship_management.attestation_report'
    _description = 'Attestation de stage'

    @api.model
    def _get_report_values(self, docids):
        """Retourne les valeurs pour l'attestation de stage"""
        docs = self.env['internship.stage'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'data': self._get_attestation_data(docs),
        }

    def _get_attestation_data(self, stages):
        """Prépare les données pour l'attestation"""
        data = {}
        for stage in stages:
            # Calculer la durée du stage
            duration_days = 0
            if stage.start_date and stage.end_date:
                duration_days = (stage.end_date - stage.start_date).days
            
            data[stage.id] = {
                'stage_name': stage.name,
                'student_name': stage.student_id.name if stage.student_id else '',
                'student_id': stage.student_id.student_id if stage.student_id else '',
                'company_name': stage.company_id.name if stage.company_id else '',
                'start_date': stage.start_date.strftime('%d/%m/%Y') if stage.start_date else '',
                'end_date': stage.end_date.strftime('%d/%m/%Y') if stage.end_date else '',
                'duration_days': duration_days,
                'grade': stage.grade or 0,
                'defense_grade': stage.defense_grade or 0,
                'final_grade': (stage.grade + stage.defense_grade) / 2 if stage.grade and stage.defense_grade else 0,
                'supervisor_name': stage.supervisor_id.name if stage.supervisor_id else '',
                'current_date': datetime.now().strftime('%d/%m/%Y'),
                'stage_type': stage.stage_type,
            }
        return data


class InternshipEvaluationReport(models.AbstractModel):
    _name = 'report.internship_management.evaluation_report'
    _description = 'Rapport d\'évaluation de stage'

    @api.model
    def _get_report_values(self, docids):
        """Retourne les valeurs pour le rapport d'évaluation"""
        docs = self.env['internship.stage'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'data': self._get_evaluation_data(docs),
        }

    def _get_evaluation_data(self, stages):
        """Prépare les données pour l'évaluation"""
        data = {}
        for stage in stages:
            data[stage.id] = {
                'stage_name': stage.name,
                'student_name': stage.student_id.name if stage.student_id else '',
                'company_name': stage.company_id.name if stage.company_id else '',
                'supervisor_name': stage.supervisor_id.name if stage.supervisor_id else '',
                'start_date': stage.start_date.strftime('%d/%m/%Y') if stage.start_date else '',
                'end_date': stage.end_date.strftime('%d/%m/%Y') if stage.end_date else '',
                'progress': stage.progress or 0,
                'grade': stage.grade or 0,
                'defense_grade': stage.defense_grade or 0,
                'final_grade': (stage.grade + stage.defense_grade) / 2 if stage.grade and stage.defense_grade else 0,
                'evaluation_notes': stage.evaluation_notes or '',
                'current_date': datetime.now().strftime('%d/%m/%Y'),
                'stage_type': stage.stage_type,
                'description': stage.description or '',
                'objectives': stage.objectives or '',
            }
        return data
