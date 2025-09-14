# -*- coding: utf-8 -*-
"""Internship Auxiliary Models"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipSkill(models.Model):
    """Skill model for internship management system.

    This model manages technical and soft skills that can be associated
    with students, supervisors, and internship requirements.

    Key Features:
    - Skill categorization (technical, soft, language, other)
    - Difficulty level management
    - Certification tracking
    - Prerequisite skill relationships
    - Integration with student profiles and internship areas
    """
    _name = 'internship.skill'
    _description = 'Internship Skill Management'
    _order = 'category, name'
    _rec_name = 'name'

    # ===============================
    # CORE IDENTIFICATION FIELDS
    # ===============================

    name = fields.Char(
        string='Skill Name',
        required=True,
        size=100,
        help="Name of the skill (e.g., Python, Communication, English)"
    )

    code = fields.Char(
        string='Skill Code',
        size=20,
        help="Short code for the skill (e.g., PYTHON, COMM, ENG)"
    )

    # ===============================
    # CLASSIFICATION FIELDS
    # ===============================

    category = fields.Selection([
        ('technical', 'Technical Skills'),
        ('soft', 'Soft Skills'),
        ('language', 'Languages'),
        ('certification', 'Certifications'),
        ('other', 'Other')
    ], string='Category', required=True,
       help="Category this skill belongs to")

    subcategory = fields.Char(
        string='Subcategory',
        size=50,
        help="More specific classification within the category"
    )

    level_required = fields.Selection([
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert')
    ], string='Required Level', default='intermediate',
       help="Minimum proficiency level required")

    difficulty_level = fields.Selection([
        ('1', 'Very Easy'),
        ('2', 'Easy'),
        ('3', 'Medium'),
        ('4', 'Hard'),
        ('5', 'Very Hard')
    ], string='Difficulty Level', default='3',
       help="Difficulty level of acquiring this skill")

    # ===============================
    # CERTIFICATION FIELDS
    # ===============================

    is_certification = fields.Boolean(
        string='Is Certification',
        default=False,
        help="Whether this skill requires certification"
    )

    certification_provider = fields.Char(
        string='Certification Provider',
        help="Organization that provides the certification"
    )

    certification_validity_months = fields.Integer(
        string='Certification Validity (Months)',
        help="How long the certification remains valid"
    )

    # ===============================
    # DESCRIPTION AND METADATA
    # ===============================

    description = fields.Text(
        string='Description',
        help="Detailed description of the skill and its applications"
    )

    learning_objectives = fields.Html(
        string='Learning Objectives',
        help="What students should achieve when learning this skill"
    )

    prerequisites = fields.Text(
        string='Prerequisites',
        help="Skills or knowledge required before learning this skill"
    )

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    prerequisite_skill_ids = fields.Many2many(
        'internship.skill',
        'skill_prerequisite_rel',
        'skill_id', 'prerequisite_id',
        string='Prerequisite Skills',
        help="Skills that must be mastered before this one"
    )

    related_area_ids = fields.Many2many(
        'internship.area',
        string='Related Areas',
        help="Areas of expertise where this skill is commonly used"
    )

    # ===============================
    # TECHNICAL FIELDS
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Whether this skill is currently available"
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order of skills in lists"
    )

    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================

    @api.constrains('certification_validity_months')
    def _check_certification_validity(self):
        """Ensure certification validity is positive."""
        for skill in self:
            if skill.is_certification and skill.certification_validity_months <= 0:
                raise ValidationError(_("Certification validity must be positive."))

    @api.constrains('prerequisite_skill_ids')
    def _check_no_circular_prerequisites(self):
        """Prevent circular prerequisite relationships."""
        for skill in self:
            if skill in skill.prerequisite_skill_ids:
                raise ValidationError(_("A skill cannot be a prerequisite of itself."))

    _sql_constraints = [
        ('unique_skill_name', 'UNIQUE(name)',
         'A skill with this name already exists.'),
        ('unique_skill_code', 'UNIQUE(code)',
         'A skill with this code already exists.'),
    ]

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_view_related_areas(self):
        """Open related areas in a dedicated view."""
        self.ensure_one()
        return {
            'name': f'Areas Using {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.area',
            'view_mode': 'tree,form',
            'domain': [('skill_ids', 'in', [self.id])],
            'target': 'current',
        }

    def get_skill_statistics(self):
        """Return statistical data for this skill."""
        self.ensure_one()
        return {
            'related_areas_count': len(self.related_area_ids),
            'prerequisite_count': len(self.prerequisite_skill_ids),
            'is_certification': self.is_certification,
            'difficulty_level': self.difficulty_level,
        }


class InternshipArea(models.Model):
    """Area of expertise model for internship management.

    This model manages different areas of expertise where internships
    can be conducted, helping to categorize and organize internship
    opportunities.

    Key Features:
    - Hierarchical area structure (parent/child relationships)
    - Skill associations
    - Supervisor expertise mapping
    - Internship categorization
    - Search and filtering capabilities
    """
    _name = 'internship.area'
    _description = 'Internship Area of Expertise'
    _order = 'parent_id, sequence, name'
    _rec_name = 'name'

    # ===============================
    # CORE IDENTIFICATION FIELDS
    # ===============================

    name = fields.Char(
        string='Area Name',
        required=True,
        size=100,
        help="Name of the expertise area (e.g., Software Development, Marketing)"
    )

    code = fields.Char(
        string='Area Code',
        size=20,
        help="Short code for the area (e.g., SWDEV, MKTG)"
    )

    # ===============================
    # HIERARCHICAL STRUCTURE
    # ===============================

    parent_id = fields.Many2one(
        'internship.area',
        string='Parent Area',
        ondelete='cascade',
        help="Parent area in the hierarchy"
    )

    child_ids = fields.One2many(
        'internship.area',
        'parent_id',
        string='Sub-areas',
        help="Child areas under this one"
    )

    level = fields.Integer(
        string='Level',
        compute='_compute_level',
        recursive=True,
        store=True,
        help="Hierarchy level (0 for root areas)"
    )

    # ===============================
    # DESCRIPTION AND METADATA
    # ===============================

    description = fields.Html(
        string='Description',
        help="Detailed description of this area of expertise"
    )

    objectives = fields.Html(
        string='Learning Objectives',
        help="What students can learn in this area"
    )

    career_paths = fields.Html(
        string='Career Paths',
        help="Career opportunities in this area"
    )

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    skill_ids = fields.Many2many(
        'internship.skill',
        string='Required Skills',
        help="Skills commonly needed in this area"
    )

    supervisor_ids = fields.Many2many(
        'internship.supervisor',
        string='Expert Supervisors',
        help="Supervisors with expertise in this area"
    )

    internship_ids = fields.One2many(
        'internship.stage',
        'area_id',
        string='Internships',
        help="Internships conducted in this area"
    )

    # ===============================
    # COMPUTED FIELDS
    # ===============================

    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        """Calculate hierarchy level."""
        for area in self:
            level = 0
            parent = area.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            area.level = level

    @api.depends('internship_ids')
    def _compute_internship_count(self):
        """Calculate number of internships in this area."""
        for area in self:
            area.internship_count = len(area.internship_ids)

    internship_count = fields.Integer(
        string='Internship Count',
        compute='_compute_internship_count',
        store=True,
        help="Number of internships in this area"
    )

    # ===============================
    # TECHNICAL FIELDS
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Whether this area is currently available"
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order of areas in lists"
    )

    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================

    @api.constrains('parent_id')
    def _check_no_circular_hierarchy(self):
        """Prevent circular parent-child relationships."""
        for area in self:
            if area.parent_id:
                parent = area.parent_id
                while parent:
                    if parent == area:
                        raise ValidationError(_("Circular hierarchy detected."))
                    parent = parent.parent_id

    _sql_constraints = [
        ('unique_area_name', 'UNIQUE(name)',
         'An area with this name already exists.'),
        ('unique_area_code', 'UNIQUE(code)',
         'An area with this code already exists.'),
    ]

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_view_internships(self):
        """Open internships in this area."""
        self.ensure_one()
        return {
            'name': f'Internships in {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.stage',
            'view_mode': 'tree,form,kanban',
            'domain': [('area_id', '=', self.id)],
            'target': 'current',
        }

    def action_view_supervisors(self):
        """Open supervisors with expertise in this area."""
        self.ensure_one()
        return {
            'name': f'Supervisors in {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.supervisor',
            'view_mode': 'tree,form,kanban',
            'domain': [('expertise_area_ids', 'in', [self.id])],
            'target': 'current',
        }

    def get_area_statistics(self):
        """Return statistical data for this area."""
        self.ensure_one()
        return {
            'internship_count': self.internship_count,
            'supervisor_count': len(self.supervisor_ids),
            'skill_count': len(self.skill_ids),
            'sub_area_count': len(self.child_ids),
            'level': self.level,
        }


class InternshipTodo(models.Model):
    """Todo/Task model for internship management.

    This model manages tasks and deliverables within internships,
    providing a structured way to track progress and assignments.

    Key Features:
    - Task assignment and tracking
    - Priority and deadline management
    - Progress monitoring
    - Integration with internship stages
    - Automatic notifications for deadlines
    """
    _name = 'internship.todo'
    _description = 'Internship Task Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, deadline, priority desc, id'
    _rec_name = 'name'

    # ===============================
    # CORE IDENTIFICATION FIELDS
    # ===============================

    name = fields.Char(
        string='Task Name',
        required=True,
        tracking=True,
        size=200,
        help="Name or title of the task"
    )

    description = fields.Html(
        string='Description',
        help="Detailed description of the task and requirements"
    )

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    stage_id = fields.Many2one(
        'internship.stage',
        string='Internship',
        required=True,
        ondelete='cascade',
        help="Internship this task belongs to"
    )

    assigned_to = fields.Many2one(
        'res.users',
        string='Assigned To',
        help="User responsible for completing this task"
    )

    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True,
        help="User who created this task"
    )

    # ===============================
    # TASK MANAGEMENT FIELDS
    # ===============================

    state = fields.Selection([
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='todo', tracking=True, required=True,
       help="Current status of the task")

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1', tracking=True,
       help="Priority level of the task")

    deadline = fields.Datetime(
        string='Deadline',
        tracking=True,
        help="When this task should be completed"
    )

    completion_date = fields.Datetime(
        string='Completion Date',
        readonly=True,
        help="When this task was actually completed"
    )

    estimated_hours = fields.Float(
        string='Estimated Hours',
        help="Estimated time to complete this task"
    )

    actual_hours = fields.Float(
        string='Actual Hours',
        help="Actual time spent on this task"
    )

    # ===============================
    # PROGRESS TRACKING FIELDS
    # ===============================

    progress_percentage = fields.Float(
        string='Progress %',
        default=0.0,
        help="Percentage of task completion (0-100)"
    )

    notes = fields.Html(
        string='Notes',
        help="Additional notes and comments about the task"
    )

    # ===============================
    # ALERT FIELDS
    # ===============================

    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_overdue_status',
        store=True,
        help="True if task is past its deadline"
    )

    days_overdue = fields.Integer(
        string='Days Overdue',
        compute='_compute_overdue_status',
        store=True,
        help="Number of days the task is overdue"
    )

    alert_sent = fields.Boolean(
        string='Alert Sent',
        default=False,
        help="True if overdue alert has been sent"
    )

    last_alert_date = fields.Datetime(
        string='Last Alert Date',
        help="When the last overdue alert was sent"
    )

    # ===============================
    # TECHNICAL FIELDS
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Whether this task is active"
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order of tasks in lists"
    )

    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================

    @api.constrains('progress_percentage')
    def _check_progress_percentage(self):
        """Ensure progress percentage is between 0 and 100."""
        for todo in self:
            if not (0 <= todo.progress_percentage <= 100):
                raise ValidationError(_("Progress percentage must be between 0 and 100."))

    @api.constrains('deadline')
    def _check_deadline(self):
        """Ensure deadline is in the future for new tasks."""
        for todo in self:
            if todo.deadline and todo.state == 'todo' and todo.deadline < fields.Datetime.now():
                raise ValidationError(_("Deadline must be in the future for new tasks."))

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_start(self):
        """Start working on the task."""
        self.write({'state': 'in_progress'})

    def action_mark_done(self):
        """Mark task as completed."""
        self.write({
            'state': 'done',
            'completion_date': fields.Datetime.now(),
            'progress_percentage': 100.0
        })

    def action_cancel(self):
        """Cancel the task."""
        self.write({'state': 'cancelled'})

    def action_reset_to_pending(self):
        """Reset task to pending state."""
        self.write({
            'state': 'todo',
            'progress_percentage': 0.0,
            'completion_date': False
        })

    def action_start(self):
        """Start the task."""
        self.write({
            'state': 'in_progress'
        })

    def action_complete(self):
        """Complete the task."""
        self.write({
            'state': 'done',
            'completion_date': fields.Datetime.now(),
            'progress_percentage': 100.0
        })

    # ===============================
    # COMPUTED METHODS
    # ===============================

    @api.depends('deadline', 'state')
    def _compute_overdue_status(self):
        """Compute overdue status and days overdue."""
        today = fields.Datetime.now()
        for todo in self:
            if todo.deadline and todo.state in ['todo', 'in_progress']:
                if todo.deadline < today:
                    todo.is_overdue = True
                    delta = today - todo.deadline
                    todo.days_overdue = delta.days
                else:
                    todo.is_overdue = False
                    todo.days_overdue = 0
            else:
                todo.is_overdue = False
                todo.days_overdue = 0

    # ===============================
    # NOTIFICATION METHODS
    # ===============================

    def send_overdue_alert(self):
        """Send overdue alert for this task."""
        self.ensure_one()
        if not self.is_overdue or self.alert_sent:
            return

        # Create communication for overdue alert
        self.env['internship.communication'].create({
            'subject': f'⚠️ Task Overdue: {self.name}',
            'content': f'''
                <p><strong>Task Overdue Alert</strong></p>
                <p>Task "{self.name}" is {self.days_overdue} days overdue.</p>
                <p><strong>Deadline:</strong> {self.deadline.strftime('%Y-%m-%d %H:%M') if self.deadline else 'Not set'}</p>
                <p><strong>Assigned to:</strong> {self.assigned_to.name if self.assigned_to else 'Not assigned'}</p>
                <p><strong>Internship:</strong> {self.stage_id.title}</p>
                <p>Please take action to complete this task as soon as possible.</p>
            ''',
            'communication_type': 'alert',
            'stage_id': self.stage_id.id,
            'sender_id': self.env.user.id,
            'recipient_ids': [(6, 0, [
                self.assigned_to.user_id.id if self.assigned_to and self.assigned_to.user_id else False,
                self.stage_id.supervisor_id.user_id.id if self.stage_id.supervisor_id and self.stage_id.supervisor_id.user_id else False
            ])],
            'priority': '3',  # High priority
            'state': 'sent'
        })

        # Update alert status
        self.write({
            'alert_sent': True,
            'last_alert_date': fields.Datetime.now()
        })

    @api.model
    def check_overdue_tasks(self):
        """Check for overdue tasks and send alerts."""
        overdue_tasks = self.search([
            ('deadline', '<', fields.Datetime.now()),
            ('state', 'in', ['todo', 'in_progress']),
            ('alert_sent', '=', False)
        ])

        for task in overdue_tasks:
            task.send_overdue_alert()

        _logger.info(f"Checked {len(overdue_tasks)} overdue tasks and sent alerts")
        return len(overdue_tasks)


    # ===============================
    # UTILITY METHODS
    # ===============================

    def name_get(self):
        """Custom name display: Name (Status)."""
        result = []
        for todo in self:
            name = todo.name
            if todo.state:
                state_name = dict(todo._fields['state'].selection).get(todo.state)
                name = f"{name} ({state_name})"
            result.append((todo.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        """Custom search: search by name or description."""
        args = args or []
        domain = []

        if name:
            domain = ['|',
                      ('name', operator, name),
                      ('description', operator, name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid, order=order)

    def get_task_statistics(self):
        """Return statistical data for this task."""
        self.ensure_one()
        return {
            'days_to_deadline': (self.deadline - fields.Datetime.now()).days if self.deadline else None,
            'is_overdue': self.deadline and self.deadline < fields.Datetime.now() and self.state != 'done',
            'completion_time': (self.completion_date - self.create_date).days if self.completion_date else None,
            'efficiency': (self.actual_hours / self.estimated_hours * 100) if self.estimated_hours and self.actual_hours else None,
        }