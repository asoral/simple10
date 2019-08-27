# -*- coding: utf-8 -*-
"""akhodifad"""
from odoo import models, fields, api


class PayslipsPayslipbatch(models.TransientModel):
    _name = 'payslips.payslipbatch'
    
    payslip_ids = fields.Many2many('hr.payslip',String="Payslips")
    payslip_ids_batch = fields.Many2many('hr.payslip.run',String="Payslip Batch")
    payodr_id = fields.Many2one('payment.order',String="Po Id")
    type = fields.Selection([('payslip_batch','Payslip Batch'),('payslips','Payslips')],related="payodr_id.type",string="Type")
    
    @api.multi
    def add_payslips(self):
        p_o_lin = self.env['payment.order.line']
        if self.type == 'payslip_batch':
            for p_b_id in self.payslip_ids_batch:
                for l in p_b_id.slip_ids:
                    p_o_lin.create({
                                    'number':l.number,
                                    'employee_id':l.employee_id.id,
                                    'name': l.name,
                                    'date_from':l.date_from,
                                    'date_to' : l.date_to,
                                    'state' : l.state,
                                    'paysslip_id':l.id,
                                    'pay_odtr_id':self.payodr_id.id})
        elif self.type == 'payslips':
            for p_id in self.payslip_ids:
                    p_o_lin.create({
                                    'number':p_id.number,
                                    'employee_id':p_id.employee_id.id,
                                    'name': p_id.name,
                                    'date_from':p_id.date_from,
                                    'date_to' : p_id.date_to,
                                    'state' : p_id.state,
                                    'paysslip_id':p_id.id,
                                    'pay_odtr_id':self.payodr_id.id})
                    
                    