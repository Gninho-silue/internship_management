# -*- coding: utf-8 -*-
"""
Modèle pour la gestion des stages (Internship Stage).
Ce modèle gère le cycle de vie complet d'un stage, de la candidature
à l'évaluation finale, en incluant le suivi de la progression,
les évaluations et la gestion documentaire.
"""

import logging
import re
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipStage(models.Model):
    """
    Définit un stage, ses acteurs, son calendrier et son état d'avancement.
    Hérite de 'mail.thread' et 'mail.activity.mixin' pour intégrer le Chatter
    et les activités, qui sont les outils standards d'Odoo pour la communication
    et le suivi des tâches.
    """
    _name = 'internship.stage'
    _description = 'Gestion de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, title'
    _rec_name = 'title'

    # ===============================
    # CHAMPS D'IDENTIFICATION
    # ===============================

    title = fields.Char(
        string='Titre du Stage',
        required=True,
        tracking=True,
        help="Sujet principal ou titre du projet de stage."
    )

    reference_number = fields.Char(
        string='Numéro de Référence',
        readonly=True,
        copy=False,
        default='Nouveau',
        help="Numéro de référence unique pour ce stage."
    )

    # ===============================
    # CLASSIFICATION
    # ===============================

    internship_type = fields.Selection([
        ('final_project', 'Projet de Fin d\'Études (PFE)'),
        ('summer_internship', 'Stage d\'été'),
        ('observation_internship', 'Stage d\'observation'),
        ('professional_internship', 'Stage professionnel')
    ], string='Type de Stage', tracking=True)

    # ===============================
    # CHAMPS RELATIONNELS
    # ===============================

    student_ids = fields.Many2many(
        'internship.student',
        'internship_student_stage_rel',  # relation (table intermédiaire)
        'stage_id',                      # column1
        'student_id',                    # column2
        string='Étudiants',
        domain=[('active', '=', True)],
        tracking=True,
        help="Étudiants assigné(e)s à ce stage."
    )

    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Encadrant(e)',
        tracking=True,
        ondelete='restrict',
        help="Encadrant(e) académique ou professionnel."
    )

    area_id = fields.Many2one(
        'internship.area',
        string='Domaine d\'Expertise',
        help="Domaine d'expertise de ce stage."
    )

    company_id = fields.Many2one(
        'res.company',
        string='Entreprise',
        default=lambda self: self.env.company,
        readonly=True,
        help="Entreprise où se déroule le stage."
    )

    # ===============================
    # GESTION DU TEMPS
    # ===============================

    start_date = fields.Date(
        string='Date de Début',
        tracking=True,
        help="Date de début officielle du stage."
    )

    end_date = fields.Date(
        string='Date de Fin',
        tracking=True,
        help="Date de fin officielle du stage."
    )

    @api.depends('start_date', 'end_date')
    def _compute_duration_days(self):
        """Calcule la durée du stage en jours."""
        for stage in self:
            if stage.start_date and stage.end_date:
                if stage.end_date >= stage.start_date:
                    delta = stage.end_date - stage.start_date
                    stage.duration_days = delta.days + 1
                else:
                    stage.duration_days = 0
            else:
                stage.duration_days = 0

    duration_days = fields.Integer(
        string='Durée (Jours)',
        compute='_compute_duration_days',
        store=True,
        help="Durée totale du stage en jours."
    )

    # ===============================
    # DESCRIPTION DÉTAILLÉE DU SUJET
    # ===============================

    subject_proposal = fields.Html(
        string='Description Détaillée du Sujet',
        help="Description détaillée du sujet de stage. Ce champ peut être utilisé pour fournir des informations supplémentaires sur le projet, les objectifs, les technologies utilisées, etc."
    )

    repository_url = fields.Char(
        string='URL du Dépôt (GitHub/GitLab)',
        help="URL du dépôt GitHub, GitLab ou autre service de gestion de code source."
    )

    # ===============================
    # CONTENU DU STAGE
    # ===============================

    project_description = fields.Html(
        string='Description du Projet',
        help="Description détaillée du projet de stage et de son contexte."
    )

    learning_objectives = fields.Html(
        string='Objectifs Pédagogiques',
        help="Objectifs pédagogiques et professionnels à atteindre."
    )

    # ===============================
    # SUIVI DE LA PROGRESSION
    # ===============================

    @api.depends('task_ids.state', 'start_date', 'end_date', 'state')
    def _compute_completion_percentage(self):
        """
        Calcule le pourcentage d'achèvement.
        - Si le stage est terminé ou évalué, le pourcentage est de 100%.
        - Si des tâches existent, le calcul se base sur le ratio de tâches terminées.
        - Sinon, il se base sur le temps écoulé par rapport à la durée totale.
        """
        for stage in self:
            if stage.state in ('completed', 'evaluated'):
                stage.completion_percentage = 100.0
                continue
            elif stage.state == 'cancelled':
                stage.completion_percentage = 0.0
                continue

            progress_value = 0.0
            total_tasks = len(stage.task_ids)
            if total_tasks > 0:
                completed_tasks = len(stage.task_ids.filtered(lambda t: t.state == 'done'))
                progress_value = (completed_tasks / total_tasks) * 100.0
            else:
                if stage.start_date and stage.end_date and stage.end_date >= stage.start_date:
                    total_duration = (stage.end_date - stage.start_date).days + 1
                    if total_duration > 0:
                        today = fields.Date.context_today(stage)
                        if today <= stage.start_date:
                            elapsed_days = 0
                        elif today >= stage.end_date:
                            elapsed_days = total_duration
                        else:
                            elapsed_days = (today - stage.start_date).days
                        progress_value = (elapsed_days / total_duration) * 100.0

            stage.completion_percentage = max(0.0, min(100.0, round(progress_value, 2)))

    completion_percentage = fields.Float(
        string='Achèvement %',
        compute='_compute_completion_percentage',
        store=True,
        tracking=True,
        help="Pourcentage global d'achèvement du stage."
    )

    # ===============================
    # GESTION D'ÉTAT (WORKFLOW)
    # ===============================

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('in_progress', 'En Cours'),
        ('completed', 'Terminé'),
        ('evaluated', 'Évalué'),
        ('cancelled', 'Annulé')
    ], string='Statut', default='draft', tracking=True)

    # ===============================
    # CHAMPS RELATIONNELS (One2many)
    # ===============================

    document_ids = fields.One2many(
        'internship.document', 'stage_id', string='Documents',
        help="Tous les documents liés à ce stage."
    )

    meeting_ids = fields.One2many(
        'internship.meeting', 'stage_id', string='Réunions',
        help="Réunions planifiées pour ce stage."
    )

    task_ids = fields.One2many(
        'internship.todo', 'stage_id', string='Tâches',
        help="Tâches et livrables pour ce stage."
    )

    presentation_ids = fields.One2many(
        'internship.presentation', 'stage_id', string='Présentations',
        help="Présentations de l'étudiant pour la soutenance."
    )

    planning_ids = fields.One2many(
        'internship.meeting', 'stage_id', string='Plannings',
        domain=[('meeting_type', '=', 'planning')],
        help="Plannings automatiques créés pour ce stage."
    )

    account_ids = fields.One2many(
        'internship.account', 'stage_id', string='Comptes Externes',
        help="Comptes externes associés à ce stage (GitHub, GitLab, etc.)."
    )

    # ===============================
    # STATISTIQUES (CHAMPS CALCULÉS)
    # ===============================

    @api.depends('task_ids', 'task_ids.state')
    def _compute_task_stats(self):
        """Calcule les statistiques sur les tâches."""
        for stage in self:
            stage.task_count = len(stage.task_ids)
            stage.completed_task_count = len(stage.task_ids.filtered(lambda t: t.state == 'done'))
            stage.pending_task_count = len(stage.task_ids.filtered(lambda t: t.state in ['todo', 'in_progress']))

    task_count = fields.Integer(string='Tâches Totales', compute='_compute_task_stats', store=True)
    completed_task_count = fields.Integer(string='Tâches Terminées', compute='_compute_task_stats', store=True)
    pending_task_count = fields.Integer(string='Tâches en Attente', compute='_compute_task_stats', store=True)

    @api.depends('presentation_ids', 'presentation_ids.status')
    def _compute_presentation_stats(self):
        """Calcule les statistiques sur les présentations."""
        for stage in self:
            stage.presentation_count = len(stage.presentation_ids)
            stage.pending_presentation_count = len(
                stage.presentation_ids.filtered(lambda p: p.status in ['submitted', 'revision_required']))

    presentation_count = fields.Integer(string='Nb Présentations', compute='_compute_presentation_stats', store=True)
    pending_presentation_count = fields.Integer(string='Présentations en Attente',
                                                compute='_compute_presentation_stats', store=True)

    @api.depends('presentation_ids.status')
    def _compute_final_presentation(self):
        """Détermine la présentation finale approuvée."""
        for stage in self:
            approved_presentation = stage.presentation_ids.filtered(lambda p: p.status == 'approved')
            stage.final_presentation_id = approved_presentation[0] if approved_presentation else False

    final_presentation_id = fields.Many2one(
        'internship.presentation', string="Présentation Finale Approuvée",
        compute='_compute_final_presentation', store=True,
        help="La dernière présentation approuvée pour la soutenance."
    )

    @api.depends('meeting_ids', 'meeting_ids.date')
    def _compute_meeting_stats(self):
        """Calcule les statistiques sur les réunions."""
        for stage in self:
            stage.meeting_count = len(stage.meeting_ids)
            stage.upcoming_meeting_count = len(stage.meeting_ids.filtered(
                lambda m: m.date and m.date > fields.Datetime.now()
            ))

    meeting_count = fields.Integer(string='Nb Réunions', compute='_compute_meeting_stats', store=True)
    upcoming_meeting_count = fields.Integer(string='Réunions à Venir', compute='_compute_meeting_stats', store=True)

    # ===============================
    # ÉVALUATION
    # ===============================

    final_grade = fields.Float(string='Note Finale', digits=(4, 2), help="Note finale du stage (sur 20).")
    defense_grade = fields.Float(string='Note de Soutenance', digits=(4, 2), help="Note de la soutenance (sur 20).")
    evaluation_feedback = fields.Html(string='Feedback d\'Évaluation', help="Feedback détaillé de l'encadrant(e).")

    # ===============================
    # GESTION DE LA SOUTENANCE
    # ===============================

    defense_date = fields.Datetime(string='Date de Soutenance', help="Date planifiée pour la soutenance.")
    defense_location = fields.Char(string='Lieu de la Soutenance', help="Lieu où se déroulera la soutenance.")
    defense_status = fields.Selection([
        ('scheduled', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée')
    ], string='Statut Soutenance', default='scheduled', tracking=True)
    jury_member_ids = fields.Many2many(
        'internship.supervisor',
        'internship_stage_jury_rel',  # relation (table intermédiaire)
        'stage_id',                   # column1
        'supervisor_id',              # column2
        string='Membres du Jury',
        help="Encadrants assignés comme membres du jury."
    )

    # ===============================
    # SIGNATURES
    # ===============================

    supervisor_signature = fields.Binary(string='Signature Encadrant(e)',
                                         help='Signature numérique de l\'encadrant(e).')
    student_signature = fields.Binary(string='Signature Étudiant(e)', help='Signature numérique de l\'étudiant(e).')
    jury_signature = fields.Binary(string='Signature Jury', help='Signature numérique du président du jury.')

    # ===============================
    # CHAMP TECHNIQUE
    # ===============================

    active = fields.Boolean(default=True, string='Actif', help="Indique si cet enregistrement de stage est actif.")

    # ===============================
    # CONTRAINTES DE VALIDATION
    # ===============================

    @api.constrains('start_date', 'end_date')
    def _check_date_consistency(self):
        """Vérifie que la date de fin est postérieure à la date de début."""
        for stage in self:
            if stage.start_date and stage.end_date and stage.start_date > stage.end_date:
                raise ValidationError(_("La date de fin doit être après la date de début."))

    @api.constrains('final_grade', 'defense_grade')
    def _check_grade_range(self):
        """Vérifie que les notes sont dans une plage valide (0-20)."""
        for stage in self:
            if stage.final_grade and not (0 <= stage.final_grade <= 20):
                raise ValidationError(_("La note finale doit être entre 0 et 20."))
            if stage.defense_grade and not (0 <= stage.defense_grade <= 20):
                raise ValidationError(_("La note de soutenance doit être entre 0 et 20."))

    # ===============================
    # MÉTHODES CRUD
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        """
        Surcharge de la méthode create pour :
        - Générer les numéros de référence
        - Envoyer les notifications email à tous les responsables
        - Créer automatiquement les plannings pour les 2 premières semaines
        """
        for vals in vals_list:
            if vals.get('reference_number', 'Nouveau') == 'Nouveau':
                vals['reference_number'] = self.env['ir.sequence'].next_by_code('internship.stage') or 'STG-N/A'

        stages = super().create(vals_list)

        for stage in stages:
            _logger.info(f"Stage créé : {stage.reference_number} - {stage.title}")
            
            # 1. Envoyer les notifications email à tous les responsables
            stage._send_creation_notifications()
            
            # 2. Créer automatiquement les plannings pour les 2 premières semaines
            if stage.start_date:
                stage._create_automatic_plannings()
            
            # 3. Notifier tous les étudiants via le Chatter (garder pour compatibilité)
            for student in stage.student_ids:
                if student.user_id and student.user_id.partner_id:
                    stage.message_post(
                        body=_(
                            "Bienvenue ! Vous avez été assigné(e) au stage "
                            "\"<strong>%s</strong>\". Veuillez consulter les détails.",
                            stage.title
                        ),
                        partner_ids=[student.user_id.partner_id.id],
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )
        return stages

    def _prepare_email_data(self):
        """
        Prépare toutes les données pour l'email en Python.
        Retourne un dictionnaire avec toutes les valeurs formatées.
        """
        self.ensure_one()
        
        # Préparer les données du stage
        # Récupérer le libellé du type de stage au lieu de la valeur technique
        internship_type_label = 'Non spécifié'
        if self.internship_type:
            # Récupérer la sélection du champ
            selection = dict(self._fields['internship_type'].selection)
            internship_type_label = selection.get(self.internship_type, self.internship_type)
        
        data = {
            'title': self.title or 'Sans titre',
            'reference_number': self.reference_number or 'N/A',
            'internship_type': internship_type_label,
            'start_date': self.start_date.strftime('%d/%m/%Y') if self.start_date else 'Non spécifiée',
            'end_date': self.end_date.strftime('%d/%m/%Y') if self.end_date else 'Non spécifiée',
            'supervisor_name': self.supervisor_id.name if self.supervisor_id else 'Non spécifié',
            'students': [],
            'base_url': self.get_base_url(),
            'stage_id': self.id,
        }
        
        # Préparer la liste des étudiants
        for student in self.student_ids:
            data['students'].append({
                'full_name': student.full_name,
            })
        
        return data
    
    def _render_email_template(self, template, data):
        """
        Rend le template email avec les données préparées.
        Remplace les variables {{ }} par les valeurs réelles.
        Utilise des regex flexibles pour gérer les variations d'espaces.
        """
        # Rendre le sujet avec regex pour gérer les variations d'espaces
        subject = re.sub(r'\{\{\s*object\.title\s*\}\}', data['title'], template.subject)
        # Nettoyer le sujet : supprimer les retours à la ligne et les espaces en début/fin
        subject = re.sub(r'[\r\n]+', ' ', subject)  # Remplacer les retours à la ligne par des espaces
        subject = subject.strip()  # Supprimer les espaces en début/fin
        
        # Rendre le corps HTML
        body_html = template.body_html
        
        # Remplacer les variables simples avec regex pour gérer les espaces
        body_html = re.sub(r'\{\{\s*object\.title\s*\}\}', data['title'], body_html)
        body_html = re.sub(r'\{\{\s*object\.reference_number\s*\}\}', data['reference_number'], body_html)
        body_html = re.sub(r'\{\{\s*object\.supervisor_id\.name\s*\}\}', data['supervisor_name'], body_html)
        
        # Remplacer object.internship_type or 'Non spécifié' (expression complexe)
        body_html = re.sub(
            r'\{\{\s*object\.internship_type\s+or\s+[\'"]Non spécifié[\'"]\s*\}\}',
            data['internship_type'],
            body_html
        )
        
        # Remplacer les dates (avec gestion des conditions t-if)
        if data['start_date'] != 'Non spécifiée':
            # Remplacer la variable de date avec regex
            body_html = re.sub(
                r'\{\{\s*object\.start_date\.strftime\([\'"]%d/%m/%Y[\'"]\)\s*\}\}',
                data['start_date'],
                body_html
            )
            # Supprimer les balises t-if pour start_date si la date existe
            body_html = re.sub(r't-if="object\.start_date"\s+', '', body_html)
        else:
            # Supprimer toute la ligne li si la date n'existe pas
            body_html = re.sub(
                r'<li t-if="object\.start_date"[^>]*>.*?</li>',
                '',
                body_html,
                flags=re.DOTALL
            )
        
        if data['end_date'] != 'Non spécifiée':
            # Remplacer la variable de date avec regex
            body_html = re.sub(
                r'\{\{\s*object\.end_date\.strftime\([\'"]%d/%m/%Y[\'"]\)\s*\}\}',
                data['end_date'],
                body_html
            )
            body_html = re.sub(r't-if="object\.end_date"\s+', '', body_html)
        else:
            body_html = re.sub(
                r'<li t-if="object\.end_date"[^>]*>.*?</li>',
                '',
                body_html,
                flags=re.DOTALL
            )
        
        # Remplacer la liste des étudiants
        if data['students']:
            students_html = ''
            for student in data['students']:
                # Le modèle student n'a que full_name, pas name, donc on affiche juste full_name
                students_html += f'<li style="margin: 5px 0;">{student["full_name"]}</li>'
            
            # Remplacer toute la boucle t-foreach avec regex
            # Le pattern doit capturer le <li> complet avec t-foreach, en gérant les retours à la ligne
            # Pattern plus flexible pour gérer les variations d'espaces et retours à la ligne
            # Note: le template utilise student.name mais le modèle n'a que full_name, donc on remplace les deux
            pattern = r'<li\s+t-foreach="object\.student_ids"\s+t-as="student"[^>]*>[\s\S]*?\{\{\s*student\.name\s*\}\}[\s\S]*?\(\{\{\s*student\.full_name\s*\}\}\)[\s\S]*?</li>'
            body_html = re.sub(pattern, students_html, body_html)
            
            # Supprimer l'attribut t-if de la div parente
            body_html = re.sub(
                r'<div\s+t-if="object\.student_ids"\s+',
                '<div ',
                body_html
            )
        else:
            # Supprimer toute la section étudiants si vide (div avec t-if)
            body_html = re.sub(
                r'<div\s+t-if="object\.student_ids"[^>]*>.*?</div>',
                '',
                body_html,
                flags=re.DOTALL
            )
        
        # Remplacer l'URL du bouton avec regex
        url = f"{data['base_url']}/web#id={data['stage_id']}&amp;model=internship.stage&amp;view_type=form"
        body_html = re.sub(
            r't-att-href="[^"]*object\.get_base_url\(\)[^"]*"',
            f'href="{url}"',
            body_html
        )
        
        return subject, body_html
    
    def _send_creation_notifications(self):
        """
        Envoie les notifications email à tous les responsables lors de la création d'un stage.
        Notifie : encadrant, étudiants, coordinateur si défini.
        """
        self.ensure_one()
        
        # Récupérer le template email
        template = self.env.ref(
            'internship_management.mail_template_stage_creation',
            raise_if_not_found=False
        )
        
        if not template:
            _logger.warning("Template email pour la création de stage non trouvé.")
            return
        
        # Collecter tous les partenaires à notifier
        partner_ids = []
        
        # Ajouter l'encadrant
        if self.supervisor_id and self.supervisor_id.user_id and self.supervisor_id.user_id.partner_id:
            partner_ids.append(self.supervisor_id.user_id.partner_id.id)
        
        # Ajouter tous les étudiants
        for student in self.student_ids:
            if student.user_id and student.user_id.partner_id:
                partner_ids.append(student.user_id.partner_id.id)
        
        # Ajouter le coordinateur si défini (à adapter selon votre modèle)
        # Exemple si vous avez un champ coordinator_id :
        # if self.coordinator_id and self.coordinator_id.user_id and self.coordinator_id.user_id.partner_id:
        #     partner_ids.append(self.coordinator_id.user_id.partner_id.id)
        
        # Envoyer l'email à tous les partenaires
        if partner_ids:
            try:
                # Préparer toutes les données en Python
                email_data = self._prepare_email_data()
                
                # Rendre le template avec les données préparées
                subject, body_html = self._render_email_template(template, email_data)
                
                # Récupérer l'email_from du template ou utiliser celui de l'utilisateur
                email_from = self.env.user.email_formatted
                if template.email_from:
                    # Essayer de rendre email_from si nécessaire
                    email_from = template.email_from.replace('{{ user.email_formatted }}', self.env.user.email_formatted)
                    # Nettoyer email_from : supprimer les retours à la ligne et les espaces en début/fin
                    email_from = re.sub(r'[\r\n]+', ' ', email_from)  # Remplacer les retours à la ligne par des espaces
                    email_from = email_from.strip()  # Supprimer les espaces en début/fin
                
                # Pour chaque partenaire, créer et envoyer un email
                for partner_id in partner_ids:
                    partner = self.env['res.partner'].browse(partner_id)
                    if not partner.email:
                        _logger.warning(f"Le partenaire {partner.name} (ID: {partner_id}) n'a pas d'email configuré.")
                        continue
                    
                    # Créer le mail avec le contenu rendu
                    mail = self.env['mail.mail'].create({
                        'subject': subject,
                        'body_html': body_html,
                        'email_from': email_from,
                        'email_to': partner.email,
                        'model': self._name,
                        'res_id': self.id,
                        'auto_delete': False,
                    })
                    
                    # Envoyer immédiatement
                    mail.send()
                    
                _logger.info(f"Notifications email envoyées à {len(partner_ids)} partenaire(s) pour le stage {self.reference_number}")
            except Exception as e:
                _logger.error(f"Erreur lors de l'envoi des emails pour le stage {self.reference_number}: {str(e)}")
                import traceback
                _logger.error(traceback.format_exc())
                # Ne pas bloquer la création du stage si l'envoi d'email échoue

    def _create_automatic_plannings(self):
        """
        Crée automatiquement deux plannings (meetings de type 'planning') lors de la création d'un stage :
        - Semaine 1 : Apprendre sur l'entreprise
        - Semaine 2 : Apprendre sur le travail
        """
        self.ensure_one()
        
        if not self.start_date:
            _logger.warning(f"Impossible de créer les plannings : pas de date de début pour le stage {self.reference_number}")
            return
        
        # Collecter tous les partenaires à assigner
        partner_ids = []
        
        # Ajouter l'encadrant
        if self.supervisor_id and self.supervisor_id.user_id and self.supervisor_id.user_id.partner_id:
            partner_ids.append(self.supervisor_id.user_id.partner_id.id)
        
        # Ajouter tous les étudiants
        for student in self.student_ids:
            if student.user_id and student.user_id.partner_id:
                partner_ids.append(student.user_id.partner_id.id)
        
        if not partner_ids:
            _logger.warning(f"Aucun partenaire à assigner aux plannings pour le stage {self.reference_number}")
            return
        
        # Calculer les dates pour les 2 semaines
        week1_start = self.start_date
        week1_end = week1_start + timedelta(days=6)  # 7 jours (0-6)
        week2_start = week1_end + timedelta(days=1)
        week2_end = week2_start + timedelta(days=6)  # 7 jours
        
        # Convertir les dates de début en datetime pour le champ date du meeting
        week1_datetime = fields.Datetime.to_datetime(week1_start)
        week2_datetime = fields.Datetime.to_datetime(week2_start)
        
        # Créer le planning de la semaine 1 (comme meeting de type 'planning')
        planning1 = self.env['internship.meeting'].create({
            'name': _('Apprendre sur l\'entreprise'),
            'stage_id': self.id,
            'meeting_type': 'planning',
            'date': week1_datetime,
            'duration': 168.0,  # 7 jours * 24 heures = 168 heures
            'planning_start_date': week1_start,
            'planning_end_date': week1_end,
            'week_number': 1,
            'partner_ids': [(6, 0, partner_ids)],
            'agenda': _(
                '<p><strong>Semaine 1 : Apprendre sur l\'entreprise</strong></p>'
                '<p>Cette première semaine est dédiée à la découverte de l\'entreprise :</p>'
                '<ul>'
                '<li>Présentation de l\'entreprise et de son histoire</li>'
                '<li>Organisation et structure</li>'
                '<li>Culture d\'entreprise et valeurs</li>'
                '<li>Processus et méthodologies utilisées</li>'
                '<li>Rencontre avec les équipes</li>'
                '</ul>'
            ),
            'state': 'scheduled'  # Créer directement en scheduled pour envoyer les emails
        })
        
        # Envoyer les notifications email pour le planning 1
        try:
            planning1._send_meeting_notification('internship_management.mail_template_meeting_invitation')
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi de l'email pour le planning 1 : {str(e)}")
        
        # Créer le planning de la semaine 2 (comme meeting de type 'planning')
        planning2 = self.env['internship.meeting'].create({
            'name': _('Apprendre sur le travail'),
            'stage_id': self.id,
            'meeting_type': 'planning',
            'date': week2_datetime,
            'duration': 168.0,  # 7 jours * 24 heures = 168 heures
            'planning_start_date': week2_start,
            'planning_end_date': week2_end,
            'week_number': 2,
            'partner_ids': [(6, 0, partner_ids)],
            'agenda': _(
                '<p><strong>Semaine 2 : Apprendre sur le travail</strong></p>'
                '<p>Cette deuxième semaine est dédiée à l\'apprentissage du travail :</p>'
                '<ul>'
                '<li>Découverte des outils et technologies utilisés</li>'
                '<li>Formation sur les processus de travail</li>'
                '<li>Prise en main des projets en cours</li>'
                '<li>Intégration dans l\'équipe</li>'
                '<li>Début des premières tâches</li>'
                '</ul>'
            ),
            'state': 'scheduled'  # Créer directement en scheduled pour envoyer les emails
        })
        
        # Envoyer les notifications email pour le planning 2
        try:
            planning2._send_meeting_notification('internship_management.mail_template_meeting_invitation')
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi de l'email pour le planning 2 : {str(e)}")
        
        _logger.info(
            f"Plannings automatiques créés pour le stage {self.reference_number} : "
            f"Semaine 1 ({week1_start} - {week1_end}) et Semaine 2 ({week2_start} - {week2_end})"
        )

    # ===============================
    # MÉTHODES MÉTIER (ACTIONS DES BOUTONS)
    # ===============================

    def action_submit(self):
        """Soumet le stage pour approbation."""
        self.write({'state': 'submitted'})

    def action_approve(self):
        """Approuve le stage."""
        self.write({'state': 'approved'})

    def action_start(self):
        """Démarre le stage."""
        self.write({'state': 'in_progress'})

    def action_complete(self):
        """Marque le stage comme terminé."""
        self.write({'state': 'completed'})

    def action_schedule_defense(self):
        """
        Crée une activité pour l'encadrant afin qu'il planifie la soutenance.
        """
        self.ensure_one()
        if self.state != 'completed':
            raise ValidationError(_("Seuls les stages terminés peuvent avoir une soutenance planifiée."))

        if self.supervisor_id.user_id:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("Planifier la soutenance pour %s", self.title),
                note=_(
                    "Le stage est terminé. Veuillez configurer la date, "
                    "le lieu et les membres du jury dans l'onglet 'Soutenance & Évaluation'."
                ),
                user_id=self.supervisor_id.user_id.id,
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Planification de la Soutenance'),
                'message': _('Une activité a été créée pour que l\'encadrant(e) configure la soutenance.'),
                'type': 'info',
            }
        }

    def action_evaluate(self):
        """Marque le stage comme évalué après vérifications."""
        self.ensure_one()
        if self.state != 'completed':
            raise ValidationError(_("Seuls les stages terminés peuvent être évalués."))

        if not all([self.defense_date, self.jury_member_ids, self.defense_grade, self.final_grade]):
            raise ValidationError(
                _("Date de soutenance, membres du jury et notes doivent être renseignés avant d'évaluer."))

        self.write({'state': 'evaluated', 'defense_status': 'completed'})

        # Notifier les parties prenantes via le Chatter
        partner_ids = []
        # Notifier tous les étudiants du stage
        for student in self.student_ids:
            if student.user_id and student.user_id.partner_id:
                partner_ids.append(student.user_id.partner_id.id)
        if self.supervisor_id.user_id:
            partner_ids.append(self.supervisor_id.user_id.partner_id.id)

        self.message_post(
            body=_(
                "<strong>Évaluation du Stage Terminée</strong><br/>"
                "Note de Soutenance: <strong>%s/20</strong><br/>"
                "Note Finale: <strong>%s/20</strong>",
                self.defense_grade, self.final_grade
            ),
            partner_ids=partner_ids,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

    def action_cancel(self):
        """Annule le stage."""
        if self.state == 'evaluated':
            raise ValidationError(_("Un stage évalué ne peut pas être annulé."))
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """Réinitialise le stage à l'état brouillon."""
        if self.state == 'evaluated':
            raise ValidationError(_("Un stage évalué ne peut pas être réinitialisé."))
        self.write({'state': 'draft'})


    # ===============================
    # ACTIONS D'OUVERTURE DE VUES
    # ===============================

    def action_create_presentation(self):
        """Ouvre le formulaire pour créer une nouvelle présentation."""
        self.ensure_one()
        return {
            'name': _('Téléverser une Présentation - %s', self.title),
            'type': 'ir.actions.act_window',
            'res_model': 'internship.presentation',
            'view_mode': 'form',
            'context': {
                'default_stage_id': self.id,
                'default_supervisor_id': self.supervisor_id.id,
            },
            'target': 'new',
        }

    def action_create_task(self):
        """Ouvre le formulaire pour créer une nouvelle tâche."""
        self.ensure_one()
        return {
            'name': _('Créer une Tâche - %s', self.title),
            'type': 'ir.actions.act_window',
            'res_model': 'internship.todo',
            'view_mode': 'form',
            'view_id': self.env.ref('internship_management.view_internship_todo_form').id,
            'context': {
                'default_stage_id': self.id,
                'default_assigned_to_ids': [(6, 0, self.student_ids.ids)],
            },
            'target': 'new',
        }

    def action_open_tasks(self):
        """Ouvre la liste des tâches de ce stage."""
        self.ensure_one()
        return {
            'name': _('Tâches - %s', self.title),
            'type': 'ir.actions.act_window',
            'res_model': 'internship.todo',
            'view_mode': 'kanban,tree,form',
            'domain': [('stage_id', '=', self.id)],
            'target': 'current',
        }

    def action_schedule_meeting(self):
        """Ouvre le formulaire pour planifier une réunion."""
        self.ensure_one()
        return {
            'name': _('Planifier une Réunion - %s', self.title),
            'type': 'ir.actions.act_window',
            'res_model': 'internship.meeting',
            'view_mode': 'form',
            'context': {
                'default_stage_id': self.id,
                'default_supervisor_id': self.supervisor_id.id,
            },
            'target': 'new',
        }

    # ===============================
    # TÂCHE AUTOMATISÉE (CRON)
    # ===============================

    @api.model
    def _cron_internship_monitoring(self):
        """
        Méthode principale appelée par le Cron pour lancer toutes les détections
        et transformer les problèmes trouvés en Activités.
        """
        _logger.info("CRON: Démarrage du suivi des stages...")

        # 1. Détection des tâches en retard (appel de la méthode dédiée)
        self.env['internship.todo']._cron_detect_overdue_tasks()

        # 2. Détection des stages inactifs
        fourteen_days_ago = fields.Datetime.now() - timedelta(days=14)
        inactive_stages = self.search([
            ('state', '=', 'in_progress'),
            ('write_date', '<', fourteen_days_ago),
            ('activity_ids', '=', False)
        ])

        for stage in inactive_stages:
            if stage.supervisor_id.user_id:
                stage.activity_schedule(
                    'internship_management.activity_type_internship_alert',
                    summary=_("Stage potentiellement inactif : %s", stage.title),
                    note=_(
                        "Aucune modification sur ce stage depuis plus de 14 jours. "
                        "Un suivi est peut-être nécessaire."
                    ),
                    user_id=stage.supervisor_id.user_id.id
                )

        _logger.info("CRON: Suivi des stages terminé.")

    # ===============================
    # MÉTHODES UTILITAIRES
    # ===============================

    def name_get(self):
        """Affichage personnalisé du nom : [Référence] - Titre."""
        result = []
        for stage in self:
            name = f"[{stage.reference_number}] {stage.title}"
            result.append((stage.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        """Recherche personnalisée sur la référence, le titre ou le nom de l'étudiant."""
        args = args or []
        domain = []
        if name:
            domain = ['|', '|',
                      ('title', operator, name),
                      ('reference_number', operator, name),
                      ('student_ids.full_name', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid, order=order)
