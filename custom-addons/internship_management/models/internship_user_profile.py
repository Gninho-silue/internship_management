ls# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InternshipUserProfile(models.Model):
    _name = 'internship.user.profile'
    _description = 'Profil utilisateur avancé'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Informations de base
    user_id = fields.Many2one('res.users', string='Utilisateur', required=True, ondelete='cascade')
    profile_type = fields.Selection([
        ('student', 'Étudiant'),
        ('supervisor', 'Encadrant'),
        ('company', 'Entreprise'),
        ('admin', 'Administrateur')
    ], string='Type de profil', required=True)

    # Informations personnelles avancées
    avatar = fields.Binary(string='Photo de profil')
    bio = fields.Text(string='Biographie')
    skills = fields.Many2many('internship.skill', string='Compétences')
    languages = fields.Many2many('internship.language', string='Langues')
    
    # Informations de contact
    phone_mobile = fields.Char(string='Téléphone mobile')
    phone_work = fields.Char(string='Téléphone travail')
    address = fields.Text(string='Adresse')
    city = fields.Char(string='Ville')
    country_id = fields.Many2one('res.country', string='Pays')
    
    # Informations professionnelles
    company_id = fields.Many2one('res.company', string='Entreprise')
    department = fields.Char(string='Département')
    position = fields.Char(string='Poste')
    experience_years = fields.Integer(string='Années d\'expérience')
    
    # Informations académiques
    education_level = fields.Selection([
        ('bac', 'Baccalauréat'),
        ('bac+2', 'Bac+2'),
        ('bac+3', 'Bac+3'),
        ('bac+4', 'Bac+4'),
        ('bac+5', 'Bac+5'),
        ('doctorat', 'Doctorat')
    ], string='Niveau d\'éducation')
    school = fields.Char(string='École/Université')
    graduation_year = fields.Integer(string='Année de diplôme')
    
    # Préférences
    notification_preferences = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Notifications push'),
        ('all', 'Toutes')
    ], string='Préférences de notification', default='email')
    
    # Statut
    is_active = fields.Boolean(string='Profil actif', default=True)
    last_login = fields.Datetime(string='Dernière connexion', readonly=True)
    login_count = fields.Integer(string='Nombre de connexions', readonly=True)

    # Contraintes
    @api.constrains('user_id', 'profile_type')
    def _check_unique_profile_per_user(self):
        for profile in self:
            existing = self.search([
                ('user_id', '=', profile.user_id.id),
                ('profile_type', '=', profile.profile_type),
                ('id', '!=', profile.id)
            ])
            if existing:
                raise ValidationError(_("Un utilisateur ne peut avoir qu'un seul profil par type."))

    # Méthodes
    def action_update_last_login(self):
        """Mettre à jour les statistiques de connexion"""
        self.write({
            'last_login': fields.Datetime.now(),
            'login_count': self.login_count + 1
        })

    def get_full_name(self):
        """Retourner le nom complet avec le type de profil"""
        return f"{self.user_id.name} ({self.profile_type})"
