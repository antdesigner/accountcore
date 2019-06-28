# -*- coding: utf-8 -*-
import time
import copy
import decimal
from odoo import http
from odoo import exceptions
import json
from odoo import models, fields, api
import sys
sys.path.append('.\\.\\server')


class Org(models.Model):
    '''会计核算机构'''
    _name = 'accountcore.org'
    _description = '会计核算机构'
    number = fields.Char(string='核算机构编码', required=True)
    name = fields.Char(string='核算机构名称', required=True)
    # items = fields.One2many('accountcore.item', 'org', string="核算项目")
    accounts = fields.One2many('accountcore.account', 'org', string='科目')
    _sql_constraints = [('accountcore_org_number_unique', 'unique(number)',
                         '核算机构编码重复了!'),
                        ('accountcore_org_name_unique', 'unique(name)',
                         '核算机构名称重复了!')]


class AccountsArch(models.Model):
    '''会计科目体系'''
    _name = 'accountcore.accounts_arch'
    _description = '会计科目体系'
    number = fields.Char(string='科目体系编码', required=True)
    name = fields.Char(string='科目体系名称', required=True)
    accounts = fields.One2many(
        'accountcore.account', 'accountsArch', string='科目')
    _sql_constraints = [('accountcore_accoutsarch_number_unique', 'unique(number)',
                         '科目体系编码重复了!'),
                        ('accountcore_accountsarch_name_unique', 'unique(name)',
                         '科目体系名称重复了!')]


class ItemClass(models.Model):
    '''核算项目类别'''
    _name = 'accountcore.itemclass'
    _description = '核算项目类别'
    name = fields.Char(string='核算项目类别名称', required=True)
    number = fields.Char(string='核算项目类别编码', required=True)
    _sql_constraints = [('accountcore_itemclass_number_unique',
                         'unique(number)', '核算项目类别编码重复了!'),
                        ('accountcore_itemclass_name_unique', 'unique(name)',
                         '核算项目类别名称重复了!')]


class Item(models.Model):
    '''核算项目'''
    _name = 'accountcore.item'
    _description = '核算项目'
    org = fields.Many2one(
        'accountcore.org',
        string='核算机构',
        help="核算项目所属核算机构",
        index=True,
        ondelete='restrict')
    uniqueNumber = fields.Char(string='唯一编号')
    number = fields.Char(string='核算项目编码')
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

    @api.model
    def create(self, values):
        '''新增项目'''
        values['uniqueNumber'] = self.env['ir.sequence'].next_by_code(
            'item.uniqueNumber')
        rl = super(Item, self).create(values)
        return rl


class RuleBook(models.Model):
    '''凭证标签'''
    _name = 'accountcore.rulebook'
    _description = '凭证标签'
    number = fields.Char(string='凭证标签编码', required=True)
    name = fields.Char(string='凭证标签名称', required=True, help='用于给凭证做标记')
    _sql_constraints = [('accountcore_rulebook_number_unique',
                         'unique(number)', '标签编码重复了!'),
                        ('accountcore_rulebook_name_unique', 'unique(name)',
                         '标签名称重复了!')]


class AccountClass(models.Model):
    '''会计科目类别'''
    _name = 'accountcore.accountclass'
    _description = '会计科目类别'
    number = fields.Char(string='科目类别编码', required=True)
    name = fields.Char(string='科目类别名称', required=True)
    _sql_constraints = [('accountcore_accountclass_number_unique',
                         'unique(number)', '科目类别编码重复了!'),
                        ('accountcore_accountclass_name_unique',
                         'unique(name)', '科目类别名称重复了!')]


class Account(models.Model):
    '''会计科目'''
    _name = 'accountcore.account'
    _description = '会计科目'
    org = fields.Many2one(
        'accountcore.org',
        string='所属机构',
        help="科目所属机构",
        index=True,
        ondelete='restrict')

    accountsArch = fields.Many2one(
        'accountcore.accounts_arch',
        string='所属科目体系',
        help="科目所属体系",
        index=True,
        ondelete='restrict')

    accountClass = fields.Many2one(
        'accountcore.accountclass',
        string='科目类别',
        index=True,
        ondelete='restrict')
    number = fields.Char(string='科目编码', required=True)
    name = fields.Char(string='科目名称', required=True)
    direction = fields.Selection(
        [('1', '借'), ('-1', '贷')], string='余额方向', required=True)
    cashFlowControl = fields.Boolean(string='分配现金流量')
    itemClasses = fields.Many2many(
        'accountcore.itemclass', string='包含的核算项目类别', ondelete='restrict')
    accountItemClass = fields.Many2one(
        'accountcore.itemclass', string='作为明细科目的类别', ondelete='restrict')
    fatherAccountId = fields.Many2one(
        'accountcore.account',
        string='上级科目',
        help="科目的上级科目",
        index=True,
        ondelete='restrict')
    currentChildNumber = fields.Integer(default=10, string='新建下级科目待用编号')
    explain = fields.Html(string='科目说明')
    itemClassesHtml = fields.Html(
        string="包含的核算项目类别", compute='_itemClassesHtml')
    _sql_constraints = [('accountcore_account_number_unique', 'unique(number)',
                         '科目编码重复了!'),
                        ('accountcore_account_name_unique', 'unique(name)',
                         '科目名称重复了!')]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('number', operator, name),
                      ('name', operator, name)]
        pos = self.search(domain+args, limit=limit, order='number')
        return pos.name_get()

    @api.model
    def get_itemClasses(self, accountId):
        '''获得科目下的核算项目'''
        account = self.browse([accountId])
        itemClasses = account.itemClasses
        accountItemClassId = account.accountItemClass.id
        return [{'id': i.id, 'name':  (("*"+i.name) if i.id == accountItemClassId else i.name)} for i in itemClasses]

    @api.multi
    def _itemClassesHtml(self):
        '''购建科目相关核算项目展示内容'''
        content = None
        itemTypes = None
        for account in self:
            content = ""
            if account.itemClasses:
                accountItemClassId = account.accountItemClass.id
                itemTypes = account.itemClasses
                for itemType in itemTypes:
                    content = content+"<span>\\" + \
                        ('*'+itemType.name if(itemType.id ==
                                              accountItemClassId) else itemType.name)+"</span>"
            account.itemClassesHtml = content
        return True


class CashFlowType(models.Model):
    '''现金流量类别'''
    _name = 'accountcore.cashflowtype'
    _description = '现金流量类别'
    number = fields.Char(string='现金流量项目类别编码', required=True)
    name = fields.Char(string='现金流量项目类别', required=True)
    _sql_constraints = [('accountcore_cashflowtype_number_unique',
                         'unique(number)', '现金流量类别编码重复了!'),
                        ('accountcore_cashflowtype_name_unique',
                         'unique(name)', '现金流量类别名称重复了!')]


class CashFlow(models.Model):
    '''现金流量项目'''
    _name = 'accountcore.cashflow'
    _description = '现金流量项目'
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
    '''凭证来源'''
    _name = 'accountcore.source'
    _description = '凭证来源'
    number = fields.Char(string='凭证来源编码', required=True)
    name = fields.Char(string='凭证来源名称', required=True)
    _sql_constraints = [('accountcore_source_number_unique', 'unique(number)',
                         '凭证来源编码重复了!'),
                        ('accountcore_source_name_unique', 'unique(name)',
                         '凭证来源名称重复了!')]


class Voucher(models.Model):
    '''会计记账凭证'''
    _name = 'accountcore.voucher'
    _description = '会计记账凭证'
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
    ruleBook = fields.Many2many(
        'accountcore.rulebook',
        string='凭证标签',
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
    entrysHtml = fields.Html(
        string="分录内容", compute='_createEntrysHtml', store=True)

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
        isCopye = self.env.context.get('ac_from_copy')
        if isCopye:
            pass
        else:
            rl._checkVoucher(values)
        rl._updateBalance()
        return rl

    @api.multi
    def write(self, values):
        '''修改编辑凭证'''
        self.ensure_one
        self._updateBalance(isAdd=False)  # 先从余额表减去原来的金额
        rl_bool = super(Voucher, self).write(values)
        self._checkVoucher(values)
        self._updateBalance()  # 再从余额表加上新的金额
        return rl_bool

    @api.multi
    def copy(self, default=None):
        '''复制凭证'''
        updateFields = {'state': 'creating',
                        'reviewer': None,
                        'createUser': self.env.uid,
                        'numberTasticsContainer_str': '{}',
                        'appendixCount': 1}
        rl = super(Voucher, self.with_context(
            {'ac_from_copy': True})).copy(updateFields)
        for entry in self.entrys:
            entry.copy({'voucher': rl.id})
        rl._updateBalance()
        return rl

    @api.multi
    def unlink(self):
        '''删除凭证'''
        for voucher in self:
            voucher._updateBalance(isAdd=False)
        rl_bool = super(Voucher, self).unlink()
        return rl_bool

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

    @api.model
    def _checkVoucher(self, voucherDist):
        '''凭证检查'''
        self._checkEntyCount(voucherDist)
        self._checkCDBalance(voucherDist)
        self._checkChashFlow(voucherDist)
        self._checkCDValue(voucherDist)
        self._checkRequiredItemClass()

    @api.model
    def _checkEntyCount(self, voucherDist):
        '''检查是否有分录'''
        # if 'entrys' in voucherDist:
        if len(self.entrys) > 1:
            return True
        else:
            raise exceptions.ValidationError('需要录入两条以上的会计分录')

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
        return True

    @api.multi
    @api.depends('entrys')
    def _createEntrysHtml(self):
        '''购建凭证分录展示内容'''
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

    @api.model
    def _updateBalance(self, isAdd=True):
        '''更新余额'''
        for entry in self.entrys:
            self._updateAccountBalance(entry, isAdd)

    @api.model
    def _updateAccountBalance(self, entry, isAdd=True):
        '''更新科目余额'''
        currentDate = self.voucherdate
        year = currentDate.year
        month = currentDate.month
        orgId = self.org.id
        accountId = entry.account.id
        itemId = (entry.getItemByitemClass(entry.account.accountItemClass)).id
        if isAdd:
            computMark = 1  # 增加金额
        else:
            computMark = -1  # 减少金额
        entry_damount = entry.damount*computMark
        entry_camount = entry.camount*computMark
        accountBalance = self._getBalanceRecord(accountId)
        if accountBalance.exists():
            if entry_damount != 0:
                accountBalance.changeDamount(entry_damount)
            elif entry_camount != 0:
                accountBalance.changeCamount(entry_camount)
        else:
            accountBalanceTable = self.env['accountcore.accounts_balance']
            domain_org = ('org', '=', orgId)
            domain_account = ('account', '=', accountId)
            domain_item = ('items', '=', itemId)
            balanceRecords = accountBalanceTable.search(
                [domain_org, domain_account, domain_item])
            pre_balanceRecords = (balanceRecords.filtered(lambda r: (
                r.year < year or (r.year == year and r.month <= month)))).sorted(key=lambda a: (a.year, a.month))
            next_balanceRecords = (balanceRecords.filtered(lambda r: (
                r.year > year or (r.year == year and r.month > month)))).sorted(key=lambda a: (a.year, a.month))
            if itemId:
                newBalanceInfo = {'org': orgId, 'createDate': currentDate, 'year': year, 'month': month,
                                  'account': accountId, 'items': itemId, 'isbegining': False}
            else:
                newBalanceInfo = {'org': orgId, 'createDate': currentDate, 'year': year, 'month': month,
                                  'account': entry.account.id, 'isbegining': False}
            if pre_balanceRecords.exists():
                pre_record = pre_balanceRecords[-1]
                newBalanceInfo['preRecord'] = pre_record.id
                newBalanceInfo['beginingDamount'] = pre_record.beginingDamount
            if next_balanceRecords.exists():
                next_record = next_balanceRecords[0]
                newBalanceInfo['nextRecord'] = next_record.id
                newBalanceInfo['beginingCamount'] = next_record.beginingCamount
            if entry.damount != 0:
                newBalanceInfo['damount'] = entry_damount
                accountBalanceTable.sudo().create(newBalanceInfo)
            elif entry.camount != 0:
                newBalanceInfo['camount'] = entry_camount
                accountBalanceTable.sudo().create(newBalanceInfo)
        return True

    @api.model
    def _getBalanceRecord(self, accountId, itemId=False):
        '''获得分录对应期间和会计科目下的核算项目的余额记录'''
        balanasTable = self.env['accountcore.accounts_balance']
        org = self.org.id
        year = self.voucherdate.year
        month = self.voucherdate.month
        record = balanasTable.search(
            [['org', '=', org], ['year', '=', year], ['month', '=', month], ['account', '=', accountId], ['items', '=', itemId], ['isbegining', '=', False]])
        return record

    @api.model
    def _checkRequiredItemClass(self):
        entrys = self.entrys
        for entry in entrys:
            itemClass_need = entry.account.accountItemClass
            if itemClass_need.id:
                items = entry.items
                itemsClasses_ids = [item.itemClass.id for item in items]
                if itemClass_need.id not in itemsClasses_ids:
                    raise exceptions.ValidationError(
                        entry.account.name+" 科目的 "+itemClass_need.name+' 为必须录入项目')
        return True


class Enty(models.Model):
    '''一条分录'''
    _name = 'accountcore.entry'
    _description = "会计分录"
    voucher = fields.Many2one(
        'accountcore.voucher', string='所属凭证', index=True, ondelete='cascade')
    sequence = fields.Integer('Sequence')
    explain = fields.Char(string='说明')
    account = fields.Many2one(
        'accountcore.account', string='科目', required=True, index=True)
    items = fields.Many2many(
        'accountcore.item', string='核算项目', index=True, ondelete='restrict')
    currency_id = fields.Many2one(
        # Monetory类型字段必须有
        'res.currency',
        compute='_get_company_currency',
        readonly=True,
        oldname='currency',
        string="Currency",
        help='Utility field to express amount currency')
    damount = fields.Monetary(string='借方金额')  # Monetory类型字段必须有currency_id
    camount = fields.Monetary(string='贷方金额')  # Monetory类型字段必须有currency_id
    cashFlow = fields.Many2one(
        'accountcore.cashflow',
        string='现金流量项目',
        index=True,
        ondelete='restrict')

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

    @api.one
    def _get_company_currency(self):
        # Monetory类型字段必须有 currency_id
        self.currency_id = self.env.user.company_id.currency_id

    @api.model
    def getItemByitemClassId(self, itemClassId):
        '''返回分录中指定类别的核算项目'''
        if self.items:
            items = self.items
            for item in items:
                if (item.itemClass.id == itemClassId):
                    return item
        return None

    @api.model
    def getItemByitemClass(self, itemClass):
        '''返回分录中指定类别的核算项目'''
        return self.getItemByitemClassId(itemClass.id)


class AccountcoreUserDefaults(models.TransientModel):
    '''用户设置模型字段的默认取值'''
    _name = 'accountcoure.userdefaults'
    default_ruleBook = fields.Many2many(
        'accountcore.rulebook', string='默认凭证标签')
    default_org = fields.Many2one('accountcore.org', string='默认机构')
    default_voucherDate = fields.Date(
        string='记账日期', default=fields.Date.today())

    # 设置新增凭证,日期,机构和账套字段的默认值
    def setDefaults(self):
        modelName = 'accountcore.voucher'
        self._setDefault(modelName, 'ruleBook', self.default_ruleBook.ids)
        self._setDefault(modelName, 'org', self.default_org.id)
        self._setDefault(
            modelName, 'voucherdate',
            json.dumps(self.default_voucherDate.strftime('%Y-%m-%d')))
        self.env.user.currentOrg = self.default_org.id
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

    accountsArch = fields.Many2one(
        'accountcore.accounts_arch',
        string='所属科目体系',
        help="科目所属体系",
        index=True,
        ondelete='restrict')

    accountClass = fields.Many2one(
        'accountcore.accountclass',
        string='科目类别',
        index=True,
        ondelete='restrict')
    number = fields.Char(string='科目编码', required=True)
    name = fields.Char(string='科目名称', required=True)
    direction = fields.Selection(
        [('1', '借'), ('-1', '贷')], string='余额方向', required=True)
    cashFlowControl = fields.Boolean(string='分配现金流量')
    itemClasses = fields.Many2many(
        'accountcore.itemclass', string='包含的核算项目类别', ondelete='restrict')
    accountItemClass = fields.Many2one(
        'accountcore.itemclass', string='作为明细科目的类别', ondelete='restrict')
    explain = fields.Html(string='科目说明')
    @api.model
    def default_get(self, field_names):
        default = super().default_get(field_names)
        fatherAccountId = self.env.context.get('active_id')
        fatherAccount = self.env['accountcore.account'].sudo().search(
            [['id', '=', fatherAccountId]])
        default['accountsArch'] = fatherAccount.accountsArch.id
        default['fatherAccountId'] = fatherAccountId
        default['org'] = fatherAccount.org.id
        default['accountClass'] = fatherAccount.accountClass.id
        default['direction'] = fatherAccount.direction
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
        accountTable.create(values)
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
    currentOrg = fields.Many2one('accountcore.org', string="当前核算机构")
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


class AccountsBalance(models.Model):
    '''科目余额'''
    _name = 'accountcore.accounts_balance'
    _description = '科目余额'
    org = fields.Many2one(
        'accountcore.org',
        string='所属机构',
        required=True,
        index=True,
        ondelete='cascade')
    createDate = fields.Date(
        string="创建日期", required=True)
    year = fields.Integer(string='年份', required=True,
                          index=True)  # 通过createDate生成,不要直接修改
    month = fields.Integer(string='月份', required=True)  # 通过createDate生成,不要直接修改
    isbegining = fields.Boolean(string="是启用期间", default=False)
    account = fields.Many2one('accountcore.account',
                              string='会计科目', required=True, index=True, ondelete='cascade')
    accountItemClass = fields.Many2one(
        'accountcore.itemclass', string='核算项目类别', related='account.accountItemClass')
    items = fields.Many2one('accountcore.item', string='核算项目',
                            index=True, ondelete='cascade')
    beginingDamount = fields.Monetary(string="期初借方")  # 当月初
    beginingCamount = fields.Monetary(string='期初贷方')
    damount = fields.Monetary(string='本期借方金额')  # Monetory类型字段必须有currency_id
    camount = fields.Monetary(string='本期贷方金额')  # Monetory类型字段必须有currency_id
    cumulativeDamount = fields.Monetary(string='本年借方累计')
    cumulativeCamount = fields.Monetary(string='本年贷方累计')
    preRecord = fields.Many2one(
        'accountcore.accounts_balance', string='最近上一期记录')
    nextRecord = fields.Many2one(
        'accountcore.accounts_balance', string='最近后一期记录')
    # Monetory类型字段必须有
    currency_id = fields.Many2one(
        'res.currency',
        compute='_get_company_currency',
        readonly=True,
        string="Currency",
        help='Utility field to express amount currency')
    # Monetory 字段必须有

    def _get_company_currency(self):
        pass

    @api.onchange('createDate')
    def chage_period(self):
        if self.createDate:
            self.year = self.createDate.year
            self.month = self.createDate.month

    @api.model
    def create(self, values):
        '''新增一条科目期初'''
        if self._check_repeat(values):
            raise exceptions.ValidationError(
                '不能新增,因为在相同会计期间,已经存在一条相同科目的期初余额记录,请在该行记录上修改!')
        else:
            rl = super(AccountsBalance, self).create(values)
        return rl

    @api.model
    def _check_repeat(self, accountBalance):
        '''检查是否已经有一条期初记录'''
        if ('items' in accountBalance):
            records = self.search([('org', '=', accountBalance['org']), ('year', '=', accountBalance['year']), ('month', '=', accountBalance['month']), (
                'account', '=', accountBalance['account']), ('items', '=', accountBalance['items']), ('isbegining', '=', accountBalance['isbegining'])])
        else:
            records = self.search([('org', '=', accountBalance['org']), ('year', '=', accountBalance['year']), ('month', '=', accountBalance['month']), (
                'account', '=', accountBalance['account']), ('isbegining', '=', accountBalance['isbegining'])])
        if records.exists():
            return True
        return False

    @api.model
    def changeDamount(self, amount):
        self.damount = self.damount+amount

    @api.model
    def changeCamount(self, amount):
        self.camount = self.camount+amount

class GetAccountsBalance(models.TransientModel):
    '''科目余额查询向导'''
    _name = 'accountcore.get_account_balance'
    startDate = fields.Date(string="开始期间", required=True,
                            default=fields.Date.today())
    endDate = fields.Date(string="结束期间", required=True,
                          default=fields.Date.today())
    onlyShowOneLevel = fields.Boolean(string="只显示一级科目", default=False)
    summaryLevelByLevel = fields.Boolean(string='逐级科目汇总', default=True)
    includeAccountItems = fields.Boolean(string='包含核算项目', default=True)
    noShowZeroBalance = fields.Boolean(string='余额为零不显示', default=False)
    noShowUnUsed = fields.Boolean(string='从未使用不显示', default=True)
    org = fields.Many2many(
        'accountcore.org',
        string='机构范围',
        default=lambda s: s.env.user.currentOrg,

    )
    account = fields.Many2many('accountcore.account', string='科目范围')

    def doAction(self, args):
        '''设置修改凭证编号'''
        pass
        return {
            'display_name': '科目余额表',
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': 'accountcore.account_balance_report',
        }
