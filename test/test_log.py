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
        log = LogWrite()
        log.log(1, 2, 3, 4, 5)
        log.log(1, 2, 3, 4, 5)
