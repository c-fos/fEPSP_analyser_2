## @package Функции для анализа сигнала
#
#  В этот модуль вынесены общие функции используемые для преобразования и анализа
#  сигнала.
#
'''
Created on 13.11.2013

@author Malakhin Ilya
'''
import logging

from numpy import arange, histogram, empty, ndarray, unique, where
from scipy import signal

logger = logging.getLogger("workflow.array_processing")

## Функция возвращает наиболее часто встречающееся в массиве число.
#
#  1. Определяем какие числа представлены в массиве
#  2. Строим гистограмму массива по этим числам
#  3. Определяем для какого числа столбик выше =)
#  @param sample 1d массив типа numpy.array()
def histMean(sample: ndarray) -> ndarray:
    try:
        uniqueValues=unique(sample)
        if len(uniqueValues)>1:
            dataHist=histogram(sample,bins=uniqueValues)
            histMax: int=dataHist[0].max()
            meanTmp = dataHist[1][where(dataHist[0]==histMax)[0]]
            return meanTmp[0]
        else:
            return uniqueValues
    except Exception as e:
        logger.exception("histMean # Error: %s", e)
        raise e


## Формирует массив значений стандартного отклонения
#
#  Проходит рамкой размера 2*frame по переданному в функцию массиву и
#  расчитывает стандартное отклонение, которое записывает в результирующий
#  массив. Размеры входящего и исходящего массивов одинаковы
#  @param sample входящий массив
#  @param frame половина размера рамки считывания
def stdArray(sample,frame):
    tmp = empty(len(sample) + frame * 2)
    result = empty(len(sample))
    tmp[frame:-frame] = sample
    tmp[:frame] = sample[:frame]
    tmp[-frame:] = sample[-frame:]
    for i in range(len(sample)):
        result[i] = tmp[i:i + frame * 2].std()
    return result

## Возвращает локальное значение ptp() в массиве
#
#  Сначала немного сглаживает массив скользяшим средним для того чтобы
#  исключить случайные выбросы. Затем проходит по массиву указанной рамкой и
#  расчитывает ptp(). Возвращает максимальное из расчитанных значений.
#  @param data Входящий массив
#  @param framesize размер рамки считывания
#
def getLocalPtp(data, framesize: int) -> float:
    ptpList=[]
    smoothedData=signal.medfilt(data, 5)
    smoothedDataLen=len(smoothedData)
    logger.warn("getLocalPtp function. data = {0}, len(data) = {1}, framesize = {2}".format(data, len(data), framesize))
    try:
        ptpList=[i.ptp() for i in [smoothedData[j:j+framesize] for j in arange(0,smoothedDataLen-framesize,round(framesize/3))]]
    except Exception as e:
        logger.exception("Unexpected error in finding local ptp: %s", e)
    if ptpList:
        return max(ptpList)
    else:
        return 0.0

## Возвращает отношение максимального локального std к максимальному локальному ptp
#
#  Попытка оценить отношение сигнала к шуму.
#
def snrFinding(data,frameSize: int):
    logger.warn("snrFinding function. Data = {0}, len(data) = {1}, framesize = {2}".format(data, len(data), frameSize))
    minSD=stdFinder(data,frameSize)
    maxSD=getLocalPtp(data, round(frameSize*0.8))
    snr=float(maxSD/minSD)
    logger.warn("snrFinding function results: snr = {0}, maxSD = {1}, minSD = {2}".format(snr, maxSD, minSD))
    return round(snr,3), round(maxSD,3), round(minSD,3)

## Возвращает минимальное и максимальное локальные стандартные отклонения в массиве
#
#  Проходит по переданному массиву рамкой считывания и расчитывает std() и
#  mean(). В зависимости от переданных агрументов может вернуть минимальное
#  стандартное отклонение, максимальное стандартное отклонение, минимальное
#  стандартное отклонение и среднее той рамки где std было минимальным.
#
def stdFinder(data, frameSize: int, mean=False,maxStd=False):
    dataSample=[]
    minSD=200
    maxSD=0
    i=frameSize
    for j in range(int(len(data)/frameSize)):
        dataSample+=[[i,j,data[j*i:i*(j+1)].mean(),data[j*i:i*(j+1)].std()]]#1/3
        dataSample+=[[i,j,data[j*i+round(j/3.0):i*(j+1)+round(j/3.0)].mean(),data[j*i+round(j/3.0):i*(j+1)+round(j/3.0)].std()]]#2/3
        dataSample+=[[i,j,data[j*i+round(j*2/3.0):i*(j+1)+round(j*2/3.0)].mean (),data[j*i+round(j*2/3.0):i*(j+1)+round(j*2/3.0)].std()]]#3/3
    if len(dataSample)>0:
        for k in range(len(dataSample)):
            if dataSample[k][3]< minSD and dataSample[k][3]!=0:
                minSD=dataSample[k][3]
                index=k
            if dataSample[k][3]>maxSD and dataSample[k][3]!=0:
                maxSD=dataSample[k][3]
        if mean==True:
            return round(minSD, 3)  #,dataSample[index][2]
        else:
            if maxStd==True:
                logger.warn((maxSD,len(dataSample)))
                return round(maxSD, 3)
            else:
                return round(minSD, 3)
    else:
        if mean==True:
            return round(data.std(), 3)  # , data.mean()
        else:
            return round(data.std(), 3)

