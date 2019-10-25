# -*- coding: utf-8 -*-

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



