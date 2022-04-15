# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ImportRegimen(models.Model):
    _name = "freight.import.regimen"

    name = fields.Char(string="Name")
    type = fields.Boolean(string="Active")
    date = fields.Date(string="Date")
    tipo = fields.Char(string="Type")