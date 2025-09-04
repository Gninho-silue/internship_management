# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class InternshipDashboardModern(http.Controller):
    """
    Contrôleur moderne pour le dashboard de gestion des stages
    Avec support API REST et fonctionnalités avancées
    """

    @http.route('/internship/dashboard', type='http', auth='user', website=True)
    def dashboard_modern(self, **kwargs):
        """Dashboard moderne avec interface améliorée"""
        user = request.env.user
        
        # Statistiques selon le rôle utilisateur
        stats = self._get_user_stats(user)
        role_stats = self._get_role_specific_stats(user)
        
        # Données pour les graphiques
        chart_data = self._get_chart_data()
        
        # Activités récentes
        recent_activities = self._get_recent_activities(user)
        
        return request.render('internship_management.dashboard_template_modern', {
            'user': user,
            'stats': stats,
            'role_stats': role_stats,
            'chart_data': chart_data,
            'recent_activities': recent_activities,
        })

    @http.route('/internship/dashboard/data', type='json', auth='user')
    def dashboard_data_api(self, **kwargs):
        """API JSON pour récupérer les données du dashboard"""
        user = request.env.user
        
        try:
            # Statistiques générales
            stats = self._get_user_stats(user)
            
            # Données pour graphiques
            chart_data = self._get_chart_data()
            
            # Statistiques par rôle
            role_stats = self._get_role_specific_stats(user)
            
            # Activités récentes
            recent_activities = self._get_recent_activities(user, limit=10)
            
            # KPIs additionnels
            kpis = self._get_kpi_data(user)
            
            return {
                'success': True,
                'stats': stats,
                'chart_data': chart_data,
                'role_stats': role_stats,
                'recent_activities': recent_activities,
                'kpis': kpis,
                'user_role': self._get_user_role(user),
                'last_update': datetime.now().isoformat(),
            }
            
        except Exception as e:
            _logger.error("Erreur lors du chargement des données dashboard: %s", str(e))
            return {
                'success': False,
                'error': 'Erreur lors du chargement des données',
                'details': str(e) if request.env.user.has_group('base.group_system') else None
            }

    @http.route('/internship/dashboard/export', type='http', auth='user')
    def export_dashboard_data(self, format='csv', **kwargs):
        """Export des données du dashboard"""
        user = request.env.user
        
        try:
            if format.lower() not in ['csv', 'xlsx', 'pdf']:
                raise ValueError("Format non supporté")
            
            data = self._get_export_data(user)
            
            if format.lower() == 'csv':
                return self._export_csv(data)
            elif format.lower() == 'xlsx':
                return self._export_xlsx(data)
            elif format.lower() == 'pdf':
                return self._export_pdf(data)
                
        except Exception as e:
            _logger.error("Erreur lors de l'export: %s", str(e))
            return request.redirect('/internship/dashboard?error=export_failed')

    @http.route('/internship/analytics', type='json', auth='user')
    def save_analytics(self, **kwargs):
        """Sauvegarde des données d'analytics utilisateur"""
        try:
            user = request.env.user
            action = kwargs.get('action')
            data = kwargs.get('data', {})
            
            # Sauvegarder l'action dans les logs ou une table dédiée
            self._log_user_action(user, action, data)
            
            return {'success': True}
            
        except Exception as e:
            _logger.error("Erreur analytics: %s", str(e))
            return {'success': False, 'error': str(e)}

    def _get_user_stats(self, user):
        """Récupère les statistiques selon l'utilisateur"""
        Stage = request.env['internship.stage']
        Student = request.env['internship.student']
        Supervisor = request.env['internship.supervisor']
        
        # Statistiques de base
        stats = {
            'total_stages': Stage.search_count([]),
            'stages_draft': Stage.search_count([('state', '=', 'draft')]),
            'stages_submitted': Stage.search_count([('state', '=', 'submitted')]),
            'stages_approved': Stage.search_count([('state', '=', 'approved')]),
            'stages_in_progress': Stage.search_count([('state', '=', 'in_progress')]),
            'stages_completed': Stage.search_count([('state', '=', 'completed')]),
            'stages_evaluated': Stage.search_count([('state', '=', 'evaluated')]),
            'stages_cancelled': Stage.search_count([('state', '=', 'cancelled')]),
            
            'total_students': Student.search_count([]),
            'total_supervisors': Supervisor.search_count([]),
            'total_companies': request.env['res.company'].search_count([('id', '!=', 1)]),
            
            # Par type de stage
            'pfe_count': Stage.search_count([('stage_type', '=', 'pfe')]),
            'summer_internship_count': Stage.search_count([('stage_type', '=', 'stage_ete')]),
            'observation_count': Stage.search_count([('stage_type', '=', 'stage_obs')]),
            
            # Soutenances
            'defense_scheduled': Stage.search_count([('defense_status', '=', 'scheduled')]),
            'defense_completed': Stage.search_count([('defense_status', '=', 'completed')]),
            
            # Progression moyenne
            'avg_progress': self._calculate_average_progress(),
        }
        
        return stats

    def _get_role_specific_stats(self, user):
        """Statistiques spécifiques au rôle de l'utilisateur"""
        Stage = request.env['internship.stage']
        
        if user.has_group('internship_management.group_internship_supervisor'):
            # Statistiques pour superviseur
            supervisor = request.env['internship.supervisor'].search([('user_id', '=', user.id)], limit=1)
            if supervisor:
                my_stages = Stage.search([('supervisor_id', '=', supervisor.id)])
                return {
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
                
        elif user.has_group('internship_management.group_internship_student'):
            # Statistiques pour étudiant
            student = request.env['internship.student'].search([('user_id', '=', user.id)], limit=1)
            if student:
                my_stages = Stage.search([('student_id', '=', student.id)])
                graded_stages = my_stages.filtered(lambda s: s.grade > 0)
                return {
                    'my_stages_count': len(my_stages),
                    'my_stages_draft': len(my_stages.filtered(lambda s: s.state == 'draft')),
                    'my_stages_in_progress': len(my_stages.filtered(lambda s: s.state == 'in_progress')),
                    'my_stages_completed': len(my_stages.filtered(lambda s: s.state == 'completed')),
                    'my_stages_evaluated': len(my_stages.filtered(lambda s: s.state == 'evaluated')),
                    'my_progress': sum(my_stages.mapped('progress')) / len(my_stages) if my_stages else 0,
                    'my_grade': sum(graded_stages.mapped('grade')) / len(graded_stages) if graded_stages else 0,
                    'my_current_stage': my_stages.filtered(lambda s: s.state == 'in_progress')[:1] if my_stages else None,
                }
        
        return {}

    def _get_chart_data(self):
        """Données pour les graphiques"""
        Stage = request.env['internship.stage']
        
        # Répartition par état
        states_data = {
            'labels': ['Brouillon', 'Soumis', 'Approuvé', 'En cours', 'Terminé', 'Évalué', 'Annulé'],
            'data': [
                Stage.search_count([('state', '=', 'draft')]),
                Stage.search_count([('state', '=', 'submitted')]),
                Stage.search_count([('state', '=', 'approved')]),
                Stage.search_count([('state', '=', 'in_progress')]),
                Stage.search_count([('state', '=', 'completed')]),
                Stage.search_count([('state', '=', 'evaluated')]),
                Stage.search_count([('state', '=', 'cancelled')]),
            ],
            'colors': ['#6b7280', '#3b82f6', '#f59e0b', '#8b5cf6', '#10b981', '#059669', '#ef4444']
        }
        
        # Répartition par type
        types_data = {
            'labels': ['PFE', "Stage d'été", "Stage d'observation"],
            'data': [
                Stage.search_count([('stage_type', '=', 'pfe')]),
                Stage.search_count([('stage_type', '=', 'stage_ete')]),
                Stage.search_count([('stage_type', '=', 'stage_obs')]),
            ],
            'colors': ['#8b5cf6', '#10b981', '#f59e0b']
        }
        
        # Évolution mensuelle (6 derniers mois)
        monthly_data = self._get_monthly_evolution()
        
        return {
            'stages_by_state': states_data,
            'stages_by_type': types_data,
            'monthly_evolution': monthly_data,
        }

    def _get_monthly_evolution(self):
        """Évolution mensuelle des stages"""
        Stage = request.env['internship.stage']
        
        # Calculer les 6 derniers mois
        months = []
        data = []
        
        for i in range(6):
            date = datetime.now().replace(day=1) - timedelta(days=30 * i)
            month_start = date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            count = Stage.search_count([
                ('create_date', '>=', month_start),
                ('create_date', '<=', month_end)
            ])
            
            months.insert(0, date.strftime('%B %Y'))
            data.insert(0, count)
        
        return {
            'labels': months,
            'data': data
        }

    def _get_recent_activities(self, user, limit=5):
        """Activités récentes selon l'utilisateur"""
        activities = []
        
        try:
            # Messages récents
            messages = request.env['mail.message'].search([
                ('model', '=', 'internship.stage'),
                ('message_type', '!=', 'notification')
            ], order='create_date desc', limit=limit)
            
            for msg in messages:
                activity = {
                    'icon': 'fas fa-comment',
                    'title': 'Nouveau message',
                    'description': msg.subject or 'Message sans sujet',
                    'time': self._format_relative_time(msg.create_date),
                    'type': 'info'
                }
                activities.append(activity)
            
            # Stages récents
            recent_stages = request.env['internship.stage'].search([
                ('create_date', '>=', datetime.now() - timedelta(days=7))
            ], order='create_date desc', limit=3)
            
            for stage in recent_stages:
                activity = {
                    'icon': 'fas fa-plus',
                    'title': 'Nouveau stage créé',
                    'description': f'Stage "{stage.name}" par {stage.student_id.name}',
                    'time': self._format_relative_time(stage.create_date),
                    'type': 'success'
                }
                activities.append(activity)
            
            # Trier par date
            activities.sort(key=lambda x: x['time'], reverse=True)
            
        except Exception as e:
            _logger.error("Erreur lors du chargement des activités: %s", str(e))
        
        return activities[:limit]

    def _get_kpi_data(self, user):
        """Indicateurs de performance clés"""
        Stage = request.env['internship.stage']
        
        total_stages = Stage.search_count([])
        if total_stages == 0:
            return {}
        
        completed_stages = Stage.search_count([('state', 'in', ['completed', 'evaluated'])])
        success_rate = (completed_stages / total_stages) * 100 if total_stages > 0 else 0
        
        # Durée moyenne des stages
        stages_with_duration = Stage.search([('duration', '>', 0)])
        avg_duration = sum(stages_with_duration.mapped('duration')) / len(stages_with_duration) if stages_with_duration else 0
        
        # Note moyenne
        graded_stages = Stage.search([('grade', '>', 0)])
        avg_grade = sum(graded_stages.mapped('grade')) / len(graded_stages) if graded_stages else 0
        
        return {
            'success_rate': round(success_rate, 1),
            'avg_duration': round(avg_duration, 0),
            'avg_grade': round(avg_grade, 2),
            'total_hours': round(avg_duration * 8, 0) if avg_duration else 0,  # Estimation 8h/jour
        }

    def _calculate_average_progress(self):
        """Calcule la progression moyenne de tous les stages actifs"""
        stages = request.env['internship.stage'].search([
            ('state', 'not in', ['cancelled', 'draft'])
        ])
        
        if not stages:
            return 0.0
        
        return sum(stages.mapped('progress')) / len(stages)

    def _get_user_role(self, user):
        """Détermine le rôle de l'utilisateur"""
        if user.has_group('internship_management.group_internship_admin'):
            return 'admin'
        elif user.has_group('internship_management.group_internship_supervisor'):
            return 'supervisor'
        elif user.has_group('internship_management.group_internship_student'):
            return 'student'
        else:
            return 'user'

    def _format_relative_time(self, dt):
        """Formate une date en temps relatif (ex: "il y a 2 heures")"""
        if not dt:
            return "Date inconnue"
        
        now = datetime.now()
        if hasattr(dt, 'replace'):
            # Si c'est un datetime aware, le convertir
            dt = dt.replace(tzinfo=None) if dt.tzinfo else dt
        
        diff = now - dt
        
        if diff.days > 0:
            return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "Il y a quelques instants"

    def _log_user_action(self, user, action, data):
        """Log des actions utilisateur pour analytics"""