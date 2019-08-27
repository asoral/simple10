{
    "name": "PaySlip Batch Extended",
    "version": "10.3.1.7",
    "category": "PaySlip",
    'summary': 'PaySlip Batch Extended',
    'description': """last Update sangita- 13/12/2018 add ver.(.1)
                    last update sangita 12/02/2019
                    Last Updated by Sangita Payment order confirm date should be payment create date 09/05/2019
                    Last Updated by Sangita 21/05/2019 Name should be date_to 
                    Last Updated by Sangita When Btach is created and close double account entries created and payslip issue
                    30/05/2019
                    """,
    "author": "Akhodifad",
    "contributors": [
                    "Dexciss Technology (Akhodifad)",
                    "Dexciss Technology (Dhananjay)",
                    "Dexciss Technology (Sangita)",
                    ],
    "depends": [
                'hr','hr_payroll','hr_holidays','hr_payroll_account','account','mail','ohrms_loan','ohrms_loan_accounting',
                'hr_payslip_monthly_report','fiscal_year'
                ],
    "data": [
            "report/payment_order_payslip_reports.xml",
            "report/payment_order_payslip_templates.xml",
            "views/payslip_batch_extended_view.xml",
            "views/report_payslipdetails_templates_inherit.xml",
#             "views/bulk_payslip_analysis_report.xml",
            "views/payment_order_view.xml",
            "views/menu_payslip_analysis_report.xml",
            "wizard/payslips_and_payslipbatch_wizard.xml",
            "wizard/payslip_report_analysis.xml",
            ],
            
    "installable": True
}
