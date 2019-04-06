# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json

# class accountcore(models.Model):
#     _name = 'accountcore.accountcore'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100


class Org(models.Model):

    _name = 'accountcore.org'
    number = fields.Char(string='机构编码', required=True)
    name = fields.Char(string='机构名称', required=True)
    # items = fields.One2many('accountcore.item', 'org', string="核算项目")
    accounts = fields.One2many('accountcore.account', 'org', string='科目')
    _sql_constraints = [('accountcore_org_number_unique', 'unique(number)',
                         '机构编码重复了!'),
                        ('accountcore_org_name_unique', 'unique(name)',
                         '机构名称重复了!')]


class ItemClass(models.Model):

    _name = 'accountcore.itemclass'
    name = fields.Char(string='核算项目类别名称', required=True)
    number = fields.Char(string='核算项目类别编码', required=True)
    _sql_constraints = [('accountcore_itemclass_number_unique',
                         'unique(number)', '核算项目类别编码重复了!'),
                        ('accountcore_itemclass_name_unique', 'unique(name)',
                         '核算项目类别名称重复了!')]


class Item(models.Model):

    _name = 'accountcore.item'
    org = fields.Many2one(
        'accountcore.org',
        string='机构',
        help="核算项目所属机构",
        index=True,
        required=True,
        ondelete='restrict')
    number = fields.Char(string='核算项目编码', required=True)
    name = fields.Char(string='核算项目名称', required=True, help="核算项目名称")
    itemClass = fields.Many2one(
        'accountcore.itemclass',
        string='核算项目类别',
        index=True,
        required=True,
        ondelete='restrict')
    _sql_constraints = [('accountcore_item_number_unique', 'unique(number)',
                         '核算项目编码重复了!'),
                        ('accountcore_item_name_unique', 'unique(name)',
                         '核算项目名称重复了!')]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if 'filter_itemByItemClass' in self.env.context:
            filter_itemClass = self.env.context['filter_itemByItemClass']
            args.append(('itemclass', 'in', filter_itemClass))
        return super(Item, self).name_search(name, args, operator, limit)


class RuleBook(models.Model):

    _name = 'accountcore.rulebook'
    number = fields.Char(string='账簿编码', required=True)
    name = fields.Char(string='账簿名称', required=True, help='用于生成不同口径的账套')
    _sql_constraints = [('accountcore_rulebook_number_unique',
                         'unique(number)', '账簿编码重复了!'),
                        ('accountcore_rulebook_name_unique', 'unique(name)',
                         '账簿名称重复了!')]


class AccountClass(models.Model):
    _name = 'accountcore.accountclass'
    number = fields.Char(string='科目类别编码', required=True)
    name = fields.Char(string='科目类别名称', required=True)
    _sql_constraints = [('accountcore_accountclass_number_unique',
                         'unique(number)', '科目类别编码重复了!'),
                        ('accountcore_accountclass_name_unique',
                         'unique(name)', '科目类别名称重复了!')]


class Account(models.Model):
    _name = 'accountcore.account'

    org = fields.Many2one(
        'accountcore.org',
        string='所属机构',
        help="科目所属机构",
        index=True,
        ondelete='restrict')

    accountClass = fields.Many2one(
        'accountcore.accountclass',
        string='科目类别',
        index=True,
        ondelete='restrict')
    number = fields.Char(string='科目编码', required=True)
    name = fields.Char(string='科目名称', required=True)
    cashFlowControl = fields.Boolean(string='分配现金流量')
    itemClasses = fields.Many2many(
        'accountcore.itemclass', string='包含的核算项目类别', ondelete='restrict')
    _sql_constraints = [('accountcore_account_number_unique', 'unique(number)',
                         '科目编码重复了!'),
                        ('accountcore_account_name_unique', 'unique(name)',
                         '科目名称重复了!')]


class CashFlowType(models.Model):

    _name = 'accountcore.cashflowtype'
    number = fields.Char(string='现金流量项目类别编码', required=True)
    name = fields.Char(string='现金流量项目类别', required=True)
    _sql_constraints = [('accountcore_cashflowtype_number_unique',
                         'unique(number)', '现金流量类别编码重复了!'),
                        ('accountcore_cashflowtype_name_unique',
                         'unique(name)', '现金流量类别名称重复了!')]


class CashFlow(models.Model):
    _name = 'accountcore.cashflow'
    cashFlowType = fields.Many2one(
        'accountcore.cashflowtype', string='现金流量类别', required=True, index=True)
    number = fields.Char(string="现金流量编码", required=True)
    name = fields.Char(string='现金流量名称', required=True)

    _sql_constraints = [('accountcore_cashflow_number_unique',
                         'unique(number)', '现金流量编码重复了!'),
                        ('accountcore_cashflow_name_unique', 'unique(name)',
                         '现金流量名称重复了!')]


class VoucherFile(models.Model):
    _name = 'accountcore.voucherfile'
    appedixfileType = fields.Char(string='文件类型', required=True)


class Source(models.Model):
    _name = 'accountcore.source'
    number = fields.Char(string='凭证来源编码', required=True)
    name = fields.Char(string='凭证来源名称', required=True)
    _sql_constraints = [('accountcore_source_number_unique', 'unique(number)',
                         '凭证来源编码重复了!'),
                        ('accountcore_source_name_unique', 'unique(name)',
                         '凭证来源名称重复了!')]


class Voucher(models.Model):
    _name = 'accountcore.voucher'
    name = fields.Char(default='凭证')
    voucherdate = fields.Date(string='记账日期', required=True, placeholder='记账日期')
    soucre = fields.Many2one(
        'accountcore.source',
        string='凭证来源',
        default=1,
        readonly=True,
        required=True,
        ondelete='restrict')
    org = fields.Many2one(
        'accountcore.org',
        string='所属机构',
        required=True,
        index=True,
        ondelete='restrict')
    ruleBook = fields.Many2one(
        'accountcore.rulebook',
        string='所属账簿',
        required=True,
        index=True,
        ondelete='restrict')
    number = fields.Char(string='凭证编号', required=True)
    appendixCount = fields.Integer(string='附件张数', default=1)
    createUser = fields.Many2one(
        'res.users',
        string='制单人',
        default=lambda s: s.env.uid,
        readonly=True,
        required=True,
        ondelete='restrict',
        index=True)
    reviewer = fields.Many2one(
        'res.users',
        string='审核人',
        ondelete='restrict',
        readonly=True,
        indext=True)
    entrys = fields.One2many('accountcore.entry', 'voucher', string='分录')
    voucherFile = fields.Many2one(
        'accountcore.voucherfile', string='附件文件', ondelete='restrict')
    state = fields.Selection([('creating', '制单'), ('reviewed', '审核')],
                             default='creating')

    # 审核凭证
    @api.multi
    def reviewing(self, ids):
        self.write({'state': 'reviewed', 'reviewer': self.env.uid})

    # 取消审核
    @api.multi
    def cancelReview(self, ids):
        self.write({'state': 'creating', 'reviewer': None})


class Enty(models.Model):
    _name = 'accountcore.entry'
    voucher = fields.Many2one(
        'accountcore.voucher', string='所属凭证', index=True, ondelete='cascade')
    sequence = fields.Integer('Sequence')
    explain = fields.Char(string='说明')
    account = fields.Many2one(
        'accountcore.account', string='科目', required=True, index=True)
    items = fields.Many2many(
        'accountcore.item', string='核算项目', index=True, ondelete='restrict')
    # dOrc = fields.Selection([(1, '借'), (-1, '贷')], string='借贷', index=True)
    currency_id = fields.Many2one(
        'res.currency',
        compute='_get_company_currency',
        readonly=True,
        string="Currency",
        help='Utility field to express amount currency')
    damount = fields.Monetary(string='借方金额')
    camount = fields.Monetary(string='贷方金额')
    cashFlow = fields.Many2one(
        'accountcore.cashflow',
        string='现金流量项目',
        index=True,
        ondelete='restrict')


# class AccountSettings(models.TransientModel):
#     _inherit = 'res.config.settings'
#     _name = 'accountcore.configsettings'

#     default_org = fields.Many2one(
#         'accountcore.org', string='所属机构', default_model='accountcore.voucher')


# 用户设置模型字段的默认取值
class AccountcoreUserDefaults(models.TransientModel):
    _name = 'accountcoure.userdefaults'
    default_ruleBook = fields.Many2one('accountcore.rulebook', string='默认账套')
    default_org = fields.Many2one('accountcore.org', string='默认机构')
    default_voucherDate = fields.Date(
        string='记账日期', default=fields.Date.today())

    @api.model
    def create(self, values):
        rl = super(AccountcoreUserDefaults, self).create(values)
        rl.setDefaults()
        return rl

    def setDefaults(self):
        modelName = 'accountcore.voucher'
        self.setDefault(modelName, 'ruleBook', self.default_ruleBook.id)
        self.setDefault(modelName, 'org', self.default_org.id)
        self.setDefault(
            modelName, 'voucherdate',
            json.dumps(self.default_voucherDate.strftime('%Y-%m-%d')))

    # 设置默认值

    def setDefault(self, modelName, fieldName, defaultValue):
        idOfField = self.getIdOfIdField(
            fieldName,
            modelName,
        )
        rd = self.getDefaultRecord(idOfField)
        if rd.exists():
            self.modifyDefault(rd, idOfField, defaultValue)
        else:
            self.createDefault(idOfField, defaultValue)

    # 获取要设置默认值的字段在ir.model.fields中的id
    def getIdOfIdField(self, fieldName, modelname):
        domain = [('model', '=', modelname), ('name', '=', fieldName)]
        rds = self.env['ir.model.fields'].sudo().search(domain, limit=1)
        return rds.id

    # 是否已经设置过该字段的默认值
    def getDefaultRecord(self, id):
        domain = [('field_id', '=', id), ('user_id', '=', self.env.uid)]
        rds = self.env['ir.default'].sudo().search(domain, limit=1)
        return rds

    def modifyDefault(self, rd, idOfField, defaultValue):
        rd.write({
            'field_id': idOfField,
            'json_value': defaultValue,
            'user_id': self.env.uid
        })

    def createDefault(self, idOfField, defaultValue):
        self.env['ir.default'].sudo().create({
            'field_id': idOfField,
            'json_value': defaultValue,
            'user_id': self.env.uid
        })
