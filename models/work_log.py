# -*- coding: utf-8 -*-

from odoo import api, models, fields
from datetime import datetime
import time


def _get_week_day(date):
    week_day_dict = {
        0: '星期一',
        1: '星期二',
        2: '星期三',
        3: '星期四',
        4: '星期五',
        5: '星期六',
        6: '星期天',
    }
    day = date.weekday()
    return week_day_dict[day]


class EmployeeLog(models.Model):
    _name = "employee.log"
    _rec_name = "employee"

    employee = fields.Many2one("res.users", string=u"员工", default=lambda self: self.env.user.id, readonly=True)
    department = fields.Char(compute="_compute_department", string=u"部门", store=True)
    date = fields.Date(string=u"日期", default=fields.Date.context_today, readonly=True)
    weekday = fields.Char(string=u"星期", default=_get_week_day(datetime.now().date()), readonly=True)
    employee_line = fields.One2many("employee.line", "employee_line_id", string=u"工作日志", required=True)
    state = fields.Boolean(string=u"是否到期", compute="_compute_state")

    @api.depends("employee")
    def _compute_department(self):
        hr_employee = self.env["hr.employee"].search([])
        for record in self:
            for employee_id in hr_employee:
                if record.employee.id == employee_id.user_id.id:
                    record.department = employee_id.department_id.name

    @api.multi
    def _compute_state(self):
        for record in self:
            current_date = datetime.now()
            end_date = datetime.strptime(record.date, "%Y-%m-%d")
            time_stamp = int(time.mktime(end_date.timetuple())) + 2 * 24 * 60 * 60
            date_array = datetime.fromtimestamp(time_stamp)
            if current_date > date_array:
                record.state = True


class EmployeeLine(models.Model):
    _name = "employee.line"

    SELECT_EMPLOYEE_LOG_LEVEL = [("general", u"一般"), ("middle", u"中等"),
                                 ("important", u"重要"), ("urgent", u"紧急")]

    employee_line_id = fields.Many2one("employee.log", string=u"Employee Line Id", required=True)
    number = fields.Integer(string=u"序号", required=True, default=1)
    log_line = fields.Text(string=u"工作日志", required=True)
    note = fields.Text(string=u"备注")
    state = fields.Boolean(string=u"是否完成", required=True)
    level = fields.Selection(SELECT_EMPLOYEE_LOG_LEVEL, string=u"级别", default="general", required=True)
