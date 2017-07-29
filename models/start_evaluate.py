# -*- coding: utf-8 -*-

from odoo import api, models, fields
from datetime import datetime
import time


class EmployeeStartEvaluate(models.Model):
    _name = "employee.start.survey"
    _rec_name = "title"

    title = fields.Many2one("survey.survey", string=u"标题", required=True)
    start_date = date = fields.Date(string=u"开始日期", default=fields.Date.context_today, required=True)
    end_date = fields.Date(string=u"结束日期", required=True)
    passive_evaluate_line = fields.One2many("employee.passive.survey", "passive_evaluate_id",
                                            string=u"Passive Evaluate Line", required=True, ondelete="set null")
    evaluate_line = fields.One2many("employee.survey", "evaluate_id", string=u"Evaluate Line", required=True,
                                    ondelete="set null")
    complete = fields.Boolean(string=u"是否结束", compute="_compute_complete", default=False)

    @api.multi
    def _compute_complete(self):
        """
            计算是否到了结束时间
            :return: True:  已结束，评价界面的 Button 不可点击
                     False: 未结束，评价界面的 Button 可以点击
        """
        for record in self:
            current_date = datetime.now()
            end = time.strptime(record.end_date, "%Y-%m-%d")
            time_stamp = int(time.mktime(end)) + 24 * 60 * 60
            date_array = datetime.fromtimestamp(time_stamp)
            if current_date > date_array:
                record.complete = True
            else:
                record.complete = False


class EmployeePassiveSurvey(models.Model):
    _name = "employee.passive.survey"
    _rec_name = "passive_survey"

    passive_evaluate_id = fields.Many2one("employee.start.survey", string=u"Passive Survey Id")
    passive_survey = fields.Many2one("hr.employee", string=u"被评价人", required=True)
    survey_title = fields.Char(string=u"评价标题", related="passive_evaluate_id.title.title", store=True)
    state = fields.Boolean(string=u"评价是否结束", related="passive_evaluate_id.complete")
    complete = fields.Boolean(string=u"是否完成", compute="_get_complete", default=False)

    @api.multi
    def action_survey_survey(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Results of the Survey",
            'target': 'self',
            'url': "/survey/start/" + str(self.passive_evaluate_id.title.id) + "/phantom/" + str(self.id)
        }

    @api.multi
    def _get_complete(self):
        """
            是否完成对某个人的评价
            :return: True:  已完成，Button 不可点击
                     False: 未完成，Button 可以点击
        """
        user_input = self.env['survey.user_input'].search([('expire', '=', False)])
        for record in user_input:
            for line in self:
                # 此处 if 判断可以用关键字 and 进行连接
                if record.passive_name == line.passive_survey.name_related:
                    if record.survey_id == line.passive_evaluate_id.title:
                        if self.env.user == record.evaluate_name:
                            line.complete = True


class EmployeeSurvey(models.Model):
    _name = "employee.survey"

    evaluate_id = fields.Many2one("employee.start.survey", string=u"Survey Id")
    survey_people = fields.Many2one("hr.employee", string=u"参与评价人", required=True)
