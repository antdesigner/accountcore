# -*- coding: utf-8 -*-

import datetime
from decimal import Decimal
import random
from . import controllers
from odoo import fields, api, SUPERUSER_ID
from . import models
from . import wizard
from . import report

# 核算项目类别ID开始
# 往来项目
items_wang_lai_id = 0
# 员工项目
items_yuan_gong_id = 0
# 部门
items_bu_men_id = 0
# 成本费用
items_cheng_ben_fei_yong_id = 0
# 原材料
items_yuan_cai_liao_id = 0
# 库存商品
items_ku_cun_shang_pin_id = 0
# 低值易耗品
items_di_zhi_yi_hao_id = 0
# 固定资产
items_gu_ding_zi_chan_id = 0
# 无形资产
items_wu_xing_zi_chan_id = 0
# 核算项目类别ID结束


def _load_demo(cr, registry):
    '''加载用于演示的明细科目,期初和凭证等'''
    env = api.Environment(cr, SUPERUSER_ID, {})
    # 判断是否加载了demo数据,未加载就不执行
    try:
        org = env.ref('accountcore.org_2')
        if org.name != '法派(北京)有限公司':
            return
    except:
        return

        # 核算项目类别ID-开始
    global items_wang_lai_id
    global items_yuan_gong_id
    global items_bu_men_id
    global items_cheng_ben_fei_yong_id
    global items_yuan_cai_liao_id
    global items_ku_cun_shang_pin_id
    global items_di_zhi_yi_hao_id
    global items_gu_ding_zi_chan_id
    global items_wu_xing_zi_chan_id
    items_wang_lai_id = env.ref('accountcore.item_class_1').id
    items_yuan_gong_id = env.ref('accountcore.item_class_2').id
    items_bu_men_id = env.ref('accountcore.item_class_3').id
    items_cheng_ben_fei_yong_id = env.ref('accountcore.item_class_4').id
    items_yuan_cai_liao_id = env.ref('accountcore.item_class_5').id
    items_ku_cun_shang_pin_id = env.ref('accountcore.item_class_6').id
    items_di_zhi_yi_hao_id = env.ref('accountcore.item_class_7').id
    items_gu_ding_zi_chan_id = env.ref('accountcore.item_class_8').id
    items_wu_xing_zi_chan_id = env.ref('accountcore.item_class_9').id
    # 核算项目类别ID-结束

    # 添加明细科目和科目关联的核算项目
    add_accounts(env)
    # 添加启用期初
    add_qichus(env)
    t_voucher = env['accountcore.voucher']
    # 添加凭证
    add_vouchers(t_voucher)


def add_accounts(env):
    '''添加明细科目'''

    # 科目表
    t_account = env['accountcore.account'].sudo()

    # 添加明细科目和核算项目-开始
    # 库存现金的明细科目
    father = env.ref('accountcore.account_1')
    add_account(t_account, father, '办公室库存现金')
    add_account(t_account, father, '项目点库存现金')
    # 银行存款的明细科目
    father = env.ref('accountcore.account_2')
    add_account(t_account, father, '工商银行4567')
    add_account(t_account, father, '工商银行7851')
    add_account(t_account, father, '民生银行7529')
    add_account(t_account, father, '重庆银行4577')
    add_account(t_account, father, '重庆银行5878')
    add_account(t_account, father, '北京银行7409')
    add_account(t_account, father, '招商银行8867')
    add_account(t_account, father, '招商银行5851')
    add_account(t_account, father, '渣打银行8879')
    # 应收账款添加往来核算项目类别
    account = env.ref('accountcore.account_12')
    add_items(account, [items_wang_lai_id], items_wang_lai_id)
    add_account(t_account, account, '内部交易', itemClasses_ids=[
        items_wang_lai_id], accountItemClass_id=items_wang_lai_id)

    # 预付账款
    father = env.ref('accountcore.account_13')
    add_account(t_account, father, '货款', itemClasses_ids=[
        items_wang_lai_id], accountItemClass_id=items_wang_lai_id)
    # 其他应收款
    father = env.ref('accountcore.account_21')
    add_account(t_account, father, '货款', itemClasses_ids=[
        items_wang_lai_id], accountItemClass_id=items_wang_lai_id)
    add_account(t_account, father, '员工借款', itemClasses_ids=[
        items_yuan_gong_id], accountItemClass_id=items_yuan_gong_id)
    add_account(t_account, father, '押金', itemClasses_ids=[
        items_yuan_gong_id], accountItemClass_id=items_yuan_gong_id)

    # 原材料
    account = env.ref('accountcore.account_30')
    add_items(account, [items_yuan_cai_liao_id], items_yuan_cai_liao_id)

    # 库存商品
    father = env.ref('accountcore.account_32')
    add_account(t_account, father, '完工产品', itemClasses_ids=[
        items_ku_cun_shang_pin_id], accountItemClass_id=items_ku_cun_shang_pin_id)
    add_account(t_account, father, '外购产品', itemClasses_ids=[
        items_ku_cun_shang_pin_id], accountItemClass_id=items_ku_cun_shang_pin_id)
    add_account(t_account, father, '半成品', itemClasses_ids=[
        items_ku_cun_shang_pin_id], accountItemClass_id=items_ku_cun_shang_pin_id)

    # 低值易耗品
    account = env.ref('accountcore.account_36')
    add_items(account, [items_di_zhi_yi_hao_id], items_di_zhi_yi_hao_id)

    # 固定资产
    account = env.ref('accountcore.account_54')
    add_items(account, [items_gu_ding_zi_chan_id], items_gu_ding_zi_chan_id)

    # 累计折旧
    account = env.ref('accountcore.account_55')
    add_items(account, [items_gu_ding_zi_chan_id], items_gu_ding_zi_chan_id)

    # 无形资产
    account = env.ref('accountcore.account_67')
    add_items(account, [items_wu_xing_zi_chan_id], items_wu_xing_zi_chan_id)

    # 累计摊销
    account = env.ref('accountcore.account_68')
    add_items(account, [items_wu_xing_zi_chan_id], items_wu_xing_zi_chan_id)

    # 无形资产减值准备

    account = env.ref('accountcore.account_69')
    add_items(account, [items_wu_xing_zi_chan_id], items_wu_xing_zi_chan_id)

    # 应付账款
    account = env.ref('accountcore.account_84')
    add_items(account, [items_wang_lai_id], items_wang_lai_id)
    add_account(t_account, account, '内部交易', itemClasses_ids=[
        items_wang_lai_id], accountItemClass_id=items_wang_lai_id)

    # 预收账款
    father = env.ref('accountcore.account_85')
    add_account(t_account, father, '客户', itemClasses_ids=[
        items_wang_lai_id], accountItemClass_id=items_wang_lai_id)
    add_account(t_account, father, '特殊订单', itemClasses_ids=[
        items_wang_lai_id], accountItemClass_id=items_wang_lai_id)
    add_account(t_account, father, '微信充值余额')
    add_account(t_account, father, '店铺')

    # 应付职工薪酬
    father = env.ref('accountcore.account_86')
    add_account(t_account, father, '工资')
    add_account(t_account, father, '社会保险')
    add_account(t_account, father, '工会经费')
    add_account(t_account, father, '辞退福利')
    add_account(t_account, father, '奖金')
    add_account(t_account, father, '职工福利费')

    # 应交税金
    father = env.ref('accountcore.account_87')
    tax_zheng_zhi = add_account(t_account, father, '应交增值税')
    add_account(t_account, tax_zheng_zhi, '进项')
    add_account(t_account, tax_zheng_zhi, '销项')
    add_account(t_account, tax_zheng_zhi, '已交税金')
    add_account(t_account, tax_zheng_zhi, '转出未交增值税')
    add_account(t_account, tax_zheng_zhi, '减免税款')
    add_account(t_account, tax_zheng_zhi, '进项税额转出')
    add_account(t_account, father, '未交增值税')
    add_account(t_account, father, '城市维护建设税')
    add_account(t_account, father, '印花税')
    add_account(t_account, father, '个人所得税')
    add_account(t_account, father, '教育费附加')

    # 其他应付款
    father = env.ref('accountcore.account_90')
    add_account(t_account, father, '股东垫付', itemClasses_ids=[
        items_yuan_gong_id], accountItemClass_id=items_yuan_gong_id)
    add_account(t_account, father, '水电费')
    add_account(t_account, father, '物业费')
    add_account(t_account, father, '租车费')
    add_account(t_account, father, '审计费')
    add_account(t_account, father, '员工费用')
    add_account(t_account, father, 'IT外包服务费')
    add_account(t_account, father, '市场营销')
    add_account(t_account, father, '维护维修费用')
    add_account(t_account, father, '个人代扣代缴社保')
    add_account(t_account, father, '票未到')
    add_account(t_account, father, '代收店铺营业款')
    add_account(t_account, father, '分公司独立核算产生资产·负债')
    add_account(t_account, father, '总部代付费用')
    add_account(t_account, father, '人力资源外包服务公司')
    add_account(t_account, father, '工会委员会')

    # 生产成本
    father = env.ref('accountcore.account_122')
    c = add_account(t_account, father, '基本生产成本')
    add_account(t_account, c, '原材料')
    add_account(t_account, c, '直接人工')
    add_account(t_account, c, '直接福利费')
    add_account(t_account, father, '辅助生产成本')

    # 制造费用
    account = env.ref('accountcore.account_123')
    add_items(account, [items_cheng_ben_fei_yong_id],
              items_cheng_ben_fei_yong_id)
    add_account(t_account, account, '结转制造费用')

    # 主营业务收入
    father = env.ref('accountcore.account_129')
    add_account(t_account, father, '工厂产品收入')
    c = add_account(t_account, father, '店铺产品收入')
    add_account(t_account, c, '食品类')
    add_account(t_account, c, '饮料类')
    c = add_account(t_account, father, '外购产品收入')
    add_account(t_account, c, '食品类')
    add_account(t_account, c, '饮料类')
    c = add_account(t_account, father, '折扣销售')
    add_account(t_account, c, '客户')
    add_account(t_account, c, '顾客')
    c = add_account(t_account, father, '内部转移收入')
    add_account(t_account, c, '门店分公司净收入')
    add_account(t_account, c, '店铺退货视同收入')
    add_account(t_account, c, '质量原因退货')
    c = add_account(t_account, father, '收入调整')
    add_account(t_account, c, '销项税')
    add_account(t_account, c, '进项税')

    # 营业外收入
    father = env.ref('accountcore.account_142')
    add_account(t_account, father, '盘盈利得')
    add_account(t_account, father, '增值税进项税额加计扣除')

    # 主营月舞成本
    father = env.ref('accountcore.account_143')
    add_account(t_account, father, '法派食品成本')
    add_account(t_account, father, '法派饮料成本')
    c = add_account(t_account, father, '外购产品成本')
    add_account(t_account, c, '食品类')
    add_account(t_account, c, '饮料类')
    add_account(t_account, father, '包装物及消耗品')
    add_account(t_account, father, '半成品成本')
    add_account(t_account, father, '成本差异')
    add_account(t_account, father, '制造费用')
    add_account(t_account, father, '法派产品成本(店铺退回)')
    add_account(t_account, father, '在途仓成本')
    add_account(t_account, father, '正常报废产品成本')
    add_account(t_account, father, '店铺产品成本')

    # 销售费用
    account = env.ref('accountcore.account_155')
    add_items(account, [items_cheng_ben_fei_yong_id],
              items_cheng_ben_fei_yong_id)

    # 管理费用
    account = env.ref('accountcore.account_156')
    add_items(account, [items_cheng_ben_fei_yong_id],
              items_cheng_ben_fei_yong_id)

    # 财务费用
    father = env.ref('accountcore.account_157')
    add_account(t_account, father, '银行手续费')
    add_account(t_account, father, '利息支出')

    # 营业外支出
    father = env.ref('accountcore.account_160')
    add_account(t_account, father, '罚款及滞纳金')
    add_account(t_account, father, '其他营业外支出')

    # 添加明细科目和核算项目-结束


def add_qichus(env):
    '''添加启用期初'''
    t_balance = env['accountcore.accounts_balance'].sudo()
    t_account = env['accountcore.account'].sudo()
    # 取安装当天为启用期初
    date = fields.Date.today()
    date_str = date.strftime('%Y-%m-%d')
    year = date.year
    month = date.month
    # 法派(北京)有限公司
    org2_id = env.ref('accountcore.org_2').id
    # 北京_华贸店
    org3_id = env.ref('accountcore.org_3').id
    # 北京_华贸店
    org4_id = env.ref('accountcore.org_4').id
    # 法派(重庆)有限公司
    org8_id = env.ref('accountcore.org_8').id
    # 法派(重庆)有限公司渝中分公司
    org13_id = env.ref('accountcore.org_13').id
    # 核算机构ids
    orgs_ids = [org2_id, org3_id, org4_id, org8_id, org13_id]

    qichus = []
    all_accounts = t_account.search([('id', '!=', 0)])
    for account in all_accounts:
        if account.accountItemClass:
            itemClassId = account.accountItemClass.id
            n = 100
            # if 往来项目类别,产生30个往来单位
            if itemClassId == items_wang_lai_id:
                n = 30
            # if 员工项目类别
            elif itemClassId == items_yuan_gong_id:
                n = 50
            item_ids = (env['accountcore.item'].sudo().search(
                [('itemClass', '=', itemClassId)], limit=n)).mapped('id')
            for org_id in orgs_ids:
                for item_id in item_ids:
                    qichus.append(buildOneBalance(
                        org_id, account, date_str, year, month, item_id))
        else:
            for org_id in orgs_ids:
                qichus.append(buildOneBalance(
                    org_id, account, date_str, year, month))

    # 添加启用期初
    for q in qichus:
        t_balance.create(q)


def add_vouchers(t_voucher):
    '''添加会计凭证'''
    # t_voucher.create({})


def add_account(t_account, father,  name, org_id=False,  itemClasses_ids=[], accountItemClass_id=False):
    '''添加一个科目'''
    account = t_account.create({'org': org_id,
                                'accountsArch': father.accountsArch.id,
                                'accountClass': father.accountClass.id,
                                'number': father.number + '.' + str(father.currentChildNumber),
                                'name': father.name+'---'+name,
                                'direction': father.direction,
                                'cashFlowControl': father.cashFlowControl,
                                'itemClasses':  [(6, 0, itemClasses_ids)],
                                'accountItemClass': accountItemClass_id,
                                'fatherAccountId': father.id,
                                })
    father.currentChildNumber = father.currentChildNumber+1
    return account


def add_items(account, itemClasses_ids=[], accountItemClass_id=False):
    '''为科目添加核算统计项目'''
    account.write({'itemClasses':  [(6, 0, itemClasses_ids)],
                   'accountItemClass': accountItemClass_id, })
    return account


def getAccounIdByNum(t_account, number):
    '''根据科目编码获得科目ID'''
    account = (t_account.sudo().search([('number', '=', number)]))[0]
    return account


def buildOneBalance(org_id, account,  date_str, year, month, item_id=False):
    '''创建一条期初'''
    if account.direction == '1':
        beginingDamount = (Decimal.from_float(int(random.random()*300)*100.01)).quantize(Decimal('0.00'))
        beginingCamount = 0
    else:
        beginingDamount = 0
        beginingCamount = (Decimal.from_float(int(random.random()*300)*100.01)).quantize(Decimal('0.00'))
    damount = (Decimal.from_float(int(random.random()*300)*10.00)).quantize(Decimal('0.00'))
    camount = (Decimal.from_float(int(random.random()*300)*10.95)).quantize(Decimal('0.00'))
    if month == 1:
        beginCumulativeDamount = 0
        beginCumulativeCamount = 0
    elif account.accountClass.name == '损益类':
        # 损益类借贷方累计发生额一般相等
        beginCumulativeDamount = (Decimal.from_float(int(random.random()*300)*120.30)).quantize(Decimal('0.00'))
        beginCumulativeCamount = beginCumulativeDamount
    else:
        beginCumulativeDamount = (Decimal.from_float(int(random.random()*300)*120.30)).quantize(Decimal('0.00'))
        beginCumulativeCamount = (Decimal.from_float(int(random.random()*300)*130.40)).quantize(Decimal('0.00'))

    b = {'org': org_id,
         'createDate': date_str,
         'year': year,
         'month': month,
         'account': account.id,
         'items': item_id,
         'beginingDamount': beginingDamount,
         'beginingCamount': beginingCamount,
         'damount': damount,
         'camount': camount,
         'beginCumulativeCamount': beginCumulativeCamount,
         'beginCumulativeDamount': beginCumulativeDamount,
         'isbegining': True},
    return b
