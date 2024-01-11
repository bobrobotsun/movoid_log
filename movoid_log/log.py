#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# File          : log
# Author        : Sun YiFan-Movoid
# Time          : 2024/1/11 22:52
# Description   : 
"""
import datetime
import pathlib
import re
import sys
import time
from typing import List


class LogError(Exception):
    pass


class LogElement:
    __level = [
        'DEBUG',
        'INFO',
        'WARN',
        'ERROR',
        'CRITICAL',
    ]

    def __init__(self, key: str, *args, console: bool = True, max_size=33554432):
        self.__key = str(key)
        self.__console = bool(console)
        self.__file_list = list(args)
        self.__max_size = int(max_size)
        self.init_file_list()

    def init_file_list(self):
        for index, one_file in enumerate(self.__file_list):
            temp_dict = {}
            if isinstance(one_file, str):
                file_path = pathlib.Path(one_file).resolve()
                temp_dict['dir'] = file_path.parent
                temp_dict['dir'].mkdir(parents=True, exist_ok=True)
                temp_dict['name'] = file_path.name
                temp_dict['pathlib'] = temp_dict['dir'] / (temp_dict['name'] + '.log')
                temp_dict['file'] = temp_dict['pathlib'].open(mode='a', encoding='utf8')
                self.check_new_file(temp_dict)
                self.__file_list[index] = temp_dict

    def check_new_file(self, file_dict, print_text=''):
        now_day = datetime.datetime.now().strftime("%Y%m%d")
        c_day = datetime.datetime.fromtimestamp(file_dict['pathlib'].stat().st_ctime).strftime("%Y%m%d")
        if now_day != c_day or file_dict['pathlib'].stat().st_size > self.__max_size:
            index_list = []
            for i in file_dict['dir'].glob(f"{file_dict['name']}-{c_day}-*.log"):
                re_result = re.search(f"{file_dict['name']}-{c_day}-(.*)\.log", str(i))
                try:
                    index_list.append(int(re_result.group(1)))
                except ValueError:
                    continue
            index = max(index_list) + 1
            str_index = '{:0>3d}'.format(index)
            file_name = f"{file_dict['name']}-{c_day}-{str_index}.log"
            new_file_path = file_dict['dir'] / file_name
            file_dict['file'].close()
            file_dict['pathlib'].replace(new_file_path)
            file_dict['pathlib'] = file_dict['dir'] / (file_dict['name'] + '.log')
            file_dict['file'] = file_dict['pathlib'].open(mode='a', encoding='utf8')
            file_dict['file'].write(print_text)
            file_dict['file'].flush()

    def analyse_level(self, level='INFO'):
        if isinstance(level, str) and level.upper() in self.__level:
            return level.upper()
        elif isinstance(level, int) and 0 <= level <= len(self.__level):
            return self.__level[level]
        else:
            raise LogError(f'unknown leve:<{level}>')

    def print(self, *args, level='INFO', sep=' ', end='\n'):
        time_text = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        arg_text = sep.join([str(_) for _ in args]) + end
        level_text = self.analyse_level(level)
        print_text = f"{time_text} [{level_text}] : {arg_text}"
        for file_dict in self.__file_list:
            file_dict['file'].write(print_text)
            file_dict['file'].flush()
        if self.__console:
            if self.__level.index(level_text) >= 3:
                print_file = sys.stderr
            else:
                print_file = sys.stdout
            print_file.write(print_text)
            print_file.flush()
        for file_dict in self.__file_list:
            self.check_new_file(file_dict, print_text)


class Log:
    __log = {}

    def __new__(cls, key="__default__", *args, console: bool = True, max_size=33554432) -> LogElement:
        cls.__log[key] = LogElement(key, *args, console=console, max_size=max_size)
        return cls.__log[key]

    @classmethod
    def get(cls, item, *args):
        return cls.__log.get(item, *args)


if __name__ == '__main__':
    log = Log('test', 'test/test_log', max_size=100)
    for i in range(10):
        log.print('1' * 20)
