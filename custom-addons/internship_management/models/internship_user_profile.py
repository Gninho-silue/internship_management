# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InternshipLanguage(models.Model):
    """Language proficiency model for international internships."""
    _name = 'internship.language'
    _description = 'Language Proficiency'
    _order = 'name'

    name = fields.Char(
        string='Language',
        required=True,
        help="Language name (e.g., English, French, Arabic)"
    )

    code = fields.Char(
        string='Language Code',
        size=5,
        help="ISO language code (e.g., en, fr, ar)"
    )

    active = fields.Boolean(default=True)


class InternshipUserProfile(models.Model):
    """Advanced user profile for internship management system."""
    _name = 'internship.user.profile'
    _description = 'Advanced User Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Information
    user_id = fields.Many2one(
        'res.users',
        string='User Account',
        required=True,
        ondelete='cascade'
    )

    profile_type = fields.Selection([
        ('student', 'Student'),
        ('supervisor', 'Supervisor'),
        ('company', 'Company Representative'),
        ('admin', 'Administrator')
    ], string='Profile Type', required=True)

    # Personal Information
    avatar = fields.Binary(string='Profile Photo')
    bio = fields.Text(string='Biography')
    skills = fields.Many2many('internship.skill', string='Skills')
    languages = fields.Many2many('internship.language', string='Languages')

    # Contact Information
    phone_mobile = fields.Char(string='Mobile Phone')
    phone_work = fields.Char(string='Work Phone')
    address = fields.Text(string='Address')
    city = fields.Char(string='City')
    country_id = fields.Many2one('res.country', string='Country')

    # Professional Information
    company_id = fields.Many2one('res.company', string='Company')
    department = fields.Char(string='Department')
    position = fields.Char(string='Position')
    experience_years = fields.Integer(string='Years of Experience')

    # Academic Information
    education_level = fields.Selection([
        ('high_school', 'High School'),
        ('bachelor_1', 'Bachelor Year 1'),
        ('bachelor_2', 'Bachelor Year 2'),
        ('bachelor_3', 'Bachelor Year 3'),
        ('master_1', 'Master Year 1'),
        ('master_2', 'Master Year 2'),
        ('phd', 'PhD')
    ], string='Education Level')

    school = fields.Char(string='School/University')
    graduation_year = fields.Integer(string='Graduation Year')

    # Preferences
    notification_preferences = fields.Selection([
        ('email', 'Email Only'),
        ('sms', 'SMS Only'),
        ('push', 'Push Notifications'),
        ('all', 'All Notifications')
    ], string='Notification Preferences', default='email')

    # Status
    is_active = fields.Boolean(string='Profile Active', default=True)
    last_login = fields.Datetime(string='Last Login', readonly=True)
    login_count = fields.Integer(string='Login Count', readonly=True)

    # Constraints
    @api.constrains('user_id', 'profile_type')
    def _check_unique_profile_per_user(self):
        """Ensure one profile per user per type."""
        for profile in self:
            existing = self.search([
                ('user_id', '=', profile.user_id.id),
                ('profile_type', '=', profile.profile_type),
                ('id', '!=', profile.id)
            ])
            if existing:
                raise ValidationError(_("A user can only have one profile per type."))

    # Methods
    def action_update_last_login(self):
        """Update login statistics."""
        self.write({
            'last_login': fields.Datetime.now(),
            'login_count': self.login_count + 1
        })

    def get_full_name(self):
        """Return full name with profile type."""
        return f"{self.user_id.name} ({dict(self._fields['profile_type'].selection).get(self.profile_type)})"