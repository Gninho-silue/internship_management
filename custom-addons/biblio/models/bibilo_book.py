from odoo import models, fields


class BiblioBook(models.Model):
    _name = 'biblio.book'
    _description = "Book Management"

    short_name = fields.Char('Short Title', required=True)
    name = fields.Char('Title', required=True)
    date_release = fields.Date('Release Date')
    active = fields.Boolean(default=True)
    state = fields.Selection([('available', 'Available'),
                              ('borrowed', 'Borrowed'),
                              ('lost', 'Lost')], 'State',
                             default="available")
    cost_price = fields.Float('Book Cost')
    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary('Retail Price')
    description = fields.Html('Description')
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of Print?')
    date_updated = fields.Datetime('Last Updated')
    pages = fields.Integer('Number of Pages')
    reader_rating = fields.Float('Reader Average Rating', digits=(14, 4))

    publisher_id = fields.Many2one('res.partner', string='Publisher')


