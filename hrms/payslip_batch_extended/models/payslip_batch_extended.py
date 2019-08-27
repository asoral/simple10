from odoo import api, fields, models, _
from datetime import datetime 
from datetime import date
import time
import pytz
from odoo import api, fields, models, tools, _
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, timedelta
from dateutil import relativedelta
import babel

from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from string import uppercase
from odoo.exceptions import except_orm

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'
    
#     def _get_partner_id(self, credit_account):
#         """
#         Get partner_id of slip line to use in account_move_line
#         """
#         # use partner of salary rule or fallback on employee's address
#         register_partner_id = self.salary_rule_id.register_id.partner_id
#         partner_id = register_partner_id.id or self.slip_id.employee_id.address_home_id.id
#         if credit_account:
#             if register_partner_id or self.salary_rule_id.account_credit.internal_type in ('receivable', 'payable'):
#                 return partner_id
#         else:
#             if register_partner_id or self.salary_rule_id.account_debit.internal_type in ('receivable', 'payable'):
#                 return partner_id
#         return partner_id

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Payslip Batches'
    
    @api.multi
    def compute_payslips(self):
        for slip in self.slip_ids:
            if slip.state == 'draft':
                slip.compute_sheet()
        
    @api.multi
    def close_payslip_run(self):
        for slip_line in self.slip_ids:
            if slip_line.state == 'draft':
                slip_line.action_payslip_done()
        return self.write({'state': 'close'})
    
    @api.multi
    def cancel_payslip_run(self):
        print"We are in new inherited button method"
        self.slip_ids.action_payslip_cancel()
        return self.write({'state': 'close'})
    
    
class HrPayslip(models.Model):
    _name = 'hr.payslip'   
    _inherit = ['mail.thread','hr.payslip'] 
    
    #added by sangita
    refund_id = fields.Many2one('hr.payslip',string="Refund ID")
    
    
    @api.model
    def _get_currency(self):
        return self.env.user.company_id.currency_id.id
    
    currency_id = fields.Many2one('res.currency',string='Currency', readonly=True, required=True, default=lambda self: self._get_currency())
    
    def compute_difference_two_date(self):
        s=datetime.strptime(self.date_from, "%Y-%m-%d")
        e=datetime.strptime(self.date_to, "%Y-%m-%d")
        start = s.day
        end = e.day
        date_days = end - start
        return date_days
#               deadline_days = (date.today() - deadline_date).days 
#             
    def convert_number2word_inv(self):
        for line in self.line_ids:
            if line.code == 'NET':
                return self.env['convert.num2word'].convert_number2word(line.amount, 'en_US', self.currency_id.name)    
        
    def leaves_type_cal_earned(self):
        earned = 0
        res = self.env['hr.holidays'].search([('holiday_type','=','employee'), ('holiday_status_id.limit', '=', False), ('state','!=', 'refuse'),('employee_id','=',self.employee_id.id),('earned_leaves','=',True)])
        for r in res:
            earned = r.number_of_days_temp
            return earned
        
    def leaves_type_cal_sick(self):
        sick = 0
        res = self.env['hr.holidays'].search([('holiday_type','=','employee'), ('holiday_status_id.limit', '=', False), ('state','!=', 'refuse'),('employee_id','=',self.employee_id.id),('sick_leaves','=',True)])
        for r in res:
            sick = r.number_of_days_temp
        return sick
    
    def leaves_type_cal_casual(self):
        casual = 0
        res = self.env['hr.holidays'].search([('holiday_type','=','employee'), ('holiday_status_id.limit', '=', False), ('state','!=', 'refuse'),('employee_id','=',self.employee_id.id),('casual_leaves','=',True)])
        for r in res:
            casual = r.number_of_days_temp
        return casual
    
    def unused_leaves_cal(self):
        unused = 0
        a = []
        unused_leaves_id = self.env['hr.holidays'].search([('holiday_type','=','employee'),('employee_id','=',self.employee_id.id), ('type','=','add'),('state','in',('confirm','validate'))])
        for i in unused_leaves_id:
            a += [i.number_of_days]
            unused = sum(a)
        return unused
    
    
    def used_leaves_cal(self):
        used = 0
        a = []
        used_leaves_id = self.env['hr.holidays'].search([('holiday_type','=','employee'),('employee_id','=',self.employee_id.id), ('type','=','remove'),('state','in',('confirm','validate'))])
        for i in used_leaves_id:
            a += [-i.number_of_days]
            used = sum(a)
        return used
    
        
    #added by sangita
    def compute_net_pay(self):
        loan_amount = 0.0
        if self.line_ids:
            for line in self.line_ids:
                if line.code == 'LOAN':
                    loan_amount = line.amount
                if line.code == 'NET':
                    net = line.amount - loan_amount
                    return net
   
    #added by sangita
    @api.multi
    @api.depends('employee_id','employee_id.leaves_count')
    def _compute_leaves_count(self):
        for t in self:
            for d in t.employee_id:
                t.leaves_count = d.leaves_count
                
    #akhodifad
    @api.constrains('date_from','date_to','employee_id')
    def _compute_ytd_count(self):
        for t in self:
            if t.employee_id:
                to_date = t.date_to.split("-")
                SQL = """
                    select ps.employee_id,
                    sum(psl.total)
                    from hr_payslip_line psl
                    inner join hr_payslip ps on ps.id=psl.slip_id
                    and extract(year from ps.date_to) = %s
                    and ps.employee_id = %s
                    and ps.company_id = %s
                    and code = 'NET'
                    group by ps.employee_id, ps.company_id;
                """
                self.env.cr.execute(SQL,(int(to_date[0]),
                                          t.employee_id.id,
                                          t.company_id.id or None,
                                          ))
                res = self.env.cr.fetchall()
                if res:
                    t.ytd_count = float(res[0][1])
    
    def _get_cash_and_bank(self):
        type_id = False
        type_id = self.env.ref('account.data_account_type_liquidity').id
        return [('user_type_id', '=', type_id)]
                
    leaves_count = fields.Integer('Number of Leaves', compute='_compute_leaves_count')
    ytd_count = fields.Float('Number of YTD', compute='_compute_ytd_count')
    account_id = fields.Many2one('account.account', 'Account',domain=_get_cash_and_bank)
   
    pay_odr_id = fields.Many2one('payment.order',string="Payment Order")
    
    #added by sangita
    @api.multi
    @api.onchange('contract_id')
    def onchange_contract(self):
        super(HrPayslip, self).onchange_contract()
        self.account_id = self.contract_id.account_id.id
#        
    #added by sangita
    @api.constrains('contract_id')
    def onchange_contract_to_account(self):
        self.account_id = self.contract_id.account_id.id
    
    @api.multi
    def create_account_voucher(self):
        ac_voucher = self.env['account.voucher']
        ac_exit = ac_voucher.search([('name','=',self.name)])
        if self.paid:
            raise UserError(_('Payment Order already created.'))
        
        ac_vc_lin = self.env['account.voucher.line']
        vals_ac = {'name' : self.number or None,
                   'pay_now' : 'pay_now',
                   'voucher_type' : 'purchase',
                   'date' : self.date,
                   'journal_id' : self.journal_id.id,
                   'account_id' : self.account_id.id,
                   'move_id' : self.move_id.id or None,
                   'payslip_id' :self.id,
                   }
        ac_obj = ac_voucher.create(vals_ac)
        self.paid = True
        for l in self.line_ids:
            if l.salary_rule_id.code.capitalize() == 'Net':
                price = l.amount
                vals_ac_lin ={ 'voucher_id' : ac_obj.id,
                               'name' : self.name,
                               'account_id' : l.salary_rule_id.account_credit.id or self.account_id.id,
                               'quantity' : 1.0,
                               'price_unit' : price,
                               'company_id' : self.company_id.id,
                           }
                ac_obj = ac_vc_lin.sudo().create(vals_ac_lin)
                
    #added by Sangita
    @api.multi
    def dummy_method_ytd(self):
        year_line = self.env['hr.payslip.year'].search([])
        year_line.unlink()
        for t in self:
            if t.employee_id and t.date_from:
                today = str(date.today())
                fiscal_year = self.env['account.fiscalyear'].search([('date_start','<=',today),('date_stop','>=',today)],limit=1)
                
                SQL = """
                    select hp.employee_id, hpl.salary_rule_id,sum(hpl.total) 
                    from hr_payslip_line as hpl 
                    inner join hr_payslip as hp
                    on hpl.slip_id = hp.id 
                    where hp.employee_id = %s and hp.state in ('done') and hp.date_from >= %s and date_to <= %s 
                    group by hpl.id ,hpl.salary_rule_id,hp.employee_id,hp.state

                """
                self.env.cr.execute(SQL,(t.employee_id.id,str(fiscal_year.date_start),str(t.date_to)
                                          ))
                res = self.env.cr.fetchall()
                if res:
                    for line in res:
#                         print"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",line
                        self.env['hr.payslip.year'].create({
                            'salary_rule_id':line[1],
                            'hr_payslip_id':self.id,
                            'total':line[2],
                            })
        return{
            'name': _('Leaves'),
            'view_type': 'form',
            'view_mode': 'tree,pivot,from',
            'res_model': 'hr.payslip.year',
            'src_model' : 'hr.payslip',
            'type': 'ir.actions.act_window',
            'context': {'search_default_employee_id': self.employee_id.id, 'default_employee_id': self.employee_id.id,
                        'group_by':'salary_rule_id'},
            'search_view_id' : self.env.ref('payslip_batch_extended.hr_payslip_year_tree').id
            }
    
    #added by sangita
    @api.multi
    def tod_calculate(self):
        for t in self:
            if t.employee_id and t.date_from:
                today = str(date.today())
                fiscal_year = self.env['account.fiscalyear'].search([('date_start','<=',today),('date_stop','>=',today)],limit=1)
                
                SQL = """
                    select hpl.salary_rule_id, hp.employee_id, hsr.name as name,sum(hpl.total) as tot 
                    from hr_payslip_line as hpl 
                    inner join hr_payslip as hp
                    on hpl.slip_id = hp.id
                    inner join hr_salary_rule hsr on hpl.salary_rule_id= hsr.id 
                    
                    where hp.employee_id = %s and hp.state in ('done') and hp.date_from >= %s and date_to <= %s
                    group by hpl.salary_rule_id,hp.employee_id,hsr.name order by hpl.salary_rule_id

                """
                self.env.cr.execute(SQL,(t.employee_id.id,str(fiscal_year.date_start),str(t.date_to)
                                          ))
                res = self.env.cr.fetchall()
                print"hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh",res
                return res
    
    @api.multi
    def view_account_voucher(self):
        return {
                'name' : _('Payment Order'),
                'view_type' : 'form',
                'view_mode' : 'tree,form',
                'res_model' : 'account.voucher',
                'type' : 'ir.actions.act_window',
                'domain' : [('payslip_id','=',self.id)],
                
                }
        
    #added by sangita    
    @api.multi
    def hr_employee_holiday_request_leave_left(self):
        return{
            'name': _('Leaves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.holidays',
            'src_model' : 'hr.employee',
            'type': 'ir.actions.act_window',
            'domain':[('holiday_type','=','employee'), ('holiday_status_id.limit', '=', False), ('state','!=', 'refuse')],
            'context': {'search_default_employee_id': self.employee_id.id, 'default_employee_id': self.employee_id.id, 'search_default_group_type': 1,
                'search_default_year': 1},
            'search_view_id' : self.env.ref('hr_holidays.view_hr_holidays_filter').id
            }
        
    
    #added by sangita
    @api.multi
    def compute_sheet(self):
#         print"@@@@@@@@@@@@@@@@@@@@@@@@@@WWWWWWWWWWWWW"
#         for contract in self.contract_id:
#             self.account_id = contract.account_id.id
#             print"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",s.account_id
        for s in self:
            for loan in s.loan_ids:
                if loan.date <= s.date_to:
                    loan.paid = True
            return super(HrPayslip,s).compute_sheet()
       
    @api.multi
    def refund_sheet(self):
        res =  super(HrPayslip,self).refund_sheet()
        self.state = 'cancel'
        for s in self:
            for loan in s.loan_ids:
                if loan.date <= s.date_to:
                    loan.paid = False
        self.refund_id = res.ids
        return True
       

    @api.multi
    def refund_sheet(self):
        for payslip in self:
            copied_payslip = payslip.copy({'credit_note': True, 'name': _('Refund: ') + payslip.name})
            copied_payslip.action_payslip_done()
            payslip.state = 'cancel'
            for loan in payslip.loan_ids:
                if loan.date <= payslip.date_to:
                    loan.paid = False
#         copied_payslip = self.copy({'credit_note': True, 'name': _('Refund: ') + s.name})
            payslip.refund_id = copied_payslip
        formview_ref = self.env.ref('hr_payroll.view_hr_payslip_form', False)
        treeview_ref = self.env.ref('hr_payroll.view_hr_payslip_tree', False)
#         print"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,",copied_payslip.ids
        return {
            'name': ("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.do_nothing',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'), (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }
   

    @api.model
    def create(self,vals):
        res = super(HrPayslip,self).create(vals)
        res.get_loan()
        return res 
    
    
    @api.multi
    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        print"???????????????????????????????????????????"
        if self.state == 'done':
            lwp_id = self.env['hr.holidays'].search([('employee_id','=',self.employee_id.id)])
            for lwp in lwp_id:
                print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",lwp_id
                lwp.payslip_status = True
                lwp.payslip_id = self.id
        return res
    #Added by Sangita When in payslip select from date is jan and to date is feb the payslip name genereated by date to name
    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):

        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_to, "%Y-%m-%d")))
        locale = self.env.context.get('lang', 'en_US')
        self.name = _('Salary Slip of %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        if not self.contract_id.struct_id:
            return
        self.struct_id = self.contract_id.struct_id

        #computation of the salary input
        worked_days_line_ids = self.get_worked_day_lines(contract_ids, date_from, date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines

        input_line_ids = self.get_inputs(contract_ids, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        return

#added by sangita
class AccountVoucher(models.Model):
    _inherit = 'account.voucher'        

    payslip_id = fields.Many2one('hr.payslip',string="payslip")
        
class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    account_id = fields.Many2one('account.account',string="Account",state={'draft': [('readonly', False)]})
     
#added by sangita
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    pf_no = fields.Char(string="P F No")
    esi_no = fields.Char(string="ESI No")
    pan = fields.Char(string="PAN")
    
#added by sangita
class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    _rec_name = 'sequence'
    _order_by = 'sequence'
    
    appear_in_allowance = fields.Boolean(string="Appear in Allowance")
    
    @api.multi
    def name_get(self):
        result=[]
        for record in self:
            name='['+str(record.sequence)+']'+' '+record.name
            result.append((record.id, name))
        return result

    
#added by sangita
class HrPayslipYear(models.Model):
    _name = 'hr.payslip.year'

    salary_rule_id = fields.Many2one('hr.salary.rule',string="Rule Name")
    total = fields.Float(string="Amount")
    hr_payslip_id = fields.Many2one('hr.payslip',string="Current Payslip Id")
    
#added by sangita
class HrHolidays(models.Model):
    _inherit = 'hr.holidays'
    
    
    #added by sangita
#     @api.multi
    @api.constrains('holiday_status_id')
    def onchange_holiday_status(self):
        if self.holiday_status_id.earned_leaves == True:
            self.earned_leaves = True
        if self.holiday_status_id.sick_leaves == True:
            self.sick_leaves = True
        if self.holiday_status_id.casual_leaves == True:
            self.casual_leaves = True
            
    
    earned_leaves = fields.Boolean(string="Earned Leaves",readonly=True)
    sick_leaves = fields.Boolean(string="Sick Leaves",readonly=True)
    casual_leaves = fields.Boolean(string="Casual Leaves",readonly=True)
     
    payslip_id = fields.Many2one('hr.payslip',string="Payslip ID")
    
#added by sangita
class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'
    
    earned_leaves = fields.Boolean(string="Earned Leaves")
    sick_leaves = fields.Boolean(string="Sick Leaves")
    casual_leaves = fields.Boolean(string="Casual Leaves") 
    
          