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
import traceback
from functools import wraps
from typing import Dict

from movoid_timer import Timer
from movoid_timer.timer import TimerElement


class LogError(Exception):
    def __init__(self, *args, **kwargs):
        super(LogError, self).__init__(*args)
        self.args = args
        self.kwargs = kwargs


class LogElement:
    __level = [
        'DEBUG',
        'INFO',
        'WARN',
        'ERROR',
        'CRITICAL',
    ]

    def __init__(self, key: str, *args, console: bool = True, max_size=None, max_day=None, max_file=None):
        self.__key = str(key)
        self.__console = bool(console)
        self.__file_list = list(args)
        self.__max_size = 33554432 if max_size is None else int(max_size)
        self.__max_day = None if max_day is None else float(max_day)
        self.__max_file = None if max_file is None else int(max_file)
        self.__timer: Dict[str, TimerElement] = {}
        self.__timer_print = {}
        self.__init_file_list()

    def __init_file_list(self):
        for index, one_file in enumerate(self.__file_list):
            temp_dict: dict = {}
            if isinstance(one_file, str):
                file_path = pathlib.Path(one_file).resolve()
                temp_dict['dir'] = file_path.parent
                temp_dict['dir'].mkdir(parents=True, exist_ok=True)
                temp_dict['name'] = file_path.stem
                temp_dict['pathlib'] = temp_dict['dir'] / (temp_dict['name'] + '.log')
                temp_dict['pathlib'].touch()
                temp_dict['file'] = temp_dict['pathlib'].open(mode='a', encoding='utf8')
                self.__check_new_file(temp_dict)
                self.__file_list[index] = temp_dict
            elif callable(one_file):
                temp_dict['function'] = one_file

    def __check_new_file(self, file_dict):
        now_day = datetime.datetime.now().strftime("%Y%m%d")
        c_day = datetime.datetime.fromtimestamp(file_dict['pathlib'].stat().st_ctime).strftime("%Y%m%d")
        if now_day != c_day or file_dict['pathlib'].stat().st_size > self.__max_size:
            index_list = []
            for i in file_dict['dir'].glob(f"{file_dict['name']}-{c_day}-*.log"):
                re_pattern = rf"{file_dict['name']}-{c_day}-(.*)\.log"
                re_result = re.search(re_pattern, str(i))
                try:
                    index_list.append(int(re_result.group(1)))
                except ValueError:
                    continue
            index = max(index_list) + 1 if index_list else 0
            str_index = '{:0>3d}'.format(index)
            file_name = f"{file_dict['name']}-{c_day}-{str_index}.log"
            new_file_path = file_dict['dir'] / file_name
            file_dict['file'].close()
            file_dict['pathlib'].rename(new_file_path)
            file_dict['pathlib'] = file_dict['dir'] / (file_dict['name'] + '.log')
            file_dict['pathlib'].unlink(missing_ok=True)
            file_dict['file'] = file_dict['pathlib'].open(mode='w+', encoding='utf8')
            self.__check_delete_file(file_dict)

    def __check_delete_file(self, file_dict):
        now_time = time.time()
        exist_file = {}
        for i in file_dict['dir'].glob(f"{file_dict['name']}-????????-*.log"):
            file_time = i.stat().st_mtime
            if self.__max_day is not None and now_time - file_time > self.__max_day * 86400:
                i.unlink()
            else:
                exist_file[file_time] = i
        if self.__max_file is not None and len(exist_file) > self.__max_file:
            file_time_list = list(exist_file.keys())
            file_time_list.sort(reverse=True)
            for i in file_time_list[self.__max_file:]:
                exist_file[i].unlink()

    def _analyse_level(self, level='INFO'):
        if isinstance(level, str) and level.upper() in self.__level:
            return level.upper()
        elif isinstance(level, int) and 0 <= level <= len(self.__level):
            return self.__level[level]
        else:
            raise LogError(f'unknown leve:<{level}>')

    def print(self, *args, level='INFO', sep=' ', end='\n', console=None):
        console = self.__console if console is None else console
        time_text = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        arg_text = sep.join([str(_) for _ in args])
        level_text = self._analyse_level(level)
        timer_text = ''
        if self.__timer:
            timer_text = ' [' + ' | '.join([f"{_i} {self.__timer[_i].now_format(2)}" for _i in self.__timer_print]) + ']'
        print_text = f"{time_text} [{level_text}]{timer_text} : {arg_text}{end}"
        if console:
            if self.__level.index(level_text) >= 3:
                print_file = sys.stderr
            else:
                print_file = sys.stdout
            print_file.write(print_text)
            print_file.flush()
        for file_dict in self.__file_list:
            if 'file' in file_dict:
                self.__check_new_file(file_dict)
                file_dict['file'].write(print_text)
                file_dict['file'].flush()
            if 'function' in file_dict:
                file_dict['function'](print_text)
        return print_text

    def input(self, input_text):
        input_text = str(input_text)
        full_input_text = self.print(input_text, console=False).rstrip('\n')
        get_input_text = input(full_input_text)
        self.print(f'you input <{get_input_text}>')
        return get_input_text

    def debug(self, *args, console=None):
        self.print(*args, level='DEBUG', console=console)

    def warn(self, *args, console=None):
        self.print(*args, level='WARN', console=console)

    def error(self, *args, console=None, **kwargs):
        self.print(*args, level='ERROR', console=console)
        raise LogError(*args, **kwargs)

    def critical(self, *args, console=None, **kwargs):
        self.print(*args, level='CRITICAL', console=console)
        raise LogError(*args, **kwargs)

    def timer(self, key, print_it=True) -> TimerElement:
        if key not in self.__timer:
            self.__timer[key] = Timer(f'-{self.__key}-{key}')
            if print_it:
                self.__timer_print[key] = True
        return self.__timer[key]

    def timer_delete(self, key):
        self.__timer[key].delete()
        self.__timer.pop(key)
        if key in self.__timer_print:
            self.__timer_print.pop(key)

    def function_mark(self, operate_text=None, timer=None, error_traceback=True, error_raise=True, level='INFO', console=None):
        if timer is True:
            timer = operate_text
        if operate_text is not None:
            start_text = Log.mark_format['start'].format(operate_text=operate_text)
            error_text = Log.mark_format['error'].format(operate_text=operate_text)
            end_text = Log.mark_format['end'].format(operate_text=operate_text)
        else:
            error_text = ''

        def dec(func):
            @wraps(func)
            def wrapping(*args, **kwargs):
                if timer is not None:
                    self.timer(timer)
                if operate_text is not None:
                    self.print(start_text, level=level, console=console)
                try:
                    re_value = func(*args, **kwargs)
                except Exception as err:
                    traceback_text = ''
                    if error_traceback:
                        traceback_text = ':' + traceback.format_exc()
                    full_error_text = f'{error_text}{traceback_text}'
                    if full_error_text:
                        self.print(full_error_text, level='error', console=console)
                    if error_raise:
                        raise err
                else:
                    return re_value
                finally:
                    if operate_text is not None:
                        self.print(end_text, level=level, console=console)
                    if timer is not None:
                        self.timer_delete(timer)

            return wrapping

        return dec


class Log:
    __log = {}
    mark_format = {
        'start': 'start to <{operate_text}>',
        'end': 'end to <{operate_text}>',
        'error': '<{operate_text}>interrupted, something error happened',
    }

    def __new__(cls, key="__default__", *args, console: bool = True, max_size=None, max_day=None, max_file=None) -> LogElement:
        if key not in cls.__log:
            cls.__log[key] = LogElement(key, *args, console=console, max_size=max_size, max_day=max_day, max_file=max_file)
        return cls.__log[key]

    @classmethod
    def get(cls, item, *args):
        return cls.__log.get(item, *args)

    @classmethod
    def function_mark(cls, operate_text=None, timer=None, error_traceback=True, error_raise=True, level='INFO', console=None):
        if timer is True:
            timer = operate_text
        if operate_text is not None:
            start_text = cls.mark_format['start'].format(operate_text=operate_text)
            error_text = cls.mark_format['error'].format(operate_text=operate_text)
            end_text = cls.mark_format['end'].format(operate_text=operate_text)
        else:
            error_text = ''

        def dec(func):
            @wraps(func)
            def wrapping(self, *args, **kwargs):
                if timer is not None:
                    self.timer(timer)
                if operate_text is not None:
                    self.print(start_text, level=level, console=console)
                try:
                    re_value = func(self, *args, **kwargs)
                except Exception as err:
                    traceback_text = ''
                    if error_traceback:
                        traceback_text = ':' + traceback.format_exc()
                    full_error_text = f'{error_text}{traceback_text}'
                    if full_error_text:
                        self.print(full_error_text, level='error', console=console)
                    if error_raise:
                        raise err
                else:
                    return re_value
                finally:
                    if operate_text is not None:
                        self.print(end_text, level=level, console=console)
                    if timer is not None:
                        self.timer_delete(timer)

            return wrapping

        return dec


class LogSub:
    @property
    def log(self) -> LogElement:
        return Log('__default')

    @property
    def print(self):
        return self.log.print

    @property
    def input(self):
        return self.log.input

    @property
    def debug(self):
        return self.log.debug

    @property
    def warn(self):
        return self.log.warn

    @property
    def error(self):
        return self.log.error

    @property
    def critical(self):
        return self.log.critical

    @property
    def timer(self):
        return self.log.timer

    @property
    def timer_delete(self):
        return self.log.timer_delete
