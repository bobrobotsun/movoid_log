#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# File          : test_log
# Author        : Sun YiFan-Movoid
# Time          : 2024/12/22 20:53
# Description   : 
"""
from movoid_log.log import LogWrite


class Test_Log:
    def test_log(self):
        log = LogWrite(roll_size=1)
        for i in range(10):
            log.log(str(i) * 1000)
