'''
Author: gwyxjtu
Date: 2022-05-22 13:31:12
LastEditors: gwyxjtu 867718012@qq.com
LastEditTime: 2022-06-15 18:49:41
FilePath: /optimization/cpeslog/log_code.py
Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.

Copyright (c) 2022 by gwyxjtu 867718012@qq.com, All Rights Reserved. 
'''
# -*- coding: utf-8 -*-
import os
import time
from logging.handlers import RotatingFileHandler
import logging

import inspect



handlers = None


def createHandlers(handlers):
    logLevels = handlers.keys()

    for level in logLevels:
        path = os.path.abspath(handlers[level])
        handlers[level] = RotatingFileHandler(path, maxBytes=10000, backupCount=2, encoding='utf-8')


# 加载模块时创建全局变量

# createHandlers()


class TNLog(object):

    def printfNow(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    def __init__(self,dir, name='', level=logging.NOTSET):
        '''
        保存日志文件，其中会生成./{dir}/{name}__info.log 和./{dir}/{name}__info.error两个文件
        Args:
            dir: log文件夹路径
            name: log文件名，如果多个log文件写在同一个目录下，可以根据name来进行区别
            level:
        '''
        self.__loggers = {}
        self.dir = dir
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        # global handlers
        handlers = {
            logging.INFO: os.path.join(self.dir, name + '_info.log'),

            logging.ERROR: os.path.join(self.dir, name + '_error.log'),
        }

        createHandlers(handlers)

        logLevels = handlers.keys()

        for level in logLevels:
            logger = logging.getLogger(str(level))

            # 如果不指定level，获得的handler似乎是同一个handler?

            logger.addHandler(handlers[level])

            logger.setLevel(level)

            self.__loggers.update({level: logger})

    def getLogMessage(self, level, message):
        frame, filename, lineNo, functionName, code, unknowField = inspect.stack()[2]

        '''日志格式：[时间] [类型] [记录代码] 信息'''

        return "[%s] [%s] [%s - %s - %s] %s" % (self.printfNow(), level, filename, lineNo, functionName, message)

    def info(self, message):
        message = self.getLogMessage("info", message)

        self.__loggers[logging.INFO].info(message)

    def error(self, message):
        message = self.getLogMessage("error", message)

        self.__loggers[logging.ERROR].error(message)



_logging = TNLog('./my_test_log')
