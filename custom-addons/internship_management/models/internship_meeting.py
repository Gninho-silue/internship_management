# -*- coding: utf-8 -*-
"""
Modèle pour la gestion des réunions de stage.
Ce modèle centralise la planification, le suivi et la gestion des réunions
liées aux stages (lancement, suivi, soutenance, etc.).
"""

import logging
import re
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class InternshipMeeting(models.Model):
    """
    Modèle de Réunion pour le système de gestion des stages.

    Ce modèle gère la planification, la gestion et le suivi des réunions
    pour les stages.

    Optimisations principales :
    - Remplacement de la gestion manuelle des participants (via internship.meeting.attendee)
      par un champ standard `partner_ids` (res.partner) pour une meilleure intégration.
    - Suppression des champs de suivi d'e-mail (`email_sent`, `reminder_sent`) au profit
      du Chatter et des Activités Odoo.
    - Utilisation des modèles d'e-mail (`mail.template`) pour les notifications,
      au lieu de générer du HTML manuellement dans le code Python.
    - Simplification de la logique de création avec un onchange pour suggérer les participants.
    """
    _name = 'internship.meeting'
    _description = 'Gestion des Réunions de Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name'
    _rec_name = 'name'

    # ===============================
    # CHAMPS PRINCIPAUX
    # ===============================

    name = fields.Char(
        string='Titre de la réunion',
        required=True,
        tracking=True,
        help="Titre ou sujet de la réunion."
    )

    meeting_type = fields.Selection([
        ('kickoff', 'Lancement'),
        ('follow_up', 'Suivi'),
        ('milestone', 'Revue d\'étape'),
        ('defense', 'Soutenance'),
        ('evaluation', 'Évaluation'),
        ('emergency', 'Urgence'),
        ('planning', 'Planning'),
        ('other', 'Autre')
    ], string='Type de réunion', default='follow_up', tracking=True, required=True,
        help="Type de réunion planifiée.")

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('scheduled', 'Planifiée'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
    ], string='Statut', default='draft', tracking=True, required=True, copy=False,
        help="Statut actuel de la réunion.")

    # ===============================
    # CHAMPS DE RELATION
    # ===============================

    stage_id = fields.Many2one(
        'internship.stage',
        string='Stage Associé',
        required=True,  # OPTIMISATION: Une réunion doit toujours être liée à un stage
        tracking=True,
        ondelete='cascade',
        help="Stage auquel cette réunion est liée."
    )

    student_ids = fields.Many2many(
        'internship.student',
        related='stage_id.student_ids',
        readonly=True,
        string="ÉtudiantS"
    )

    supervisor_id = fields.Many2one(
        related='stage_id.supervisor_id',
        store=True,
        readonly=True,
        string="Encadrant(e)"
    )

    organizer_id = fields.Many2one(
        'res.users',
        string='Organisateur',
        default=lambda self: self.env.user,
        tracking=True,
        required=True,
        help="Utilisateur qui a organisé cette réunion."
    )

    # OPTIMISATION: Remplacement de 'participant_ids' et 'attendee_ids' par un seul champ standard
    # pointant vers 'res.partner' pour une intégration parfaite avec le calendrier et les e-mails d'Odoo.
    partner_ids = fields.Many2many(
        'res.partner',
        'internship_meeting_partner_rel',  # relation (table intermédiaire)
        'meeting_id',                      # column1
        'partner_id',                      # column2
        string='Participants',
        tracking=True,
        help="Personnes qui doivent assister à cette réunion."
    )

    # ===============================
    # CHAMPS DE PLANIFICATION
    # ===============================

    date = fields.Datetime(
        string='Date et Heure',
        required=True,
        tracking=True,
        help="Date et heure prévues pour la réunion."
    )

    duration = fields.Float(
        string='Durée (Heures)',
        default=1.0,
        tracking=True,
        help="Durée prévue de la réunion en heures."
    )

    # OPTIMISATION: Renommé de 'end_date' à 'stop_date' pour correspondre aux conventions du calendrier Odoo
    @api.depends('date', 'duration')
    def _compute_stop_date(self):
        """Calcule l'heure de fin de la réunion."""
        for meeting in self:
            if meeting.date and meeting.duration:
                meeting.stop_date = meeting.date + timedelta(hours=meeting.duration)
            else:
                meeting.stop_date = meeting.date

    stop_date = fields.Datetime(
        string='Heure de fin',
        compute='_compute_stop_date',
        store=True,
        help="Heure de fin calculée de la réunion."
    )

    # ===============================
    # CHAMPS POUR LES PLANNINGS (Périodes)
    # ===============================

    is_planning = fields.Boolean(
        string='Est un Planning',
        compute='_compute_is_planning',
        store=True,
        help="Indique si cette entrée est un planning (période) plutôt qu'une réunion ponctuelle."
    )

    @api.depends('meeting_type')
    def _compute_is_planning(self):
        """Détermine si c'est un planning basé sur le type."""
        for meeting in self:
            meeting.is_planning = meeting.meeting_type == 'planning'

    planning_start_date = fields.Date(
        string='Date de Début (Planning)',
        help="Date de début pour les plannings (périodes). Utilisé uniquement si le type est 'Planning'."
    )

    planning_end_date = fields.Date(
        string='Date de Fin (Planning)',
        help="Date de fin pour les plannings (périodes). Utilisé uniquement si le type est 'Planning'."
    )

    week_number = fields.Integer(
        string='Numéro de Semaine',
        help="Numéro de la semaine pour les plannings (1 ou 2)."
    )

    # ===============================
    # CHAMPS DE MODALITÉ
    # ===============================

    location = fields.Char(
        string='Lieu',
        tracking=True,
        help="Lieu physique de la réunion."
    )

    meeting_url = fields.Char(
        string='URL de la réunion',
        help="URL pour les réunions virtuelles (Zoom, Teams, etc.)."
    )

    # NOTE: Ce champ n'est pas strictement nécessaire si location/meeting_url est utilisé,
    # mais conservé pour le filtrage.
    meeting_modality = fields.Selection([
        ('physical', 'En Présentiel'),
        ('virtual', 'En Ligne'),
    ], string='Modalité', default='virtual', tracking=True,
        help="Comment la réunion se déroulera.")

    # ===============================
    # CHAMPS DE CONTENU
    # ===============================

    agenda = fields.Html(
        string='Ordre du jour',
        help="Ordre du jour et sujets à discuter."
    )

    summary = fields.Html(
        string='Compte-rendu',
        help="Résumé de ce qui a été discuté lors de la réunion."
    )

    # ===============================
    # CHAMPS TECHNIQUES
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Actif',
        help="Indique si cet enregistrement est actif."
    )

    # ===============================
    # CONTRAINTES
    # ===============================

    @api.constrains('date')
    def _check_meeting_date(self):
        """Vérifie que la date de la réunion est dans le futur pour les brouillons."""
        for meeting in self:
            if meeting.state == 'draft' and meeting.date and meeting.date < fields.Datetime.now():
                raise ValidationError(_("La date de la réunion doit être dans le futur."))

    @api.constrains('duration')
    def _check_duration(self):
        """Vérifie que la durée est positive."""
        for meeting in self:
            if meeting.duration <= 0:
                raise ValidationError(_("La durée de la réunion doit être positive."))

    @api.constrains('stage_id')
    def _check_students(self):
        """Vérifie qu'une réunion a au moins un étudiant via le stage."""
        for meeting in self:
            if meeting.stage_id and not meeting.stage_id.student_ids:
                raise ValidationError("Une réunion doit être associée à un stage avec au moins un étudiant.")

    # ===============================
    # ONCHANGE
    # ===============================

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """
        OPTIMISATION: Suggère automatiquement les participants (étudiant, encadrant)
        et l'organisateur lors de la sélection d'un stage.
        """
        if not self.stage_id:
            self.partner_ids = False
            return

        partners = self.env['res.partner']

        # Récupération des partenaires des étudiants
        student_partners = self.stage_id.student_ids.mapped('user_id.partner_id')
        if student_partners:
            partners |= student_partners

        # Récupération du partenaire de l'encadrant
        supervisor_partner = self.stage_id.supervisor_id.user_id.partner_id
        if supervisor_partner:
            partners |= supervisor_partner

        # Ajout de l'organisateur s'il existe déjà
        if self.organizer_id.partner_id:
            partners |= self.organizer_id.partner_id

        self.partner_ids = partners

    # ===============================
    # MÉTHODES D'ENVOI D'EMAILS
    # ===============================

    def _prepare_meeting_email_data(self):
        """
        Prépare toutes les données pour l'email de meeting en Python.
        Retourne un dictionnaire avec toutes les valeurs formatées.
        """
        self.ensure_one()
        
        # Formater la date
        date_str = ''
        if self.date:
            # Format: "lundi 19 novembre 2025 à 14:30"
            date_str = self.date.strftime('%A %d %B %Y à %H:%M')
            # Traduire le jour de la semaine (optionnel, pour français)
            days_fr = {
                'Monday': 'lundi', 'Tuesday': 'mardi', 'Wednesday': 'mercredi',
                'Thursday': 'jeudi', 'Friday': 'vendredi', 'Saturday': 'samedi', 'Sunday': 'dimanche'
            }
            months_fr = {
                'January': 'janvier', 'February': 'février', 'March': 'mars',
                'April': 'avril', 'May': 'mai', 'June': 'juin',
                'July': 'juillet', 'August': 'août', 'September': 'septembre',
                'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
            }
            for en, fr in days_fr.items():
                date_str = date_str.replace(en, fr)
            for en, fr in months_fr.items():
                date_str = date_str.replace(en, fr)
        
        # Formater la date courte pour le sujet
        date_short = ''
        if self.date:
            date_short = self.date.strftime('%d/%m/%Y à %H:%M')
        
        # Récupérer le libellé du type de réunion
        meeting_type_label = 'Réunion'
        if self.meeting_type:
            selection = dict(self._fields['meeting_type'].selection)
            meeting_type_label = selection.get(self.meeting_type, self.meeting_type)
        
        data = {
            'name': self.name or 'Réunion',
            'date': date_str,
            'date_short': date_short,
            'duration': f'{self.duration:.2f}' if self.duration else '0.00',
            'organizer_name': self.organizer_id.name if self.organizer_id else 'Organisateur',
            'organizer_email': self.organizer_id.email_formatted if self.organizer_id else '',
            'company_name': self.organizer_id.company_id.name if self.organizer_id and self.organizer_id.company_id else '',
            'location': self.location or '',
            'meeting_url': self.meeting_url or '',
            'agenda': self.agenda or '',
            'meeting_type': meeting_type_label,
        }
        
        return data
    
    def _render_meeting_template(self, template, data):
        """
        Rend le template email de meeting avec les données préparées.
        Remplace les variables {{ }} par les valeurs réelles.
        """
        # Rendre le sujet
        subject = re.sub(r'\{\{\s*object\.name\s*\}\}', data['name'], template.subject)
        subject = re.sub(r'\{\{\s*object\.date\.strftime\([^)]+\)\s*\}\}', data['date_short'], subject)
        # Nettoyer le sujet : supprimer les retours à la ligne et les espaces en début/fin
        subject = re.sub(r'[\r\n]+', ' ', subject)  # Remplacer les retours à la ligne par des espaces
        subject = subject.strip()  # Supprimer les espaces en début/fin
        
        # Rendre le corps HTML
        body_html = template.body_html
        
        # Remplacer les variables simples
        body_html = re.sub(r'\{\{\s*object\.name\s*\}\}', data['name'], body_html)
        body_html = re.sub(r'\{\{\s*object\.organizer_id\.name\s*\}\}', data['organizer_name'], body_html)
        body_html = re.sub(r'\{\{\s*object\.location\s*\}\}', data['location'], body_html)
        body_html = re.sub(r'\{\{\s*object\.meeting_url\s*\}\}', data['meeting_url'], body_html)
        body_html = re.sub(r'\{\{\s*object\.agenda\s*\}\}', data['agenda'], body_html)
        
        # Remplacer la date formatée
        body_html = re.sub(
            r'\{\{\s*object\.date\.strftime\([^)]+\)\s*\}\}',
            data['date'],
            body_html
        )
        
        # Remplacer la durée (format: {{ '%.2f' % object.duration }} heures)
        # On remplace toute l'expression par la durée déjà formatée
        body_html = re.sub(
            r'\{\{\s*[\'"]%.2f[\'"]\s*%\s*object\.duration\s*\}\}',
            data['duration'],
            body_html
        )
        
        # Gérer les conditions t-if pour location
        if data['location']:
            body_html = re.sub(r't-if="object\.location"\s+', '', body_html)
        else:
            body_html = re.sub(
                r'<li t-if="object\.location"[^>]*>.*?</li>',
                '',
                body_html,
                flags=re.DOTALL
            )
        
        # Gérer les conditions t-if pour meeting_url
        if data['meeting_url']:
            body_html = re.sub(r't-if="object\.meeting_url"\s+', '', body_html)
            # Remplacer le lien
            body_html = re.sub(
                r'<a\s+t-att-href="object\.meeting_url"[^>]*>.*?</a>',
                f'<a href="{data["meeting_url"]}">{data["meeting_url"]}</a>',
                body_html,
                flags=re.DOTALL
            )
        else:
            body_html = re.sub(
                r'<li t-if="object\.meeting_url"[^>]*>.*?</li>',
                '',
                body_html,
                flags=re.DOTALL
            )
        
        # Gérer les conditions t-if pour agenda
        if data['agenda']:
            body_html = re.sub(r't-if="object\.agenda"\s+', '', body_html)
        else:
            body_html = re.sub(
                r'<div t-if="object\.agenda"[^>]*>.*?</div>',
                '',
                body_html,
                flags=re.DOTALL
            )
        
        # Rendre email_from
        email_from = self.env.user.email_formatted
        if template.email_from:
            email_from = re.sub(
                r'\{\{\s*object\.organizer_id\.company_id\.name\s*\}\}',
                data['company_name'],
                template.email_from
            )
            email_from = re.sub(
                r'\{\{\s*object\.organizer_id\.email_formatted[^}]*\}\}',
                data['organizer_email'],
                email_from
            )
            email_from = re.sub(
                r'\{\{\s*user\.email_formatted\s*\}\}',
                self.env.user.email_formatted,
                email_from
            )
            # Nettoyer email_from : supprimer les retours à la ligne et les espaces en début/fin
            email_from = re.sub(r'[\r\n]+', ' ', email_from)  # Remplacer les retours à la ligne par des espaces
            email_from = email_from.strip()  # Supprimer les espaces en début/fin
        
        return subject, body_html, email_from
    
    def _send_meeting_notification(self, template_xmlid):
        """
        Envoie les notifications email pour une réunion en utilisant le template spécifié.
        Prépare les données en Python et rend le template manuellement.
        """
        self.ensure_one()
        
        if not self.partner_ids:
            _logger.warning(f"Aucun participant pour envoyer l'email de la réunion {self.name}")
            return
        
        # Récupérer le template email
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        
        if not template:
            _logger.warning(f"Template email {template_xmlid} non trouvé.")
            return
        
        try:
            # Préparer toutes les données en Python
            email_data = self._prepare_meeting_email_data()
            
            # Rendre le template avec les données préparées
            subject, body_html, email_from = self._render_meeting_template(template, email_data)
            
            # Pour chaque partenaire, créer et envoyer un email
            for partner in self.partner_ids:
                if not partner.email:
                    _logger.warning(f"Le partenaire {partner.name} (ID: {partner.id}) n'a pas d'email configuré.")
                    continue
                
                # Créer le mail avec le contenu rendu
                mail = self.env['mail.mail'].create({
                    'subject': subject,
                    'body_html': body_html,
                    'email_from': email_from,
                    'email_to': partner.email,
                    'model': self._name,
                    'res_id': self.id,
                    'auto_delete': template.auto_delete,
                })
                
                # Envoyer immédiatement
                mail.send()
            
            _logger.info(f"Notifications email envoyées pour la réunion {self.name}")
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi des emails pour la réunion {self.name}: {str(e)}")
            import traceback
            _logger.error(traceback.format_exc())
            # Ne pas bloquer si l'envoi d'email échoue

    # ===============================
    # MÉTHODES D'ACTION (WORKFLOW)
    # ===============================

    def action_schedule(self):
        """Passe la réunion à l'état 'Planifiée' et envoie les invitations."""
        self.ensure_one()
        if not self.partner_ids:
            raise UserError(_("Veuillez ajouter au moins un participant avant de planifier la réunion."))

        self.write({'state': 'scheduled'})
        # Envoyer les invitations avec rendu manuel du template
        self._send_meeting_notification('internship_management.mail_template_meeting_invitation')

    def action_complete(self):
        """Passe la réunion à l'état 'Terminée'."""
        self.write({'state': 'completed'})

    def action_cancel(self):
        """Passe la réunion à l'état 'Annulée' et envoie une notification."""
        self.write({'state': 'cancelled'})
        # Envoyer les notifications d'annulation avec rendu manuel du template
        self._send_meeting_notification('internship_management.mail_template_meeting_cancellation')

    def action_reset_to_draft(self):
        """Réinitialise la réunion à l'état 'Brouillon'."""
        self.write({'state': 'draft'})

    # ===============================
    # MÉTHODES D'AFFICHAGE
    # ===============================

    def name_get(self):
        result = []
        for record in self:
            date_str = fields.Date.to_string(record.date) if record.date else ''
            students = ', '.join(record.student_ids.mapped('full_name'))
            name = f"{date_str} - {students}" if students else date_str
            if record.name:
                name = f"{name} ({record.name})"
            result.append((record.id, name))
        return result

