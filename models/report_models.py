# -*- coding: utf-8 -*-
from odoo import models, fields
from .main_models import Glob_tag_Model


# 报表接收者
class Receiver(models.Model, Glob_tag_Model):
    '''报表接收者'''
    _name = "accountcore.receiver"
    _description = '报表的报送对象'
    number = fields.Char(string='接收者编号')
    name = fields.Char(string='接收者', required=True)
    _sql_constraints = [ ('accountcore_receiver_name_unique', 'unique(name)',
                         '接收者名称重复了!')]


# 报表类型
class ReportType(models.Model, Glob_tag_Model):
    '''报表类型'''
    _name = 'accountcore.report_type'
    _description = '报表的类型，例如：资产负债表，利润表等'
    number = fields.Char(string='报表类型编号')
    name = fields.Char(string='报表类型名称', required=True)
    _sql_constraints = [('accountcore_reportytpe_name_unique', 'unique(name)',
                         '报表类型名称重复了!')]


# 归档报表
class StorageReport(models.Model, Glob_tag_Model):
    '''归档的报表'''
    _name = 'accountcore.storage_report'
    _description = '归档的报表'
    report_type = fields.Many2one('accountcore.report_type')
    number = fields.Char(string='归档报表编号')
    name = fields.Char(string='归档报表名称', required=True)
    create_user = fields.Many2one('res.users',
                                  string='归档人',
                                  default=lambda s: s.env.uid,
                                  readonly=True,
                                  required=True,
                                  ondelete='restrict',
                                  index=True)
    start_date = fields.Date(string='数据开始月份')
    end_date = fields.Date(string='数据结束月份')
    orgs = fields.Many2many('accountcore.org', string='机构范围', required=True)
    receivers = fields.Many2many('accountcore.receiver', string='接收者')
    summary = fields.Text(string='归档报表说明')
    data = fields.Text(string='数据内容')
    htmlstr = fields.Html(string='html内容')


# 报表模板
class ReportModel(models.Model, Glob_tag_Model):
    '''报表模板'''
    _name = 'accountcore.report_model'
    _description = '报表模板，用于生成报表'
    guid = fields.Char(string='报表模板唯一码', required=True)
    name = fields.Char(string='报表模板名称', required=True)
    version = fields.Char(string='报表模板版本')
    summary = fields.Text(string='报表模板简介')
    explain = fields.Html(string='报表模板详细介绍')
    _sql_constraints = [ ('accountcore_repormodel_name_unique', 'unique(name)',
                         '报表模板唯一码重复了!')]
