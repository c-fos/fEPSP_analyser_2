#!/usr/bin/python2
# -*- coding: utf-8 -*-
## @package InOut_lib Модуль чтения и записи из файлов и отрисовки изображений
#
#
#
'''
Created on 05.12.2011

@author: pilat
'''
import sys
from mimetypes import guess_type
from numpy import loadtxt, fromfile, int16
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import array_prepare as ap
import logging

logger = logging.getLogger("workflow.InOut")

## Загрузка массива из файла
#
#  Обрабатываются два типа файлов: записаные в виде столбца чисел в
#  текстовом файле и сохраненный в бинарном виде массив типа int16. Тип
#  определяется по mime типу файла. Если он текстовый, то читается как
#  текст, в противном случае читается как бинарный.
#
def dataLoading(fileName):
    if guess_type(fileName)[0] == 'text/plain' or guess_type(fileName)[0] == 'chemical/x-mopac-input':
        tmpData = loadtxt(fileName,dtype='float32')
        source_data = ap.amplLoad(fileName, tmpData)
        data, deltaLen = ap.dataFitting(source_data)
    else:
        data = fromfile(fileName, int16)
        source_data = ap.amplLoad(fileName, tmpData)
        data, deltaLen = ap.dataFitting(source_data)
    return data, deltaLen, source_data


## Загрузка значения частоты из .ins файла
#
#  Функция читает одноименный и .dat файлом .ins файл, находит там строку
#  содержащую значение частоты с которой осуществлялась запись и возвращает
#  частоту.
#
#
def freqLoad(filename, defFrequ, varName = "CodingFreq"):
    try:
        dictionary = {}
        iniName = "{0}.ins".format(filename.strip('.dat'))
        logger.warn("freqLoad # .ins file name: {0}".format(iniName))
        fd = file(iniName,'r')
        for line in fd.readlines():
            pairs = line.split("=")
            for variable, value in zip(pairs[::2], pairs[1::2]):
                dictionary[variable] = value.strip()
        frequency = int(dictionary[varName].strip()) * 1000
    except:
        logger.error("freqLoad # Error: {0}".format(sys.exc_info()))
        frequency = int(defFrequ)
    logger.warn("freqLoad # Frequency = {0}Hz".format(frequency))
    return frequency

def plotData(analyserObj):
    fig, ax = plt.subplots(1, 1)
    fig.canvas.set_window_title(analyserObj.fileName.split("/")[-1])
    ax.plot(analyserObj.cleanData,'y')
    try:
        ax.plot(analyserObj.result,'b')
        try:
            ax.plot(analyserObj.epsp[0],analyserObj.epsp[1],'r')
        except:
            analyserObj.softError=1
        ax.grid(color='k', linestyle='-', linewidth=0.4)
        try:
            logger.warn("plotData # analyserObj.responseDict: {0}".format(analyserObj.responseDict))
            for i in analyserObj.responseDict.values():
                tmpObject=getattr(analyserObj,i)
                logger.warn("plotData # tmpObject created")
                rect = Rectangle((tmpObject.responseStart, tmpObject.response_bottom),
                                 tmpObject.responseEnd-tmpObject.responseStart,
                                 tmpObject.response_top-tmpObject.response_bottom,
                                 facecolor="#aaaaaa", alpha=0.3)
                ax.add_patch(rect)
                ax.text(tmpObject.responseStart,tmpObject.response_top+20,
                        "EPSP="+str(tmpObject.epsp), fontsize=12, va='bottom')
                try:
                    for j in tmpObject.spikes:
                        tmpObject2=getattr(analyserObj,j)
                        tex = str((tmpObject2.responsNumber,tmpObject2.spikeNumber,tmpObject2.spikeAmpl))
                        ax.plot(tmpObject2.spikeMin,analyserObj.result[tmpObject2.spikeMin],'or')
                        ax.plot(tmpObject2.spikeMax1,analyserObj.result[tmpObject2.spikeMax1],'og')
                        ax.plot(tmpObject2.spikeMax2,analyserObj.result[tmpObject2.spikeMax2],'og')
                        ax.vlines(tmpObject2.spikeMin,analyserObj.result[tmpObject2.spikeMin],
                                  analyserObj.result[tmpObject2.spikeMin]+tmpObject2.spikeAmpl,
                                  color='k',
                                  linestyles='dashed')
                        ax.text(tmpObject2.spikeMin,analyserObj.result[tmpObject2.spikeMin]-15,
                                tex,
                                fontsize=12,
                                va='bottom')
                except:
                    logger.error("plotData # Error wile spike ploating: {0}".format(sys.exc_info()))
        except:
            logger.error("plotData # Error wile ploating: {0}".format(sys.exc_info()))
            analyserObj.hardError=1
        for i in range(len(analyserObj.stimuli[0])):
            ax.axvline(x=analyserObj.stimuli[0][i],color='g')
    except:
        logger.error("plotData # Error wile ploating computedData: {0}".format(sys.exc_info()))
        analyserObj.hardError=1
    plt.savefig(analyserObj.fileName+"_graph.png")
    plt.close()
    del fig

def writeExport(fileName, data):
    fd = open(fileName, "w")
    fd.write("Название эксперимента,Имя файла,Номер спайка,Время изменения файла,Амплитуда\n")
    for line in data:
        fd.write("{0},{1},{2},{3},{4}\n".format(line[0], line[1], int(line[2]),
                                                str(line[3]), line[4]))
    fd.close()
    logger.info("writeExport # Filename: {0}, Data length: {1}".format(fileName,
                                                                       len(data)))

