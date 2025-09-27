# -*- coding: utf-8 -*-


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
    ], string='Category', required=False,
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





