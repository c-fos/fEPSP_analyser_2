## @package array_prepare Модуль подготовки сигнала к поиску спайков
#
#
#
'''
Created on 05.12.2011

@author: pilat
'''
import logging

from numpy import math, empty, ndarray

import main.array_processing_functions as ar

logger = logging.getLogger("workflow.array_prepare")


## приводит массив к размеру 2^x
#
#  Поскольку фильтрация идет с помощью многоуровневого вейвлет разложения, то
#  размер массива должен быть на каждом этапе разложения кратен двойке. Т.е.
#  как минимум длинна массива должна быть кратна 2*КОЛИЧЕСТВО_УРОВНЕЙ. Но
#  поскольку количество уровней заранее не известно, то в данной функции длинна
#  массива наращивается до ближайшего 2^x.
#
#  Дополненный участок заполняется наиболее часто встречающимся в массиве
#  числом.
#
def dataFitting(data: ndarray):
    try:
        dataLen: int = len(data)
        tmp: int = 2**(math.ceil(math.log(dataLen, 2)))
        delta: int = tmp - dataLen
        meanTmp = ar.histMean(data[:round(dataLen / 4)])
        newData = empty(tmp, dtype='float32')
        newData.fill(meanTmp)
        newData[delta:] = data
        return newData, delta
    except Exception as e:
        logger.exception("dataFitting # Error: %s", e)
        raise e

## Если запись велась в режиме 5мв/дел домножаем массив на коэфициент
#
#  Узнать о том в каком режиме велась запись можно только с помощью ключевого
#  слова в названии файла. Возможно это можно определить по анализу шума в
#  сигнале, но это сложнее.
#
def amplLoad(filename: str, data: ndarray) -> ndarray:
    if ("5мв" in filename) or ("5мВ" in filename) or ("5mv" in filename) or ("5mV" in filename):
        logger.warn("amplLoad # 5mv amplifier")
        return(data * 2.5)  # *5/2
    else:
        return data


