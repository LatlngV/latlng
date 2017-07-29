# -*- coding: utf-8 -*-

from odoo import api, models, fields
from datetime import datetime
import time


class LeaderCountersign(models.Model):
    _name = "leader.countersign"
    _rec_name = "name"

    SELECT_LAUNCH_COUNTERSIGN = [("apply", U"申请"), ("countersign", u"会签中"), ("finish", u"结束")]
    SELECT_FINAL_RESULT = [("confirm", u"通过"), ("cancel", u"拒绝"), ("no_confirm", u"通过 (有人未选择)"),
                           ("no_cancel", u"拒绝 (有人未选择)")]

    title = fields.Char(string=u"标题", required=True)
    name = fields.Many2one("res.users", string=u"申请人", default=lambda self: self.env.user.id, readonly=True)
    department = fields.Char(compute="_compute_department", string=u"部门", store=True)
    datetime = fields.Datetime(string=u"日期", default=fields.Datetime.now, readonly=True)
    # datetime = fields.Date(string=u"日期", default=fields.Date.context_today, readonly=True)
    state = fields.Selection(SELECT_LAUNCH_COUNTERSIGN, string=u"会签状态", default="apply")
    hide_state = fields.Char(string=u"隐藏状态", compute="_compute_state")
    final_state = fields.Selection(SELECT_FINAL_RESULT, string=u"申请结果", compute="_compute_final_state", store=True)
    apply_detail_line = fields.One2many("apply.detail", "countersign_id", string=u"申请详情", required=True)
    leader_line = fields.One2many("leader.line", "leader_line_id", string=u"会签领导", required=True)
    total = fields.Float(string=u"总计 (人民币)", digits=(10, 1), compute="_compute_total_money", help=u"单位:元", store=True)
    count = fields.Integer(string=u"计数", default=0)
    receive_account = fields.Char(string=u"收款账户", required=True)
    payee = fields.Char(string=u"收款人", required=True)
    bank = fields.Char(string=u"开户银行", required=True)

    @api.depends("name")
    def _compute_department(self):
        """
            计算员工所属部门:
                1. 获取所有员工
                2. 获取当前用户的 ID 与员工表关联的 res.users 表里的 ID 比较
                3. 相等就返回员工所在部门
        """
        hr_employee = self.env["hr.employee"].search([])
        for record in self:
            for employee_id in hr_employee:
                if record.name.id == employee_id.user_id.id:
                    record.department = employee_id.department_id.name
                    return True

    @api.depends("state")
    def _compute_final_state(self):
        """
            /**
             * 1. 判断会签的状态是不是 "finish"，如果不是结束本次循环
             * 2. 判断 count 与 Leader 的数量是否相等 (封装了一个函数 "_set_final_state"，以下逻辑都在此函数中)
             *      True:
             *          1.) 判断 Leader 有没有 "cancel"，如果有就将申请状态置为 "cancel"，
             *              并将 flag 置为 False，结束当前循环
             *          2.）先进入 1.） 中进行判断，Leader 没有 "cancel" 状态就将申请状态置为 "confirm"
             *      False:
             *          同 True，只是申请状态不一样
             */
        """
        for record in self:
            if record.state != "finish":
                break
            if record.count == len(record.leader_line):
                self._set_final_state(record, "cancel", "confirm")
            else:
                self._set_final_state(record, "no_cancel", "no_confirm")

    def _set_final_state(self, record, cancel, confirm):
        flag = True
        for line in record.leader_line:
            if line.state == "cancel":
                record.final_state = cancel
                flag = False
                break
        if flag:
            record.final_state = confirm

    @api.multi
    def _compute_state(self):
        """
            计算状态:
                1. 判断是不是在 countersign 状态
                2. 如果是就判断当前日期是不是超过设定日期
                    1) 设定日期: 创建申请单的日期加上两天
                3. 如果是就将状态设置为 “结束”
        """
        for record in self:
            if record.state == "apply" or record.state == "finish":
                continue
            current_date = datetime.now()
            record_date = datetime.strptime(record.datetime, "%Y-%m-%d %H:%M:%S")
            time_stamp = int(time.mktime(record_date.timetuple())) + 24 * 60 * 60
            end_date = datetime.fromtimestamp(time_stamp)
            if current_date > end_date:
                record.write({"state": "finish"})

    @api.depends("apply_detail_line")
    def _compute_total_money(self):
        """
            计算总钱数
        """
        for record in self:
            for line in record.apply_detail_line:
                record.total += line.money

    @api.multi
    def action_apply(self):
        """
            发起申请: 判断当前用户是不是申请人
            :return: True:  改变状态
                     False: 状态不变
        """
        if self.env.user.id == self.name.id:
            self.state = "countersign"
            self.datetime = datetime.now()
            return True
        else:
            return True

    @api.multi
    def action_confirm(self):
        self._change_state("confirm")

    @api.multi
    def action_cancel(self):
        self._change_state("cancel")

    def _change_state(self, state):
        """
            同意或拒绝申请人的申请:
                1. 判断当前用户是不是 Leader
                2. 判断 Leader 是不是确认过
                3. 判断 “确认” + “拒绝” 的数量与 Leader 的数量是否相等
        """
        if self.env.user.id == self.name.id:
            return True
        for record in self.leader_line:
            if self.env.user.id == record.leader.user_id.id:
                if record.state == "confirm" or record.state == "cancel":
                    return True
                else:
                    record.state = state
        self.count += 1
        if self.count == len(self.leader_line):
            self.state = "finish"
            return True

    @api.multi
    def action_reapply(self):
        """
            重新申请:
                1. 判断当前用户是不是申请人
                2. 判断 Leader 有没有拒绝
                3. 如果有拒绝，清空所有状态，并把 “数量” 重置为 0
        """
        if self.env.user.id != self.name.id:
            return True
        for record in self.leader_line:
            if record.state == "cancel":
                self.state = "apply"
                self.count = 0
                for line in self.leader_line:
                    line.state = ""


class ApplyDetail(models.Model):
    _name = "apply.detail"

    countersign_id = fields.Many2one("leader.countersign", string=u"申请人")
    number = fields.Integer(string=u"序号", default=1)
    detail = fields.Char(string=u"原由", required=True)
    money = fields.Float(string=u"金额 (人民币)", digits=(10, 1),
                         required=True, help=u"单位:元，精确到 '角'，例如：123.4")


class LeaderLine(models.Model):
    _name = "leader.line"

    SELECT_STATE = [("confirm", u"确认"), ("cancel", u"拒绝")]

    leader_line_id = fields.Many2one("leader.countersign", string=u"申请人", required=True)
    leader = fields.Many2one("hr.employee", string=u"领导", required=True)
    state = fields.Selection(SELECT_STATE, string=u"状态", readonly=True)
