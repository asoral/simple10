from odoo import api, fields, models

class PayslipAnalysisReport(models.Model):
    _name='payslip.analysis.report'


    slip_ref = fields.Char(string='Slip Reference')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    employee_id = fields.Many2one('hr.employee',string="Employee")
    contract_id = fields.Many2one('hr.contract',string="Contract")
    structure_id = fields.Many2one('hr.payroll.structure',string="Structure")
    move_id = fields.Many2one('account.account',string="Account")
    journal_id = fields.Many2one('account.journal',string="Journal")
    department_id = fields.Many2one('hr.department',string="Department")
    designation_id = fields.Many2one('hr.job',string="Designation")
    category_id = fields.Many2one('hr.salary.rule.category',string="Category")
    rule_id = fields.Many2one('hr.salary.rule',string="Rule")
    total = fields.Float(string="Total")