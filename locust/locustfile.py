# -*- coding: utf-8 -*-
# By mrshelly<mrshelly@hotmail.com> 2019-07

import re, random, datetime, time, json
from locust import HttpLocust, TaskSet, task

import urllib

import logging
_logger = logging.getLogger(__name__)


class UserBehavior(TaskSet):
    uid = False

    def logout(self):
        _logger.info('Logout...!')
        self.client.get("/web/session/logout")

    def login(self, user, passwd, dbname):
        _logger.info('Start login')
        self.client.get("/")
        self.client.get("/web")
        _logger.info('Select DB')
        self.client.get("/web?db="+dbname)
        resp = self.client.get("/web/login")
        crsf_token = re.compile('csrf_token: "([^\"]*)",').findall(resp.content)
        _logger.info('Login Process')
        resp = self.client.post("/web/login",{
            "csrf_token": crsf_token,
            "login": user,
            "password": passwd,
            "redirect": ""
        })
        self.client.get("/web")
        _logger.info('Login Done!')

    def create_random_accountcore_voucher(self, data=None):
        data = data or {}
        resp = self.client.post("/web/dataset/call_kw/accountcore.voucher/create", headers={"content-type": "application/json"}, json=data)
        return resp.content

    @task(2)
    def task_post_purchase_voucher_1(self):
        _logger.info('Post Voucher start')
        amount = int(random.random()*300)*100.00
        cost = round(amount * (0.3+random.random()*0.04), 2)
        _logger.info('Voucher Amount %0.2f Cost: %0.2f' % (amount, cost))

        entry_datas = [
            {
                'name': u"购买原材料",
                'date': '2019-06-24',
                'entries': [
                    (28, 'damount', False, '材料采购'),
                    (84, 'camount', False, '应付账款')],
                'org': 1},
            {
                'name': u"原材料入库",
                'date': '2019-07-04',
                'entries': [
                    (32, 'damount', False, '库存商品'),
                    (28, 'camount', False, '材料采购')],
                'org': 1},
            {
                'name': u"采购付款",
                'date': '2019-07-22',
                'entries': [
                    (84, 'damount', False, '应付账款'),
                    (2, 'camount', 7, '银行存款')],
                'org': 1},
        ]

        date0 = datetime.datetime.strptime('2019-%02d-%02d' % (range(1,13)[int(random.random()*12)], range(1,29)[int(random.random()*28)]), '%Y-%m-%d')
        date1 = date0 + datetime.timedelta(days=1+int(random.random()*5))
        date2 = date1 + datetime.timedelta(days=27+int(random.random()*5))

        entry_datas[0]['date'] = date0.strftime('%Y-%m-%d')
        entry_datas[1]['date'] = date1.strftime('%Y-%m-%d')
        entry_datas[2]['date'] = date2.strftime('%Y-%m-%d')

        # account = account_ids[int(random.random()*len(entry_datas))]
        for account in entry_datas:
            self.create_random_accountcore_voucher({
                "jsonrpc":"2.0",
                "method":"call",
                "params":{
                    "args":[{
                        "state":"creating",
                        "appendixCount":1,
                        "voucherdate": account.get('date'),
                        "org": account.get('org'),
                        "ruleBook":[[6,False,[4]]],
                        "entrys":[
                            [0,"virtual_66",{
                                "sequence": 0,
                                "explain": account.get('name'),
                                "account": account.get('entries')[0][0],
                                "damount": account.get('entries')[0][1] == 'damount' and amount or 0.0,
                                "camount": account.get('entries')[0][1] == 'camount' and amount or 0.0,
                                "items":[[6,False,[]]],
                                "cashFlow": account.get('entries')[0][2]}],
                            [0,"virtual_77",{
                                "sequence": 1,
                                "explain": account.get('name'),
                                "account": account.get('entries')[1][0],
                                "damount": account.get('entries')[1][1] == 'damount' and amount or 0.0,
                                "camount": account.get('entries')[1][1] == 'camount' and amount or 0.0,
                                "items":[[6,False,[]]],
                                "cashFlow": account.get('entries')[1][2]}]
                        ]
                    }],
                    "model":"accountcore.voucher",
                    "method":"create",
                    "kwargs":{"context":{"tz":False,"lang":"zh_CN","uid": self.uid}}},
                    "id": int(100000000*random.random())})
        _logger.info('Post Voucher Done!')


    @task(3)
    def task_post_sale_voucher_1(self):
        _logger.info('Post Voucher start')
        amount = int(random.random()*300)*100.00
        cost = round(amount * (0.3+random.random()*0.04), 2)
        _logger.info('Voucher Amount %0.2f Cost: %0.2f' % (amount, cost))

        entry_datas = [
            {
                'name': u"产品销售",
                'date': '2019-07-04',
                'entries': [
                    (12, 'damount', False, '应收账款'),
                    (129, 'camount', False, '主营收入')],
                'org': 1},
            {
                'name': u"产品出库",
                'date': '2019-07-06',
                'entries': [
                    (143, 'damount', False, '主营成本'),
                    (32, 'camount', False, '库存商品')],
                'org': 1},
            {
                'name': u"销售收款",
                'date': '2019-07-29',
                'entries': [
                    (2, 'damount', 1, '银行存款'),
                    (143, 'camount', False, '应收账款')],
                'org': 1},
        ]

        date0 = datetime.datetime.strptime('2019-%02d-%02d' % (range(1,13)[int(random.random()*12)], range(1,29)[int(random.random()*28)]), '%Y-%m-%d')
        date1 = date0 + datetime.timedelta(days=1+int(random.random()*5))
        date2 = date1 + datetime.timedelta(days=27+int(random.random()*5))

        entry_datas[0]['date'] = date0.strftime('%Y-%m-%d')
        entry_datas[1]['date'] = date1.strftime('%Y-%m-%d')
        entry_datas[2]['date'] = date2.strftime('%Y-%m-%d')

        # account = account_ids[int(random.random()*len(entry_datas))]
        for account in entry_datas:
            if account.get('entries')[0][3] == '主营成本' or account.get('entries')[1][3] == '主营成本':
                amount = cost
            self.create_random_accountcore_voucher({
                "jsonrpc":"2.0",
                "method":"call",
                "params":{
                    "args":[{
                        "state":"creating",
                        "appendixCount":1,
                        "voucherdate": account.get('date'),
                        "org": account.get('org'),
                        "ruleBook":[[6,False,[4]]],
                        "entrys":[
                            [0,"virtual_66",{
                                "sequence": 0,
                                "explain": account.get('name'),
                                "account": account.get('entries')[0][0],
                                "damount": account.get('entries')[0][1] == 'damount' and amount or 0.0,
                                "camount": account.get('entries')[0][1] == 'camount' and amount or 0.0,
                                "items":[[6,False,[]]],
                                "cashFlow": account.get('entries')[0][2]}],
                            [0,"virtual_77",{
                                "sequence": 1,
                                "explain": account.get('name'),
                                "account": account.get('entries')[1][0],
                                "damount": account.get('entries')[1][1] == 'damount' and amount or 0.0,
                                "camount": account.get('entries')[1][1] == 'camount' and amount or 0.0,
                                "items":[[6,False,[]]],
                                "cashFlow": account.get('entries')[1][2]}]
                        ]
                    }],
                    "model":"accountcore.voucher",
                    "method":"create",
                    "kwargs":{"context":{"tz":False,"lang":"zh_CN","uid": self.uid}}},
                    "id": int(100000000*random.random())})
        _logger.info('Post Voucher Done!')


    @task(15)
    def task_post_account_report_1(self):
        _logger.info('Account Report start')
        all_account = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162]
        data = {"jsonrpc":"2.0","method":"call","params":{"args":[{
            "onlyShowOneLevel":False,
            "noShowNoAmount":True,
            "no_show_no_hanppend":False,
            "noShowZeroBalance":False,
            "includeAccountItems":True,
            "org":[[6,False,[1]]],
            "order_orgs":False,
            "startDate":False,
            "endDate":False,
            "account":[[6,False, all_account]]
            }],"model":"accountcore.get_account_balance","method":"create","kwargs":{"context":{"lang":"zh_CN","uid": self.uid,"tz":False}}},"id": int(100000000*random.random())}
        _logger.info('Account Report create')
        resp = self.client.post('/web/dataset/call_kw/accountcore.get_account_balance/create', headers={"content-type": "application/json"}, json=data)
        result = json.loads(resp.content)
        report_id = result.get('result')
        _logger.info('Account Report create done, report id: %d' % report_id)
        if report_id:
            resp = self.client.post('/web/dataset/call_button', headers={"content-type": "application/json"}, json={"jsonrpc":"2.0","method":"call","params":{"args":[[report_id],{"lang":"zh_CN","uid":self.uid,"tz":False}],"method":"getReport","model":"accountcore.get_account_balance"},"id": int(100000000*random.random())})
            ret = json.loads(resp.content)
            data_form = ret.get('result').get('data')
            self.client.get('/report/html/accountcore.account_balance_report?options=%s' % urllib.quote_plus(json.dumps(data_form)))
            self.client.get('/web/webclient/qweb?mods=')
            self.client.post('/web/webclient/bootstrap_translations', headers={"content-type": "application/json"}, json={"jsonrpc":"2.0","method":"call","params":{"mods":[]},"id": int(100000000*random.random())})
        _logger.info('Account Report done!')


    def on_start(self):
        dbname = 'acntbox'
        users = [
            {'user': 'user001', 'pass': 'user001', 'uid': 7},
            {'user': 'user002', 'pass': 'user002', 'uid': 8},
            {'user': 'user003', 'pass': 'user003', 'uid': 9},
            {'user': 'user004', 'pass': 'user004', 'uid': 10},
        ]
        user = users[int(random.random()*len(users))]
        self.uid = user['uid']
        self.login(user['user'], user['pass'], dbname)

    def on_stop(self):
        self.logout()


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000
