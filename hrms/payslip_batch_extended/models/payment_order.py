import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp

class PaymentOrder(models.Model):
    _name = 'payment.order'
    
    def _get_cash_and_bank(self):
        type_id = False
        type_id = self.env.ref('account.data_account_type_liquidity').id
        return [('user_type_id', '=', type_id)]


    name = fields.Char(string='Name')
    date = fields.Date(string="Date",default=fields.Date.context_today)
    type = fields.Selection([('payslip_batch','Payslip Batch'),('payslips','Payslips')],string="Type",default="payslip_batch")
    payslip_line_ids = fields.One2many('payment.order.line', 'pay_odtr_id', string='payslip')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Confirm'),
    ], string='Status', index=True, copy=False, default='draft')
    journal_id = fields.Many2one('account.journal', string='Journal',required=True)
    account_id = fields.Many2one('account.account', domain=_get_cash_and_bank, string='Account',
        required=True)
    move_id = fields.Many2one('account.move', 'Journal Entry', copy=False)
   
    #Some changes by sangita   
    @api.multi
    def confirm_payment_order(self):
        
        company_currency = self.journal_id.company_id.currency_id.id
        current_currency =  company_currency
        line = []
        descrip = "vycjycyndbfngy-------"
        moves = self.env['account.move']
        Journal = self.journal_id.id
        if 'operating_unit_id' in self._fields:
            values = {
                'journal_id':Journal,
                'ref': "kl",
                'pay_odr_id':self.id,
                'date':self.date,
                'line_ids': [(6,0,line)],
                'operating_unit_id': self.operating_unit_id.id,
                }
        else:
            values = {
                'journal_id': Journal,
                'ref': "lk",
                'pay_odr_id':self.id,
                'date':self.date,
                'line_ids': [(6,0,line)],
            }
        res = moves.create(values)
        print"we are creating MOVESSSS------>>>", res
        amount = 0.0
        for line in self.payslip_line_ids:
            for l in line.paysslip_id.line_ids:
                if l.salary_rule_id.code.capitalize() == 'Net':
                    amount += line.net_salary
                    debit_line = self.env['account.move.line'].with_context(
                        check_move_validity=False).create({
                        'move_id': res.id,
                        'account_id': l.salary_rule_id.account_credit.id or self.account_id.id,
                        'partner_id':line.employee_id.address_home_id.id,
                        'name': self.name,
                        'debit': abs(line.net_salary) if line.net_salary else 0.0,
                    })
        credit_line = self.env['account.move.line'].with_context(
            check_move_validity=False).create({
            'move_id': res.id,
            'account_id': self.account_id.id,
#             'partner_id':self.partner_id.id,
            'name': self.name,
            'credit': abs(amount) if amount else 0.0,
        })
        res.line_ids += debit_line
        res.line_ids += credit_line
        res.post()
        
#        
        self.filtered(lambda s: s.state == 'draft').write({'state': 'done'})
    
    
    @api.multi
    def view_account_pay_order_po(self):
        return {
                'name' : _('Payment Order'),
                'view_type' : 'form',
                'view_mode' : 'tree,form',
                'res_model' : 'account.move',
                'type' : 'ir.actions.act_window',
                'domain' : [('pay_odr_id','=',self.id)],
                }
        
    @api.multi
    def payslip_by_batch_and_payslips(self):
        return {
            'name' : _('Payslip Batch'),
            'view_type' : 'form',
            'view_mode' : 'form',
            'res_model' : 'payslips.payslipbatch',
            'type' : 'ir.actions.act_window',
            'target' : 'new',
            'context': {'default_payodr_id':self.id},
            }
    @api.multi
    def unlink(self):
        """Allow to delete only cancelled state"""
        if any(x.state == 'done' for x in self):
            raise UserError(
                _("You can't delete done Payment Order."))
        return super(PaymentOrder, self).unlink()

    
class AccountMove(models.Model):
    _inherit = 'account.move'        

    pay_odr_id = fields.Many2one('payment.order',string="Payment Order")

class PaymentOrderLine(models.Model):
    _name = 'payment.order.line'
    
    
    @api.onchange('paysslip_id')
    def _get_net_salary_payslip(self):
        for line in self:
            if line.paysslip_id:
#                 print"==================>>>>>>",line.paysslip_id,line.paysslip_id.line_ids
                for pay in line.paysslip_id.line_ids:
#                     print"ooooooooooooooo===>",pay.code
                    if pay.code == 'NET' or pay.code == 'net' or pay.code == 'Net':
#                         print"AAAAAGGGGAAAAYE SOLUTION Pe===>>.",pay.total
                        line.net_salary = pay.total
                
    
    pay_odtr_id = fields.Many2one('payment.order',string="Payment Order")
    paysslip_id = fields.Many2one('hr.payslip',string="Payslip")
    name = fields.Char(string='Payslip Name',readonly=True)
    number = fields.Char(string='Reference', copy=False,readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True,)
    date_from = fields.Date(string='Date From', readonly=True, default=time.strftime('%Y-%m-01'), )
    date_to = fields.Date(string='Date To', readonly=True,
        default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    #Djay Added
    net_salary = fields.Monetary(string='Net Salary',compute='_get_net_salary_payslip')
    currency_id = fields.Many2one('res.currency',string='Currency', readonly=True, required=True, default=lambda self: self._get_currency())

    @api.model
    def _get_currency(self):
        return self.env.user.company_id.currency_id.id
                                
                                
                                
                                
                                