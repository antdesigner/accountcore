# -*- coding: utf-8 -*-
import logging
import time
import copy
import decimal
from odoo import exceptions
import json
from odoo import models, fields, api
import datetime
import calendar
import sys
import multiprocessing
sys.path.append('.\\.\\server')
_logger = logging.getLogger(__name__)

# 新增,修改,删除凭证时对科目余额的改变加锁
vocher_lock = multiprocessing.Lock()


class Glob_tag_Model(models.AbstractModel):
    '''全局标签模型,用于多重继承方式添加到模型'''
    _name = "accountcore.glob_tag_model"
    glob_tag = fields.Many2many('accountcore.glob_tag',
                                string='全局标签',
                                index=True)


class Org(models.Model, Glob_tag_Model):
    '''会计核算机构'''
    _name = 'accountcore.org'
    _description = '会计核算机构'
    number = fields.Char(string='核算机构编码', required=True)
    name = fields.Char(string='核算机构名称', required=True)
    accounts = fields.One2many('accountcore.account',
                               'org',
                               string='科目')

    _sql_constraints = [('accountcore_org_number_unique', 'unique(number)',
                         '核算机构编码重复了!'),
                        ('accountcore_org_name_unique', 'unique(name)',
                         '核算机构名称重复了!')]


class AccountsArch(models.Model, Glob_tag_Model):
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


class ItemClass(models.Model, Glob_tag_Model):
    '''核算项目类别'''
    _name = 'accountcore.itemclass'
    _description = '核算项目类别'
    number = fields.Char(string='核算项目类别编码', required=True)
    name = fields.Char(string='核算项目类别名称', required=True)
    _sql_constraints = [('accountcore_itemclass_number_unique', 'unique(number)',
                         '核算项目类别编码重复了!'),
                        ('accountcore_itemclass_name_unique', 'unique(name)',
                         '核算项目类别名称重复了!')]


class Item(models.Model, Glob_tag_Model):
    '''核算项目'''
    _name = 'accountcore.item'
    _description = '核算项目'
    org = fields.Many2one('accountcore.org',
                          string='核算机构',
                          help="核算项目所属核算机构",
                          index=True,
                          ondelete='restrict')
    uniqueNumber = fields.Char(string='唯一编号')
    number = fields.Char(string='核算项目编码')
    name = fields.Char(string='核算项目名称',
                       required=True,
                       help="核算项目名称")
    itemClass = fields.Many2one('accountcore.itemclass',
                                string='核算项目类别',
                                index=True,
                                required=True,
                                ondelete='restrict')
    item_class_name = fields.Char(related='itemClass.name',
                                  string='核算项目类别',
                                  store=True,
                                  ondelete='restrict')
    _sql_constraints = [('accountcore_item_number_unique', 'unique(number)',
                         '核算项目编码重复了!'),
                        ('accountcore_item_name_unique', 'unique(name)',
                         '核算项目名称重复了!')]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=20):
        # 更据context中account的值来对item的搜索进行过滤,仅查找account下挂的item类别中的item
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
            itemslist.append({'id': i.id,
                              'name': i.name,
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
    _sql_constraints = [('accountcore_rulebook_number_unique', 'unique(number)',
                         '标签编码重复了!'),
                        ('accountcore_rulebook_name_unique', 'unique(name)',
                         '标签名称重复了!')]


class AccountClass(models.Model, Glob_tag_Model):
    '''会计科目类别'''
    _name = 'accountcore.accountclass'
    _description = '会计科目类别'
    number = fields.Char(string='科目类别编码', required=True)
    name = fields.Char(string='科目类别名称', required=True)
    _sql_constraints = [('accountcore_accountclass_number_unique', 'unique(number)',
                         '科目类别编码重复了!'),
                        ('accountcore_accountclass_name_unique', 'unique(name)',
                         '科目类别名称重复了!')]


class Account(models.Model, Glob_tag_Model):
    '''会计科目'''
    _name = 'accountcore.account'
    _description = '会计科目'
    org = fields.Many2one('accountcore.org',
                          string='所属机构',
                          help="科目所属机构",
                          index=True,
                          ondelete='restrict')

    accountsArch = fields.Many2one('accountcore.accounts_arch',
                                   string='所属科目体系',
                                   help="科目所属体系",
                                   index=True,
                                   ondelete='restrict')

    accountClass = fields.Many2one('accountcore.accountclass',
                                   string='科目类别',
                                   index=True,
                                   ondelete='restrict')
    number = fields.Char(string='科目编码', required=True)
    name = fields.Char(string='科目名称', required=True)
    direction = fields.Selection([('1', '借'),
                                  ('-1', '贷')],
                                 string='余额方向',
                                 required=True)
    cashFlowControl = fields.Boolean(string='分配现金流量')
    itemClasses = fields.Many2many('accountcore.itemclass',
                                   string='科目要统计的核算项目类别',
                                   help="录入凭证分录时供的核算项目类别",
                                   ondelete='restrict')
    accountItemClass = fields.Many2one('accountcore.itemclass',
                                       string='作为明细科目的类别',
                                       help="录入凭证分录时必须输输入的核算项目类别,作用相当于明细科目",
                                       ondelete='restrict')
    fatherAccountId = fields.Many2one('accountcore.account',
                                      string='上级科目',
                                      help="科目的上级科目",
                                      index=True,
                                      ondelete='restrict')
    childs_ids = fields.One2many('accountcore.account',
                                 'fatherAccountId',
                                 string='直接下级科目',
                                 ondelete='restrict')
    # is_end = fields.Boolean(string='是否最明细级科目')
    currentChildNumber = fields.Integer(default=10,
                                        string='新建下级科目待用编号')
    explain = fields.Html(string='科目说明')
    itemClassesHtml = fields.Html(string="核算类别",
                                  help="录入凭证分录时可以选择的核算项目.其中带*的相当于明细科目,为必选.其他不带*的为统计项目,可选",
                                  compute='_itemClassesHtml',
                                  store=True)
    _sql_constraints = [('accountcore_account_number_unique', 'unique(number)',
                         '科目编码重复了!'),
                        ('accountcore_account_name_unique', 'unique(name)',
                         '科目名称重复了!')]

    @api.onchange('accountItemClass')
    def _checkAccountItem(self):
        '''改变作为明细科目的核算项目类别'''
        account_id = self.env.context.get('account_id')
        old_accountItemClass = self.env['accountcore.account'].sudo().browse(
            [account_id]).accountItemClass
        old_accountItemClass_id = old_accountItemClass.id
        accountBalances = self.env['accountcore.accounts_balance'].sudo().search(
            [('account', '=', account_id),
             ('items', '=', old_accountItemClass_id)])
        if accountBalances.exists():
            if old_accountItemClass:
                raise exceptions.ValidationError('该科目下的核算项目['+old_accountItemClass.name+'] \
                已经使用,不能改变.你可以添加新的明细科目,在新的明细科目下设置你想要的核算项目类别')
            else:
                raise exceptions.ValidationError(
                    '该科目已经使用,不能改变.你可以添加新的明细科目,在新的明细科目下设置你想要的核算项目类别')

    @api.onchange('itemClasses')
    def _checkItemClasses(self):
        '''改变科目的核算项目类别 '''
        item_ids = [item.id for item in self.itemClasses]
        if self.accountItemClass and self.accountItemClass.id not in item_ids:
            raise exceptions.ValidationError(
                '['+self.accountItemClass.name+"]已经作为明细科目的类别,不能删除.如果要删除,请你在'作为明细的类别'中先取消它")

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=0):
        args = args or []
        domain = []
        # 同时根据科目编号和名称进行搜索
        if name:
            domain = ['|', ('number', operator, name),
                      ('name', operator, name)]
        # 源代码默认为160,突破其限制   详细见 /web/static/src/js/views/form_common.js
        if limit == 160:
            limit = 0
        pos = self.search(domain+args, limit=limit, order='number')
        # return pos.name_get()
        return pos._my_name_get()

    @api.multi
    def _my_name_get(self):
        # 原name_get基类方法:
        # result = []
        # name = self._rec_name
        # if name in self._fields:
        #     convert = self._fields[name].convert_to_display_name
        #     for record in self:
        #         result.append((record.id, convert(record[name], record)))
        # else:
        #     for record in self:
        #         result.append((record.id, "%s,%s" % (record._name, record.id)))
        result = []
        name = self._rec_name
        if name in self._fields:
            convert = self._fields[name].convert_to_display_name
            for record in self:
                # if record['org'].name:
                #     org_name = record['org'].name
                # else:
                #     org_name = ''
                result.append(
                    (record.id, (record['number']).ljust(11, '_') + convert(record[name], record)))
        else:
            for record in self:
                result.append((record.id, "%s,%s" % (record._name, record.id)))

        return result

    @api.model
    def get_itemClasses(self, accountId):
        '''获得科目下的核算项目类别'''
        account = self.browse([accountId])
        itemClasses = account.itemClasses
        accountItemClassId = account.accountItemClass.id
        return [{'id': i.id, 'name':  (("*"+i.name)
                                       if i.id == accountItemClassId else i.name)}
                for i in itemClasses]

    @api.multi
    @api.depends('itemClasses', 'accountItemClass')
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

    @api.multi
    def getMeAndChild_ids(self):
        '''获得科目下的全部明细科目和自生'''
        self.ensure_one()
        # 通过科目编码来判断
        return self.search([('number', 'like', self.number)]).mapped('id')

    # @api.multi
    # @api.depends('fa')
    # def _is_end(self):


class CashFlowType(models.Model, Glob_tag_Model):
    '''现金流量类别'''
    _name = 'accountcore.cashflowtype'
    _description = '现金流量类别'
    number = fields.Char(string='现金流量项目类别编码', required=True)
    name = fields.Char(string='现金流量项目类别', required=True)
    _sql_constraints = [('accountcore_cashflowtype_number_unique', 'unique(number)',
                         '现金流量类别编码重复了!'),
                        ('accountcore_cashflowtype_name_unique', 'unique(name)',
                         '现金流量类别名称重复了!')]


class CashFlow(models.Model, Glob_tag_Model):
    '''现金流量项目'''
    _name = 'accountcore.cashflow'
    _description = '现金流量项目'
    cashFlowType = fields.Many2one('accountcore.cashflowtype',
                                   string='现金流量类别',
                                   required=True,
                                   index=True)
    number = fields.Char(string="现金流量编码", required=True)
    name = fields.Char(string='现金流量名称', required=True)
    direction = fields.Selection(
        [("-1", "流出"), ("1", "流入")], string='流量方向', required=True)
    _sql_constraints = [('accountcore_cashflow_number_unique', 'unique(number)',
                         '现金流量编码重复了!'),
                        ('accountcore_cashflow_name_unique', 'unique(name)',
                         '现金流量名称重复了!')]


class VoucherFile(models.Model):
    _name = 'accountcore.voucherfile'
    _description = "凭证相关文件"
    appedixfileType = fields.Char(string='文件类型', required=True)


class Source(models.Model, Glob_tag_Model):
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
    voucherdate = fields.Date(string='记账日期',
                              required=True,
                              placeholder='记账日期')
    real_date = fields.Date(string='业务日期', placehplder='业务日期')
    # 前端通过voucherDate生成,不要直接修改
    year = fields.Integer(string='年份',
                          compute='_getYearMonth',
                          store=True,
                          index=True)
    # 前端通过voucherDate生成,不要直接修改
    month = fields.Integer(string='月份',
                           compute='_getYearMonth',
                           store=True,
                           index=True)
    soucre = fields.Many2one('accountcore.source',
                             string='凭证来源',
                             # 手工输入
                             default=1,
                             readonly=True,
                             required=True,
                             ondelete='restrict')
    org = fields.Many2one('accountcore.org',
                          string='所属机构',
                          required=True,
                          index=True,
                          ondelete='restrict')
    ruleBook = fields.Many2many('accountcore.rulebook',
                                string='凭证标签',
                                index=True,
                                help='可用于标记不同的凭证',
                                ondelete='restrict')
    number = fields.Integer(string='凭证编号',
                            help='该编号更据不同凭证编号策略会不同,一张凭证可以有多个不同编号',
                            compute='_getVoucherNumber',
                            search="_searchNumber")
    appendixCount = fields.Integer(string='附件张数',
                                   default=1,
                                   required=True)
    createUser = fields.Many2one('res.users',
                                 string='制单人',
                                 default=lambda s: s.env.uid,
                                 readonly=True,
                                 required=True,
                                 ondelete='restrict',
                                 index=True)
    reviewer = fields.Many2one('res.users',
                               string='审核人',
                               ondelete='restrict',
                               readonly=True,
                               indext=True)
    entrys = fields.One2many('accountcore.entry',
                             'voucher',
                             string='分录')
    voucherFile = fields.Many2one('accountcore.voucherfile',
                                  string='附件文件',
                                  ondelete='restrict')
    state = fields.Selection([('creating', '制单'),
                              ('reviewed', '已审核')],
                             default='creating', index=True)
    uniqueNumber = fields.Char(string='唯一编号', help='一张凭证只有一个唯一编号')
    numberTasticsContainer_str = fields.Char(string='凭证可用编号策略',
                                             default="{}")
    entrysHtml = fields.Html(string="分录内容",
                             compute='_createEntrysHtml',
                             store=True)
    roolbook_html = fields.Html(string="凭证的标签",
                                compute='_buildRuleBook',
                                store=True)
    sum_amount = fields.Monetary(string='借贷方差额', default=0, compute='total')

    # Monetory类型字段必须有
    currency_id = fields.Many2one('res.currency',
                                  compute='_get_company_currency',
                                  readonly=True,
                                  oldname='currency',
                                  string="Currency",
                                  help='Utility field to express amount currency')

    @api.one
    def _get_company_currency(self):
        # Monetory类型字段必须有 currency_id
        self.currency_id = self.env.user.company_id.currency_id

    @api.depends('entrys')
    def total(self):
        d_amount = 0
        c_amount = 0
        for e in self.entrys:
            d_amount = e.damount+d_amount
            c_amount = e.camount+c_amount
        self.sum_amount = d_amount-c_amount
        return True

    @api.multi
    @api.depends('voucherdate')
    def _getYearMonth(self):
        for v in self:
            v.year = v.voucherdate.year
            v.month = v.voucherdate.month

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
        # 只允许一条分录更新余额表,进程锁
        vocher_lock.acquire()
        values['uniqueNumber'] = self.env['ir.sequence'].next_by_code(
            'voucher.uniqueNumber')
        rl = super(Voucher, self).create(values)
        # 如果是复制新增就不执行凭证检查
        isCopye = self.env.context.get('ac_from_copy')
        if isCopye:
            pass
        else:
            rl._checkVoucher(values)
        rl._updateBalance()
        # 跟新处理并发冲突
        self.env.cr.commit()
        vocher_lock.release()
        return rl

    @api.multi
    def write(self, values):
        '''修改编辑凭证'''
        vocher_lock.acquire()
        self.ensure_one
        self._updateBalance(isAdd=False)  # 先从余额表减去原来的金额
        rl_bool = super(Voucher, self).write(values)
        self._checkVoucher(values)
        self._updateBalance()  # 再从余额表加上新的金额
        # 跟新处理并发冲突
        self.env.cr.commit()
        vocher_lock.release()
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
            if voucher.state == "reviewed":
                raise exceptions.ValidationError('有凭证已审核不能删除，请选择未审核凭证')
        vocher_lock.acquire()
        for voucher in self:
            voucher._updateBalance(isAdd=False)
        rl_bool = super(Voucher, self).unlink()
        # 跟新处理并发冲突
        self.env.cr.commit()
        vocher_lock.release()
        return rl_bool

    @staticmethod
    def getNumber(container_str, numberTastics_id):
        '''设置获得对应策略下的凭证编号'''
        number = VoucherNumberTastics.get_number(
            container_str, numberTastics_id)
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
        # if 用户设置了默认编号策略
        if(self.env.user.voucherNumberTastics):
            currentUserNumberTastics_id = self.env.user.voucherNumberTastics.id
        else:
            for record in self:
                record.number = 0
            return True
        for record in self:
            record.number = self.getNumber(record.numberTasticsContainer_str,
                                           currentUserNumberTastics_id)
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
        # if camount == damount and camount != 0:
        if camount == damount:
            return True
        else:
            raise exceptions.ValidationError('借贷金额不平衡')

    @api.model
    def _checkCDValue(self, voucherDist):
        '''分录借贷方是否全部为零'''
        for entry in self.entrys:
            if entry.camount == 0 and entry.damount == 0:
                raise exceptions.ValidationError('借贷方金额不能全为零')
        return True

    @api.model
    def _checkChashFlow(self, voucherDist):
        # TODO -tiger:''
        return True

    @api.multi
    @api.depends('entrys', 'entrys.account.name', 'entrys.items.name')
    def _createEntrysHtml(self):
        '''创建凭证分录展示内容'''
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

    @api.multi
    @api.depends('ruleBook', 'ruleBook.name')
    def _buildRuleBook(self):
        '''购建凭证标签展示内容'''
        for voucher in self:
            content = '<table class="ac_rulebook">'
            for item in voucher.ruleBook:
                content = content+'<tr><td>'+item.name+'</td></tr>'
            voucher.roolbook_html = content+"</table>"

    def _buildingEntryHtml(self, entry):
        '''购建一条分录展示内容'''
        content = ""
        items = ""
        for item in entry.items:
            items = items+"<div>"+item.name+"</div>"
        if entry.explain:
            explain = entry.explain
        else:
            explain = "*"
        damount = format(entry.damount, '0.2f') if entry.damount != 0 else ""
        camount = format(entry.camount, '0.2f') if entry.camount != 0 else ""
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
            str(self.env.user.voucherNumberTastics.id)+'": ' \
            + str(value)+',%'
        tasticsValue2 = '%"' + \
            str(self.env.user.voucherNumberTastics.id)+'": '  \
            + str(value)+'}%'
        return['|', ('numberTasticsContainer_str', 'like', tasticsValue1),
               ('numberTasticsContainer_str', 'like', tasticsValue2)]

    @api.model
    def _checkRequiredItemClass(self):
        '''检查科目的必录核算项目类别'''
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

    @api.model
    def _updateBalance(self, isAdd=True):
        '''更新余额'''
        for entry in self.entrys:
            # isAdd 表示是否依据分录金额减少(false)还是增加余额表金额(TRUE)
            self._updateAccountBalance(entry, isAdd)

    @api.model
    def _updateAccountBalance(self, entry, isAdd=True):
        '''新增和修改凭证，更新科目余额'''
        item = entry.getItemByitemClass(entry.account.accountItemClass)
        if item:
            itemId = item.id
        else:
            itemId = False

        if isAdd:
            computMark = 1  # 增加金额
        else:
            computMark = -1  # 减少金额
        entry_damount = entry.damount*computMark
        entry_camount = entry.camount*computMark
        accountBalanceTable = self.env['accountcore.accounts_balance']
        accountBalanceMark = AccountBalanceMark(orgId=self.org.id,
                                                accountId=entry.account.id,
                                                itemId=itemId,
                                                createDate=self.voucherdate,
                                                accountBalanceTable=accountBalanceTable,
                                                isbegining=False)
        # if 一条会计分录有核算项目
        if entry.items:
            for item_ in entry.items:
                accountBalance = self._getBalanceRecord(entry.account.id,
                                                        item_.id)
                # if 当月已经存在一条该科目的余额记录（不包括启用期初余额那条）
                if accountBalance.exists():
                    self._modifyBalance(entry_damount,
                                        accountBalance,
                                        entry_camount)
                # else 不存在就新增一条,但必须是科目的必选核算项目类
                elif item_.id == itemId:
                    self._buildBalance(True,
                                       accountBalanceMark,
                                       entry,
                                       entry_damount,
                                       entry_camount)
        # else 一条会计分录没有核算项目
        else:
            accountBalance = self._getBalanceRecord(entry.account.id)
            # if 当月已经存在一条该科目的余额记录（不包括启用期初余额那条）
            if accountBalance.exists():
                self._modifyBalance(entry_damount,
                                    accountBalance,
                                    entry_camount)
            # else 不存在就新增一条
            else:
                # 不排除启用期初那条记录
                self._buildBalance(False,
                                   accountBalanceMark,
                                   entry,
                                   entry_damount,
                                   entry_camount)

        return True

    def _modifyBalance(self, entry_damount, accountBalance, entry_camount):
        '''对已存在的科目余额记录进行修改'''
        if entry_damount != 0:
            # 科目借方余额=科目借方余额+凭证分录借方
            accountBalance.addDamount(entry_damount)
        elif entry_camount != 0:
            accountBalance.addCamount(entry_camount)
            # 更新以后各期期初
        accountBalance.changeNextBalanceBegining(accountBalance.endDamount,
                                                 accountBalance.endCamount)
        # else 不存在就新增一条,但必须是科目的必选核算项目类

    def _buildBalance(self, haveItem, accountBalanceMark, entry, entry_damount, entry_camount):
        '''在余额表创建一条余额记录，该科目包含核算项目'''
        accountBalanceTable = self.env['accountcore.accounts_balance']
        # 不排除启用期初那条记录
        pre_balanceRecords = accountBalanceMark.get_pre_balanceRecords_all()
        # 不排除启用期初那条记录
        next_balanceRecords = accountBalanceMark.get_next_balanceRecords_all()

        if haveItem:
            newBalanceInfo = dict(accountBalanceMark)
        else:
            accountBalanceMark.items = None
            newBalanceInfo = dict(accountBalanceMark)
        # 以前月份存在数据就根据最近一月来更新期初数据
        if pre_balanceRecords.exists():
            pre_record = pre_balanceRecords[-1]
            newBalanceInfo['preRecord'] = pre_record.id
            newBalanceInfo['beginingDamount'] = \
                pre_record.beginingDamount + pre_record.damount
            newBalanceInfo['beginingCamount'] = \
                pre_record.beginingCamount + pre_record.cumulativeCamount
        # 以后月份存在数据就添加以后最近一月那条记录的关联
        if next_balanceRecords.exists():
            next_record = next_balanceRecords[0]
            newBalanceInfo['nextRecord'] = next_record.id

        if entry.damount != 0:
            newBalanceInfo['damount'] = entry_damount
        elif entry.camount != 0:
            newBalanceInfo['camount'] = entry_camount
        # 创建新的余额记录
        newBalance = accountBalanceTable.sudo().create(newBalanceInfo)

        if pre_balanceRecords.exists():
            pre_record.nextRecord = newBalance.id

        # 更新以后各月的余额数据
        newBalance.changeNextBalanceBegining(
            newBalance.endDamount, newBalance.endCamount)

    @api.model
    def _getBalanceRecord(self, accountId, itemId=False):
        '''获得分录对应期间和会计科目下的核算项目的余额记录，排除启用期初那条记录'''
        balanasTable = self.env['accountcore.accounts_balance']
        org = self.org.id
        year = self.voucherdate.year
        month = self.voucherdate.month
        record = balanasTable.search([['org', '=', org],
                                      ['year', '=', year],
                                      ['month', '=', month],
                                      ['account', '=', accountId],
                                      ['items', '=', itemId],
                                      ['isbegining', '=', False]])
        return record


class Enty(models.Model):
    '''一条分录'''
    _name = 'accountcore.entry'
    _description = "会计分录"
    voucher = fields.Many2one('accountcore.voucher',
                              string='所属凭证',
                              index=True,
                              ondelete='cascade')
    org = fields.Many2one(related="voucher.org", store=True, string="核算机构")
    v_year = fields.Integer(related="voucher.year",
                            store=True,
                            string="年",
                            index=True)
    v_month = fields.Integer(related="voucher.month",
                             store=True,
                             string="月",
                             index=True)
    updata_balance = fields.Boolean(string='是否更新科目余额内部标记', default=False)
    # sequence = fields.Integer('Sequence')
    explain = fields.Char(string='说明')
    account = fields.Many2one('accountcore.account',
                              string='科目',
                              required=True,
                              index=True,
                              ondelete='restrict')
    items = fields.Many2many('accountcore.item',
                             string='核算项目',
                             index=True,
                             ondelete='restrict')
    # Monetory类型字段必须有
    currency_id = fields.Many2one('res.currency',
                                  compute='_get_company_currency',
                                  readonly=True,
                                  oldname='currency',
                                  string="Currency",
                                  help='Utility field to express amount currency')
    # Monetory类型字段必须有currency_id
    damount = fields.Monetary(string='借方金额', default=0)
    # Monetory类型字段必须有currency_id
    camount = fields.Monetary(string='贷方金额', default=0)
    cashFlow = fields.Many2one('accountcore.cashflow',
                               string='现金流量项目',
                               index=True,
                               ondelete='restrict')
    # 必录的核算项目
    account_item = fields.Many2one(string='*核算项目',
                                   compute="_getAccountItem",
                                   store=True,
                                   index=True)
    items_html = fields.Html(string="分录内容",
                             compute='_createItemsHtml',
                             store=True)

    @api.multi
    @api.depends('items.name', 'account_item', 'items.item_class_name')
    def _createItemsHtml(self):
        for entry in self:
            content = ["<div>["+item.item_class_name+"]" +
                       item.name+"</div>" for item in entry.items]
            entry.items_html = ''.join(content)

    @api.multi
    @api.depends('items', 'account')
    def _getAccountItem(self):
        for entry in self:
            if not entry.account.accountItemClass:
                entry.account_item = None
                return
            if entry.items:
                for item in entry.items:
                    if item.itemClass.id == entry.account.accountItemClass.id:
                        entry.account_item = item.id
                        return
                entry.account_item = None

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
    _description = '用户设置模型字段默认值'
    default_ruleBook = fields.Many2many('accountcore.rulebook',
                                        string='默认凭证标签')
    default_org = fields.Many2one('accountcore.org',
                                  string='默认机构')
    default_voucherDate = fields.Date(string='记账日期',
                                      default=fields.Date.today())
    default_real_date = fields.Date(string='业务日期')

    # 设置新增凭证,日期,机构和账套字段的默认值
    def setDefaults(self):
        modelName = 'accountcore.voucher'
        self._setDefault(modelName,
                         'ruleBook',
                         self.default_ruleBook.ids)
        self._setDefault(modelName,
                         'org',
                         self.default_org.id)
        self._setDefault(modelName, 'voucherdate',
                         json.dumps(self.default_voucherDate.strftime('%Y-%m-%d')))
        if self.default_real_date:
            self._setDefault(modelName, 'real_date',
                             json.dumps(self.default_real_date.strftime('%Y-%m-%d')))
        self.env.user.currentOrg = self.default_org.id
        return True

    # 设置默认值
    def _setDefault(self, modelName, fieldName, defaultValue):
        idOfField = self._getIdOfIdField(fieldName,
                                         modelName,)
        rd = self._getDefaultRecord(idOfField)
        if rd.exists():
            self._modifyDefault(rd, idOfField, defaultValue)
        else:
            self._createDefault(idOfField, defaultValue)

    # 获取要设置默认值的字段在ir.model.fields中的id
    def _getIdOfIdField(self, fieldName, modelname):
        domain = [('model', '=', modelname),
                  ('name', '=', fieldName)]
        rds = self.env['ir.model.fields'].sudo().search(domain, limit=1)
        return rds.id

    # 是否已经设置过该字段的默认值
    def _getDefaultRecord(self, id):
        domain = [('field_id', '=', id),
                  ('user_id', '=', self.env.uid)]
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
    _description = '新增下级科目向导'
    fatherAccountId = fields.Many2one('accountcore.account',
                                      string='上级科目',
                                      help='新增科目的直接上级科目')
    fatherAccountNumber = fields.Char(related='fatherAccountId.number',
                                      string='上级科目编码')

    org = fields.Many2one('accountcore.org',
                          string='所属机构',
                          help="科目所属机构",
                          index=True,
                          ondelete='restrict')

    accountsArch = fields.Many2one('accountcore.accounts_arch',
                                   string='所属科目体系',
                                   help="科目所属体系",
                                   index=True,
                                   ondelete='restrict')

    accountClass = fields.Many2one('accountcore.accountclass',
                                   string='科目类别',
                                   index=True,
                                   ondelete='restrict')
    number = fields.Char(string='科目编码', required=True)
    name = fields.Char(string='科目名称', required=True)
    direction = fields.Selection([('1', '借'),
                                  ('-1', '贷')],
                                 string='余额方向',
                                 required=True)
    cashFlowControl = fields.Boolean(string='分配现金流量')
    itemClasses = fields.Many2many('accountcore.itemclass',
                                   string='包含的核算项目类别',
                                   help="录入凭证时,提示选择该类别下的核算项目",
                                   ondelete='restrict')
    accountItemClass = fields.Many2one('accountcore.itemclass',
                                       string='作为明细科目的类别',
                                       help="录入凭证分录时必须输入的该类别下的一个核算项目,作用相当于明细科目",
                                       ondelete='restrict')
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
                      'number': fatherAccount.number + '.'
                      + str(fatherAccount.currentChildNumber)}
        fatherAccount.currentChildNumber = fatherAccount.currentChildNumber+1
        values.update(newAccount)
        rl = super(CreateChildAccountWizard, self).create(values)
        a = accountTable.create(values)
        # 添加到上级科目的直接下级
        fatherAccount.write({'childs_ids': [(4, a.id)]})
        return rl


class VoucherNumberTastics(models.Model):
    '''凭证编号的生成策略,一张凭证在不同的策略下有不同的凭证编号,自动生成凭证编号时需要指定一个策略'''
    _name = 'accountcore.voucher_number_tastics'
    _description = '凭证编号生成策略'
    number = fields.Char(string='凭证编号策略编码', required=True)
    name = fields.Char(string='凭证编号策略', required=True)
    # is_defualt = fields.Boolean(string='默认使用')
    _sql_constraints = [('accountcore_voucher_number_tastics_unique', 'unique(number)',
                         '凭证编号策略编码重复了!'),
                        ('accountcore_voucher_number_tastics_unique', 'unique(name)',
                         '凭证编号策略名称重复了!')]

    @staticmethod
    def get_number(tastics_str, tastics_id):
        '''设置获得对应策略下的凭证编号'''
        container = json.loads(tastics_str)
        number = container.get(str(tastics_id), 0)
        return number


class ExtensionUser(models.Model):
    '''扩展基础用户属性'''
    _inherit = 'res.users'
    currentOrg = fields.Many2one('accountcore.org', string="当前核算机构")
    voucherNumberTastics = fields.Many2one('accountcore.voucher_number_tastics',
                                           string='默认凭证编号策略')


class NumberStaticsWizard(models.TransientModel):
    '''设置用户默认凭证编码策略向导'''
    _name = 'accountcore.voucher_number_statics_default'
    _description = '设置用户默认凭证编码策略向导'
    voucherNumberTastics = fields.Many2one('accountcore.voucher_number_tastics',
                                           string='用户默认凭证编码策略')

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
    _description = '设置凭证编号向导'
    voucherNumberTastics = fields.Many2one('accountcore.voucher_number_tastics',
                                           '要使用的凭证编码策略',
                                           required=True)
    startNumber = fields.Integer(string='从此编号开始', default=1, required=True)

    @api.model
    def default_get(self, field_names):
        '''获得用户的默认凭证编号策略'''
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
                voucher.numberTasticsContainer_str,
                numberTasticsId,
                startNumber)
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
    _description = '设置单张凭证编号向导'
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
            voucher.numberTasticsContainer_str,
            currentUserNumberTastics_id,
            newNumber)
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
    # 通过createDate生成,不要直接修改
    year = fields.Integer(string='年', required=True,
                          index=True)
    # 通过createDate生成,不要直接修改
    month = fields.Integer(string='月', required=True)
    isbegining = fields.Boolean(string="是启用期间", default=False)
    account = fields.Many2one('accountcore.account',
                              string='会计科目',
                              required=True,
                              index=True,
                              ondelete='cascade')
    accountItemClass = fields.Many2one('accountcore.itemclass',
                                       string='核算项目类别',
                                       related='account.accountItemClass')
    items = fields.Many2one('accountcore.item',
                            string='核算项目',
                            index=True,
                            ondelete='cascade')
    beginingDamount = fields.Monetary(string="期初借方", default=0)  # 当月初
    beginingCamount = fields.Monetary(string='期初贷方', default=0)
    # Monetory类型字段必须有currency_id
    damount = fields.Monetary(string='本期借方金额', default=0)
    camount = fields.Monetary(string='本期贷方金额', default=0)
    endDamount = fields.Monetary(string="期末借方余额",
                                 compute='getEndingBalance_D',
                                 store=True)
    endCamount = fields.Monetary(string="期末贷方余额",
                                 compute='getEndingBalance_C',
                                 store=True)
    cumulativeDamount = fields.Monetary(string='本年借方累计',
                                        compute='getCumulativeDamount',
                                        store=True,
                                        default=0)
    cumulativeCamount = fields.Monetary(string='本年贷方累计',
                                        compute='getCumulativeCamount',
                                        store=True,
                                        default=0)

    beginCumulativeDamount = fields.Monetary(string='月初本年借方累计', default=0)
    beginCumulativeCamount = fields.Monetary(string='月初本年贷方累计', default=0)
    preRecord = fields.Many2one(
        'accountcore.accounts_balance', string='最近上一期记录')
    nextRecord = fields.Many2one(
        'accountcore.accounts_balance', string='最近后一期记录')
    # Monetory类型字段必须有,要不无法正常显示
    currency_id = fields.Many2one('res.currency',
                                  compute='_get_company_currency',
                                  readonly=True,
                                  string="Currency",
                                  help='Utility field to express amount currency')

    @api.one
    def _get_company_currency(self):
        self.currency_id = self.env.user.company_id.currency_id

    # @api.onchange('createDate')
    @api.depends('createDate')
    def chage_period(self):
        if self.createDate:
            self.year = self.createDate.year
            self.month = self.createDate.month

    @api.model
    def create(self, values):
        '''新增一条科目期初'''
        if self._check_repeat(values):
            raise exceptions.ValidationError(
                '不能新增,因为已经存在一条相同科目的期初余额记录,请在该行记录上修改!')
        else:
            rl = super(AccountsBalance, self).create(values)
            # if 创建启用期初
            if rl.isbegining:
                nextBalances = (rl.get_next_balanceRecords(True)).filtered(
                    lambda r: r.isbegining == False)
                preBalances = rl.get_pre_balanceRecords(False)
                # 更新启用期以后各期的期初余额
                if len(nextBalances) > 0:
                    rl.setNextBalance(nextBalances[0])
                    rl.changeNextBalanceBegining(rl.endDamount,
                                                 rl.endCamount)
                    # 更新当年各期的本年累计
                    # rl.updateCumulative(
                    #     rl.beginCumulativeDamount, rl.beginCumulativeCamount)
                # 更新启用期以前各期的期初余额
                if len(preBalances) > 0:
                    preBalances[-1].setNextBalance(rl)
                    rl.changePreBalanceBegining(rl.beginingDamount,
                                                rl.beginingCamount)
        return rl

    @api.multi
    def unlink(self):
        '''删除科目余额记录'''
        for mySelf in self:
            mySelf.deleteRelatedAndUpdate()
            # if 删除的是启用期余额记录,更新启用期当年各月本年累计
            if mySelf.isbegining:
                mySelf.updateCumulative(-mySelf.beginCumulativeDamount,
                                        -mySelf.beginCumulativeCamount)
        rl_bool = super(AccountsBalance, self).unlink()
        return rl_bool

    @api.multi
    def write(self, values):
        '''修改编辑科目余额'''
        self.ensure_one()
        if self.isbegining:
            if any(['account' in values,
                    'items' in values,
                    'year' in values,
                    'month' in values,
                    'org' in values]):
                oldSelf = {}
                oldSelf['org'] = self.org.id
                oldSelf['createDate'] = self.createDate
                oldSelf['year'] = self.year
                oldSelf['month'] = self.month
                oldSelf['account'] = self.account.id
                if (self.items.id == False):
                    oldSelf['items'] = None
                else:
                    oldSelf['items'] = self.items.id
                oldSelf['beginingDamount'] = self.beginingDamount
                oldSelf['beginingCamount'] = self.beginingCamount
                oldSelf['damount'] = self.damount
                oldSelf['camount'] = self.camount
                oldSelf['endDamount'] = self.endDamount
                oldSelf['endCamount'] = self.endCamount
                oldSelf['cumulativeDamount'] = self.beginCumulativeDamount+self.damount
                oldSelf['cumulativeCamount'] = self.beginCumulativeCamount+self.camount
                oldSelf['beginCumulativeDamount'] = self.beginCumulativeDamount
                oldSelf['beginCumulativeCamount'] = self.beginCumulativeCamount
                oldSelf['preRecord'] = None
                oldSelf['nextRecord'] = None
                oldSelf['isbegining'] = self.isbegining
                oldSelf.update(values)
                if self._check_repeat(oldSelf):
                    raise exceptions.ValidationError(
                        '不能修改,因为已经存在一条相同科目的期初余额记录行,请取消,在另一行已存在的记录上修改!若不想保留本行，请进行删除操作')
                self.deleteRelatedAndUpdate()
                old_beginCumulativeDamount = self.beginCumulativeDamount
                old_beginCumulativeCamount = self.beginCumulativeCamount
                # 更新本年累计
                # self.updateCumulative(-self.beginCumulativeDamount, -
                #                       self.beginCumulativeCamount)
                rl_bool = super(AccountsBalance, self).write(oldSelf)
                self.buildRelatedAndUpdate()
                # 更新本年累计
                self.updateCumulative(
                    self.beginCumulativeDamount-old_beginCumulativeDamount,
                    self.beginCumulativeCamount-old_beginCumulativeCamount)
                return rl_bool
            else:
                # 更新本年累计
                if 'beginCumulativeDamount' in values:
                    values.update(
                        {'cumulativeDamount': values['beginCumulativeDamount']})
                if 'beginCumulativeCamount' in values:
                    values.update(
                        {'cumulativeCamount': values['beginCumulativeCamount']})
                rool_bool = super(AccountsBalance, self).write(values)
                nextBalances = (self.get_next_balanceRecords(True)).filtered(
                    lambda r: r.isbegining == False)
                preBalances = self.get_pre_balanceRecords(False)
                if len(nextBalances) > 0:
                    self.changeNextBalanceBegining(
                        self.endDamount, self.endCamount)
                if len(preBalances) > 0:
                    self.changePreBalanceBegining(
                        self.beginingDamount, self.beginingCamount)
                # 更新本年累计
                # self.updateCumulative(
                #     self.beginCumulativeDamount, self.beginCumulativeCamount)
                return rool_bool
        else:
            rl_bool = super(AccountsBalance, self).write(values)
            return rl_bool

    @api.model
    def _check_repeat(self, accountBalance):
        '''检查是否已经有一条期初或余额记录'''
        if ('items' in accountBalance):
            if accountBalance['isbegining'] == True:
                records = self.search([('org', '=', accountBalance['org']),
                                       ('account', '=',
                                        accountBalance['account']),
                                       ('items', '=', accountBalance['items']),
                                       ('isbegining', '=', True)])
            else:
                records = self.search([('org', '=', accountBalance['org']),
                                       ('year', '=', accountBalance['year']),
                                       ('month', '=', accountBalance['month']),
                                       ('account', '=',
                                        accountBalance['account']),
                                       ('items', '=', accountBalance['items']),
                                       ('isbegining', '=', False)])

        else:
            if accountBalance['isbegining'] == True:
                records = self.search([('org', '=', accountBalance['org']),
                                       ('account', '=',
                                        accountBalance['account']),
                                       ('isbegining', '=', True)])
            else:
                records = self.search([('org', '=', accountBalance['org']),
                                       ('year', '=', accountBalance['year']),
                                       ('month', '=', accountBalance['month']),
                                       ('account', '=',
                                        accountBalance['account']),
                                       ('isbegining', '=', False)])
        if records.exists():
            return True
        return False

    @api.model
    def addDamount(self, amount):
        self.damount = self.damount+amount

    @api.model
    def addCamount(self, amount):
        self.camount = self.camount+amount

    @api.model
    def changeNextBalanceBegining(self, end_damount, end_camount):
        '''更新以后各期的期初余额,依据对象的nextRecord属性,damount变动的借方'''
        if self.nextRecord:
            nextRecord = self.nextRecord
            nextRecord.beginingDamount = end_damount
            nextRecord.beginingCamount = end_camount
            nextRecord.changeNextBalanceBegining(
                nextRecord.endDamount, nextRecord.endCamount)
        else:
            return

    @api.model
    def updateCumulative(self, cumulativeDamount, cumulativeCamount):
        '''更新启用期初当年的各余额记录的本年累计'''
        currenYearRecords = self.search(
            [('year', '=', self.year),
             ('org', '=', self.org.id),
             ('account', '=', self.account.id),
             ('items', '=', self.items.id),
             ('isbegining', '=', False)])
        for r in currenYearRecords:
            r.write({'cumulativeDamount': r.cumulativeDamount+cumulativeDamount,
                     'cumulativeCamount': r.cumulativeCamount+cumulativeCamount})

    @api.model
    def changePreBalanceBegining(self, begin_damount, begin_camount):
        '''更新以前各期期的期初余额,依据对象的preRecord属性'''
        if self.preRecord:
            preRecord = self.preRecord
            preRecord.beginingDamount = begin_damount-self.preRecord.damount
            preRecord.beginingCamount = begin_camount-self.preRecord.camount
            preRecord.changePreBalanceBegining(
                preRecord.beginingDamount, preRecord.beginingCamount)
        else:
            return

    @api.multi
    @api.depends('beginCumulativeDamount', 'damount')
    def getEndingBalance_D(self):
        '''计算期末贷方余额'''
        for record in self:
            record.endDamount = record.beginingDamount+record.damount
        return True

    @api.depends('beginCumulativeDamount', 'damount')
    def getCumulativeDamount(self):
        '''计算本年借方累计发生额'''
        # 机构科目项目在本年内1月到本月的余额记录
        # 如果是改变启用期初,就不处理
        if self.isbegining == True:
            self.cumulativeDamount = self.beginCumulativeDamount+self.damount
            return True
        records = self.search(
            [('year', '=', self.year),
                ('month', "<=", self.month),
                ('org', '=', self.org.id),
                ('account', '=', self.account.id),
                ('items', '=', self.items.id)])
        yearDamount = sum(records.mapped('damount'))
        beginingRecord = records.filtered(lambda r: r.isbegining)
        if beginingRecord.exists():
            yearDamount = yearDamount+beginingRecord.beginCumulativeDamount
        self.cumulativeDamount = yearDamount
        return True

    @api.depends('beginCumulativeCamount', 'camount')
    def getCumulativeCamount(self):
        '''计算本年借方累计发生额'''
        # 如果不是改变启用期初,就不处理
        if self.isbegining == True:
            self.cumulativeCamount = self.beginCumulativeCamount+self.camount
            return True
        records = self.search(
            [('year', '=', self.year),
                ('month', "<=", self.month),
                ('org', '=', self.org.id),
                ('account', '=', self.account.id),
                ('items', '=', self.items.id)])
        # 对camount字段求和
        yearCamount = sum(records.mapped('camount'))
        beginingRecord = records.filtered(lambda r: r.isbegining)
        if beginingRecord.exists():
            yearCamount = yearCamount+beginingRecord.beginCumulativeCamount
        self.cumulativeCamount = yearCamount
        return True

    @api.multi
    @api.depends('beginingCamount', 'camount')
    def getEndingBalance_C(self):
        '''计算期末借方余额'''
        for record in self:
            record.endCamount = record.beginingCamount+record.camount
        return True

    def get_pre_balanceRecords(self, includeCrrentMonth=True):
        '''获得记录科目余额的当月以前月份记录集合，默认包含当月'''
        balanceRecords = self.get_my_balanceRecords()
        if not includeCrrentMonth:
            pre_balanceRecords = (balanceRecords.filtered(lambda r: (
                r.year < self.year
                or (r.year == self.year
                    and r.month < self.month)))).sorted(key=lambda a: (a.year, a.month))
        else:
            pre_balanceRecords = (balanceRecords.filtered(lambda r: (
                r.year < self.year
                or (r.year == self.year
                    and r.month <= self.month)))).sorted(key=lambda a: (a.year, a.month))
        return pre_balanceRecords

    def get_next_balanceRecords(self, inCludeCurrentMonth=False):
        '''获得记录科目余额的以后月份记录集合，默认不包含当月'''
        balanceRecords = self.get_my_balanceRecords()
        if not inCludeCurrentMonth:
            next_balanceRecords = (balanceRecords.filtered(lambda r: (
                r.year > self.year
                or (r.year == self.year
                    and r.month > self.month)))).sorted(key=lambda a: (a.year, a.month))
        else:
            next_balanceRecords = (balanceRecords.filtered(lambda r: (
                r.year > self.year
                or (r.year == self.year
                    and r.month >= self.month)))).sorted(key=lambda a: (a.year, a.month))
        return next_balanceRecords

    def get_my_balanceRecords(self):
        '''获得记录科目余额的各月份记录集合'''
        accountBalanceTable = self.env['accountcore.accounts_balance']
        domain_org = ('org', '=', self.org.id)
        domain_account = ('account', '=', self.account.id)
        if self.items:
            domain_item = ('items', '=', self.items.id)
            balanceRecords = accountBalanceTable.search(
                [domain_org, domain_account, domain_item])
        else:
            balanceRecords = accountBalanceTable.search(
                [domain_org, domain_account])
        return balanceRecords

    def setNextBalance(self, accountBalance):
        '''设置两期余额对象的关联关系'''
        self.nextRecord = accountBalance
        accountBalance.preRecord = self

    def isSameWith(self, accountBalance):
        '''判断两个余额对象是不是同一机构,科目和核算项目'''
        if (self.org != accountBalance.org) or (self.account != accountBalance.account):
            return False
        elif self.items != AccountsBalance.items:
            return False
        return True

    def deleteRelatedAndUpdate(self):
        '''取消余额记录前后期的关联，同时更新关联余额'''
        if all([self.nextRecord, (not self.preRecord)]):  # 前期没有余额记录，后期有
            self.changeNextBalanceBegining(0, 0)
            self.nextRecord = None
        elif all([self.nextRecord, self.preRecord]):  # 前后期都有余额记录
            self.preRecord.setNextBalance(self.nextRecord)
            self.changeNextBalanceBegining(0, 0)
            self.changePreBalanceBegining(
                0-self.preRecord.Damount, 0-self.preRecord.Camount)
        elif all([(not self.nextRecord), self.preRecord]):  # 前期有，后期都没有余额记录
            self.changePreBalanceBegining(
                0-self.preRecord.beginingDamount, 0-self.preRecord.beginingCamount)
        return self

    def buildRelatedAndUpdate(self):
        '''新建余额记录的前后期关系，同时更新关联记录余额'''
        nextBalances = (self.get_next_balanceRecords(True)).filtered(
            lambda r: r.isbegining == False)
        preBalances = self.get_pre_balanceRecords(False)
        if len(nextBalances) > 0:
            self.setNextBalance(nextBalances[0])
            self.changeNextBalanceBegining(self.endDamount,
                                           self.endCamount)
        if len(preBalances) > 0:
            preBalances[-1].setNextBalance(self)
            self.changePreBalanceBegining(self.beginingDamount,
                                          self.beginingCamount)

    def updata_balance(self):
        '''根据会计分录定时更新余额表'''
        # 获得要更新的会计分录
        entrys = self.env['accountcore.entry'].sudo().search(
            [('updata_balance', '=', False)])

        for entry in entrys:
            self._updateAccountBalance(entry)

    # @api.model
    # def _updateBalance(self, isAdd=True):
    #     '''更新余额'''
    #     for entry in self.entrys:
    #         self._updateAccountBalance(entry, isAdd)

    @api.model
    def _updateAccountBalance(self, entry, isAdd=True):
        '''新增和修改凭证，更新科目余额'''
        item = entry.getItemByitemClass(entry.account.accountItemClass)
        if item:
            itemId = item.id
        else:
            itemId = False

        if isAdd:
            computMark = 1  # 增加金额
        else:
            computMark = -1  # 减少金额
        entry_damount = entry.damount*computMark
        entry_camount = entry.camount*computMark
        accountBalanceTable = self.env['accountcore.accounts_balance']
        accountBalanceMark = AccountBalanceMark(orgId=entry.org.id,
                                                # accountId=entry.account.id,
                                                accountId=entry.account.id,
                                                itemId=itemId,
                                                createDate=self.voucherdate,
                                                accountBalanceTable=accountBalanceTable,
                                                isbegining=False)
        # if 一条会计分录有核算项目
        if entry.items:
            for item_ in entry.items:
                accountBalance = self._getBalanceRecord(entry.account.id,
                                                        item_.id)
                # if 当月已经存在一条该科目的余额记录（不包括启用期初余额那条）
                if accountBalance.exists():
                    self._modifyBalance(entry_damount,
                                        accountBalance,
                                        entry_camount)
                # else 不存在就新增一条,但必须是科目的必选核算项目类
                elif item_.id == itemId:
                    self._buildBalance(True,
                                       accountBalanceMark,
                                       entry,
                                       entry_damount,
                                       entry_camount)
        # else 一条会计分录没有核算项目
        else:
            accountBalance = self._getBalanceRecord(entry.account.id)
            # if 当月已经存在一条该科目的余额记录（不包括启用期初余额那条）
            if accountBalance.exists():
                self._modifyBalance(entry_damount,
                                    accountBalance,
                                    entry_camount)
            # else 不存在就新增一条
            else:
                # 不排除启用期初那条记录
                self._buildBalance(False,
                                   accountBalanceMark,
                                   entry,
                                   entry_damount,
                                   entry_camount)

        return True

    @api.model
    # def _getBalanceRecord(self, accountId, itemId=False):
    def _getBalanceRecord(self, entry, itemId=False):
        '''获得分录对应期间和会计科目下的核算项目的余额记录，排除启用期初那条记录'''
        balanasTable = self.env['accountcore.accounts_balance']
        org = entry.org.id
        year = entry.v_year
        month = entry.v_month
        record = balanasTable.searcFh([['org', '=', org],
                                       ['year', '=', year],
                                       ['month', '=', month],
                                       ['account', '=', entry.account.id],
                                       ['items', '=', itemId],
                                       ['isbegining', '=', False]])
        return record


class AccountBalanceMark(object):
    def __init__(self, orgId, accountId, itemId, createDate, accountBalanceTable, isbegining):
        self.org = orgId
        self.account = accountId
        self.items = itemId
        self.createDate = createDate
        self.year = createDate.year
        self.month = createDate.month
        self.isbegining = isbegining
        self.accountBalanceTable = accountBalanceTable

    def keys(self):
        return ('org',
                'account',
                'items',
                'createDate',
                'year',
                'month',
                'isbegining')

    def __getitem__(self, item):
        return getattr(self, item)

    def get_pre_balanceRecords_all(self):
        '''获得相同科目余额前期记录集合，不排除期初那条'''
        accountBalanceTable = self.accountBalanceTable
        domain_org = ('org', '=', self.org)
        domain_account = ('account', '=', self.account)
        domain_item = ('items', '=', self.items)
        balanceRecords = accountBalanceTable.search(
            [domain_org, domain_account, domain_item])
        # 该科目的前期记录集合
        pre_balanceRecords = (balanceRecords.filtered(lambda r: (
            r.year < self.year
            or (r.year == self.year
                and r.month <= self.month)))).sorted(key=lambda a: (a.year, a.month, not a.isbegining))
        return pre_balanceRecords

    def get_next_balanceRecords_all(self):
        '''获得相同科目余额后期记录集合，不排除期初那条'''
        accountBalanceTable = self.accountBalanceTable
        domain_org = ('org', '=', self.org)
        domain_account = ('account', '=', self.account)
        domain_item = ('items', '=', self.items)
        balanceRecords = accountBalanceTable.search(
            [domain_org, domain_account, domain_item])
        # 该科目的后期记录集合
        next_balanceRecords = (balanceRecords.filtered(lambda r: (
            r.year > self.year
            or (r.year == self.year
                and r.month > self.month)))).sorted(key=lambda a: (a.year, a.month, not a.isbegining))
        return next_balanceRecords


class SpecialAccounts(models.Model):
    '''特殊的会计科目'''
    _name = "accountcore.special_accounts"
    _description = '特殊的会计科目'
    name = fields.Char(string='特殊性', required=True)
    purpos = fields.Html(string='用途说明')
    accounts = fields.Many2many('accountcore.account',
                                string='科目',
                                required=True)
    children = fields.Boolean(string='包含明细科目')
    items = fields.Many2many('accountcore.item', string='核算项目')
    _sql_constraints = [('accountcore_special_accounts_name_unique', 'unique(name)',
                         '特殊性描述重复了!')]


class GetAccountsBalance(models.TransientModel):
    '''科目余额查询向导'''
    _name = 'accountcore.get_account_balance'
    _description = '科目查询向导'
    startDate = fields.Date(string="开始期间")
    endDate = fields.Date(string="结束期间")
    onlyShowOneLevel = fields.Boolean(string="只显示一级科目", default=False)
    summaryLevelByLevel = fields.Boolean(string='逐级汇总科目',
                                         default=True,
                                         readonly=True)
    includeAccountItems = fields.Boolean(string='包含核算项目', default=True)
    no_show_no_hanppend = fields.Boolean(string='隐藏无发生额的科目', default=False)
    order_orgs = fields.Boolean(string='多机构分开显示', default=False)
    noShowZeroBalance = fields.Boolean(string='隐藏余额为零的科目', default=False)
    noShowNoAmount = fields.Boolean(
        string='没有任何金额不显示', default=True)
    org = fields.Many2many(
        'accountcore.org',
        string='机构范围',
        default=lambda s: s.env.user.currentOrg,
        required=True

    )
    account = fields.Many2many('accountcore.account',
                               string='科目范围',
                               required=True)

    @api.multi
    def getReport(self, args):
        '''查询科目余额'''
        self.ensure_one()
        if len(self.org) == 0:
            raise exceptions.ValidationError('你还没选择机构范围！')
            return False
        if len(self.account) == 0:
            raise exceptions.ValidationError('你需要选择查询的科目范围！')
            return False
        self._setDefaultDate()
        [data] = self.read()
        datas = {
            'form': data
        }
        return self.env.ref('accountcore.accounctore_accountsbalance_report').report_action([], data=datas)

    def _setDefaultDate(self):
        if not self.startDate:
            self.startDate = '1970-01-01'
        if not self.endDate:
            self.endDate = '9999-12-31'
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')


class GetSubsidiaryBook(models.TransientModel):
    "科目明细账查询向导"
    _name = 'accountcore.get_subsidiary_book'
    startDate = fields.Date(string='开始月份')
    endDate = fields.Date(string='结束月份')
    orgs = fields.Many2many(
        'accountcore.org',
        string='机构范围',
        default=lambda s: s.env.user.currentOrg, required=True)
    account = fields.Many2one(
        'accountcore.account', string='查询的科目', required=True)
    item = fields.Many2one('accountcore.item', string='查询的核算项目')
    voucher_number_tastics = fields.Many2one('accountcore.voucher_number_tastics',
                                             string='凭证号策略',
                                             required=True,
                                             default=lambda s: s.env.user.voucherNumberTastics)

    @api.multi
    def getReport(self, *args):
        self.ensure_one()
        if len(self.orgs) == 0:
            raise exceptions.ValidationError('你还没选择机构范围！')
            return False
        if not self.account:
            raise exceptions.ValidationError('你需要选择查询的科目！')
            return False
        if not self.voucher_number_tastics:
            raise exceptions.ValidationError('你需要选择查询凭证编码策略！')
            return False
        self._setDefaultDate()
        [data] = self.read()
        datas = {
            'form': data
        }
        return self.env.ref('accountcore.subsidiarybook_report').report_action([], data=datas)

    def _setDefaultDate(self):
        if not self.startDate:
            self.startDate = '1970-01-01'
        if not self.endDate:
            self.endDate = '9999-12-31'
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')


class Period(object):
    '''一个期间'''

    def __init__(self, start_date, end_date):
        if isinstance(start_date, str):
            self.start_date = datetime.datetime.strptime(
                start_date, '%Y-%m-%d')
        else:
            self.start_date = start_date
        if isinstance(end_date, str):
            self.end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        else:
            self.end_date = end_date
        self.start_year = self.start_date.year
        self.end_year = self.end_date.year
        self.start_month = self.start_date.month
        self.end_month = self.end_date.month

    def getPeriodList(self):
        '''获得日期范围内的会计期间列表'''

        months = (self.end_year - self.start_year) * \
            12 + self.end_month - self.start_month
        month_range = ['%s-%s-%s' % (self.start_year + mon//12, mon % 12+1, 1)
                       for mon in range(self.start_month-1, self.start_month + months)]
        voucherPeriods = [VoucherPeriod(
            datetime.datetime.strptime(d, '%Y-%m-%d')) for d in month_range]

        return voucherPeriods


class VoucherPeriod(object):
    '''一个会计期间,月份'''

    def __init__(self, date):
        self.date = date
        self.year = date.year
        self.month = date.month
        # 当月第一天
        self.firstDate = datetime.date(year=self.year,
                                       month=self.month,
                                       day=1)
        # 当月天数
        self.days = calendar.monthrange(self.year,
                                        self.month)[1]
        # 当月最后一天
        self.endDate = datetime.date(year=self.year,
                                     month=self.month,
                                     day=self.days)


class currencyDown_sunyi(models.TransientModel):
    "自动结转损益向导"
    _name = 'accountcore.currency_down_sunyi'
    startDate = fields.Date(string='开始月份', required=True)
    endDate = fields.Date(string='结束月份', required=True)
    orgs = fields.Many2many(
        'accountcore.org',
        string='机构范围',
        default=lambda s: s.env.user.currentOrg, required=True)

    def soucre(s): return s.env.ref('rulebook_999')

    @api.multi
    def do(self, *args):
        '''执行结转损益'''
        self.ensure_one()
        if len(self.orgs) == 0:
            raise exceptions.ValidationError('你还没选择机构范围！')
            return False
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')

        # 获得需要结转的会计期间
        periods = Period(self.startDate, self.endDate).getPeriodList()

        self.t_entry = self.env['accountcore.entry']
        # 本年利润科目
        self.ben_nian_li_run_account = self.env['accountcore.special_accounts'].sudo().search([
            ('name', '=', '本年利润科目')]).accounts
        # 损益调整科目
        self.sun_yi_tiao_zhen_account = self.env['accountcore.special_accounts'].sudo().search([
            ('name', '=', '以前年度损益调整科目')]).accounts
        # 依次处理选种机构
        # 生成的凭证列表
        voucher_ids = []
        for org in self.orgs:
            # 依次处理会计期间
            for p in periods:
                voucher = self._do_currencyDown(org, p)
                if voucher:
                    voucher_ids.append(voucher.id)

        return {'name': '自动生成的结转损益凭证',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'accountcore.voucher',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in',  voucher_ids)]
                }

    def _do_currencyDown(self, org, voucher_period):
        '''结转指定机构某会计期间的损益'''

        # 找出损益类相关科目
        accounts = self._get_sunyi_accounts(org)
        # 获得损益类相关科目在期间的余额
        accountsBalance = self._get_balances(org, voucher_period, accounts)
        # 根据余额生成结转损益的凭证
        voucher = self._creat_voucher(accountsBalance, org, voucher_period)
        return voucher

    def _get_sunyi_accounts(self, org):
        '''获得该机构的结转损益类科目'''
        # 属于损益类别的科目,但不包括"以前年度损益调整"
        accounts = self.env['accountcore.account'].sudo().search([('accountClass.name', '=', '损益类'),
                                                                  ('id', '!=',
                                                                   self.sun_yi_tiao_zhen_account.id),
                                                                  '|', ('org',
                                                                        '=', org.id),
                                                                  ('org', '=', False)])
        return accounts

    def _get_balances(self, org, voucer_period, accounts):
        '''获得某一机构在一个会计月份的余额记录'''
        ids = accounts.mapped('id')
        balances = self.env['accountcore.accounts_balance'].sudo().search([('org', '=', org.id),
                                                                           ('year', '=',
                                                                            voucer_period.year),
                                                                           ('month', '=',
                                                                            voucer_period.month),
                                                                           ('account', 'in', ids)])
        return balances

    def _creat_voucher(self, accountsBalance, org, voucer_period):
        '''新增结转损益凭证'''
        # 结转到本年利润的借方合计
        sum_d = 0
        # 结转到本年利润的贷方合计
        sum_c = 0

        entrys_value = []
        # 根据科目余额生成分录
        for b in accountsBalance:
            endAmount = b.endDamount-b.endCamount
            if b.account.direction == '1':
                if endAmount != 0:
                    entrys_value.append({"explain": '结转损益',
                                         "account": b.account.id,
                                         "items": [(6, 0, [b.items.id])],
                                         "camount": endAmount
                                         })
                    sum_d = sum_d+endAmount
            else:
                if endAmount != 0:
                    entrys_value.append({"explain": '结转损益',
                                         "account": b.account.id,
                                         "items": [(6, 0, [b.items.id])],
                                         "damount": -endAmount
                                         })
                    sum_c = sum_c+endAmount
        # 本年利润科目分录

        # 结转到贷方
        if sum_d != 0:
            entrys_value.append({"explain": '结转损益',
                                 "account": self.ben_nian_li_run_account.id,
                                 "damount": sum_d
                                 })
        # 结转到借方
        if sum_c != 0:
            entrys_value.append({"explain": '结转损益',
                                 "account": self.ben_nian_li_run_account.id,
                                 "camount": sum_c
                                 })
        if len(entrys_value) < 2:
            return None
        entrys = self.t_entry.sudo().create(entrys_value)
        voucher = self.env['accountcore.voucher'].sudo().create({
            'voucherdate': voucer_period.endDate,
            'org': org.id,
            'soucre': self.env.ref('accountcore.source_2').id,
            'ruleBook': [(6, 0, [self.env.ref('accountcore.rulebook_999').id])],
            'entrys': [(6, 0, entrys.ids)]
        })
        return voucher


class HelpClass(models.Model):
    '''帮助类别'''
    _name = 'accountcore.help_class'
    _description = '帮助类别'
    name = fields.Char(string='帮助类别', required=True)
    _sql_constraints = [('accountcore_help_class_name_unique', 'unique(name)',
                         '帮助类别名称重复了!')]


class GlobTag(models.Model):
    '''模块全局标签'''
    _name = 'accountcore.glob_tag'
    _description = '模块全局标签'
    name = fields.Char(string='全局标签名称', required=True)
    summary = fields.Char(string='使用范围和简介', required=True)
    js_code = fields.Text(string='js代码')
    python_code = fields.Text(string='python代码')
    sql_code = fields.Text(string='sql代码')
    str_code = fields.Text(string='字符串')
    application = fields.Html(string='详细使用说明')
    _sql_constraints = [('accountcore_glob_tag_name_unique', 'unique(name)',
                         '模块全局标签重复了!')]


class Helpes(models.Model):
    '''详细帮助'''
    _name = 'accountcore.helps'
    _description = '详细帮助'
    name = fields.Char(string='标题', required=True)
    help_class = fields.Many2one('accountcore.help_class',
                                 string='帮助类别',
                                 required=True)
    content = fields.Html(string='内容')
