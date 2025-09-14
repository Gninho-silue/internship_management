# -*- coding: utf-8 -*-
"""Internship Stage Model"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipStage(models.Model):
    """Internship Stage model for managing internship lifecycle.

    This model handles the complete internship process from application
    to completion, including progress tracking, evaluations, and documentation.
    """
    _name = 'internship.stage'
    _description = 'Internship Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, title'
    _rec_name = 'title'

    # ===============================
    # CORE IDENTIFICATION FIELDS
    # ===============================

    title = fields.Char(
        string='Internship Title',
        required=True,
        tracking=True,
        help="Main subject or title of the internship project"
    )

    reference_number = fields.Char(
        string='Reference Number',
        readonly=True,
        copy=False,
        default='New',
        help="Unique reference number for this internship"
    )

    # ===============================
    # TYPE AND CLASSIFICATION
    # ===============================

    internship_type = fields.Selection([
        ('final_project', 'Final Year Project (PFE)'),
        ('summer_internship', 'Summer Internship'),
        ('observation_internship', 'Observation Internship'),
        ('professional_internship', 'Professional Internship')
    ], string='Internship Type', required=True, tracking=True)



    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    student_id = fields.Many2one(
        'internship.student',
        string='Student',
        tracking=True,
        ondelete='restrict',
        help="Student assigned to this internship"
    )

    supervisor_id = fields.Many2one(
        'internship.supervisor',
        string='Supervisor',
        tracking=True,
        ondelete='restrict',
        help="Academic or professional supervisor"
    )
    
    area_id = fields.Many2one(
        'internship.area',
        string='Area of Expertise',
        help="Area of expertise for this internship"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Host Organization',
        required=True,
        tracking=True,
        default=lambda self: self.env.company,
        help="Organization hosting the internship"
    )

    # ===============================
    # TIMELINE FIELDS
    # ===============================

    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True,
        help="Official start date of the internship"
    )

    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True,
        help="Official end date of the internship"
    )

    @api.depends('start_date', 'end_date')
    def _compute_duration_days(self):
        """Calculate internship duration in days."""
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
        string='Duration (Days)',
        compute='_compute_duration_days',
        store=True,
        help="Total duration of internship in days"
    )

    # ===============================
    # CONTENT FIELDS
    # ===============================

    project_description = fields.Html(
        string='Project Description',
        required=True,
        help="Detailed description of the internship project and context"
    )

    learning_objectives = fields.Html(
        string='Learning Objectives',
        help="Educational and professional objectives to be achieved"
    )

    # ===============================
    # PROGRESS TRACKING
    # ===============================

    @api.depends('task_ids.state', 'start_date', 'end_date', 'state')
    def _compute_completion_percentage(self):
        """Calculate completion percentage based on tasks and timeline."""
        for stage in self:
            if stage.state in ('completed', 'evaluated'):
                stage.completion_percentage = 100.0
                continue
            elif stage.state == 'cancelled':
                stage.completion_percentage = 0.0
                continue

            progress_value = 0.0

            # Calculate based on completed tasks if available
            total_tasks = len(stage.task_ids)
            if total_tasks > 0:
                completed_tasks = len(stage.task_ids.filtered(lambda t: t.state == 'completed'))
                progress_value = (completed_tasks / total_tasks) * 100.0
            else:
                # Fallback: time-based calculation
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

            # Ensure progress is within 0-100 range
            stage.completion_percentage = max(0.0, min(100.0, round(progress_value, 2)))

    completion_percentage = fields.Float(
        string='Completion %',
        compute='_compute_completion_percentage',
        store=True,
        tracking=True,
        help="Overall completion percentage of the internship"
    )

    # ===============================
    # STATE MANAGEMENT
    # ===============================

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('evaluated', 'Evaluated'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    document_ids = fields.One2many(
        'internship.document',
        'stage_id',
        string='Documents',
        help="All documents related to this internship"
    )
    
    
    # ===============================
    # COMMUNICATION INTEGRATION
    # ===============================
    
    communication_ids = fields.One2many(
        'internship.communication',
        'stage_id',
        string='Communications',
        help="All communications related to this internship"
    )
    
    document_feedback_ids = fields.One2many(
        'internship.document.feedback',
        'stage_id',
        string='Document Feedback',
        help="All feedback on documents for this internship"
    )
    
    # ===============================
    # COMMUNICATION STATISTICS
    # ===============================
    
    @api.depends('communication_ids', 'document_feedback_ids')
    def _compute_communication_stats(self):
        for stage in self:
            stage.total_communications = len(stage.communication_ids)
            stage.unread_communications = len(stage.communication_ids.filtered(
                lambda c: c.state == 'sent' and self.env.user in c.recipient_ids
            ))
            stage.pending_feedback = len(stage.document_feedback_ids.filtered(
                lambda f: f.status == 'pending'
            ))
            stage.total_document_feedback = len(stage.document_feedback_ids)

    @api.depends('task_ids', 'task_ids.state')
    def _compute_task_stats(self):
        for stage in self:
            stage.task_count = len(stage.task_ids)
            stage.completed_task_count = len(stage.task_ids.filtered(
                lambda t: t.state == 'done'
            ))
            stage.pending_task_count = len(stage.task_ids.filtered(
                lambda t: t.state in ['todo', 'in_progress']
            ))
    
    total_communications = fields.Integer(
        string='Total Communications',
        compute='_compute_communication_stats',
        store=True
    )
    
    unread_communications = fields.Integer(
        string='Unread Communications',
        compute='_compute_communication_stats',
        store=True
    )
    
    pending_feedback = fields.Integer(
        string='Pending Feedback',
        compute='_compute_communication_stats',
        store=True
    )
    
    total_document_feedback = fields.Integer(
        string='Total Document Feedback',
        compute='_compute_communication_stats',
        store=True
    )

    meeting_ids = fields.One2many(
        'internship.meeting',
        'stage_id',
        string='Meetings',
        help="Meetings scheduled for this internship"
    )

    task_ids = fields.One2many(
        'internship.todo',
        'stage_id',
        string='Tasks',
        help="Tasks and deliverables for this internship"
    )

    # Task statistics
    task_count = fields.Integer(
        string='Total Tasks',
        compute='_compute_task_stats',
        store=True
    )

    completed_task_count = fields.Integer(
        string='Completed Tasks',
        compute='_compute_task_stats',
        store=True
    )

    pending_task_count = fields.Integer(
        string='Pending Tasks',
        compute='_compute_task_stats',
        store=True
    )

    # ===============================
    # EVALUATION FIELDS
    # ===============================

    final_grade = fields.Float(
        string='Final Grade',
        digits=(4, 2),
        help="Final grade for the internship"
    )

    defense_grade = fields.Float(
        string='Defense Grade',
        digits=(4, 2),
        help="Grade from the defense presentation"
    )

    evaluation_feedback = fields.Html(
        string='Evaluation Feedback',
        help="Detailed feedback from supervisor"
    )

    # ===============================
    # DEFENSE MANAGEMENT
    # ===============================

    defense_date = fields.Datetime(
        string='Defense Date',
        help="Scheduled date for defense presentation"
    )

    defense_status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Defense Status', default='scheduled', tracking=True)

    jury_member_ids = fields.Many2many(
        'internship.supervisor',
        string='Jury Members',
        help="Supervisors assigned as jury members"
    )

    # ===============================
    # TECHNICAL FIELDS
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Whether this internship record is active"
    )

    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================

    @api.constrains('start_date', 'end_date')
    def _check_date_consistency(self):
        """Ensure end date is after start date."""
        for stage in self:
            if stage.start_date and stage.end_date:
                if stage.start_date > stage.end_date:
                    raise ValidationError(_("End date must be after start date."))

    @api.constrains('final_grade', 'defense_grade')
    def _check_grade_range(self):
        """Ensure grades are within valid range (0-20)."""
        for stage in self:
            if stage.final_grade and not (0 <= stage.final_grade <= 20):
                raise ValidationError(_("Final grade must be between 0 and 20."))
            if stage.defense_grade and not (0 <= stage.defense_grade <= 20):
                raise ValidationError(_("Defense grade must be between 0 and 20."))

    # ===============================
    # CRUD METHODS
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to generate reference numbers."""
        for vals in vals_list:
            if vals.get('reference_number', 'New') == 'New':
                vals['reference_number'] = self.env['ir.sequence'].next_by_code('internship.stage') or 'STG-NEW'

        stages = super().create(vals_list)

        for stage in stages:
            _logger.info(f"Created internship: {stage.reference_number} - {stage.title}")

            # Create welcome communication for student
            if stage.student_id and stage.student_id.user_id:
                self.env['internship.communication'].create({
                    'subject': f'New Internship Assigned: {stage.title}',
                    'content': f'<p>You have been assigned to internship "{stage.title}". Please review the details.</p>',
                    'communication_type': 'system_notification',
                    'stage_id': stage.id,
                    'sender_id': self.env.user.id,
                    'recipient_ids': [(6, 0, [stage.student_id.user_id.id])],
                    'priority': '1',
                    'state': 'sent'
                })

        return stages

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_submit(self):
        """Submit internship for approval."""
        self.write({'state': 'submitted'})

    def action_approve(self):
        """Approve internship."""
        self.write({'state': 'approved'})

    def action_start(self):
        """Start internship."""
        self.write({'state': 'in_progress'})

    def action_complete(self):
        """Mark internship as completed."""
        self.write({'state': 'completed'})

    def action_evaluate(self):
        """Mark internship as evaluated."""
        self.write({'state': 'evaluated'})

    def action_cancel(self):
        """Cancel internship."""
        if self.state == 'evaluated':
            raise ValidationError(_("Cannot cancel an evaluated internship."))
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """Reset internship to draft state."""
        if self.state == 'evaluated':
            raise ValidationError(_("Cannot reset an evaluated internship to draft."))
        self.write({'state': 'draft'})

    def action_open_communications(self):
        """Open communications for this internship."""
        self.ensure_one()
        return {
            'name': f'Communications - {self.title}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.communication',
            'view_mode': 'kanban,tree,form',
            'domain': [('stage_id', '=', self.id)],
            'context': {
                'default_stage_id': self.id,
                'default_sender_id': self.env.user.id,
            },
            'target': 'current',
        }
    
    def action_open_document_feedback(self):
        """Open document feedback for this internship."""
        self.ensure_one()
        return {
            'name': f'Document Feedback - {self.title}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.document.feedback',
            'view_mode': 'tree,form',
            'domain': [('stage_id', '=', self.id)],
            'context': {
                'default_stage_id': self.id,
                'default_reviewer_id': self.env.user.id,
            },
            'target': 'current',
        }


    # ===============================
    # UTILITY METHODS
    # ===============================

    def name_get(self):
        """Custom name display: Reference - Title."""
        result = []
        for stage in self:
            name = f"{stage.reference_number} - {stage.title}"
            result.append((stage.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        """Custom search: search by reference, title, or student name."""
        args = args or []
        domain = []

        if name:
            domain = ['|', '|', '|',
                      ('title', operator, name),
                      ('reference_number', operator, name),
                      ('student_id.full_name', operator, name),
                      ('project_description', operator, name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid, order=order)

    def action_create_task(self):
        """Open form to create a new task for this internship."""
        self.ensure_one()
        return {
            'name': f'Create Task - {self.title}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.todo',
            'view_mode': 'form',
            'view_id': self.env.ref('internship_management.view_internship_todo_form').id,
            'context': {
                'default_stage_id': self.id,
                'default_assigned_to': self.student_id.id if self.student_id else False,
            },
            'target': 'new',
        }

    def action_open_tasks(self):
        """Open tasks for this internship."""
        self.ensure_one()
        return {
            'name': f'Tasks - {self.title}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.todo',
            'view_mode': 'kanban,tree,form',
            'domain': [('stage_id', '=', self.id)],
            'context': {
                'default_stage_id': self.id,
                'default_assigned_to': self.student_id.id if self.student_id else False,
            },
            'target': 'current',
        }
