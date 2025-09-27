# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
        required=False,
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
