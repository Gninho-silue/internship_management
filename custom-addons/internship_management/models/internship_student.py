# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InternshipStudent(models.Model):
    _name = 'internship.student'
    _description = 'Stagiaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Information personnelles
    name = fields.Char(string='Nom complet', required=True, tracking=True, size=100)
    user_id = fields.Many2one('res.users', string='Utilisateur associé', ondelete='restrict')
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Téléphone', size=20)
    birth_date = fields.Date(string='Date de naissance')
    linkedin_profile = fields.Char(string='Profil LinkedIn')
    cv = fields.Binary(string='CV', attachment=True)

    # Informations académiques
    school = fields.Char(string='École/Université', required=True, size=100)
    study_level = fields.Selection([
        ('bac+1', 'Bac+1'),
        ('bac+2', 'Bac+2'),
        ('bac+3', 'Bac+3'),
        ('bac+4', 'Bac+4'),
        ('bac+5', 'Bac+5'),
        ('doctorat', 'Doctorat')
    ], string='Niveau d\'études', required=True)
    speciality = fields.Char(string='Spécialité', required=True, size=100)
    student_number = fields.Char(string='Numéro étudiant', size=20)
    expected_graduation = fields.Date(string='Date diplôme prévue')

    # Relations
    stage_ids = fields.One2many('internship.stage', 'student_id', string='Stages')
    skill_ids = fields.Many2many('internship.skill', string='Compétences')
    interest_areas = fields.Many2many('internship.area', string='Domaines d\'intérêt')
    document_ids = fields.One2many('internship.document', 'student_id', string='Documents')

    # Champs calculés
    stage_count = fields.Integer(compute='_compute_stage_count', string='Nombre de stages', store=True)
    average_grade = fields.Float(string='Note moyenne stages', compute='_compute_average_grade')
    completion_rate = fields.Float(string='Taux de complétion', compute='_compute_completion_rate')

    # Champs techniques
    image = fields.Binary(string='Photo', attachment=True)
    active = fields.Boolean(default=True, string='Actif')

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for student in self:
            student.stage_count = len(student.stage_ids)

    @api.depends('stage_ids.grade')
    def _compute_average_grade(self):
        for student in self:
            grades = student.stage_ids.filtered(lambda s: s.grade > 0).mapped('grade')
            student.average_grade = sum(grades) / len(grades) if grades else 0

    @api.depends('stage_ids.progress')
    def _compute_completion_rate(self):
        for student in self:
            stages = student.stage_ids.filtered(lambda s: s.state != 'cancelled')
            if stages:
                student.completion_rate = sum(stages.mapped('progress')) / len(stages)
            else:
                student.completion_rate = 0

    @api.constrains('email')
    def _check_email(self):
        for student in self:
            if student.email:
                if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", student.email):
                    raise ValidationError(_("L'adresse email n'est pas valide."))

    @api.constrains('phone')
    def _check_phone(self):
        for student in self:
            if student.phone and not re.match(r"^\+?[\d\s-]{8,20}$", student.phone):
                raise ValidationError(_("Le numéro de téléphone n'est pas valide."))

    _sql_constraints = [
        ('unique_email', 'UNIQUE(email)', 'Cette adresse email est déjà utilisée.'),
        ('unique_user_id', 'UNIQUE(user_id)', 'Cet utilisateur est déjà associé à un autre stagiaire.'),
    ]
