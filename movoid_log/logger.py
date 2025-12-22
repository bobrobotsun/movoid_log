#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# File          : logger
# Author        : Sun YiFan-Movoid
# Time          : 2024/10/19 21:14
# Description   : 
"""
import inspect
import logging
import math
import os
import pathlib
import re
import time
from movoid_function import wraps, analyse_args_value_from_function, STACK
from stat import ST_MTIME
from typing import Union, Dict
from logging.handlers import BaseRotatingHandler


class TimeSizeRotatingFileHandler(BaseRotatingHandler):
    def __init__(self, filename, interval: Union[str, int] = '1d', max_time=7, max_byte=0, max_file=0, encoding='utf8', delay=False, at_time=0):
        file_path = pathlib.Path(filename).with_suffix('.log')
        filename = str(file_path)
        self.base_path = pathlib.Path(file_path).resolve()
        self.base_dir = self.base_path.parent
        if not self.base_dir.exists():
            self.base_dir.mkdir(parents=True, exist_ok=True)
        if not self.base_path.exists():
            self.base_path.touch()
        super().__init__(filename=filename, mode='a', encoding=encoding, delay=delay)
        self.at_time = int(at_time)
        self.max_time = int(max_time)
        self.max_byte = int(max_byte)
        self.max_file = int(max_file)
        if isinstance(interval, str):
            interval = interval.lower()
            if interval.endswith('s'):
                self.interval = 1  # one second
                self.suffix = "%Y-%m-%d_%H-%M-%S"
                self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(\.\w+)?$"
            elif interval.endswith('m'):
                self.interval = 60  # one minute
                self.suffix = "%Y-%m-%d_%H-%M"
                self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(\.\w+)?$"
            elif interval.endswith('h'):
                self.interval = 3600  # one hour
                self.suffix = "%Y-%m-%d_%H"
                self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}(\.\w+)?$"
            elif interval.endswith('d'):
                self.interval = 86400  # one day
                self.suffix = "%Y-%m-%d"
                self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
            else:
                raise ValueError("Invalid rollover interval specified: %s" % self.interval)
            try:
                num = int(interval[:-1])
            except:
                num = 1
            self.interval *= num
        else:
            try:
                self.interval = int(interval)
                if self.interval < 60:
                    self.suffix = "%Y-%m-%d_%H-%M-%S"
                    self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(\.\w+)?$"
                elif self.interval < 3600:
                    self.suffix = "%Y-%m-%d_%H-%M"
                    self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(\.\w+)?$"
                elif self.interval < 86400:
                    self.suffix = "%Y-%m-%d_%H"
                    self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}(\.\w+)?$"
                else:
                    self.suffix = "%Y-%m-%d"
                    self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
            except:
                raise ValueError("Invalid rollover interval specified: %s" % self.interval)
        self.extMatch = re.compile(self.extMatch, re.ASCII)
        filename = self.baseFilename
        if os.path.exists(filename):
            t = os.stat(filename)[ST_MTIME]
        else:
            t = int(time.time())
        self.roll_over_at = self.calculate_roll_over(t)

    def _open(self):
        if not self.base_path.exists():
            self.base_path.touch(exist_ok=True)
        return super()._open()

    def calculate_roll_over(self, target_time):
        return (target_time + self.interval - self.at_time) // self.interval * self.interval + self.at_time

    def shouldRollover(self, record):
        if self.stream is None:
            self.stream = self._open()
        if self.max_byte > 0:
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)  # due to non-posix-compliant Windows feature
            if self.stream.tell() + len(msg) >= self.max_byte:
                return 1
        t = int(time.time())
        if t >= self.roll_over_at:
            return 1
        return 0

    def delete_files(self):
        if self.max_time > 0:
            should_delete_time = (time.time() - self.max_time * self.interval - self.at_time) // self.interval * self.interval + self.at_time
            for i in self.base_dir.glob(f'{self.base_path.stem}.*.log'):
                if os.stat(str(i))[ST_MTIME] < should_delete_time:
                    i.unlink()
        if self.max_file > 0:
            file_list = list(self.base_dir.glob(f'{self.base_path.stem}.*.log'))
            if len(file_list) >= self.max_file:
                file_sorted = sorted(file_list, key=lambda p: os.stat(str(p))[ST_MTIME], reverse=True)
                for i in file_sorted[self.max_file - 1:]:
                    i.unlink()

    def create_roll_over_file_name(self, time_tuple):
        time_str = time.strftime(self.suffix, time_tuple)
        index = len(list(self.base_dir.glob(f'{self.base_path.stem}.{time_str}.*.log')))
        while True:
            temp_file = self.base_path.with_suffix(f'.{time_str}.{index:>03d}.log')
            if temp_file.exists():
                index += 1
            else:
                break
        return str(temp_file)

    def doRollover(self) -> object:
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        current_time = int(time.time())
        t = self.roll_over_at - self.interval
        time_tuple = time.localtime(t)
        dfn = self.create_roll_over_file_name(time_tuple)
        self.rotate(self.baseFilename, dfn)
        self.delete_files()
        if not self.delay:
            self.stream = self._open()
        self.roll_over_at = self.calculate_roll_over(current_time)


class LoggerBase:
    """
    这个类是为了能直接生成logger，并生成print等函数，方便使用
    因此这个类可以用于继承
    这个类会使用_logger这个变量来作为基础logging.logger，因此需要注意不要重名
    继承该类时，需要调用logger_init这个函数。
    """
    _logger_instance: Dict[str, logging.Logger] = {}

    def logger_init(self, file_name, interval: Union[str, int] = '1d', max_time=0, max_byte=0, max_file=0, level=logging.INFO, console=logging.INFO, encoding='utf8',
                    formatter='%(asctime)s %(name)s %(filename)s [line:%(lineno)d] %(levelname)s: %(message)s'):
        """
        创建一个可以直接按照文件和日期来拆分的日志系统
        :param file_name: 文件的名称，不需要后缀
        :param interval: 保留多少天的内容。默认为0时，无论多久都不分文件
            _s：若干秒一组
            _m：若干分钟一组
            _h：若干小时一组
            _d：若干天一组
            _：若干秒
        :param max_time: 最多支持保存多少个间隔的时间。默认为0时，无论多久都不删除文件
        :param max_byte: 一个文件支持的最大大小。默认为0时，无论文件多大都不分文件
        :param max_file: 对多支持多少个log分文件。默认为0时，无论多少文件都不删除
        :param level: 日志上打印的等级
        :param console: 是否在std上打印，输入console上打印的等级
        :param encoding: 打印格式
        :param formatter: 可以输入字符串，也可以直接传入 logging.Formatter
        """
        name = pathlib.Path(file_name).stem
        if name in self._logger_instance:
            self._logger = self._logger_instance[name]
        else:
            self._logger: logging.Logger = logging.Logger(name)
            self._logger_instance[name] = self._logger
            log_format = logging.Formatter(formatter) if isinstance(formatter, str) else formatter
            time_handler = TimeSizeRotatingFileHandler(file_name, interval=interval, max_time=max_time, max_byte=max_byte, max_file=max_file, encoding=encoding)
            time_handler.setFormatter(log_format)
            time_handler.setLevel(level)
            self._logger.addHandler(time_handler)
            if console:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(log_format)
                console_handler.setLevel(console)
                self._logger.addHandler(console_handler)

    def print(self, *args, sep=' ', level: Union[str, int] = 'INFO', stacklevel=None, **kwargs):
        print_text = str(sep).join([str(_) for _ in args])
        level_int = LogLevel(level).int
        stack_level = 0 if stacklevel is None else int(stacklevel)
        frame, frame_stack_level = STACK.get_frame(stack_level + 1, with_stack_level=True)
        self._logger.log(level=level_int, msg=print_text, stacklevel=frame_stack_level, **kwargs)

    def trace(self, *args, sep=' ', **kwargs):
        stack_level = kwargs.get('_stack_level', kwargs.get('_stacklevel', kwargs.get('stack_level', kwargs.get('stacklevel', 0))))
        stack_level += 1
        self.print(*args, sep=sep, level=logging.NOTSET, stacklevel=stack_level, **kwargs)

    def debug(self, *args, sep=' ', **kwargs):
        stack_level = kwargs.get('_stack_level', kwargs.get('_stacklevel', kwargs.get('stack_level', kwargs.get('stacklevel', 0))))
        stack_level += 1
        self.print(*args, sep=sep, level=logging.DEBUG, stacklevel=stack_level, **kwargs)

    def info(self, *args, sep=' ', **kwargs):
        stack_level = kwargs.get('_stack_level', kwargs.get('_stacklevel', kwargs.get('stack_level', kwargs.get('stacklevel', 0))))
        stack_level += 1
        self.print(*args, sep=sep, level=logging.INFO, stacklevel=stack_level, **kwargs)

    def warn(self, *args, sep=' ', **kwargs):
        stack_level = kwargs.get('_stack_level', kwargs.get('_stacklevel', kwargs.get('stack_level', kwargs.get('stacklevel', 0))))
        stack_level += 1
        self.print(*args, sep=sep, level=logging.WARNING, stacklevel=stack_level, **kwargs)

    def error(self, *args, sep=' ', **kwargs):
        stack_level = kwargs.get('_stack_level', kwargs.get('_stacklevel', kwargs.get('stack_level', kwargs.get('stacklevel', 0))))
        stack_level += 1
        self.print(*args, sep=sep, level=logging.ERROR, stacklevel=stack_level, **kwargs)

    def fatal(self, *args, sep=' ', **kwargs):
        stack_level = kwargs.get('_stack_level', kwargs.get('_stacklevel', kwargs.get('stack_level', kwargs.get('stacklevel', 0))))
        stack_level += 1
        self.print(*args, sep=sep, level=logging.FATAL, stacklevel=stack_level, **kwargs)

    @classmethod
    def __class_getitem__(cls, item):
        if item in cls._logger_instance:
            return cls._logger_instance[item]
        else:
            raise KeyError(f'there is no logger "{item}" yet.')


LOG_PRINT_FORMAT = '{value}({type})'


def analyse_value(value):
    value_class = type(value).__name__
    return LOG_PRINT_FORMAT.format(value=str(value), type=value_class)


def analyse_input_value(func, self, args, kwargs, print_bool):
    re_str = ''
    if print_bool:
        arg_value = analyse_args_value_from_function(func, self, *args, **kwargs)
        arg_list = [f'{_k}={analyse_value(_v)}' for _k, _v in arg_value['arg'].items() if _k != 'self']
        if 'args' in arg_value:
            arg_list += [f'*{_k}::' + ' , '.join([analyse_value(_w) for _w in _v]) for _k, _v in arg_value['args'].items()]
        arg_list += [f'{_k}={analyse_value(_v)}' for _k, _v in arg_value['kwarg'].items()]
        if 'kwargs' in arg_value:
            arg_list += [f'*{_k}::' + ' , '.join([f'{_l}={analyse_value(_w)}' for _l, _w in _v.items()]) for _k, _v in arg_value['kwargs'].items()]
        temp_str = ' , '.join(arg_list)
        if isinstance(print_bool, bool):
            print_len = math.inf
        else:
            print_len = max(4, print_bool)
        re_str = ' input is:' + (temp_str if len(temp_str) < print_len else (temp_str[:print_len - 3] + '...'))
    return re_str


def analyse_return_value(re_value, print_bool):
    re_str = ''
    if print_bool:
        if isinstance(re_value, tuple):
            temp_str = ' , '.join([analyse_value(_) for _ in re_value])
        else:
            temp_str = analyse_value(re_value)
        if isinstance(print_bool, bool):
            print_len = math.inf
        else:
            print_len = max(4, print_bool)
        re_str = ' return is:' + (temp_str if len(temp_str) < print_len else (temp_str[:print_len - 3] + '...'))
    return re_str


def function_log(process: bool = True, input_value: Union[bool, int] = True, return_value: Union[bool, int] = True):
    """
    装饰器将当前函数运行时的内容，简单打印在日志里
    :param process: 开始和结束运行时，需要打印日志
    :param input_value: 开始时，是否将当前详细的输入值打印在日志中。如果输入数值，那么将会把文字缩减至相应长度，最少显示4位
    :param return_value: 结束后，是否将返回值打印在日志中。如果输入数值，那么将会把文字缩减至相应长度，最少显示4位
    """
    if callable(process):
        # 如果只把装饰器当一层装饰器用，仍旧能生效
        return function_log()(process)

    def dec(func):
        @wraps(func)
        def wrapper(self: LoggerBase, *args, **kwargs):
            start_time = time.time()
            if process:
                self.print(f'[{func.__name__}] start.{analyse_input_value(func, self, args, kwargs, input_value)}', stacklevel=2)
            try:
                re_value = func(self, *args, **kwargs)
            except Exception as err:
                self.error(f'{err}<< occurs when [{func.__name__}] running and cost {time.time() - start_time:.3f}s.', stacklevel=2)
                raise err
            else:
                if process:
                    self.print(f'[{func.__name__}] end and cost {time.time() - start_time:.3f}s.{analyse_return_value(re_value, return_value)}', stacklevel=2)
                return re_value

        return wrapper

    return dec


class LogLevel:
    TEXT = {
        'TRACE': 0,
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
        'FATAL': logging.FATAL,
    }

    def __init__(self, level: Union[str, int, 'LogLevel'], plus: bool = True):
        plus_str = '+' if plus else ''
        if isinstance(level, str):
            level_upper = level.upper()
            if level.lower() in ['trace', 'debug', 'info', 'warn', 'warning', 'error', 'fatal', 'critical']:
                self._int = self.TEXT[level_upper]
                self._str = level_upper
            else:
                raise ValueError(f'invalid log level :"{level}"')
        elif isinstance(level, int):
            self._int = level
            self._plus = ''
            if level < 0:
                raise ValueError(f'invalid log level :"{level}"')
            elif level == 0:
                self._str = 'TRACE'
            elif level < logging.DEBUG:
                self._str = 'TRACE'
                self._plus = plus_str
            elif level == logging.DEBUG:
                self._str = 'DEBUG'
            elif level < logging.INFO:
                self._str = 'DEBUG'
                self._plus = plus_str
            elif level == logging.INFO:
                self._str = 'INFO'
            elif level < logging.WARN:
                self._str = 'INFO'
                self._plus = plus_str
            elif level == logging.WARN:
                self._str = 'WARN'
            elif level < logging.ERROR:
                self._str = 'WARN'
                self._plus = plus_str
            elif level == logging.ERROR:
                self._str = 'ERROR'
            elif level < logging.FATAL:
                self._str = 'ERROR'
                self._plus = plus_str
            elif level == logging.FATAL:
                self._str = 'FATAL'
            else:
                self._str = 'FATAL'
                self._plus = plus_str
        elif isinstance(level, LogLevel):
            self._int = level._int
            self._plus = level._plus
            self._str = level._str

    def __str__(self):
        return self._str + self._plus

    def __repr__(self):
        return f'LogLevel({self._int})'

    def __int__(self):
        return self._int

    def __eq__(self, other):
        if isinstance(other, LogLevel):
            return self._int == other._int
        elif isinstance(other, str):
            return self._int == LogLevel(other)._int
        else:
            return self._int == int(other)

    def __lt__(self, other):
        if isinstance(other, LogLevel):
            return self._int < other._int
        elif isinstance(other, str):
            return self._int < LogLevel(other)._int
        else:
            return self._int < int(other)

    def __gt__(self, other):
        if isinstance(other, LogLevel):
            return self._int > other._int
        elif isinstance(other, str):
            return self._int > LogLevel(other)._int
        else:
            return self._int > int(other)

    def __le__(self, other):
        if isinstance(other, LogLevel):
            return self._int <= other._int
        elif isinstance(other, str):
            return self._int <= LogLevel(other)._int
        else:
            return self._int <= int(other)

    def __ge__(self, other):
        if isinstance(other, LogLevel):
            return self._int >= other._int
        elif isinstance(other, str):
            return self._int >= LogLevel(other)._int
        else:
            return self._int >= int(other)

    @property
    def int(self):
        return self._int

    @property
    def str(self):
        return self._str

    @property
    def str_plus(self):
        return self._str + self._plus


STACK.this_file_lineno_should_ignore(304, check_text='re_value = func(self, *args, **kwargs)')
