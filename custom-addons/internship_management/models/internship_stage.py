# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InternshipStage(models.Model):
    _name = 'internship.stage'
    _description = 'Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, name'

    name = fields.Char(string='Sujet du stage', required=True, tracking=True)
    reference = fields.Char(string='Référence', readonly=True, copy=False, default='Nouveau')

    # Type de stage
    stage_type = fields.Selection([
        ('pfe', 'PFE'),
        ('stage_ete', 'Stage d\'été'),
        ('stage_obs', 'Stage d\'observation')
    ], string='Type de stage', required=True)

    # Relations
    student_id = fields.Many2one('internship.student', string='Stagiaire', tracking=True)
    supervisor_id = fields.Many2one('internship.supervisor', string='Encadrant', tracking=True)
    company_id = fields.Many2one('internship.company', string='Entreprise d\'accueil', required=True, tracking=True)

    # Dates
    start_date = fields.Date(string='Date de début', required=True, tracking=True)
    end_date = fields.Date(string='Date de fin', required=True, tracking=True)
    duration = fields.Integer(string='Durée (jours)', compute='_compute_duration', store=True)

    # Description et objectifs
    description = fields.Text(string='Description', required=True)
    objectives = fields.Text(string='Objectifs')

    # Suivi du stage
    progress = fields.Float(string='Progression (%)', tracking=True)
    next_meeting_date = fields.Datetime(string='Prochaine réunion')
    todo_ids = fields.One2many('internship.todo', 'stage_id', string='Tâches à faire')

    # État du stage
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('evaluated', 'Évalué'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)

    # Documents et soutenance
    document_ids = fields.One2many('internship.document', 'stage_id', string='Documents')
    convention_generated = fields.Boolean(string='Convention générée', default=False)
    defense_date = fields.Datetime(string='Date soutenance')
    jury_ids = fields.Many2many('internship.supervisor', string='Jury')
    defense_room = fields.Char(string='Salle soutenance')
    presentation_uploaded = fields.Boolean(string='Présentation déposée')

    # Évaluation
    grade = fields.Float(string='Note finale', digits=(4, 2))
    defense_grade = fields.Float(string='Note soutenance')
    feedback = fields.Text(string='Commentaire d\'évaluation')

    # Champs techniques
    active = fields.Boolean(default=True, string='Actif')

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for stage in self:
            if stage.start_date and stage.end_date:
                if stage.end_date >= stage.start_date:
                    delta = stage.end_date - stage.start_date
                    stage.duration = delta.days + 1
                else:
                    stage.duration = 0
            else:
                stage.duration = 0

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for stage in self:
            if stage.start_date and stage.end_date and stage.start_date > stage.end_date:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début."))

    @api.model
    def create(self, vals):
        if vals.get('reference', 'Nouveau') == 'Nouveau':
            vals['reference'] = self.env['ir.sequence'].next_by_code('internship.stage') or 'Nouveau'
        return super(InternshipStage, self).create(vals)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_evaluate(self):
        self.write({'state': 'evaluated'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_generate_convention(self):
        self.write({'convention_generated': True})
        return True