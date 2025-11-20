# -*- coding: utf-8 -*-
"""
Rapports de Stage
================================
Système de reporting  pour la gestion des stages, avec une préparation
complète des données et une mise en forme.
"""

import logging
from datetime import datetime

from odoo import api, models, _

_logger = logging.getLogger(__name__)


class InternshipDefenseReport(models.AbstractModel):
    """
    Modèle abstrait pour le rapport de Procès-Verbal de Soutenance.

    Ce modèle prépare les données nécessaires à la génération du PDF du
    procès-verbal de la soutenance d'un stage.
    """
    _name = 'report.internship_management.defense_report_document'
    _description = 'Procès-Verbal de Soutenance de Stage'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Prépare les valeurs pour le rapport de soutenance.
        Cette méthode est l'entrée standard pour le moteur de reporting d'Odoo.
        """
        docs = self.env['internship.stage'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'company': self.env.company,
        }


class InternshipConventionReport(models.AbstractModel):
    """
    Modèle abstrait pour le rapport de Convention de Stage.

    Ce modèle collecte toutes les informations requises pour générer
    le document officiel de la convention de stage entre l'étudiant,
    l'entreprise et l'établissement.
    """
    _name = 'report.internship_management.convention_report_document'
    _description = 'Convention de Stage'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prépare les valeurs pour le rapport de convention."""
        docs = self.env['internship.stage'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'company': self.env.company,
        }


class InternshipAttestationReport(models.AbstractModel):
    """
    Modèle abstrait pour le rapport d'Attestation de Stage.

    Ce modèle est responsable de la préparation des données pour générer
    l'attestation de fin de stage, certifiant la participation et la
    performance de l'étudiant.
    """
    _name = 'report.internship_management.attestation_report_document'
    _description = 'Attestation de Stage'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prépare les valeurs pour le rapport d'attestation."""
        docs = self.env['internship.stage'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'data': self._prepare_attestation_data(docs),
            'company': self.env.company,
        }

    def _prepare_attestation_data(self, stages):
        """
        Prépare les données spécifiques à l'attestation, comme le niveau de performance.
        """
        data = {}
        for stage in stages:
            data[stage.id] = {
                'performance': self._get_performance_level(stage.final_grade),
            }
        return data

    def _get_performance_level(self, grade):
        """
        Retourne une appréciation textuelle basée sur la note finale.
        Les chaînes de caractères sont traduisibles.
        """
        if not grade or grade < 10:
            return _("Passable")
        elif grade >= 16:
            return _("Excellent")
        elif grade >= 14:
            return _("Très Bien")
        elif grade >= 12:
            return _("Bien")
        return _("Assez Bien")


class InternshipEvaluationReport(models.AbstractModel):
    """
    Modèle abstrait pour le rapport d'Évaluation de Stage.

    Ce modèle prépare les données pour le rapport d'évaluation détaillé,
    incluant les notes et les commentaires de l'encadrant.
    """
    _name = 'report.internship_management.evaluation_report_document'
    _description = 'Rapport d\'Évaluation de Stage'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prépare les valeurs pour le rapport d'évaluation."""
        docs = self.env['internship.stage'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'company': self.env.company,
        }


class InternshipStageReport(models.AbstractModel):
    """
    Modèle abstrait pour le rapport de Synthèse de Stage.

    Ce modèle fournit un aperçu complet et consolidé de l'état d'un stage.
    """
    _name = 'report.internship_management.stage_report_document'
    _description = 'Rapport de Synthèse de Stage'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prépare les valeurs pour le rapport de synthèse."""
        docs = self.env['internship.stage'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'internship.stage',
            'docs': docs,
            'company': self.env.company,
            'current_date': datetime.now().date(),
        }


# ===================================================
# RAPPORTS INDIVIDUELS PAR ÉTUDIANT
# ===================================================

class InternshipAttestationReportStudent(models.AbstractModel):
    """
    Modèle abstrait pour le rapport d'Attestation de Stage individuel par étudiant.
    """
    _name = 'report.internship_management.attestation_student'
    _description = 'Attestation de Stage (Individuelle)'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prépare les valeurs pour le rapport d'attestation individuel."""
        students = self.env['internship.student'].browse(docids)
        # Créer un mapping student_id -> stage
        stage_map = {}
        for student in students:
            # Si un stage_id est passé dans le contexte, l'utiliser
            if data and data.get('stage_id'):
                stage = self.env['internship.stage'].browse(data['stage_id'])
                if student in stage.student_ids:
                    stage_map[student.id] = stage
            elif student.internship_ids:
                # Sinon, utiliser le premier stage actif
                active_stage = student.internship_ids.filtered(lambda s: s.state in ['completed', 'evaluated'])
                stage_map[student.id] = active_stage[0] if active_stage else student.internship_ids[0]
        
        return {
            'doc_ids': docids,
            'doc_model': 'internship.student',
            'docs': students,
            'stage_map': stage_map,
            'data': self._prepare_attestation_data_student(students, stage_map),
            'company': self.env.company,
        }

    def _prepare_attestation_data_student(self, students, stage_map):
        """Prépare les données spécifiques à l'attestation individuelle."""
        data = {}
        for student in students:
            stage = stage_map.get(student.id)
            if stage:
                data[student.id] = {
                    'performance': self._get_performance_level(stage.final_grade),
                    'stage': stage,
                }
        return data

    def _get_performance_level(self, grade):
        """Retourne une appréciation textuelle basée sur la note finale."""
        if not grade or grade < 10:
            return _("Passable")
        elif grade >= 16:
            return _("Excellent")
        elif grade >= 14:
            return _("Très Bien")
        elif grade >= 12:
            return _("Bien")
        return _("Assez Bien")


class InternshipConventionReportStudent(models.AbstractModel):
    """
    Modèle abstrait pour le rapport de Convention de Stage individuel par étudiant.
    """
    _name = 'report.internship_management.convention_student'
    _description = 'Convention de Stage (Individuelle)'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prépare les valeurs pour le rapport de convention individuel."""
        students = self.env['internship.student'].browse(docids)
        stage_map = {}
        for student in students:
            if data and data.get('stage_id'):
                stage = self.env['internship.stage'].browse(data['stage_id'])
                if student in stage.student_ids:
                    stage_map[student.id] = stage
            elif student.internship_ids:
                active_stage = student.internship_ids.filtered(lambda s: s.state in ['draft', 'submitted', 'approved', 'in_progress'])
                stage_map[student.id] = active_stage[0] if active_stage else student.internship_ids[0]
        
        return {
            'doc_ids': docids,
            'doc_model': 'internship.student',
            'docs': students,
            'stage_map': stage_map,
            'company': self.env.company,
        }


class InternshipDefenseReportStudent(models.AbstractModel):
    """
    Modèle abstrait pour le rapport de Procès-Verbal de Soutenance individuel par étudiant.
    """
    _name = 'report.internship_management.defense_student'
    _description = 'Procès-Verbal de Soutenance (Individuel)'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prépare les valeurs pour le rapport de soutenance individuel."""
        students = self.env['internship.student'].browse(docids)
        stage_map = {}
        for student in students:
            if data and data.get('stage_id'):
                stage = self.env['internship.stage'].browse(data['stage_id'])
                if student in stage.student_ids:
                    stage_map[student.id] = stage
            elif student.internship_ids:
                active_stage = student.internship_ids.filtered(lambda s: s.defense_status in ['scheduled', 'completed'])
                stage_map[student.id] = active_stage[0] if active_stage else student.internship_ids[0]
        
        return {
            'doc_ids': docids,
            'doc_model': 'internship.student',
            'docs': students,
            'stage_map': stage_map,
            'company': self.env.company,
        }


class InternshipEvaluationReportStudent(models.AbstractModel):
    """
    Modèle abstrait pour le rapport d'Évaluation de Stage individuel par étudiant.
    """
    _name = 'report.internship_management.evaluation_student'
    _description = 'Rapport d\'Évaluation de Stage (Individuel)'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prépare les valeurs pour le rapport d'évaluation individuel."""
        students = self.env['internship.student'].browse(docids)
        stage_map = {}
        for student in students:
            if data and data.get('stage_id'):
                stage = self.env['internship.stage'].browse(data['stage_id'])
                if student in stage.student_ids:
                    stage_map[student.id] = stage
            elif student.internship_ids:
                active_stage = student.internship_ids.filtered(lambda s: s.state in ['completed', 'evaluated'])
                stage_map[student.id] = active_stage[0] if active_stage else student.internship_ids[0]
        
        return {
            'doc_ids': docids,
            'doc_model': 'internship.student',
            'docs': students,
            'stage_map': stage_map,
            'company': self.env.company,
        }