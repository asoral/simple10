from odoo import api, fields, models, _
from odoo.exceptions import UserError

class WizardPayslipAnalysisReport(models.TransientModel):
    _name = 'wizard.payslip.analysis.report'
    
    @api.depends('date_range')
    @api.onchange('date_range','date_from','date_to')
    def get_dates(self):
        for s in self:
            if s.date_range:
                s.date_from = s.date_range.date_start
                s.date_to = s.date_range.date_end
                
    date_range = fields.Many2one('date.range','Date range')
    date_from = fields.Date(string="Date From",required=True)
    date_to = fields.Date(string="Date To",required=True)
    employee_id = fields.Many2many('hr.employee',string="Employee")
    department_id = fields.Many2many('hr.department',string="Department")
    designation_id = fields.Many2many('hr.job',string="Designation")



    @api.multi
    def confirm_wizard_payslip_analysis(self):
        analysis_id=self.env['payslip.analysis.report'].search([])
        analysis_id.unlink()
        if self.employee_id:
            payslip_ids = self.env['hr.payslip.line'].search([('slip_id.employee_id','=',self.employee_id.id),('slip_id.state','=','done')])
            self.create_report(payslip_ids)
            
        elif self.department_id:
            payslip_ids = self.env['hr.payslip.line'].search([('slip_id.employee_id.department_id','=',self.department_id.id),('slip_id.state','=','done')])
            self.create_report(payslip_ids)
        
        elif self.designation_id:
            payslip_ids = self.env['hr.payslip.line'].search([('slip_id.employee_id.job_id','=',self.designation_id.id),('slip_id.state','=','done')])
            self.create_report(payslip_ids)
        else:
            payslip_ids = self.env['hr.payslip.line'].search([('slip_id.employee_id','!=',False),('slip_id.state','=','done')])
            self.create_report(payslip_ids)
        
        return {
            'name': 'Payslip Analysis Report',
            'view_type': 'form',
            'view_mode': 'tree,pivot',
            'res_model': 'payslip.analysis.report',
            'type': 'ir.actions.act_window',
            'target': 'current',
           
            }
        
    def create_report(self,payslip_entry_ids):
        for payslip in payslip_entry_ids:
            report_id = self.env['payslip.analysis.report'].create({
                                    'slip_ref':payslip.slip_id.number,
                                    'date_from':payslip.slip_id.date_from,
                                    'date_to':payslip.slip_id.date_to,
                                    'employee_id':payslip.slip_id.employee_id.id,
                                    'department_id':payslip.slip_id.employee_id.department_id.id,
                                    'contract_id':payslip.slip_id.contract_id.id,
                                    'structure_id':payslip.slip_id.struct_id.id,
                                    'designation_id':payslip.slip_id.employee_id.job_id.id,
#                                     'move_id':payslip.slip_id.move_id.id,
                                    'journal_id':payslip.slip_id.journal_id.id,
                                    'category_id':payslip.category_id.id,
                                    'rule_id':payslip.salary_rule_id.id,
                                    'total':payslip.total
                                    
                                    })
        