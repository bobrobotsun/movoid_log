#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# File          : log
# Author        : Sun YiFan-Movoid
# Time          : 2024/12/21 18:38
# Description   : 
"""
import pathlib
import traceback
from datetime import datetime, date
from io import TextIOWrapper
from typing import Union

LOG_SPLIT = f'\x1c'  # 用于分隔每条不同的日志
MODULE_SPLIT = f'\x1d'  # 用于分隔日志内的模块
ELEMENT_SPLIT = '\x1e'  # 用于在日志内的详细内容中分隔不同元素
MINI_SPLIT = '\x1f'  # 用于一些极为特殊的分隔情况

GROUP_START = '\x02'  # 日志的左括号
GROUP_END = '\x03'  # 日志的右括号

"%Y-%m-%d %H:%M:%S"


class LogWrite:
    def __init__(self, file='log', folder='', roll_size=0, max_day=0, max_file=-1):
        self._file_path = pathlib.Path(file).with_suffix('.log').resolve().absolute()
        self._file_name = self._file_path.stem
        self._file_dir = self._file_path.parent
        self._ori_file_path = str(self._file_path)
        self._folder_name = folder
        self._roll_size = int(roll_size * 1048576)
        self._max_day = max_day
        self._max_file = max_file
        if self._folder_name == '':
            self._folder_path = self._file_path.parent
            self._folder_name = str(self._folder_path)
        else:
            self._folder_path = pathlib.Path(self._folder_name).resolve().absolute()
        self._folder_path = pathlib.Path(self._folder_name)
        self._file_date: Union[date, None] = None
        self._file: Union[TextIOWrapper, None] = None
        self._depth = 0
        self.init()

    def _flush_print(self, print_text: str):
        self.check_roll()
        self._file.write(str(print_text) + LOG_SPLIT)
        self._file.flush()
        if self._file_date is None:
            self._file_date = datetime.now().date()
        self.check_roll()

    def _fast_print(self, print_text: str):
        self._file.write(str(print_text) + LOG_SPLIT)

    def _complete_text(self, time_str, style_str, log_text):
        """
        混合log文本
        :param time_str: 时间的文本
        :param style_str: 日志类型的文本
        :param log_text: 实际日志文本
        :return: 混合后的文本
        """
        depth_text = str(self._depth) if self._depth else ''
        return MODULE_SPLIT.join([time_str, style_str, depth_text, log_text, '\n'])

    def log(self, *args, sep=' ', level='INFO', fast=False):
        log_text = str(sep).join([str(_) for _ in args])
        level = str(level).upper()
        if level in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            level_text = level
        else:
            level_text = 'INFO'
        print_text = self._complete_text(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            ELEMENT_SPLIT + level_text,
            log_text
        )
        if fast:
            self._fast_print(print_text)
        else:
            self._flush_print(print_text)

    def init(self):
        """初次运行软件时的一些基础原则。"""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        file_text = ''
        if self._file_path.exists() and self._file_path.is_file():
            try:
                with self._file_path.open(mode='r') as f:
                    file_text = f.read()
                    if LOG_SPLIT in file_text:
                        part_txt = file_text.split(LOG_SPLIT, 2)[1]
                        if MODULE_SPLIT in part_txt:
                            text_list = part_txt.split(MODULE_SPLIT)
                            if len(text_list) >= 1:
                                time_module = text_list[0]
                                time_date = datetime.strptime(time_module, "%Y-%m-%d %H:%M:%S.%f")
                                self._file_date = time_date.date()
            except:
                self._file_date = None
        else:
            self._file_path.touch(exist_ok=True)
        add_log = len(file_text) == 0 or file_text[-1] != LOG_SPLIT
        self._file = self._file_path.open('a')
        if add_log:
            self._file.write(LOG_SPLIT)

    def check_roll(self):
        should_roll = False
        if self._file_date is not None and datetime.now().date() > self._file_date:
            should_roll = True
        else:
            if self._roll_size > 0:
                file_size = self._file_path.stat().st_size
                should_roll = file_size >= self._roll_size
        if should_roll:
            self._roll_file()

    def _roll_file(self):
        self._file.flush()
        self._file.close()
        self._folder_path.mkdir(parents=True, exist_ok=True)
        index = 1
        while True:
            new_path = self._folder_path / (f'{self._file_name}-' + self._file_date.strftime("%Y_%m_%d") + f'-{index:>03d}.log')
            if new_path.exists():
                index += 1
            else:
                break
        self._file_path.rename(new_path)
        self._file_path = self._file_dir / (self._file_name + '.log')
        self._file_path.unlink(missing_ok=True)
        self._file = self._file_path.open('w')
        self._file_date = None
        self._file.write(LOG_SPLIT)
        if self._max_day > 0:
            for log_path in self._folder_path.glob(f'{self._file_name}-????_??_??-*.log'):
                log_time_str = log_path.stem.split('-')[-2]
                log_time_date = datetime.strptime(log_time_str, "%Y_%m_%d")
                date_delta = datetime.now() - log_time_date
                if date_delta.days >= self._max_day:
                    log_path.unlink(missing_ok=True)
        if self._max_file > 0:
            file_list = []
            for log_path in self._folder_path.glob(f'{self._file_name}-????_??_??-*.log'):
                file_list.append([log_path, log_path.stat().st_ctime])
            if len(file_list) > self._max_file:
                file_list.sort(key=lambda x: x[1], reverse=True)
                for log_path, ctime in file_list[self._max_file:]:
                    log_path.unlink(missing_ok=True)
