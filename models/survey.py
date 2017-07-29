# -*- coding: utf-8 -*-

from odoo import api, models, fields
from datetime import datetime


class Survey(models.Model):
    _inherit = "survey.survey"

    title = fields.Char(string=u"标题", required=True)
    start_survey_line = fields.One2many("employee.start.survey", "title", string=u"Start Survey Line", required=True)


class SurveyUseInput(models.Model):
    _inherit = "survey.user_input"
    _rec_name = "passive_name"

    passive_name = fields.Char(string=u"被评价人")
    evaluate_name = fields.Many2one("res.users", string=u"评价人", default=lambda self: self.env.user)
    score = fields.Integer(string=u"分数", compute="_compute_score", required=True)
    expire = fields.Boolean(string=u"是否过期", compute="_compute_expire")

    @api.multi
    def _compute_score(self):
        """
            计算总分
        """
        for employee in self:
            for line in employee.user_input_line_ids:
                employee.score += line.value_number

    @api.multi
    def _compute_expire(self):
        """
            用来判断记录是否在评价时间段内
            @:return True:  在评价时间内
                     False: 不在评价时间内
        """
        start_survey = self.env['employee.start.survey'].search([])
        for record in start_survey:
            current_date = datetime.now()
            end = datetime.strptime(record.end_date, "%Y-%m-%d")
            for line in self:
                if current_date > end and record.title == line.survey_id.title:
                    line.expire = True
                else:
                    line.expire = False
