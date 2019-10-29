# -*- coding: utf-8 -*-
import calendar
import datetime


# 一到多个会计期间
class Period(object):
    '''一到多个会计期间'''

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
        self.voucherPeriods = self.getPeriodList()

    def getPeriodList(self):
        '''获得日期范围内的会计期间列表'''
        months = (self.end_year - self.start_year) * \
            12 + self.end_month - self.start_month
        month_range = ['%s-%s-%s' % (self.start_year + mon//12, mon % 12+1, 1)
                       for mon in range(self.start_month-1, self.start_month + months)]
        voucherPeriods = [VoucherPeriod(
            datetime.datetime.strptime(d, '%Y-%m-%d')) for d in month_range]
        return voucherPeriods

    @property
    def startP(self):
        '''最早的会计期间'''
        return self.voucherPeriods[0]

    @property
    def endP(self):
        '''最晚的会计期间'''
        return self.voucherPeriods[-1]
# 一个会计期间，月份


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

    def getPreP(self):
        '''上一个会计期间（月份）'''
        year = self.year
        month = self.month
        if self.month == 1:
            year -= 1
            month = 13
        date = datetime.date(year, month-1, 1)

        return VoucherPeriod(date)
