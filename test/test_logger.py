#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# File          : test_logger
# Author        : Sun YiFan-Movoid
# Time          : 2024/10/20 0:13
# Description   : 
"""
import time

from movoid_log import LoggerBase


class TestLogger:
    def test_logger(self):
        class Log1(LoggerBase):
            def __init__(self):
                self.logger_init('log/test1', 1, 5, 1000, 10)

        log1 = Log1()
        for i in range(100):
            time.sleep(0.1)
            log1.print('asdf')
