# -*- coding: utf-8 -*-
"""Internship Student Model """

import logging
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class InternshipStudent(models.Model):
    """Student model for internship management system.

    This model handles all student-related information including
    personal details, academic background, and internship history.
    """
    _name = 'internship.student'
    _description = 'Internship Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'full_name'
    _rec_name = 'full_name'

    # ===============================
    # PERSONAL INFORMATION FIELDS
    # ===============================

    full_name = fields.Char(
        string='Full Name',
        required=True,
        tracking=True,
        size=100,
        help="Student's complete name"
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

    birth_date = fields.Date(
        string='Date of Birth',
        help="Student's birth date"
    )

    linkedin_profile = fields.Char(
        string='LinkedIn Profile',
        help="LinkedIn profile URL"
    )

    cv_document = fields.Binary(
        string='CV Document',
        attachment=True,
        help="Upload student's curriculum vitae"
    )

    profile_image = fields.Binary(
        string='Profile Photo',
        attachment=True,
        help="Student's profile photograph"
    )

    # ===============================
    # ACADEMIC INFORMATION FIELDS
    # ===============================

    institution = fields.Char(
        string='Educational Institution',
        required=True,
        size=100,
        help="Name of school, university, or college"
    )

    education_level = fields.Selection([
        ('bachelor_1', 'Bachelor Year 1'),
        ('bachelor_2', 'Bachelor Year 2'),
        ('bachelor_3', 'Bachelor Year 3'),
        ('engineer', 'Engineer'),
        ('master_1', 'Master Year 1'),
        ('master_2', 'Master Year 2'),
        ('phd', 'PhD')
    ], string='Education Level', required=True)

    field_of_study = fields.Char(
        string='Field of Study',
        required=True,
        size=100,
        help="Major or specialization area"
    )

    student_id_number = fields.Char(
        string='Student ID Number',
        size=20,
        help="Official student identification number"
    )

    expected_graduation_date = fields.Date(
        string='Expected Graduation',
        help="Expected graduation date"
    )

    # ===============================
    # RELATIONSHIP FIELDS
    # ===============================

    internship_ids = fields.One2many(
        'internship.stage',
        'student_id',
        string='Internships',
        help="All internships associated with this student"
    )

    skill_ids = fields.Many2many(
        'internship.skill',
        string='Skills',
        help="Technical and soft skills possessed by student"
    )

    interest_area_ids = fields.Many2many(
        'internship.area',
        string='Areas of Interest',
        help="Areas where student is interested to do internship"
    )

    document_ids = fields.One2many(
        'internship.document',
        'student_id',
        string='Documents',
        help="All documents uploaded by or for this student"
    )

    # ===============================
    # COMPUTED FIELDS
    # ===============================

    @api.depends('internship_ids')
    def _compute_internship_count(self):
        """Calculate total number of internships for this student."""
        for student in self:
            student.internship_count = len(student.internship_ids)

    @api.depends('internship_ids.final_grade')
    def _compute_average_grade(self):
        """Calculate average grade across all completed internships."""
        for student in self:
            completed_internships = student.internship_ids.filtered(
                lambda x: x.final_grade > 0
            )
            if completed_internships:
                total_grade = sum(completed_internships.mapped('final_grade'))
                student.average_grade = total_grade / len(completed_internships)
            else:
                student.average_grade = 0.0

    @api.depends('internship_ids.completion_percentage')
    def _compute_completion_rate(self):
        """Calculate overall completion rate of all internships."""
        for student in self:
            active_internships = student.internship_ids.filtered(
                lambda x: x.state != 'cancelled'
            )
            if active_internships:
                total_progress = sum(active_internships.mapped('completion_percentage'))
                student.completion_rate = total_progress / len(active_internships)
            else:
                student.completion_rate = 0.0

    internship_count = fields.Integer(
        string='Number of Internships',
        compute='_compute_internship_count',
        store=True,
        help="Total number of internships for this student"
    )

    average_grade = fields.Float(
        string='Average Grade',
        compute='_compute_average_grade',
        digits=(4, 2),
        help="Average grade across all completed internships"
    )

    completion_rate = fields.Float(
        string='Completion Rate',
        compute='_compute_completion_rate',
        help="Overall completion rate of all internships"
    )

    # ===============================
    # TECHNICAL FIELDS
    # ===============================

    active = fields.Boolean(
        default=True,
        string='Active',
        help="Whether this student record is active"
    )

    # ===============================
    # CONSTRAINTS AND VALIDATIONS
    # ===============================

    @api.constrains('email')
    def _check_email_format(self):
        """Validate email format using proper regex pattern."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for student in self:
            if student.email and not re.match(email_pattern, student.email):
                raise ValidationError(_("Please enter a valid email address format."))

    @api.constrains('phone')
    def _check_phone_format(self):
        """Validate phone number format."""
        phone_pattern = r'^\+?[\d\s\-\(\)]{8,20}$'
        for student in self:
            if student.phone and not re.match(phone_pattern, student.phone):
                raise ValidationError(_("Please enter a valid phone number format."))

    @api.constrains('birth_date')
    def _check_birth_date(self):
        """Ensure birth date is reasonable (not in future, not too old)."""
        from datetime import date, timedelta
        today = date.today()
        min_date = today - timedelta(days=365 * 80)  # 80 years ago

        for student in self:
            if student.birth_date:
                if student.birth_date > today:
                    raise ValidationError(_("Birth date cannot be in the future."))
                if student.birth_date < min_date:
                    raise ValidationError(_("Please verify the birth date."))

    _sql_constraints = [
        ('unique_email', 'UNIQUE(email)',
         'This email address is already registered by another student.'),
        ('unique_user_id', 'UNIQUE(user_id)',
         'This user account is already associated with another student.'),
        ('unique_student_id', 'UNIQUE(student_id_number)',
         'This student ID number is already in use.'),
    ]

    # ===============================
    # CRUD METHODS
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method with logging and validation."""
        _logger.info(f"Creating {len(vals_list)} student record(s)")

        for vals in vals_list:
            # Auto-generate user account if email provided
            if vals.get('email') and not vals.get('user_id'):
                user_vals = {
                    'name': vals.get('full_name', 'Student'),
                    'login': vals['email'],
                    'email': vals['email'],
                    'groups_id': [(4, self.env.ref('internship_management.group_internship_student').id)]
                }
                try:
                    user = self.env['res.users'].create(user_vals)
                    vals['user_id'] = user.id
                    _logger.info(f"Created user account for student: {vals['email']}")
                except Exception as e:
                    _logger.warning(f"Could not create user account: {e}")

        return super().create(vals_list)

    def write(self, vals):
        """Override write method with logging."""
        if 'active' in vals:
            action = "activated" if vals['active'] else "deactivated"
            _logger.info(f"Student {self.full_name} {action}")

        return super().write(vals)

    # ===============================
    # BUSINESS METHODS
    # ===============================

    def action_view_internships(self):
        """Open student's internships in a dedicated view."""
        self.ensure_one()
        return {
            'name': f'Internships - {self.full_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'internship.stage',
            'view_mode': 'tree,form,kanban',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
            'target': 'current',
        }

    def action_send_welcome_email(self):
        """Send welcome email to student."""
        self.ensure_one()
        if not self.email:
            raise ValidationError(_("Student must have an email address to send welcome email."))

        # TODO: Implement email template
        _logger.info(f"Welcome email sent to {self.full_name} at {self.email}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Welcome Email Sent"),
                'message': f"Welcome email sent to {self.full_name}",
                'type': 'success',
            }
        }

    def get_student_statistics(self):
        """Return statistical data for this student."""
        self.ensure_one()
        return {
            'total_internships': self.internship_count,
            'average_grade': self.average_grade,
            'completion_rate': self.completion_rate,
            'active_internships': len(self.internship_ids.filtered(lambda x: x.state == 'in_progress')),
            'completed_internships': len(self.internship_ids.filtered(lambda x: x.state in ['completed', 'evaluated'])),
        }

    # ===============================
    # UTILITY METHODS
    # ===============================

    def name_get(self):
        """Custom name display: Full Name (Institution)."""
        result = []
        for student in self:
            name = student.full_name
            if student.institution:
                name = f"{name} ({student.institution})"
            result.append((student.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        """Custom search: search by name, email, or student ID."""
        args = args or []
        domain = []

        if name:
            domain = ['|', '|',
                      ('full_name', operator, name),
                      ('email', operator, name),
                      ('student_id_number', operator, name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid, order=order)
