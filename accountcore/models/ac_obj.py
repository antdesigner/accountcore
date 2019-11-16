# -*- coding: utf-8 -*-
from decimal import Decimal
from odoo.tools import pycompat
# 快速构造简单的对象


class Structure:
    _fields = []

    def __init__(self, *args, **kwargs):
        if len(args) != len(self._fields):
            raise TypeError('Excepted {} arguments'.format(len(self._fields)))
        for name, value in zip(self._fields, args):
            setattr(self, name, value)

        for name in self._fields[len(args)]:
            setattr(self, name, kwargs.pop(name))
        if kwargs:
            raise TypeError(
                'invalid arguments (s): {}'.format(','.join(kwargs)))


class ACTools():
    @staticmethod
    def TranslateToDecimal(amount):
        '''金额的float类型转换为保留两位小数的Decimal类型，用于准确计算'''
        try:
            return Decimal.from_float(amount).quantize(Decimal('0.00'))
        except TypeError:
            if isinstance(amount, Decimal):
                return amount

    @staticmethod
    def ZeroAmount():
        '''0的Decimal表示'''
        return Decimal.from_float(0).quantize(Decimal('0.00'))

    @staticmethod
    def readCsvFile(f, head):
        '''读取csv文件,返回列表'''
        lines = []
        reader = pycompat.csv_reader(f)
        if head:
            reader.__next__()
        for row in reader:
            lines.append(row)
        return lines
