# -*- coding: utf-8 -*-
from decimal import Decimal
import datetime
import json
from odoo import api
from odoo import exceptions
from odoo import fields
from odoo import models
from ..models.main_models import AccountsBalance
from ..models.main_models import Voucher
from ..models.ac_period import Period
from ..models.main_models import Glob_tag_Model
from ..models.ac_obj import ACTools
# 向导部分-开始
# 新增下级科目的向导


class CreateChildAccountWizard(models.TransientModel, Glob_tag_Model):
    '''新增下级科目的向导'''
    _name = 'accountcore.create_child_account'
    _description = '新增下级科目向导'
    fatherAccountId = fields.Many2one('accountcore.account',
                                      string='上级科目',
                                      help='新增科目的直接上级科目')
    fatherAccountNumber = fields.Char(related='fatherAccountId.number',
                                      string='上级科目编码')
    org = fields.Many2many('accountcore.org',
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
    is_show = fields.Boolean(string='凭证中显示', default=True)
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
        default['org'] = fatherAccount.org.ids
        default['accountClass'] = fatherAccount.accountClass.id
        default['direction'] = fatherAccount.direction
        default['cashFlowControl'] = fatherAccount.cashFlowControl
        default['number'] = fatherAccount.number + \
            '.' + str(fatherAccount.currentChildNumber)
        return default

    @api.model
    def create(self, values):
        if self.env.user.current_date:
            voucher_date = self.env.user.current_date
        if 'name' in values:
            if '-' in values['name']:
                raise exceptions.ValidationError("科目名称中不能含有'-'字符")
            if ' ' in values['name']:
                raise exceptions.ValidationError("科目名称中不能含有空格")
        fatherAccountId = self.env.context.get('active_id')
        accountTable = self.env['accountcore.account'].sudo()
        fatherAccount = accountTable.search(
            [['id', '=', fatherAccountId]])
        newAccount = {'fatherAccountId': fatherAccountId,
                      'accountClass': fatherAccount.accountClass.id,
                      'cashFlowControl': values['cashFlowControl'],
                      'name': fatherAccount.name+'---'+values['name'],
                      'direction': fatherAccount.direction,
                      'number': fatherAccount.number + '.'
                      + str(fatherAccount.currentChildNumber)}
        fatherAccount.currentChildNumber = fatherAccount.currentChildNumber+1
        values.update(newAccount)
        rl = super(CreateChildAccountWizard, self).create(values)
        if values["accountItemClass"] and (values["accountItemClass"] not in values["itemClasses"][0][2]):
            (values["itemClasses"][0][2]).insert(0, values["accountItemClass"])
        a = accountTable.create(values)
        # 添加到上级科目的直接下级
        fatherAccount.write({'childs_ids': [(4, a.id)], 'is_show': False})
        return rl
# 用户设置模型字段的默认取值向导(如，设置凭证默认值)


class AccountcoreUserDefaults(models.TransientModel):
    '''用户设置模型字段的默认取值向导'''
    _name = 'accountcoure.userdefaults'
    _description = '用户设置模型字段默认值'
    # default_ruleBook = fields.Many2many('accountcore.rulebook',
    #                                     string='默认凭证标签')
    default_org = fields.Many2one('accountcore.org',
                                  string='默认机构', default=lambda s: s.env.user.currentOrg)
    default_voucherDate = fields.Date(string='记账日期',
                                      default=lambda s: s.env.user.current_date)
    default_real_date = fields.Date(string='业务日期')
    default_glob_tag = fields.Many2many('accountcore.glob_tag',
                                        string='默认全局标签')
    # 设置新增凭证,日期,机构和账套字段的默认值

    def setDefaults(self):
        modelName = 'accountcore.voucher'
        self._setDefault(modelName,
                         'glob_tag',
                         self.default_glob_tag.ids)
        self._setDefault(modelName,
                         'org',
                         self.default_org.id)
        self._setDefault(modelName, 'voucherdate',
                         json.dumps(self.default_voucherDate.strftime('%Y-%m-%d')))
        if self.default_real_date:
            self._setDefault(modelName, 'real_date',
                             json.dumps(self.default_real_date.strftime('%Y-%m-%d')))
        else:
            self._setDefault(modelName, 'real_date', json.dumps(""))
        self.env.user.currentOrg = self.default_org.id
        self.env.user.current_date = self.default_voucherDate
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
# 设置用户默认凭证策略号策略向导


class NumberStaticsWizard(models.TransientModel):
    '''设置用户默认凭证策略号策略向导'''
    _name = 'accountcore.voucher_number_statics_default'
    _description = '设置用户默认凭证策略号策略向导'
    voucherNumberTastics = fields.Many2one('accountcore.voucher_number_tastics',
                                           string='当前用户的策略')

    @api.model
    def default_get(self, field_names):
        default = super().default_get(field_names)
        default['voucherNumberTastics'] = self.env.user.voucherNumberTastics.id
        return default
    
    def setVoucherNumberTastics(self, args):
        currentUser = self.env['res.users'].sudo().browse(self.env.uid)
        currentUser.write(
            {'voucherNumberTastics': self. voucherNumberTastics.id})
        return True
# 设置凭证策略号向导


class SetingVoucherNumberWizard(models.TransientModel):
    '''设置凭证策略号向导'''
    _name = 'accountcore.seting_vouchers_number'
    _description = '设置凭证策略号向导'
    voucherNumberTastics = fields.Many2one('accountcore.voucher_number_tastics',
                                           '要使用的凭证编码策略',
                                           required=True)
    startNumber = fields.Integer(string='从此编号开始', default=1, required=True)
    @api.model
    def default_get(self, field_names):
        '''获得用户的默认凭证编号策略'''
        default = super().default_get(field_names)
        if self.env.user.voucherNumberTastics:
            default['voucherNumberTastics'] = self.env.user.voucherNumberTastics.id
        return default
    @ACTools.refuse_role_search
    def setingNumber(self):
        args = self.env.context
        startNumber = self.startNumber
        numberTasticsId = self.voucherNumberTastics.id
        currentUserId = self.env.uid
        currentUser = self.env['res.users'].sudo().browse(currentUserId)
        currentUser.write(
            {'voucherNumberTastics': numberTasticsId})
        vouchers = self.env['accountcore.voucher'].sudo().browse(
            args['active_ids'])
        vouchers.sorted(key=lambda r: r.sequence)
        if startNumber <= 0:
            startNumber = 1
        for voucher in vouchers:
            oldstr = voucher.numberTasticsContainer_str
            voucher.numberTasticsContainer_str = Voucher.getNewNumberDict(
                oldstr,
                numberTasticsId,
                startNumber)
            startNumber += 1
        return {'name': '已生成凭证策略号',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'accountcore.voucher',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in',  args['active_ids'])]
                }
# 设置凭证号向导


class SetingVNumberWizard(models.TransientModel):
    '''设置凭证号向导'''
    _name = 'accountcore.seting_v_number'
    _description = '设置凭证号向导'
    startNumber = fields.Integer(string='从此编号开始', default=1, required=True)
    @ACTools.refuse_role_search
    def setingNumber(self):
        args = self.env.context
        startNumber = self.startNumber
        vouchers = self.env['accountcore.voucher'].sudo().browse(
            args['active_ids'])
        vouchers.sorted(key=lambda r: r.voucherdate)
        if startNumber <= 0:
            startNumber = 1
        for voucher in vouchers:
            voucher.v_number = startNumber
            startNumber += 1
        return {'name': '已生成凭证号',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'accountcore.voucher',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in',  args['active_ids'])]
                }
# 设置单张凭证编号向导


class SetingVoucherNumberSingleWizard(models.TransientModel):
    '''设置单张凭证策略号向导'''
    _name = 'accountcore.seting_voucher_number_single'
    _description = '设置单张凭证策略号向导'
    voucherNumberTastics = fields.Many2one('accountcore.voucher_number_tastics',
                                           '要使用的凭证编码策略',
                                           required=True)
    newNumber = fields.Integer(string='新凭证策略号', required=True)
    @api.model
    def default_get(self, field_names):
        '''获得用户的默认凭证编号策略'''
        default = super().default_get(field_names)
        if self.env.user.voucherNumberTastics:
            default['voucherNumberTastics'] = self.env.user.voucherNumberTastics.id
        return default
    @ACTools.refuse_role_search
    def setVoucherNumberSingle(self):
        '''设置修改凭证策略号'''
        argsDist = self.env.context
        newNumber = self.newNumber
        if newNumber < 0:
            newNumber = 0
        newTasticsId = self.voucherNumberTastics.id
        currentUserId = self.env.uid
        currentUser = self.env['res.users'].sudo().browse(currentUserId)
        currentUser.write(
            {'voucherNumberTastics': newTasticsId})
        voucher = self.env['accountcore.voucher'].sudo().browse(
            argsDist['active_id'])
        voucher.numberTasticsContainer_str = Voucher.getNewNumberDict(
            voucher.numberTasticsContainer_str,
            newTasticsId,
            newNumber)
        return True
# 设置单张凭证编号向导


class SetingVNumberSingleWizard(models.TransientModel):
    '''设置单张凭证号向导'''
    _name = 'accountcore.seting_v_number_single'
    _description = '设置单张凭证号向导'
    newNumber = fields.Integer(string='新凭证号', required=True)
    @ACTools.refuse_role_search
    def setVoucherNumberSingle(self):
        '''设置修改凭证号'''
        argsDist = self.env.context
        voucher = self.env['accountcore.voucher'].sudo().browse(
            argsDist['active_id'])
        if self.newNumber < 0:
            voucher.v_number = 0
        else:
            voucher.v_number = self.newNumber
        return True
# 科目余额查询向导


class GetAccountsBalance(models.TransientModel):
    '''科目余额查询向导'''
    _name = 'accountcore.get_account_balance'
    _description = '科目查询向导'
    startDate = fields.Date(string="开始期间")
    endDate = fields.Date(string="结束期间")
    fast_period = fields.Date(string="选取期间", store=False)
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
    sum_orgs = fields.Boolean(
        string='多机构合并显示', default=False)
    orgs = fields.Many2many(
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
        if len(self.orgs) == 0:
            raise exceptions.ValidationError('你还没选择机构范围！')
            return False
        if len(self.account) == 0:
            self.account = self.env['accountcore.account'].search([])
            # raise exceptions.ValidationError('你需要选择查询的科目范围！')
            # return False
        self._setDefaultDate()
        [data] = self.read()
        startDate = data['startDate']
        start_year = startDate.year
        start_month = startDate.month
        period = self._periodIsBeforBeging(
            start_year, start_month, data['orgs'],  data['account'])
        if period:
            raise exceptions.ValidationError(
                "查询范围内有科目的启用期间晚于查询的开始期间" + str(start_year) + "-"+str(start_month) + ", \
                查询的开始期间不能大于启用期间,当前选择的机构和科目范围的最早启用期间为"+period+"请选择该期间为查询的开始期间")
        datas = {
            'form': data
        }
        return self.env.ref('accountcore.accounctore_accountsbalance_report').report_action([], data=datas)

    def _setDefaultDate(self):
        if not self.startDate:
            self.startDate = '1900-01-01'
        if not self.endDate:
            self.endDate = '2219-12-31'
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')

    def _periodIsBeforBeging(self, start_year, start_month, org_ids, account_ids):
        '''检查查询期间是否早于启用期间'''
        domain = [('isbegining', '=', True),
                  ('org', 'in', org_ids),
                  ('account', 'in', account_ids), '|', '&',
                  ('year', '=', start_year),
                  ('month', '>', start_month),
                  ('year', '>', start_year)]
        records = self.env['accountcore.accounts_balance'].sudo().search(
            domain)
        if records.exists():
            records_sorted = records.sorted(key=lambda r: r.year+r.month*12)
            period_str = str(records_sorted[-1].year) + \
                "-"+str(records_sorted[-1].month)
            return period_str
        return False
# 科目明细账查询向导


class GetSubsidiaryBook(models.TransientModel):
    "科目明细账查询向导"
    _name = 'accountcore.get_subsidiary_book'
    _description = '科目明细账查询向导'
    startDate = fields.Date(string='开始月份')
    endDate = fields.Date(string='结束月份')
    fast_period = fields.Date(string="选取期间", store=False)
    orgs = fields.Many2many('accountcore.org',
                            string='机构范围',
                            default=lambda s: s.env.user.currentOrg,
                            required=True)
    account = fields.Many2many(
        'accountcore.account', string='查询的科目', required=True)
    only_this_level = fields.Boolean(string='只包含本级科目', default=False)
    item = fields.Many2one('accountcore.item', string='查询的核算项目')

    @api.multi
    def getReport(self, *args):
        self.ensure_one()
        if len(self.orgs) == 0:
            raise exceptions.ValidationError('你还没选择机构范围！')
        if not self.account:
            raise exceptions.ValidationError('你需要选择查询的科目！')
        self._setDefaultDate()
        [data] = self.read()
        datas = {
            'form': data
        }
        return self.env.ref('accountcore.subsidiarybook_report').report_action([], data=datas)

    def _setDefaultDate(self):
        if not self.startDate:
            self.startDate = '1900-01-01'
        if not self.endDate:
            self.endDate = '2219-12-31'
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
# 自动结转损益向导


class currencyDown_sunyi(models.TransientModel):
    "自动结转损益向导"
    _name = 'accountcore.currency_down_sunyi'
    _description = '自动结转损益向导'
    startDate = fields.Date(string='开始月份', required=True)
    endDate = fields.Date(string='结束月份', required=True)
    fast_period = fields.Date(string="选取期间", store=False)
    orgs = fields.Many2many(
        'accountcore.org',
        string='机构范围',
        default=lambda s: s.env.user.currentOrg, required=True)
    # def soucre(self):
    #     return self.env.ref('rulebook_1')
    @ACTools.refuse_role_search
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
        if self.ben_nian_li_run_account:
            self.ben_nian_li_run_account_id = self.ben_nian_li_run_account.id
        else:
            self.ben_nian_li_run_account_id = self.env.ref(
                'special_accounts_1')
        # 损益调整科目
        self.sun_yi_tiao_zhen_account = self.env['accountcore.special_accounts'].sudo().search([
            ('name', '=', '以前年度损益调整科目')]).accounts
        if self.sun_yi_tiao_zhen_account:
            self.sun_yi_tiao_zhen_account_id = self.sun_yi_tiao_zhen_account.id
        else:
            self.sun_yi_tiao_zhen_account_id = self.env.ref(
                'special_accounts_3')
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
                'domain': [('id', 'in', voucher_ids)]
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
                                                                   #    self.sun_yi_tiao_zhen_account.id),
                                                                   self.sun_yi_tiao_zhen_account_id),
                                                                  '|', ('org',
                                                                        '=', org.id),
                                                                  ('org', '=', False)])
        return accounts

    def _get_balances(self, org, vouhcer_period, accounts):
        '''获得某一机构在一个会计月份的余额记录'''
        accountsBalance = []
        for account in accounts:
            if not account.accountItemClass:
                balance = account.getBalanceOfVoucherPeriod(vouhcer_period,
                                                            org,
                                                            None)
                if balance:
                    accountsBalance.append(balance)
            else:
                items = account.getAllItemsInBalancesOf(org)
                if items:
                    for item in items:
                        balance = account.getBalanceOfVoucherPeriod(vouhcer_period,
                                                                    org,
                                                                    item)
                        if balance:
                            accountsBalance.append(balance)
        return accountsBalance

    def _creat_voucher(self, accountsBalance, org, voucer_period):
        '''新增结转损益凭证'''
        # 结转到本年利润的借方合计
        zero = Decimal.from_float(0).quantize(Decimal('0.00'))
        sum_d = Decimal.from_float(0).quantize(Decimal('0.00'))
        # 结转到本年利润的贷方合计
        sum_c = Decimal.from_float(0).quantize(Decimal('0.00'))
        entrys_value = []
        # 根据科目余额生成分录
        for b in accountsBalance:
            b_items_id = []
            if b.items.id:
                b_items_id = [b.items.id]
            endAmount = Decimal.from_float(b.endDamount).quantize(
                Decimal('0.00'))-Decimal.from_float(b.endCamount).quantize(Decimal('0.00'))
            if b.account.direction == '1':
                if endAmount != zero:
                    entrys_value.append({"explain": '结转损益',
                                         "account": b.account.id,
                                         "items": [(6, 0, b_items_id)],
                                         "camount": endAmount
                                         })
                    sum_d = sum_d + endAmount
            else:
                if endAmount != zero:
                    entrys_value.append({"explain": '结转损益',
                                         "account": b.account.id,
                                         "items": [(6, 0, b_items_id)],
                                         "damount": -endAmount
                                         })
                    sum_c = sum_c - endAmount
        # 本年利润科目分录
        # 结转到贷方
        if sum_d != zero:
            entrys_value.append({"explain": '结转损益',
                                 #  "account": self.ben_nian_li_run_account.id,
                                 "account": self.ben_nian_li_run_account_id,
                                 "damount": sum_d
                                 })
        # 结转到借方
        if sum_c != zero:
            entrys_value.append({"explain": '结转损益',
                                 #  "account": self.ben_nian_li_run_account.id,
                                 "account": self.ben_nian_li_run_account_id,
                                 "camount": sum_c
                                 })
        if len(entrys_value) < 2:
            return None
        entrys = self.t_entry.sudo().create(entrys_value)
        voucher = self.env['accountcore.voucher'].sudo().create({
            'voucherdate': voucer_period.endDate,
            'org': org.id,
            'soucre': self.env.ref('accountcore.source_2').id,
            'ruleBook': [(6, 0, [self.env.ref('accountcore.rulebook_1').id])],
            'entrys': [(6, 0, entrys.ids)],
            'createUser': self.env.uid,
        })
        return voucher
# 启用期初试算平衡向导


class BeginBalanceCheck(models.TransientModel):
    '''启用期初试算平衡向导'''
    _name = 'accountcore.begin_balance_check'
    _description = '启用期初试算平衡向导'
    org_ids = fields.Many2many('accountcore.org',
                               string='待检查机构',
                               required=True,
                               default=lambda s: s.env.user.currentOrg)
    result = fields.Html(string='检查结果')
    @api.multi
    def do_check(self, *args):
        '''对选中机构执行平衡检查'''
        self.ensure_one()
        check_result = {}
        result_htmlStr = ''
        for org in self.org_ids:
            check_result[org.name] = self._check(org)
        for (key, value) in check_result.items():
            result_htmlStr = result_htmlStr+"<h6>" + \
                key+"</h6>"+"".join([v[1] for v in value])
        self.result = result_htmlStr
        return {
            'name': '启用期初平衡检查',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'accountcore.begin_balance_check',
            'res_id': self.id,
        }

    def _check(self, org):
        '''对一个机构执行平衡检查'''
        rl = []
        # 获得机构期初
        balance_records = AccountsBalance.getBeginOfOrg(org)
        # 检查月初本年累计发生额借方合计=贷方合计
        rl.append(self._checkCumulativeAmountBalance(balance_records))
        # 检查月初余额借方合计=贷方合计
        rl.append(self._checkBeginingAmountBalance(balance_records))
        # 检查月已发生额借方合计=贷方合计
        rl.append(self._checkAmountBalance(balance_records))
        # 检查资产=负债+所有者权益+收入-理论
        rl.append(self._checkBalance(balance_records))
        return rl

    def _checkCumulativeAmountBalance(self, balance_records):
        '''检查月初本年累计发生额借方合计'''
        damount = AccountsBalance._sumFieldOf(
            'cumulativeDamount', balance_records)
        camount = AccountsBalance._sumFieldOf(
            'cumulativeCamount', balance_records)
        imbalanceAmount = damount-camount
        if imbalanceAmount == 0:
            rl_html = "<div><span class='text-success fa fa-check'></span>月初本年借方累计发生额=月初本年贷方累计发生额【" + \
                str(damount) + "="+str(camount)+"】</div>"
            return (True, rl_html)
        else:
            rl_html = "<div><span class='text-danger fa fa-close'></span>月初本年借方累计发生额合计=月初本年贷方累计发生额合计【" + \
                str(damount)+"-" + str(camount) + \
                "="+str(imbalanceAmount)+"】</div>"
            return (False, rl_html)

    def _checkBeginingAmountBalance(self, balance_records):
        '''检查月初余额借方合计'''
        damount = AccountsBalance._sumFieldOf('beginingDamount',
                                              balance_records)
        camount = AccountsBalance._sumFieldOf('beginingCamount',
                                              balance_records)
        imbalanceAmount = damount-camount
        if imbalanceAmount == 0:
            rl_html = "<div><span class='text-success fa fa-check'></span>月初借方余额合计=月初贷方贷方余额合计【" + \
                str(damount) + "=" + str(camount) + "】</div>"
            return (True, rl_html)
        else:
            rl_html = "<div><span class='text-danger fa fa-close'></span>月初借方余额合计=月初贷方余额合计【" +  \
                str(damount) + "-" + str(camount) + \
                "="+str(imbalanceAmount)+"】</div>"
            return (False, rl_html)

    def _checkAmountBalance(self, balance_records):
        '''检查月已发生额借方合计'''
        damount = AccountsBalance._sumFieldOf('damount',
                                              balance_records)
        camount = AccountsBalance._sumFieldOf('camount',
                                              balance_records)
        imbalanceAmount = damount-camount
        if imbalanceAmount == 0:
            rl_html = "<div><span class='text-success fa fa-check'></span>月借方已发生额合计=月贷方已发生额合计【" + \
                str(damount) + "=" + str(camount) + "】</div>"
            return (True, rl_html)
        else:
            rl_html = "<div><span class='text-danger fa fa-exclamation'></span>月借方已发生额合计=月贷方已发生额合计【" + \
                str(damount) + "-" + str(camount) + \
                "="+str(imbalanceAmount)+"】</div>"
            return (False, rl_html)

    def _checkBalance(self, balance_records):
        '''检查资产=负债+所有者权益+收入-成本'''
        return (True, ".....")
# 新增下级现金流量向导


class CreateChildCashoFlowWizard(models.TransientModel, Glob_tag_Model):
    '''新增下级现金流量的向导'''
    _name = 'accountcore.create_child_cashflow'
    _description = '新增下级现金流量向导'
    parent_id = fields.Many2one('accountcore.cashflow',
                                string='上级现金流量名称',
                                help='新增现金流量的直接上级科目')
    parent_number = fields.Char(related='parent_id.number',
                                string='上级现金流量编码')
    cashFlowType = fields.Many2one('accountcore.cashflowtype',
                                     string='现金流量类别',
                                     index=True,
                                     ondelete='restrict')
    number = fields.Char(string='现金流量编码', required=True)
    name = fields.Char(string='现金流量名称', required=True)
    direction = fields.Selection(
        [("-1", "流出"), ("1", "流入")], string='流量方向', required=True)
    sequence = fields.Integer(string="显示优先级", help="显示顺序", default=100)
    @api.model
    def default_get(self, field_names):
        default = super().default_get(field_names)
        parent_id = self.env.context.get('active_id')
        parent = self.env['accountcore.cashflow'].sudo().search(
            [['id', '=', parent_id]])
        default['parent_id'] = parent_id
        default['cashFlowType'] = parent.cashFlowType.id
        default['direction'] = parent.direction
        default['number'] = parent.number + \
            '.' + str(parent.currentChildNumber)
        return default
    @api.model
    def create(self, values):
        if self.env.user.current_date:
            voucher_date = self.env.user.current_date
        parent_id = self.env.context.get('active_id')
        Table = self.env['accountcore.cashflow'].sudo()
        parent = Table.search(
            [['id', '=', parent_id]])
        newOne = {'parent_id': parent_id,
                  'cashFlowType': parent.cashFlowType.id,
                  'name':  parent.name+'---'+values['name'],
                  'number': parent.number + '.'
                  + str(parent.currentChildNumber),
                  'direction': parent.direction}
        parent.currentChildNumber = parent.currentChildNumber+1
        values.update(newOne)
        rl = super(CreateChildCashoFlowWizard, self).create(values)
        a = Table.create(values)
        # 添加到上级科目的直接下级
        parent.write({'childs_ids': [(4, a.id)]})
        return rl
        # 向导部分-结束
# 报表生成向导


class GetReport(models.TransientModel):
    "报表生成向导"
    _name = 'accountcore.get_report'
    _description = '报表生成向导'
    report_model = fields.Many2one('accountcore.report_model',
                                   string='报表模板')
    guid = fields.Char(related='report_model.guid')
    summary = fields.Text(related='report_model.summary')
    startDate = fields.Date(string='开始月份',
                            required=True,
                            default=lambda s: s.env.user.current_date)
    endDate = fields.Date(string='结束月份',
                          required=True,
                          default=lambda s: s.env.user.current_date)
    fast_period = fields.Date(string="选取期间", store=False)
    orgs = fields.Many2many('accountcore.org',
                            string='机构范围',
                            default=lambda s: s.env.user.currentOrg,
                            required=True)
    
    def do(self):
        '''根据模板生成报表'''
        report = self.env['accountcore.report_model'].sudo().browse(
            self.report_model.id)
        report[0].startDate = self.startDate
        report[0].endDate = self.endDate
        report[0].orgs = self.orgs
        return {
            'name': "生成报表",
            'type': 'ir.actions.act_window',
            'res_model': 'accountcore.report_model',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'main',
            'res_id': self.report_model.id,
            'context': {
                'form_view_initial_mode': 'edit',
            }
        }
# 设置报表模板公式向导


class ReportModelFormula(models.TransientModel):
    '''设置报表公式向导'''
    _name = 'accountcore.reportmodel_formula'
    _description = '设置报表公式向导'
    account_id = fields.Many2one('accountcore.account', string='会计科目')
    has_child = fields.Boolean(string='是否包含明细科目', default=True)
    item_ids = fields.Many2many('accountcore.item', string='作为明细科目的核算项目')
    account_amount_type = fields.Many2one('accountcore.account_amount_type',
                                          string='金额类型')
    formula = fields.Text(string='公式内容')
    btn_join_reduce = fields.Char()
    btn_join_add = fields.Char()
    btn_clear = fields.Char()
    btn_show_orgs = fields.Char(store=False)
    btn_start_date = fields.Char(store=False)
    btn_end_date = fields.Char(store=False)
    btn_between_date = fields.Char(store=False)
    @api.model
    def default_get(self, field_names):
        default = super().default_get(field_names)
        if self.env.context.get('ac'):
            default['formula'] = self.env.context.get('ac')
        return default
    @ACTools.refuse_role_search
    def do(self):
        '''公式填入单元格'''
        return {
            'type': 'ir.actions.client',
            'name': '',
            'tag': 'update_formula',
            'target': 'new',
            'context': {'ac_formula': self.formula}
        }

    @api.onchange('btn_join_reduce')
    def join_reduce(self):
        '''减进公式'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_join_reduce:
            return
        if not self.account_id.name:
            return {
                'warning': {
                    'message': "请选择会计科目",
                },
            }
        if not self.account_amount_type:
            return {
                'warning': {
                    'message': "请选择金额类型",
                },
            }
        items = ''
        for i in self.item_ids:
            items = items+i.name+'/'
        mark = "-"
        if not self.formula:
            self.formula = ""
        self.formula = (self.formula+mark+"account('"
                        + self.account_id.name
                        + "','"+str(self.has_child)
                        + "','"+self.account_amount_type.name
                        + "','"+items
                        + "')")

    @api.onchange('btn_join_add')
    def join_add(self):
        '''加进公式'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_join_add:
            return
        if not self.account_id.name:
            return {
                'warning': {
                    'message': "请选择会计科目",
                },
            }
        if not self.account_amount_type:
            return {
                'warning': {
                    'message': "请选择金额类型",
                },
            }
        items = ''
        for i in self.item_ids:
            items = items+i.name+'/'
        mark = ""
        if self.formula:
            mark = "+"
        else:
            self.formula = ""
        self.formula = (self.formula+mark+"account('"
                        + self.account_id.name
                        + "','"+str(self.has_child)
                        + "','"+self.account_amount_type.name
                        + "','"+items
                        + "')")

    @api.onchange('btn_clear')
    def join_clear(self):
        '''清除公式'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_clear:
            return
        self.formula = ""

    @api.onchange('btn_show_orgs')
    def join_show_orgs(self):
        '''填入取机构名称的公式'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_show_orgs:
            return
        self.formula = "show_orgs()"

    @api.onchange('btn_start_date')
    def join_start_date(self):
        '''填入取数的开始日期'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_start_date:
            return
        self.formula = "startDate()"

    @api.onchange('btn_end_date')
    def join_end_date(self):
        '''填入取数的结束日期'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_end_date:
            return
        self.formula = "endDate()"

    @api.onchange('btn_between_date')
    def join_between_date(self):
        '''填入取数的期间'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_between_date:
            return
        self.formula = "betweenDate()"


class StoreReport(models.TransientModel):
    '''报表归档向导'''
    _name = 'accountcore.store_report'
    _description = '报表归档向导'
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
    receivers = fields.Many2many('accountcore.receiver', string='接收者(报送对象)')
    summary = fields.Text(string='归档报表说明')
    htmlstr = fields.Html(string='html内容')
    @ACTools.refuse_role_search
    def do(self):
        reportModelId = self._context["model_id"]
        reportModel = self.env['accountcore.report_model'].sudo().browse([
            reportModelId])[0]
        orgIds = [org.id for org in reportModel.orgs]
        receiversIds = [r.id for r in self.receivers]
        self.env['accountcore.storage_report'].sudo().create([{
            "report_type": reportModel.report_type.id,
            "receivers":  [(6, 0, receiversIds)],
            "endDate": reportModel.endDate,
            "startDate": reportModel.startDate,
            "summary": self.summary,
            "data": reportModel.data,
            "data_style":reportModel.data_style,
            "width_info":reportModel.width_info,
            "height_info":reportModel.height_info,
            "header_info":reportModel.header_info,
            "comments_info":reportModel.comments_info,
            "merge_info":reportModel.merge_info,
            "meta_info":reportModel.meta_info,
            "number": self.number,
            "name": self.name,
            "create_user": self.env.uid,
            "orgs":  [(6, 0, orgIds)],
        }
        ])
# 设置报表现金流量公式向导


class ReportCashFlowFormula(models.TransientModel):
    '''设置报表现金流量公式向导'''
    _name = 'accountcore.report_cashflow_formula'
    _description = '设置报表现金流量公式向导'
    cashflow_id = fields.Many2one('accountcore.cashflow', string='现金流量项目')
    has_child = fields.Boolean(string='是否包含明细', default=True)
    formula = fields.Text(string='公式内容')
    btn_join_reduce = fields.Char()
    btn_join_add = fields.Char()
    btn_clear = fields.Char()
    btn_show_orgs = fields.Char(store=False)
    btn_start_date = fields.Char(store=False)
    btn_end_date = fields.Char(store=False)
    btn_between_date = fields.Char(store=False)
    @api.model
    def default_get(self, field_names):
        default = super().default_get(field_names)
        if self.env.context.get('ac'):
            default['formula'] = self.env.context.get('ac')
        return default
    @ACTools.refuse_role_search
    def do(self):
        '''公式填入单元格'''
        return {
            'type': 'ir.actions.client',
            'name': '',
            'tag': 'update_formula',
            'target': 'new',
            'context': {'ac_formula': self.formula}
        }
    
    @api.onchange('btn_join_reduce')
    def join_reduce(self):
        '''减进公式'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_join_reduce:
            return
        if not self.cashflow_id.name:
            return {
                'warning': {
                    'message': "请选择现金流量项目",
                },
            }
        mark = "-"
        if not self.formula:
            self.formula = ""
        self.formula = (self.formula+mark+"cashflow('"
                        + self.cashflow_id.name
                        + "','"+str(self.has_child)
                        + "')")

    @api.onchange('btn_join_add')
    def join_add(self):
        '''加进公式'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_join_add:
            return
        if not self.cashflow_id.name:
            return {
                'warning': {
                    'message': "请选择现金流量项目",
                },
            }
        mark = ""
        if self.formula:
            mark = "+"
        else:
            self.formula = ""
        self.formula = (self.formula+mark+"cashflow('"
                        + self.cashflow_id.name
                        + "','"+str(self.has_child)
                        + "')")

    @api.onchange('btn_clear')
    def join_clear(self):
        '''清除公式'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_clear:
            return
        self.formula = ""

    @api.onchange('btn_show_orgs')
    def join_show_orgs(self):
        '''填入取机构名称的公式'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_show_orgs:
            return
        self.formula = "show_orgs()"

    @api.onchange('btn_start_date')
    def join_start_date(self):
        '''填入取数的开始日期'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_start_date:
            return
        self.formula = "startDate()"

    @api.onchange('btn_end_date')
    def join_end_date(self):
        '''填入取数的结束日期'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_end_date:
            return
        self.formula = "endDate()"

    @api.onchange('btn_between_date')
    def join_between_date(self):
        '''填入取数的期间'''
        # 窗口弹出时不执行，直接返回
        if not self.btn_between_date:
            return
        self.formula = "betweenDate()"
