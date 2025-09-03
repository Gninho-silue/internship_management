# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class InternshipDashboard(http.Controller):

    @http.route('/internship/dashboard', type='http', auth='user', website=True)
    def dashboard(self, **kwargs):
        """Dashboard principal avec statistiques par rôle"""
        user = request.env.user
        
        # Statistiques générales (admin)
        stats = {
            'total_stages': request.env['internship.stage'].search_count([]),
            'stages_draft': request.env['internship.stage'].search_count([('state', '=', 'draft')]),
            'stages_submitted': request.env['internship.stage'].search_count([('state', '=', 'submitted')]),
            'stages_approved': request.env['internship.stage'].search_count([('state', '=', 'approved')]),
            'stages_in_progress': request.env['internship.stage'].search_count([('state', '=', 'in_progress')]),
            'stages_completed': request.env['internship.stage'].search_count([('state', '=', 'completed')]),
            'stages_evaluated': request.env['internship.stage'].search_count([('state', '=', 'evaluated')]),
            'stages_cancelled': request.env['internship.stage'].search_count([('state', '=', 'cancelled')]),
            
            'total_students': request.env['internship.student'].search_count([]),
            'total_supervisors': request.env['internship.supervisor'].search_count([]),
            'total_companies': request.env['res.company'].search_count([('id', '!=', 1)]),  # Exclure la société principale
            
            # Statistiques par type de stage
            'pfe_count': request.env['internship.stage'].search_count([('stage_type', '=', 'pfe')]),
            'summer_internship_count': request.env['internship.stage'].search_count([('stage_type', '=', 'stage_ete')]),
            'observation_count': request.env['internship.stage'].search_count([('stage_type', '=', 'stage_obs')]),
            
            # Statistiques de progression
            'avg_progress': request.env['internship.stage'].search([('state', '!=', 'cancelled')]).mapped('progress'),
            'defense_scheduled': request.env['internship.stage'].search_count([('defense_status', '=', 'scheduled')]),
            'defense_completed': request.env['internship.stage'].search_count([('defense_status', '=', 'completed')]),
        }
        
        # Calculer la moyenne de progression
        if stats['avg_progress']:
            stats['avg_progress'] = sum(stats['avg_progress']) / len(stats['avg_progress'])
        else:
            stats['avg_progress'] = 0
            
        # Statistiques par rôle
        if user.has_group('internship_management.group_internship_admin'):
            # Admin : toutes les statistiques
            role_stats = stats
        elif user.has_group('internship_management.group_internship_supervisor'):
            # Superviseur : ses stages et étudiants
            supervisor = request.env['internship.supervisor'].search([('user_id', '=', user.id)], limit=1)
            if supervisor:
                my_stages = request.env['internship.stage'].search([('supervisor_id', '=', supervisor.id)])
                role_stats = {
                    'my_stages_count': len(my_stages),
                    'my_stages_draft': len(my_stages.filtered(lambda s: s.state == 'draft')),
                    'my_stages_in_progress': len(my_stages.filtered(lambda s: s.state == 'in_progress')),
                    'my_stages_completed': len(my_stages.filtered(lambda s: s.state == 'completed')),
                    'my_stages_evaluated': len(my_stages.filtered(lambda s: s.state == 'evaluated')),
                    'my_students_count': len(my_stages.mapped('student_id')),
                    'my_avg_progress': sum(my_stages.mapped('progress')) / len(my_stages) if my_stages else 0,
                    'my_defense_scheduled': len(my_stages.filtered(lambda s: s.defense_status == 'scheduled')),
                    'my_defense_completed': len(my_stages.filtered(lambda s: s.defense_status == 'completed')),
                }
            else:
                role_stats = {
                    'my_stages_count': 0,
                    'my_stages_draft': 0,
                    'my_stages_in_progress': 0,
                    'my_stages_completed': 0,
                    'my_stages_evaluated': 0,
                    'my_students_count': 0,
                    'my_avg_progress': 0,
                    'my_defense_scheduled': 0,
                    'my_defense_completed': 0,
                }
        elif user.has_group('internship_management.group_internship_student'):
            # Étudiant : ses stages
            student = request.env['internship.student'].search([('user_id', '=', user.id)], limit=1)
            if student:
                my_stages = request.env['internship.stage'].search([('student_id', '=', student.id)])
                role_stats = {
                    'my_stages_count': len(my_stages),
                    'my_stages_draft': len(my_stages.filtered(lambda s: s.state == 'draft')),
                    'my_stages_in_progress': len(my_stages.filtered(lambda s: s.state == 'in_progress')),
                    'my_stages_completed': len(my_stages.filtered(lambda s: s.state == 'completed')),
                    'my_stages_evaluated': len(my_stages.filtered(lambda s: s.state == 'evaluated')),
                    'my_progress': sum(my_stages.mapped('progress')) / len(my_stages) if my_stages else 0,
                    'my_grade': sum(my_stages.mapped('grade')) / len(my_stages.filtered(lambda s: s.grade > 0)) if my_stages.filtered(lambda s: s.grade > 0) else 0,
                }
            else:
                role_stats = {
                    'my_stages_count': 0,
                    'my_stages_draft': 0,
                    'my_stages_in_progress': 0,
                    'my_stages_completed': 0,
                    'my_stages_evaluated': 0,
                    'my_progress': 0,
                    'my_grade': 0,
                }
        else:
            # Utilisateur sans rôle spécifique
            role_stats = {
                'my_stages_count': 0,
                'my_stages_draft': 0,
                'my_stages_in_progress': 0,
                'my_stages_completed': 0,
                'my_stages_evaluated': 0,
                'my_students_count': 0,
                'my_avg_progress': 0,
                'my_defense_scheduled': 0,
                'my_defense_completed': 0,
                'my_progress': 0,
                'my_grade': 0,
            }
            
        return request.render('internship_management.dashboard_template', {
            'stats': stats,
            'role_stats': role_stats,
            'user': user,
        })

    @http.route('/internship/dashboard/data', type='json', auth='user')
    def dashboard_data(self):
        """API pour récupérer les données du dashboard en JSON"""
        user = request.env.user
        
        # Données pour graphiques
        chart_data = {
            'stages_by_state': {
                'labels': ['Brouillon', 'Soumis', 'Approuvé', 'En cours', 'Terminé', 'Évalué', 'Annulé'],
                'data': [
                    request.env['internship.stage'].search_count([('state', '=', 'draft')]),
                    request.env['internship.stage'].search_count([('state', '=', 'submitted')]),
                    request.env['internship.stage'].search_count([('state', '=', 'approved')]),
                    request.env['internship.stage'].search_count([('state', '=', 'in_progress')]),
                    request.env['internship.stage'].search_count([('state', '=', 'completed')]),
                    request.env['internship.stage'].search_count([('state', '=', 'evaluated')]),
                    request.env['internship.stage'].search_count([('state', '=', 'cancelled')]),
                ]
            },
            'stages_by_type': {
                'labels': ['PFE', 'Stage d\'été', 'Stage d\'observation'],
                'data': [
                    request.env['internship.stage'].search_count([('stage_type', '=', 'pfe')]),
                    request.env['internship.stage'].search_count([('stage_type', '=', 'stage_ete')]),
                    request.env['internship.stage'].search_count([('stage_type', '=', 'stage_obs')]),
                ]
            }
        }
        
        return {
            'chart_data': chart_data,
            'user_role': 'admin' if user.has_group('internship_management.group_internship_admin') else 
                        'supervisor' if user.has_group('internship_management.group_internship_supervisor') else 
                        'student' if user.has_group('internship_management.group_internship_student') else 'user'
        }
