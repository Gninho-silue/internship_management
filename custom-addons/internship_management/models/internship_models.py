# -*- coding: utf-8 -*-

from odoo import models, fields


class InternshipSkill(models.Model):
    _name = 'internship.skill'
    _description = 'Compétence'

    name = fields.Char(string='Nom', required=True)
    category = fields.Selection([
        ('technical', 'Technique'),
        ('soft', 'Soft Skills'),
        ('language', 'Langue'),
        ('other', 'Autre')
    ], string='Catégorie', required=True)
    description = fields.Text(string='Description')
    level_required = fields.Selection([
        ('basic', 'Basique'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert')
    ], string='Niveau requis')


class InternshipArea(models.Model):
    _name = 'internship.area'
    _description = 'Domaine d\'expertise'

    name = fields.Char(string='Nom', required=True)
    description = fields.Text(string='Description')
    parent_id = fields.Many2one('internship.area', string='Parent')
    child_ids = fields.One2many('internship.area', 'parent_id', string='Sous-domaines')


class InternshipMeeting(models.Model):
    _name = 'internship.meeting'
    _description = 'Réunion de suivi'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sujet', required=True)
    stage_id = fields.Many2one('internship.stage', string='Stage', required=True)
    date = fields.Datetime(string='Date et heure', required=True)
    duration = fields.Float(string='Durée (heures)')
    type = fields.Selection([
        ('kickoff', 'Kick-off'),
        ('followup', 'Suivi'),
        ('evaluation', 'Évaluation'),
        ('defense', 'Soutenance')
    ], string='Type', required=True)
    attendee_ids = fields.Many2many('res.partner', string='Participants')
    summary = fields.Text(string='Compte-rendu')
    next_actions = fields.Text(string='Actions à suivre')


class InternshipTodo(models.Model):
    _name = 'internship.todo'
    _description = 'Tâches du stage'
    _order = 'sequence, id'

    name = fields.Char(string='Tâche', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    stage_id = fields.Many2one('internship.stage', required=True)
    deadline = fields.Date(string='Échéance')
    state = fields.Selection([
        ('todo', 'À faire'),
        ('in_progress', 'En cours'),
        ('done', 'Terminé')
    ], default='todo')

    assigned_to = fields.Many2one('res.users', string='Assigné à')
    description = fields.Text(string='Description')
    priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Très haute')
    ], default='1', string='Priorité')