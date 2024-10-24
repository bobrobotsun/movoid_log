#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# File          : logger
# Author        : Sun YiFan-Movoid
# Time          : 2024/10/19 21:14
# Description   : 
"""
import logging
import os
import pathlib
import re
import time
from stat import ST_MTIME, ST_CTIME
from typing import Union
from logging.handlers import BaseRotatingHandler


class TimeSizeRotatingFileHandler(BaseRotatingHandler):
    def __init__(self, filename, interval: Union[str, int] = 1, max_time=7, max_byte=0, max_file=0, encoding=None, delay=False, at_time=0):
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

    def logger_init(self, file_name, interval: Union[str, int] = 0, max_time=0, max_byte=0, max_file=0, console=True):
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
        :param console: 是否在std上打印
        """
        self._logger = logging.Logger(pathlib.Path(file_name).stem)
        log_format = logging.Formatter('%(asctime)s-%(name)s-%(filename)s-[line:%(lineno)d]-%(levelname)s: %(message)s')
        time_handler = TimeSizeRotatingFileHandler(file_name, interval=interval, max_time=max_time, max_byte=max_byte, max_file=max_file)
        time_handler.setFormatter(log_format)
        self._logger.addHandler(time_handler)
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_format)
            console_handler.setLevel(logging.INFO)
            self._logger.addHandler(console_handler)

    def print(self, *args, sep=' ', level: Union[str, int] = 'INFO', exc_info=False, **kwargs):
        print_text = str(sep).join([str(_) for _ in args])
        level_int = logging._nameToLevel.get(level, logging.INFO) if isinstance(level, str) else int(level)
        kwargs.setdefault('stacklevel', 2)
        self._logger.log(level=level_int, msg=print_text, exc_info=exc_info, **kwargs)

    def debug(self, *args, sep=' ', exc_info=False, **kwargs):
        kwargs.setdefault('stacklevel', 3)
        self.print(*args, sep=sep, level=logging.DEBUG, exc_info=exc_info, **kwargs)

    def info(self, *args, sep=' ', exc_info=False, **kwargs):
        kwargs.setdefault('stacklevel', 3)
        self.print(*args, sep=sep, level=logging.INFO, exc_info=exc_info, **kwargs)

    def warn(self, *args, sep=' ', exc_info=False, **kwargs):
        kwargs.setdefault('stacklevel', 3)
        self.print(*args, sep=sep, level=logging.WARNING, exc_info=exc_info, **kwargs)

    def error(self, *args, sep=' ', exc_info=True, **kwargs):
        kwargs.setdefault('stacklevel', 3)
        self.print(*args, sep=sep, level=logging.ERROR, exc_info=exc_info, **kwargs)

    def critical(self, *args, sep=' ', exc_info=True, **kwargs):
        kwargs.setdefault('stacklevel', 3)
        self.print(*args, sep=sep, level=logging.CRITICAL, exc_info=exc_info, **kwargs)
