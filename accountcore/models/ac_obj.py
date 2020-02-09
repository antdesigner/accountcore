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
      # 给定科目名称,分解出级次

    @staticmethod
    def splitAccountName(accountName):
        '''给定科目名称,分解出级次'''
        # 去掉空格
        _str = accountName.replace(" ", "")
        # 判断是否是一级科目样式
        _list = _str.split("---")
        accountNames = []
        for i in range(0, len(_list)):
            name = '---'.join(str(_list[j]) for j in range(0, i+1))
            accountNames.append(name)
        return accountNames
    # 对两个核算项目类别列表进行适配,返回需要添加的类别
    @staticmethod
    def itemClassUpdata(class_a, class_b):
        rl = []
        '''对两个核算项目类别列表进行适配,返回需要添加的类别'''
        rl = [b for b in class_b if b not in class_a]
        mast_a = [a for a in class_a if a[1]]
        mast_b = [b for b in class_b if b[1]]
        if len(mast_b) > 1:
            raise exceptions.UserError('必选项目只能有一个')
        if mast_a and not mast_b:
            raise exceptions.UserError('必须项目必须有')
        if mast_a and mast_b and mast_a[0][0] != mast_b[0][0]:
            raise exceptions.UserError(
                '必选项目类别【'+mast_b[0][0]+"】和科目的必选项目类别【"+mast_a[0][0]+"】不符")
        return rl
