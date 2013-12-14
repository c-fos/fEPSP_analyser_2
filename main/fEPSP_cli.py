#!/usr/bin/python2
# -*- coding: utf-8 -*-
#signal filtering and spike finding
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
import argparse  #Для передачи аргументов в режиме командной строки
import os  #для проверки существования файлов
import sys  #для выхода из программы
from main.workFlow_lib import workFlow  #Передача введеных аргументов основному алгоритму обработки

if __name__ == "__main__":
    #перечислены обязательные и опциональные аргументы, их описания и значения по умолчанию
    parser = argparse.ArgumentParser(description="Comand line interface for fEPSP_analyser")
    parser.add_argument("inputDir", help="Folder with files to analyse")
    parser.add_argument("-f", "--frequency", dest='frequ', default=200000,  help="Frequency of record (default = 200000)")
    parser.add_argument("-s", "--smooth", dest='smooth', default=1, help="Smoothing coefficient (default = 1)")
    parser.add_argument("-o", "--output", dest='imgPath', default="./", help="Folder to save images")
    parser.add_argument("-w", "--write", action='store_true', default=False, help="write results to db")
    parser.add_argument("-t", "--tags", dest='tags', default="test", help="String of tags, separated by coma")
    parser.add_argument("-m", "--manual", action='store_true', default=False, help="Manual fibre search (Use for NN learning)")
    parser.add_argument("-d", "--debug", action='store_true', default=False, help="run with debug output")
    options = parser.parse_args()

    #Проверка путей до файлов и графиков
    if os.path.exists(options.inputDir):
        pass
    else:
        print("Path to directory with files to analyse is incorrect! Exit!")
        sys.exit(1)

    imgPath=options.imgPath
    if not os.path.exists(imgPath):
        print("Invalid img directory: {0}. Set to './'".format(imgPath))
        imgPath = "./"

    #Формируем словарь аргументов
    argumentDict={"input":options.inputDir,"frequ":int(options.frequ),"smooth":int(options.smooth),"imgPath":imgPath,"write":options.write,"tags":options.tags,"manual":options.manual,"debug":options.debug}

    #Создаем объект класса workFlow (основной алгоритм) и передаем ему собранные аргументы
    workFlow(argumentDict)
    print("Обработка завершена.")
