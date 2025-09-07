# -*- coding: utf-8 -*-
"""
Internship Supervisor Model

This module handles supervisor management for the internship system,
including capacity management, expertise areas, and workload tracking.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InternshipSupervisor(models.Model):
    """Supervisor model for internship management.

    This model manages supervisors who guide students during their internships,
    including their professional information, expertise areas, availability,
    and current workload tracking.

    Key Features:
    - Supervisor capacity management (max students)
    - Expertise area tracking
    - Automatic availability calculation
    - Workload monitoring
    - Integration with user accounts
    """
    _name = 'internship.supervisor'
    _description = 'Internship Supervisor Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ===============================
    # CORE IDENTIFICATION FIELDS
    # ===============================

    name = fields.Char(
        string='Full Name',
        required=True,
        tracking=True,
        size=100,
        help="Supervisor's complete name"
    )

    user_id = fields.Many2one(
        'res.users',
        string='User Account',
        ondelete='restrict',
        help="Associated user account for system access"
    )

    email = fields.Char(
        string='Email Address',
        required=True,
        help="Primary email address for communication"
    )

    phone = fields.Char(
        string='Phone Number',
        size=20,
        help="Primary contact phone number"
    )

    # ===============================
    # PROFESSIONAL INFORMATION
    # ===============================

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Company or organization where supervisor works"
    )

    department = fields.Char(
        string='Department',
        required=True,
        size=100,
        help="Department or division within the organization"
    )

    position = fields.Char(
        string='Position',
        required=True,
        size=100,
        help="Job title or professional position"
    )

    expertise_area_ids = fields.Many2many(
        'internship.area',
        string='Areas of Expertise',
        help="Professional domains where supervisor can provide guidance"
    )

    # ===============================
    # INTERNSHIP MANAGEMENT
    # ===============================

    stage_ids = fields.One2many(
        'internship.stage',
        'supervisor_id',
        string='Supervised Internships',
        help="All internships supervised by this person"
    )

    max_students = fields.Integer(
        string='Maximum Students',
        default=3,
        help="Maximum number of students this supervisor can handle simultaneously"
    )

    @api.depends('stage_ids.state')
    def _compute_current_students_count(self):
        """Calculate number of currently active students."""
        for supervisor in self:
            active_stages = supervisor.stage_ids.filtered(
                lambda s: s.state in ['approved', 'in_progress']
            )
            supervisor.current_students_count = len(active_stages)

    current_students_count = fields.Integer(
        string='Current Students',
        compute='_compute_current_students_count',
        store=True,
        help="Number of students currently being supervised"
    )

    availability = fields.Selection([
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('unavailable', 'Unavailable')
    ], string='Availability Status',
        default='available',
        tracking=True,
        help="Current availability for new student assignments")

    # ===============================
    # PROFILE AND STATUS
    # ===============================

    profile_image = fields.Binary(
        string='Profile Photo',
        attachment=True,
        help="Supervisor's profile photograph"
    )

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Whether this supervisor record is active"
    )

    # ===============================
    # COMPUTED FIELDS
    # ===============================

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        """Calculate total number of internships supervised."""
        for supervisor in self:
            supervisor.stage_count = len(supervisor.stage_ids)

    stage_count = fields.Integer(
        string='Total Internships Supervised',
        compute='_compute_stage_count',
        store=True,
        help="Total number of internships supervised by this person"
    )

    @api.depends('current_students_count', 'max_students')
    def _compute_workload_percentage(self):
        """Calculate supervisor workload as percentage."""
        for supervisor in self:
            if supervisor.max_students > 0:
                workload = (supervisor.current_students_count / supervisor.max_students) * 100
                supervisor.workload_percentage = min(workload, 100.0)
            else:
                supervisor.workload_percentage = 0.0

    workload_percentage = fields.Float(
        string='Workload Percentage',
        compute='_compute_workload_percentage',
        help="Current workload as percentage of maximum capacity"
    )

    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================

    @api.constrains('max_students')
    def _check_max_students(self):
        """Ensure maximum students is a positive number."""
        for supervisor in self:
            if supervisor.max_students < 1:
                raise ValidationError(_("Maximum students must be at least 1."))

    @api.constrains('email')
    def _check_email_format(self):
        """Validate email format."""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for supervisor in self:
            if supervisor.email and not re.match(email_pattern, supervisor.email):
                raise ValidationError(_("Please enter a valid email address."))

    # ===============================
    # AUTOMATED METHODS
    # ===============================

    @api.onchange('current_students_count', 'max_students')
    def _onchange_students_count(self):
        """Automatically update availability based on workload."""
        for supervisor in self:
            if supervisor.current_students_count >= supervisor.max_students:
                supervisor.availability = 'busy'
            elif supervisor.current_students_count < supervisor.max_students:
                if supervisor.availability == 'busy':
                    supervisor.availability = 'available'

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_view_supervised_internships(self):
        """Open supervised internships in dedicated view."""
        self.ensure_one()
        return {
            'name': f'Internships Supervised by {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.stage',
            'view_mode': 'tree,form,kanban',
            'domain': [('supervisor_id', '=', self.id)],
            'context': {'default_supervisor_id': self.id},
            'target': 'current',
        }

    def check_availability_for_new_student(self):
        """Check if supervisor can take on new student."""
        self.ensure_one()
        return (
                self.active and
                self.availability == 'available' and
                self.current_students_count < self.max_students
        )

    def get_supervisor_statistics(self):
        """Return comprehensive supervisor statistics."""
        self.ensure_one()
        total_completed = len(
            self.stage_ids.filtered(lambda s: s.state in ['completed', 'evaluated'])
        )

        # Calculate average grade if grades exist
        graded_stages = self.stage_ids.filtered(lambda s: s.final_grade > 0)
        avg_grade = (
            sum(graded_stages.mapped('final_grade')) / len(graded_stages)
            if graded_stages else 0.0
        )

        return {
            'total_supervised': self.stage_count,
            'currently_active': self.current_students_count,
            'completed_internships': total_completed,
            'average_grade': avg_grade,
            'workload_percentage': self.workload_percentage,
            'availability_status': self.availability,
        }

    # ===============================
    # UTILITY METHODS
    # ===============================

    def name_get(self):
        """Custom name display: Name (Department)."""
        result = []
        for supervisor in self:
            name = supervisor.name
            if supervisor.department:
                name = f"{name} ({supervisor.department})"
            result.append((supervisor.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Custom search: search by name, email, department, or position."""
        args = args or []
        domain = []

        if name:
            domain = ['|', '|', '|',
                      ('name', operator, name),
                      ('email', operator, name),
                      ('department', operator, name),
                      ('position', operator, name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def get_available_supervisors(self, expertise_area=None):
        """Get list of available supervisors, optionally filtered by expertise area."""
        domain = [
            ('active', '=', True),
            ('availability', '=', 'available'),
            ('current_students_count', '<', 'max_students')
        ]

        if expertise_area:
            domain.append(('expertise_area_ids', 'in', [expertise_area]))

        return self.search(domain)