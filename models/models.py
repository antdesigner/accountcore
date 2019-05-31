# -*- coding: utf-8 -*-
from odoo import models, fields, api
import sys
import json
from odoo import exceptions
from odoo import http
import decimal
import copy
import time
sys.path.append('.\.\server')

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
    number = fields.Char(string='核算机构编码', required=True)
    name = fields.Char(string='核算机构名称', required=True)
    # items = fields.One2many('accountcore.item', 'org', string="核算项目")
    accounts = fields.One2many('accountcore.account', 'org', string='科目')
    _sql_constraints = [('accountcore_org_number_unique', 'unique(number)',
                         '核算机构编码重复了!'),
                        ('accountcore_org_name_unique', 'unique(name)',
                         '核算机构名称重复了!')]


class ItemClass(models.Model):
    '''核算项目类别'''
    _name = 'accountcore.itemclass'
    name = fields.Char(string='核算项目类别名称', required=True)
    number = fields.Char(string='核算项目类别编码', required=True)
    _sql_constraints = [('accountcore_itemclass_number_unique',
                         'unique(number)', '核算项目类别编码重复了!'),
                        ('accountcore_itemclass_name_unique', 'unique(name)',
                         '核算项目类别名称重复了!')]


class Item(models.Model):
    '''核算项目'''
    _name = 'accountcore.item'
    org = fields.Many2one(
        'accountcore.org',
        string='核算机构',
        help="核算项目所属核算机构",
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
    def name_search(self, name='', args=None, operator='ilike', limit=20):
        if 'account' in self.env.context:
            accountId = self.env.context['account']
            account = self.env['accountcore.account'].sudo().browse(accountId)
            filter_itemClass = [
                itemclass.id for itemclass in account.itemClasses]
            args.append(('itemClass', 'in', filter_itemClass))
        return super(Item, self).name_search(name, args, operator, limit)

    @api.model
    def getEntryItems(self, ids):
        '''获得核算项目列表(前端凭证分录获得核算项目列表)'''
        items = self.browse(ids)
        itemslist = []
        for i in items:
            itemslist.append({'id': i.id, 'name': i.name,
                              'itemClass': i.itemClass.id})
        return itemslist
        # return [{'id': i.id, 'name': i.name,
        #                      'itemClass': i.itemClass.id} for i  in items]


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
    fatherAccountId = fields.Many2one(
        'accountcore.account',
        string='上级科目',
        help="科目的上级科目",
        index=True,
        ondelete='restrict')
    currentChildNumber = fields.Integer(default=10, string='新建下级科目待用编号')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('number', operator, name),
                      ('name', operator, name)]
        pos = self.search(domain+args, limit=limit)
        return pos.name_get()

    @api.model
    def get_itemClasses(self, accountId):
        '''获得科目下的核算项目'''
        itemClasses = self.browse([accountId]).itemClasses
        return [{'id': i.id, 'name': i.name} for i in itemClasses]


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
    direction = fields.Selection(
        [("-1", "流出"), ("1", "流入")], string='流量方向', required=True)
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
    '''会计凭证'''
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
    number = fields.Integer(
        string='凭证编号', help='该编号更据不同凭证编号策略会不同',  compute='_getVoucherNumber', search="_searchNumber")
    appendixCount = fields.Integer(string='附件张数', default=1, required=True)
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
    entrys = fields.One2many(
        'accountcore.entry', 'voucher', string='分录')
    voucherFile = fields.Many2one(
        'accountcore.voucherfile', string='附件文件', ondelete='restrict')
    state = fields.Selection([('creating', '制单'), ('reviewed', '已审核')],
                             default='creating')
    uniqueNumber = fields.Char(string='唯一编号')
    numberTasticsContainer_str = fields.Char(string='凭证可用编号策略', default="{}")
    entrysHtml = fields.Html(string="分录内容", compute='_createEntrysHtml')
    @api.multi
    def reviewing(self, ids):
        '''审核凭证'''
        self.write({'state': 'reviewed', 'reviewer': self.env.uid})
        return False

    @api.multi
    def cancelReview(self, ids):
        '''取消凭证审核'''
        self.write({'state': 'creating', 'reviewer': None})

    @api.model
    def create(self, values):
        '''新增凭证'''

        values['uniqueNumber'] = self.env['ir.sequence'].next_by_code(
            'voucher.uniqueNumber')
        rl = super(Voucher, self).create(values)
        if 'entrys' in values:
            rl._checkVoucher(values)
        return rl

    @api.multi
    def write(self, values):
        '''修改编辑凭证'''
        self.ensure_one
        rl_bool = super(Voucher, self).write(values)
        if 'entrys' in values:
            self._checkVoucher(values)
        return rl_bool

    @api.depends('numberTasticsContainer_str')
    def _getVoucherNumber(self):
        '''获得凭证编号,依据用户默认的凭证编号策略'''
        if(self.env.user.voucherNumberTastics):
            currentUserNumberTastics_id = self.env.user.voucherNumberTastics.id
        else:
            for record in self:
                record.number = 0
            return True
        for record in self:
            record.number = self.getNumber(
                record.numberTasticsContainer_str, currentUserNumberTastics_id)
        return record.number

    @staticmethod
    def getNumber(container_str, numberTastics_id):
        '''设置获得对应策略下的凭证编号'''
        container = json.loads(container_str)
        number = container.get(str(numberTastics_id), 0)
        return number

    @staticmethod
    def getNewNumberDict(container_str, numberTastics_id, number):
        '''获得改变后的voucherNumberTastics字段数字串'''
        container = json.loads(container_str)
        container[str(numberTastics_id)] = number
        newNumberDict = json.dumps(container)
        return newNumberDict

    @api.model
    def _checkVoucher(self, voucherDist):
        '''凭证检查'''
        self._checkEntyCount(voucherDist)
        self._checkCDBalance(voucherDist)
        self._checkChashFlow(voucherDist)
        self._checkCDValue(voucherDist)

    @api.model
    def _checkEntyCount(self, voucherDist):
        '''检查是否有分录'''
        if 'entrys' in voucherDist:
            return True
        else:
            raise exceptions.ValidationError('没有录入会计分录')

    @api.model
    def _checkCDBalance(self, voucherDist):
        '''检查借贷平衡'''
        camount = 0
        damount = 0
        camount = sum(entry.camount for entry in self.entrys)
        damount = sum(entry.damount for entry in self.entrys)
        if camount == damount and camount != 0:
            return True
        else:
            raise exceptions.ValidationError('借贷金额不平衡或不能在同一方向')

    @api.model
    def _checkCDValue(self, voucherDist):
        '''分录借贷方是否全部为零'''
        for entry in self.entrys:
            if entry.camount == 0 and entry.damount == 0:
                raise exceptions.ValidationError('借贷方金额不能全为零')
        return True

    @api.model
    def _checkChashFlow(self, voucherDist):
        pass

    @api.multi
    def copy(self, default=None):
        '''复制凭证'''
        updateFields = {'state': 'creating',
                        'reviewer': None,
                        'createUser': self.env.uid,
                        'numberTasticsContainer_str': '{}',
                        'appendixCount': 1}
        rl = super(Voucher, self).copy(updateFields)
        for entry in self.entrys:
            entry.copy({'voucher': rl.id})
        return rl

    @api.multi
    def _createEntrysHtml(self):
        '''购建凭证分录展示内容'''
        start_cpu = time.clock()
        content = None
        entrys = None
        for voucher in self:
            content = "<table class='oe_accountcore_entrys'>"
            if voucher.entrys:
                entrys = voucher.entrys
                for entry in entrys:
                    content = content+self._buildingEntryHtml(entry)
            content = content+"</table>"
            voucher.entrysHtml = content
        end_cpu = time.clock()
        print("%f cpu seconds" % (end_cpu-start_cpu))
        return True

    def _buildingEntryHtml(self, entry):
        content = ""
        items = ""
        for item in entry.items:
            items = items+"<div>"+item.name+"</div>"
        if entry.explain:
            explain = entry.explain
        else:
            explain = "*"
        damount = format(
            entry.damount, '0.2f') if entry.damount != 0 else ""
        camount = format(
            entry.camount, '0.2f') if entry.camount != 0 else ""
        content = content+"<tr>"+"<td class='oe_ac_explain'>" + \
            explain+"</td>"+"<td class='oe_ac_account'>" + \
            entry.account.name+"</td>" + "<td class='o_list_number'>" + \
            damount+"</td>" + "<td class='o_list_number'>" + \
            camount+"</td>" + "<td class='oe_ac_items'>" + \
            items+"</td>"
        if entry.cashFlow:
            content = content+"<td class='oe_ac_cashflow'>"+entry.cashFlow.name+"</td></tr>"
        else:
            content = content+"<td class='oe_ac_cashflow'></td></tr>"
        return content

    def _searchNumber(self, operater, value):
        '''计算字段凭证编号的查找'''
        comparetag = ('>', '>=', '<', '<=')
        if operater in comparetag:
            raise exceptions.UserError('这里不能使用比较大小查询,请使用=号')
        tasticsValue1 = '%"' + \
            str(self.env.user.voucherNumberTastics.id)+'": '+str(value)+',%'
        tasticsValue2 = '%"' + \
            str(self.env.user.voucherNumberTastics.id)+'": '+str(value)+'}%'
        return['|', ('numberTasticsContainer_str', 'like', tasticsValue1), ('numberTasticsContainer_str', 'like', tasticsValue2)]


class Enty(models.Model):
    '''一条分录'''
    _name = 'accountcore.entry'
    voucher = fields.Many2one(
        'accountcore.voucher', string='所属凭证', index=True, ondelete='cascade')
    sequence = fields.Integer('Sequence')
    explain = fields.Char(string='说明')
    account = fields.Many2one(
        'accountcore.account', string='科目', required=True, index=True)
    items = fields.Many2many(
        'accountcore.item', string='核算项目', index=True, ondelete='restrict')
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

    # accountItemClasses = fields.Many2many(
    #     related='account.itemClasses', string='科目的核算项目类别')

    @api.onchange('damount')
    def _damountChange(self):
        if self.damount != 0:
            self.camount = 0

    @api.onchange('camount')
    def _CamountChange(self):
        if self.camount != 0:
            self.damount = 0

    @api.onchange('account')
    # 改变科目时删除核算项目关联
    def _deleteItemsOnchange(self):
        self.items = None

    def _get_company_currency(self):
        pass


class AccountcoreUserDefaults(models.TransientModel):
    '''用户设置模型字段的默认取值'''
    _name = 'accountcoure.userdefaults'
    default_ruleBook = fields.Many2one('accountcore.rulebook', string='默认账套')
    default_org = fields.Many2one('accountcore.org', string='默认机构')
    default_voucherDate = fields.Date(
        string='记账日期', default=fields.Date.today())

    # 设置新增凭证,日期,机构和账套字段的默认值
    def setDefaults(self):
        modelName = 'accountcore.voucher'
        self._setDefault(modelName, 'ruleBook', self.default_ruleBook.id)
        self._setDefault(modelName, 'org', self.default_org.id)
        self._setDefault(
            modelName, 'voucherdate',
            json.dumps(self.default_voucherDate.strftime('%Y-%m-%d')))
        return True

    # 设置默认值
    def _setDefault(self, modelName, fieldName, defaultValue):
        idOfField = self._getIdOfIdField(
            fieldName,
            modelName,
        )
        rd = self._getDefaultRecord(idOfField)
        if rd.exists():
            self._modifyDefault(rd, idOfField, defaultValue)
        else:
            self._createDefault(idOfField, defaultValue)

    # 获取要设置默认值的字段在ir.model.fields中的id
    def _getIdOfIdField(self, fieldName, modelname):
        domain = [('model', '=', modelname), ('name', '=', fieldName)]
        rds = self.env['ir.model.fields'].sudo().search(domain, limit=1)
        return rds.id

    # 是否已经设置过该字段的默认值
    def _getDefaultRecord(self, id):
        domain = [('field_id', '=', id), ('user_id', '=', self.env.uid)]
        rds = self.env['ir.default'].sudo().search(domain, limit=1)
        return rds

    def _modifyDefault(self, rd, idOfField, defaultValue):
        rd.write({
            'field_id': idOfField,
            'json_value': defaultValue,
            'user_id': self.env.uid
        })

    def _createDefault(self, idOfField, defaultValue):
        self.env['ir.default'].sudo().create({
            'field_id': idOfField,
            'json_value': defaultValue,
            'user_id': self.env.uid
        })

# test


class Academe(http.Controller):
    @http.route('/academy/academy/', auth='public')
    def index(self, **kw):
        return "hello,world!"


class CreateChildAccountWizard(models.TransientModel):
    '''新增下级科目的向导'''
    _name = 'accountcore.create_child_account'
    fatherAccountId = fields.Many2one(
        'accountcore.account', string='上级科目', help='新增科目的直接上级科目')
    fatherAccountNumber = fields.Char(
        related='fatherAccountId.number', string='上级科目编码')

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
    @api.model
    def default_get(self, field_names):
        default = super().default_get(field_names)
        fatherAccountId = self.env.context.get('active_id')
        fatherAccount = self.env['accountcore.account'].sudo().search(
            [['id', '=', fatherAccountId]])
        default['fatherAccountId'] = fatherAccountId
        default['org'] = fatherAccount.org.id
        default['accountClass'] = fatherAccount.accountClass.id
        default['cashFlowControl'] = fatherAccount.cashFlowControl
        default['number'] = fatherAccount.number + \
            '.' + str(fatherAccount.currentChildNumber)
        return default

    @api.model
    def create(self, values):
        fatherAccountId = self.env.context.get('active_id')
        accountTable = self.env['accountcore.account'].sudo()
        fatherAccount = accountTable.search(
            [['id', '=', fatherAccountId]])
        newAccount = {'fatherAccountId': fatherAccountId,
                      'org': fatherAccount.org.id,
                      'accountClass': fatherAccount.accountClass.id,
                      'cashFlowControl': values['cashFlowControl'],
                      'name': fatherAccount.name+'---'+values['name'],
                      'number': fatherAccount.number + '.' + str(fatherAccount.currentChildNumber)}
        fatherAccount.currentChildNumber = fatherAccount.currentChildNumber+1
        values.update(newAccount)
        rl = super(CreateChildAccountWizard, self).create(values)
        accountTable.create(newAccount)
        return rl


class VoucherNumberTastics(models.Model):
    '''凭证编号的生成策略,一张凭证在不同的策略下有不同的凭证编号,自动生成凭证编号时需要指定一个策略'''
    _name = 'accountcore.voucher_number_tastics'
    _description = '凭证编号生成策略'
    number = fields.Char(string='凭证编号策略编码', required=True,)
    name = fields.Char(string='凭证编号策略', required=True)
    # is_defualt = fields.Boolean(string='默认使用')
    _sql_constraints = [('accountcore_voucher_number_tastics_unique',
                         'unique(number)', '凭证编号策略编码重复了!'),
                        ('accountcore_voucher_number_tastics_unique', 'unique(name)',
                         '凭证编号策略名称重复了!')]


class ExtensionUser(models.Model):
    '''扩展基础用户属性'''
    _inherit = 'res.users'
    voucherNumberTastics = fields.Many2one(
        'accountcore.voucher_number_tastics', string='默认凭证编号策略')


class NumberStaticsWizard(models.TransientModel):
    '''设置用户默认凭证编码策略向导'''
    _name = 'accountcore.voucher_number_statics_default'
    voucherNumberTastics = fields.Many2one(
        'accountcore.voucher_number_tastics', string='用户默认凭证编码策略')

    @api.model
    def default_get(self, field_names):
        default = super().default_get(field_names)
        default['voucherNumberTastics'] = self.env.user.voucherNumberTastics.id
        return default

    def setVoucherNumberTastics(self, args):
        currentUserId = self.env.uid
        currentUserTable = self.env['res.users'].sudo().browse(currentUserId)
        currentUserTable.write(
            {'voucherNumberTastics': self. voucherNumberTastics.id})
        return True


class SetingVoucherNumberWizard(models.TransientModel):
    '''设置凭证编号向导'''
    _name = 'accountcore.seting_vouchers_number'
    voucherNumberTastics = fields.Many2one(
        'accountcore.voucher_number_tastics', '要使用的凭证编码策略', required=True)
    startNumber = fields.Integer(string='从此编号开始', default=1, required=True)

    @api.model
    def default_get(self, field_names):
        default = super().default_get(field_names)
        default['voucherNumberTastics'] = self.env.user.voucherNumberTastics.id
        return default

    def setingNumber(self, args):
        startNumber = self.startNumber
        numberTasticsId = self.voucherNumberTastics.id
        vouchers = self.env['accountcore.voucher'].sudo().browse(
            args['active_ids'])
        if startNumber <= 0:
            startNumber = 1
        for voucher in vouchers:
            voucher.numberTasticsContainer_str = Voucher.getNewNumberDict(
                voucher.numberTasticsContainer_str, numberTasticsId, startNumber)
            startNumber += 1
        return {'name': '已生成凭证编号',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'accountcore.voucher',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in',  args['active_ids'])]
                }


class SetingVoucherNumberSingleWizard(models.TransientModel):
    '''设置单张凭证编号向导'''
    _name = 'accountcore.seting_voucher_number_single'
    newNumber = fields.Integer(string='新凭证编号', required=True)

    def setVoucherNumberSingle(self, argsDist):
        '''设置修改凭证编号'''
        newNumber = self.newNumber
        currentUserNumberTastics_id = 0
        if(self.env.user.voucherNumberTastics):
            currentUserNumberTastics_id = self.env.user.voucherNumberTastics.id
        voucher = self.env['accountcore.voucher'].sudo().browse(
            argsDist['active_id'])
        voucher.numberTasticsContainer_str = Voucher.getNewNumberDict(
            voucher.numberTasticsContainer_str, currentUserNumberTastics_id, newNumber)
        return True
