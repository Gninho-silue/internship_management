# -*- coding: utf-8 -*-

from odoo import api, models


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
