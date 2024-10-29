#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# File          : test_logger
# Author        : Sun YiFan-Movoid
# Time          : 2024/10/20 0:13
# Description   : 
"""
import time

import pytest

from movoid_log import LoggerBase
from movoid_log.logger import analyse_value


class TestLogger:
    def test_logger(self):
        class Log1(LoggerBase):
            def __init__(self):
                self.logger_init('log/test1.log', 1, 5, 1000, 10)

        log1 = Log1()
        for i in range(20):
            time.sleep(0.1)
            log1.print('asdf')


class Test_function_analyse_value:
    @pytest.mark.parametrize("input_value, return_str", [
        ('123', '>123<(str)'),
        (23, '>23<(int)'),
        (6.87, '>6.87<(float)'),
        (True, '>True<(bool)'),
        (None, '>None<(NoneType)'),
        ((1, 2), '>(1, 2)<(tuple)'),
        ([0, 3], '>[0, 3]<(list)'),
        ({8}, '>{8}<(set)'),
        ({6: 66}, '>{6: 66}<(dict)'),
    ])
    def test_input_return(self, input_value, return_str):
        assert analyse_value(input_value) == return_str
