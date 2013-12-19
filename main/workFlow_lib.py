#!/usr/bin/python2
# -*- coding: utf-8 -*-
## @package workFlow_lib
#  Модуль содержащий алгоритм обработки эксперимента в целом.
#
#  Задача данного модуля запустить анализ для каждого из .dat файлов в
#  указанном каталоге, и при этом сохранить информацию об отдельных файлах, как
#  о частях единого целого.
#
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
'''
Created on 23.11.2011
@author: Malakhin Ilya (pilat1988@gmail.com)

'''
from os import stat
import datetime as dt
from glob import glob
import sys
from dbAccess_lib_2 import Mysql_writer
from analyser_lib import dataSample
import shutil, logging


## Функция определяющая алгоритм обработки на уровне эксперимента
def workFlow(argDict):
    logging.basicConfig(filename='fEPSP.log', filemode='w', level=logging.DEBUG)
    logger = logging.getLogger("workflow")
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('fEPSP.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    if argDict["debug"]:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info(argDict)
    dirPath = argDict["input"]
    fileList = glob(dirPath+"/*.dat")
    if not fileList:
        logger.warn("There are no *.dat files in the directory! Exit!")
        sys.exit(1)
    if argDict["write"]:
        mysql_writer = Mysql_writer(argDict["dbConf"]["dbType"], argDict["dbConf"]["dbUser"], argDict["dbConf"]["dbPass"], argDict["dbConf"]["dbAdress"], argDict["dbConf"]["dbScheme"])
        mysql_writer.loadExpInfo(fileList[0], argDict["tags"])
        logger.info("Write to database enabled")
        mysql_writer.dbWriteExperiment()
        mysql_writer.tagWriter()
    else:
        logger.info("Write to database doesn`t enabled")
        mysql_writer="pass"
    for i in fileList:
        fileName = i.split('/')[-1]
        try:
            creatingTime = dt.datetime.fromtimestamp(stat(i).st_mtime).time()
            if argDict["write"]:
                mysql_writer.filePath = i
                mysql_writer.time = creatingTime
                mysql_writer.dbWriteRecord()
                mysql_writer.dbWriteRecordTags(fileName)
            dataSample1 = dataSample(i, mysql_writer, argDict)
            dataSample1.dataProcessing()
            if dataSample1.hardError==1:
                errorProcessing(i, "hard", logger)
            elif dataSample1.softError==1:
                errorProcessing(i, "soft", logger)
            else:
                pass
            del dataSample1
        except:
            logger.error("Error: {0}".format(sys.exc_info()))
            try:
                del dataSample1
            except:
                pass
    if argDict["write"]:
        try:
            mysql_writer.dbDisconnect()
        except:
            logger.error("Unexpected error in dbDisconect: {0}".format(sys.exc_info()))

## Функция копирования файлов с ошибками в отдельные каталоги для дальнейшего анализа
def errorProcessing(filename, errorType, logger):
    try:
        logger.info("copy file with trouble to separate directory")
        if errorType=="soft":
            shutil.copy2(filename,"./softErrors/")
        else:
            shutil.copy2(filename,"./hardErrors/")
    except:
        logger.error("Can`t copy files with errors: {0}".format(sys.exc_info()))
        raise
