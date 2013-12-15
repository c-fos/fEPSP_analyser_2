#!/usr/bin/python2
# -*- coding: utf-8 -*-
## @package analyser_lib Модуль анализа сигнала
#
#
#
'''
Created on 05.12.2011

@author: pilat
'''
#library for filtering
import sys
import os
from numpy import zeros, log, asmatrix, math, sqrt, ones, diff, array,\
                    unique, where, float16, argmin, median
import pywt
import tempfile
os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()
import matplotlib
matplotlib.use('agg')
from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
from externalFunctions_lib import iswt, extrema
from objects_lib import Spike, Response
from scipy import polyval, polyfit, signal
from clussterization_lib import clusterization, clusterAnalyser
import rInterface_lib as rInterface
import array_processing_functions as ar
#import main.array_prepare as ap
import InOut_lib as ioLib
import logging

logger = logging.getLogger("workflow.analyser")

class dataSample:
    def __init__(self, filename, dbobject, argDict):
        #variables
        self.spikeObjectList=[]
        self.spikeDict={}
        self.responseList=[]
        self.responseDict={}
        self.fileName = filename
        self.mysql_writer = dbobject
        self.argDict = argDict
        self.hardError = 0
        self.softError = 0
        self.wavelet='sym3'#'bior3.5
        self.defaultFrame = 0
        self.epsp = 0
        self.frequency = 0
        self.result = []
        self.signalPtp = 0
        self.localDelay = 0
        self.highNoiseLevel = 0
        self.clusters = []
        self.responsMatrix = []
        self.fibreIndex = 0
        self.baseFrequency = 300
        self.deltaLen = 0
        self.minimumsForFibre = []
        self.snr = 0
        self.data = []
        self.level = 0
        self.cleanData = []
        self.resultRough = []
        self.mainLevel = 0
        self.stimulyDuration = 0
        self.stimuli = 0
        self.signalStd = 0


    def dataProcessing(self):
        logger.info("File name: {0}".format(self.fileName))
        try:
            self.frequency = ioLib.freqLoad(self.fileName,
                                            self.argDict["frequ"])
        except:
            logger.error("ioLib.freqLoad() error: {0}".format(sys.exc_info()))
        try:
            self.data, self.deltaLen, self.source_data = ioLib.dataLoading(self.fileName)
        except:
            logger.error("dataLoading() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        try:
            self.mysql_writer.addSource(self.frequency, self.source_data)
        except:
            logger.error("addSource() error: {0}".format(sys.exc_info()))
        try:
            self.tresholdCreating()
        except:
            logger.error("tresholdCreating() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        try:
            self.mysql_writer.dbWriteTechInfo(self.defaultFrame, self.stimulyDuration)
        except:
            logger.error("Unexpected error wile dbWriteTechInfo: {0}".format(sys.exc_info()))
        try:
            self.cleanData = self.cutStimuli(self.data)
        except:
            logger.error("cutStimuli() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        try:
            self.snr, self.signalPtp, self.signalStd = ar.snrFinding(self.cleanData[self.deltaLen+self.stimulyDuration:],
                                                                     self.defaultFrame)
        except:
            logger.error("snrFinding() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        try:
            self.mainLevelFinding()
        except:
            logger.error("mainLevelFinding() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        self.mysql_writer.dbTechInfo_level(self.snr, self.signalPtp,
                                           self.signalStd, self.mainLevel)
        try:
            self.resultRough = self.filtering(self.argDict["smooth"])
            self.result = self.filtering(self.argDict["smooth"]-5)
        except:
            logger.error("filtering() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        try:
            self.spikeFinding()
        except:
            logger.error("spikeFinding() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        try:
            self.clusters = clusterization(self, self.spikeDict, self.stimuli)
        except:
            logger.error("clusterization() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        try:
            clusterAnalyser(self, self.spikeDict, self.clusters)
        except:
            logger.error("clusterAnalyser() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        try:
            self.responsMatrix = self.responsLength()
        except:
            logger.error("responsLength() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        try:
            self.responsAnalysis()
        except:
            logger.error("responsAnalysis() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        try:
            ioLib.plotData(self)
        except:
            logger.error("plotData() error: {0}".format(sys.exc_info()))
            self.hardError = 1
        if self.mysql_writer!="pass":
            try:
                self.writeData()
            except:
                logger.error("writeData() error: {0}".format(sys.exc_info()))
                self.hardError = 1
            if self.hardError!=0 or self.softError!=0:
                try:
                    self.mysql_writer.dbWriteError(self.softError,
                                                   self.hardError)
                except:
                    logger.error("dbWriteError error: {0}".format(sys.exc_info()))
                    self.hardError = 1


    ## Расчет велечины некоторых переменных, зависящих от частоты записи
    #
    #  После того как частота определена, расчитывается размер милисекунды, а
    #  по нему характерные размеры стимула, спайка, рамок считывания.
    #
    def tresholdCreating(self):
        msec = self.frequency / 1000 # 1 msec =  frequency/1000 points
        self.defaultFrame = 4 * msec #frame size for mean() and std() finding must depend on frequency. assume it equal to 4 msec
        self.stimulyDuration = int(0.8 * msec) #1msec# treshold for stimuli filtering ~20points==2msec==2*self.msec
        self.level = int((math.log(100.0 / self.frequency, 0.5) - 1)) #wavelet decomposition level. level 6 to 10kHz signal.
        highNoiseFrequency = 14000.0
        self.highNoiseLevel = int((math.log(highNoiseFrequency / self.frequency, 0.5)))
        self.localDelay = 1 * msec #time delay before spike(filtering of local responses)

    ## Поиск артифактов от электрических стимулов
    #
    #  Ищем в высокочастотной составляющей сигнала всплески превышающие
    #  пороговое значение зависящее от стандартного отклонения высокочастотной
    #  составляющей. Проверяем эти всплески на то являются ли они спайками с
    #  помощью нейронной сети
    #
    def findStimuli(self, data):
        wavelet='haar'
        filterSize = pywt.Wavelet(wavelet).dec_len
        pwr = pywt.swt(data, wavelet, 2)
        pwr2 = array(pwr[0][1])  # вейвлет коефициенты высокочастотной составляющей сигнала
        pwr2Std = ar.stdFinder(pwr2[self.deltaLen:], self.defaultFrame)
        treshold = pwr2Std*1.5*log(pwr2.ptp()/pwr2Std)#11 - empirical finding coef
        try:
            self.mysql_writer.dbTechInfo_stim(pwr2Std, treshold)
        except:
            logger.warn("findStimuli # Error: {0}".format(sys.exc_info()))

        pwr5 = zeros(len(pwr2))
        # pwr5 по сути первая производная от вейвлет коефициентов
        # высокочастотной составляющей сигнала
        pwr5[1:] += abs(diff(pwr2))
        pwr5[0] = pwr5[1]
        # оставляем только резкие изменения в высокочастотной составляющей
        pwr5[pwr5 < treshold] = 0
        pwr5[pwr5 > 0] = treshold
        # dpwr - координаты точек в которых начинались резкие изменения в
        # высокочастотной составляющей сигнала
        dpwr = where(diff(pwr5)==treshold)[0]
        dpwrMask = ones(len(dpwr), dtype='bool')
        for i in range(len(dpwr)-1):
            if dpwr[i+1]-dpwr[i] < self.stimulyDuration/3.0:  # если две точки слишком близко, то оставляем первую.
                dpwrMask[i+1] = 0
        dpwr = dpwr[dpwrMask]
        dpwrMask = ones(len(dpwr), dtype='bool')
        for i in range(len(dpwr)):
            #  по характеристикам сигнала в окрестностях этих точек будем
            #  решать является ли это артефактом от электрического стимула.
            length1 = len(where((abs(diff(pwr2[dpwr[i]+filterSize:dpwr[i]+filterSize+self.stimulyDuration/2])) >= treshold))[0])
            sample1 = data[dpwr[i]+filterSize*2:dpwr[i]+filterSize*2+self.stimulyDuration/2]
            sample2 = data[dpwr[i]+filterSize*2-self.stimulyDuration/2:dpwr[i]+filterSize*2]
            sample3 = pwr2[dpwr[i]+filterSize:dpwr[i]+filterSize+self.stimulyDuration/2]
            sample4 = pwr2[dpwr[i]+filterSize-self.stimulyDuration/2:dpwr[i]+filterSize]
            sample5 = data[dpwr[i]+filterSize*2-self.stimulyDuration/2:dpwr[i]+filterSize*2+self.stimulyDuration/2]
            sampleSumDiff = abs(median(sample1)-median(sample2))
            std_diff = sample3.std()/sample4.std()
            ptp_diff = abs(sample3).mean()/abs(sample4).mean()
            sampleGlobalStd = median(sample5)/median(sample2)
            length = length1*100000.0/self.frequency
            ptp_1 = sample1.ptp()*0.1
            ptp_2 = sample2.ptp()*0.1
            std_1 = sample1.std()
            std_2 = sample2.std()
            median_1 = median(sample1)*0.1
            median_2 = median(sample2)*0.1
            mean_1 = sample1.mean()*0.1
            mean_2 = sample2.mean()*0.1
            median_diff_1 = median(diff(sample1*1.0))
            median_diff_2 = median(diff(sample2*1.0))
            if sampleSumDiff > 0:
                neuroTestResult = rInterface.stimNeuroCheck(length,
                                                            ptp_1,
                                                            ptp_2,
                                                            std_1,
                                                            median_1,
                                                            mean_1,
                                                            mean_2,
                                                            median_2,
                                                            std_2,
                                                            median_diff_1,
                                                            median_diff_2,
                                                            std_diff,
                                                            ptp_diff) >= 0.5
                try:
                    self.mysql_writer.dbStimProp_write(i, length, ptp_1, ptp_2,
                                                   std_1, std_2, median_1,
                                                   median_2, mean_1, mean_2,
                                                   median_diff_1, median_diff_2,
                                                   std_diff, ptp_diff,
                                                   neuroTestResult, 1)
                except:
                    logger.error("findStimuli # Error when write stim prop: {0}".format(sys.exc_info()))

                if neuroTestResult:
                    logger.warn("findStimul # Accepted! Start: {0}, ptp_diff: {1}, std_diff: {2}, sampleSumDiff: {3}, sampleGlobalStd: {4}".format(dpwr[i]+filterSize, ptp_diff, std_diff, sampleSumDiff, sampleGlobalStd))
                    #self.mysql_writer.dbWriteStim(sample2, sample1, length1, i, "1", self.frequency, std_diff, ptp_diff)
                else:
                    dpwrMask[i] = 0
                    #self.mysql_writer.dbWriteStim(sample2, sample1, length1, i, "0", self.frequency, std_diff, ptp_diff)
                    logger.warn("findStimuli # Dropped! Start: {0}, ptp_diff: {1}, std_diff: {2}, sampleSumDiff: {3}, sampleGlobalStd: {4}".format(dpwr[i]+filterSize, ptp_diff, std_diff, sampleSumDiff, sampleGlobalStd))
            else:
                dpwrMask[i] = 0
                #self.mysql_writer.dbWriteStim(sample2, sample1, length1, i, "0", self.frequency, std_diff, ptp_diff)
                logger.warn("findStimuli # Dropped! Start: {0}, ptp_diff: {1}, std_diff: {2}, sampleSumDiff: {3}, sampleGlobalStd: {4}".format(dpwr[i]+filterSize, ptp_diff, std_diff, sampleSumDiff, sampleGlobalStd))
        dpwr = dpwr[dpwrMask]
        logger.info("findStimuli # Number of finded stimuls: {0}".format(len(dpwr)))
        stimList=[[],[]]
        for i in range(len(dpwr)):
            start = dpwr[i]+filterSize*2
            length = self.stimulyDuration/4
            if self.stimulyDuration > 35:
                baseline = ar.histMean(data[start-int(self.stimulyDuration/7):start])
                baseStd = data[start-int(self.stimulyDuration/7):start].std()
            else:
                baseline = data[start-1]
                baseStd = data[start-6:start-1].std()
            tmpStop = start+length
            if tmpStop+self.defaultFrame+5 > len(data):
                tmpStop = len(data)-self.defaultFrame-5
            stimMean = data[start:tmpStop].mean()
            logger.warn("findStimuli # Baseline: {0}, baseStd: {1}, start: {2}, tmpStop: {3}, stimMean: {4}".format(baseline, baseStd, start, tmpStop, stimMean))
            try:
                sample = signal.medfilt(data[tmpStop-5:tmpStop+self.defaultFrame+5], int(self.stimulyDuration/20))
            except:
                sample = data[tmpStop-int(self.stimulyDuration/40):tmpStop+self.defaultFrame+int(self.stimulyDuration/40)]
            firstArray = abs(diff(sample)) <= baseStd
            secondArray = abs(sample[1:]-baseline) < baseStd/2
            fourthArray = ar.stdArray(sample[1:], 5) <= baseStd*3
            fivthArray = abs(sample[1:]-baseline) < baseStd*4
            logger.warn("findStimuli # {0}".format((any(firstArray), any(secondArray), any(fourthArray), any(fivthArray))))
            try:
                shift = where((firstArray*fivthArray+secondArray)*fourthArray)[0]
                if len(shift) > 0:
                    realStop = tmpStop+shift[0]
                else:
                    realStop = tmpStop
                    logger.warn("findStimuli # Can`t find stimulum end =(")
                    self.softError = 1
            except:
                logger.error("findSimuli # Unexpected error in finding of stimuli end:{0}".format(sys.exc_info()))
                realStop = tmpStop
            logger.warn("findStimuli # start {0}, tmpStop {1}, realStop {2}".format(start, tmpStop, realStop))
            stimList[0]+=[start]
            stimList[1]+=[realStop]
        self.stimuli = stimList

    ## Вырезаем из сигнала найденные стимулы
    def cutStimuli(self, data):
        try:
            self.findStimuli(data)
        except:
            logger.error("cutStimuli # Error: {0}".format(sys.exc_info()))
        stim = self.stimuli[0]
        if stim:
            processedData = zeros(len(data), dtype='int')
            processedData += data
            logger.warn("cutStimuli # Start")
            for i in range(len(stim)):
                try:
                    if stim[i] < self.stimulyDuration:
                        patchValue = ar.histMean(data[:stim[i] + self.stimulyDuration])
                    else:
                        patchValue = ar.histMean(data[stim[i] - (self.stimuli[1][i] - stim[i]):stim[i]])
                    processedData[stim[i]:self.stimuli[1][i]] = patchValue
                except:
                    self.hardError = 1
            logger.warn("cutStimuli # End")
            return processedData
        else:
            logger.warn("cutStimuli # End")
            return data

    ## Определение основного уровня вейвлет разложения
    #
    #  Определение уровня вейвлет разложения на котором предположительно
    #  основная часть интересующего нас сигнала и который нужно
    #  искажать минимально
    #
    def mainLevelFinding(self):
        self.mainLevel = int(math.log((self.baseFrequency * (0.5 + sqrt(sqrt(self.snr)) / 2)) / self.frequency, 0.5) - 1.4)  # magic
        logger.warn("mainLevelFinding # self.mainLevel: {0}, self.snr: {1}".format(self.mainLevel, self.snr))

    ## Фильтрация сигнала
    #
    #  Фильтрация сигнала с помощью вейвлет разложения сигнала на уровни,
    #  адаптивной фильтрации каждого из уровней и последующей
    #  реконструкции сигнала.
    #
    def filtering(self, coeffTreshold):
        coeffs = pywt.swt(self.cleanData, self.wavelet, level = self.mainLevel+1)
        coeffsLen = len(coeffs)
        for i in range(len(coeffs)):
            cA, cD = coeffs[i]
            if i >= (coeffsLen - self.highNoiseLevel):
                cD = zeros(len(cA), dtype='float32')
                minSD = 0
                maxSD = 0
                snr = 0
                smoothCoef = 0
                logger.warn("filtering # noisLevel: {0}".format(i))
            else:
                minSD = ar.stdFinder(cD[self.deltaLen:], self.defaultFrame)
                maxSD = ar.getLocalPtp(cD[self.deltaLen:], self.defaultFrame*0.8)
                snr = maxSD / minSD
                smoothCoef = minSD*(coeffTreshold*(snr**(i**(0.7)/(i**(1.5)+i+1)))+i*2)
                logger.warn("filtering # minSD: {0}, maxSD: {1}, snr: {2}, level: {3}, smoothCoef: {4}".format(minSD, maxSD, snr, i, smoothCoef))
                cD = pywt.thresholding.soft(cD, smoothCoef)
            self.mysql_writer.dbWaveLevel_write(coeffTreshold, i, minSD, maxSD, smoothCoef)
            coeffs[i] = cA, cD
        return iswt(coeffs, self.wavelet)

    ## Поиск спайков
    #
    #  Ищем всплески в сигнале характерные для спайков. Для этого находим
    #  экстремумы и проверяем идущие подряд триплеты (максимум, минимум,
    #  максимум) на превышение порогового значение амплитуды и соответствие
    #  объективным ограничением на минимальное и максимальное расстояния между
    #  минимумами и максимумами.
    #
    def spikeFinding(self):
        resultDataForSearch = self.resultRough
        resultData = self.result
        start = self.defaultFrame/4
        stop = -self.defaultFrame/4
        minimum, minimumValue = extrema(resultDataForSearch[start:stop],_max = False, _min = True, strict = False, withend = True)  # попробовать заменить на функцию из scipy
        maximum, maximumValue = extrema(resultDataForSearch[start:stop],_max = True, _min = False, strict = False, withend = True)
        minimumValue = resultData[minimum + start]
        tmpMaximum = maximum.tolist()
        tmpMaximum.extend(array(self.stimuli[1]) - start)
        maximum = array(tmpMaximum)
        maximum.sort()
        maximumValue = resultData[maximum + start]
        std = ar.stdFinder(self.cleanData[self.deltaLen:], self.defaultFrame)
        SD = float16(std + std*self.snr**(0.25) / 4) # another magic
        self.mysql_writer.dbTechInfo_clean(std, SD)
        logger.warn("spikeFinding # snr: {0}, std: {1}, SD: {2}".format(self.snr, std, SD))
        spikePoints=[]
        if minimum[0] < maximum[0]:
            minimum = minimum[1:]
            minimumValue = minimumValue[1:]
        for i in range(len(minimum)):
            tmpMaximum1 = 0
            for j in range(len(maximum)):
                if maximum[j] < minimum[i]:
                    tmpMaximum1 = j
                if maximum[j] > minimum[i]:
                    tmpMaximum2 = j
                    break
            if maximumValue[tmpMaximum1]-minimumValue[i] > SD and maximumValue[tmpMaximum2]-minimumValue[i] > SD\
             and (maximum[tmpMaximum2]-maximum[tmpMaximum1]) > self.stimulyDuration/2:
                spikePoints.append([start+maximum[tmpMaximum1], start+minimum[i], start+maximum[tmpMaximum2]])
        ##общее количество триплетов (макс-мин-макс)
        spikePointsLen = len(spikePoints)
        for i in range(spikePointsLen):
            try:
                ## Переменная-лист состоящая из координат экстремумов входящих в триплет (макс-мин-макс)
                triplet = spikePoints[i]
                ampl = round(resultData[triplet[0]]-resultData[triplet[1]]+\
                       (resultData[triplet[2]]-resultData[triplet[0]])/\
                       (triplet[2]-triplet[0])*(triplet[1]-triplet[0]), 1)
                logger.warn("spikeFinding # len(spikePoints): {0}, Spike: {1}, Ampl={2}, SD={3}".format(spikePointsLen, i, ampl, SD))
                if ampl > SD:
                    index = len(self.spikeDict)
                    self.spikeDict[index] = "n{0}".format(str(i))
                    setattr(self, self.spikeDict[index], Spike(self.frequency))
                    tmpObject = getattr(self, self.spikeDict[index])
                    tmpObject.responseStart = start
                    tmpObject.responseEnd = stop
                    tmpObject.spikeMax1 = triplet[0]
                    tmpObject.spikeMax1Val = self.result[triplet[0]]
                    tmpObject.spikeMin = triplet[1]
                    tmpObject.spikeMinVal = self.result[triplet[1]]
                    tmpObject.spikeMax2 = triplet[2]
                    tmpObject.spikeMax2Val = self.result[triplet[2]]
                    tmpObject.spikeMaxToMin = tmpObject.spikeMax2Val - tmpObject.spikeMinVal
                    tmpObject.spikeAmpl = ampl
                    tmpObject.manual = self.argDict["manual"]
                    tmpObject.spikeLength = self.getSpikeLength(triplet[0], triplet[1], triplet[2]) * 1000.0 / self.frequency
                    tmpObject.spikeFront, tmpObject.spikeBack = self.getSpikeAngles(resultData[triplet[0]:triplet[2]])
            except:
                logger.error("spikeFinding # Error: {0}".format(sys.exc_info()))
        logger.info("spikeFinding # Для файла {0} найдены спайки: {1}".format(self.fileName, self.spikeDict))

    ## Проверка что найдено: спайк или волоконный ответ
    #  Проверяем для первого спайка в каждой группе спайков является ли он
    #  волоконным ответом.
    #  @param respDictValue объект - группа спайков
    #  @param spikeList список спайков данной группы
    #
    def checkForFibrePotential(self, respDictValue):
        try:
            tmpObject = getattr(self, respDictValue)
            tmpObject2 = getattr(self, tmpObject.spikes[0])
            if rInterface.neuroCheck(tmpObject2.spikeMax2Val - tmpObject2.spikeMinVal,
                                     tmpObject2.spikeDelay,
                                     tmpObject2.spikeLength,
                                     tmpObject2.spikeFront,
                                     tmpObject2.spikeBack) >= 0.5:
                tmpObject2.fibre = 1
                logger.warn("checkForFibrePotential # There are AP at zero position")
        except:
            logger.error("checkForFibrePotential # Error: {0}".format(sys.exc_info()))

    ## Интерактивный поиск волоконных ответов
    #
    #  Открывается окно с графиком и возможностью вручную указать на волоконный
    #  ответ кликнув мышью вблизи минимума волоконного ответа
    #
    def interactiveFibreSearch(self, respDictValue):
        try:
            logger.info("interactiveFibreSerach # Response dict values: {0}".format(self.responseDict.values()))
            tmpObject = getattr(self, respDictValue)
            tmpObject2 = getattr(self, tmpObject.spikes[0])
            start = tmpObject2.spikeMax1 - (tmpObject2.spikeMin-tmpObject2.spikeMax1)
            tmpObject2 = getattr(self, tmpObject.spikes[-1])
            stop = tmpObject2.spikeMax2 + (tmpObject2.spikeMax2-tmpObject2.spikeMin)
            fig, ax = plt.subplots(1, 1)
            ax.grid(color='k', linestyle='-', linewidth = 0.4)
            ax.plot(self.cleanData, 'y')
            ax.plot(self.result, 'b')
            ax.set_xlim((start, stop))
            tmpObject = getattr(self, respDictValue)
            plt.show()
            try:
                self.minimumsForFibre = []
                logger.info("interactiveFibreSerach # tmpObject.spikes: {0}".format(tmpObject.spikes))
                for j in tmpObject.spikes:
                    tmpObject2 = getattr(self, j)
                    ax.plot(tmpObject2.spikeMin, self.result[tmpObject2.spikeMin],'or')
                    ax.text(tmpObject2.spikeMin, self.result[tmpObject2.spikeMin]-15, str(j), fontsize = 12, va='bottom')
                    self.minimumsForFibre.append(tmpObject2.spikeMin)
            except:
                logger.info("interactiveFibreSerach # Error: {0}".format(sys.exc_info()))
            self.fibreIndex=''
            cursor = Cursor(ax, useblit = True, color='black', linewidth = 2 )
            #_widgets=[cursor]
            fig.canvas.mpl_connect('button_press_event', self.click)
            plt.show()
            del fig, ax # very important to stop memory leak
            if self.fibreIndex!='':
                logger.info("interactiveFibreSerach # Fibre spike: {0}".format(tmpObject.spikes[self.fibreIndex]))
            else:
                logger.info("interactiveFibreSerach # No fibre spikes selected")
            fibre = tmpObject.spikes[self.fibreIndex]
            if not fibre:
                pass
            else:
                tmpObject2 = getattr(self, fibre)
                tmpObject2.fibre = 1
        except:
            logger.info("interactiveFibreSerach # Error wile ploating: {0}".format(sys.exc_info()))

    ## Обработка клика по графику во время интерактивного поиска волоконного ответа
    def click(self, event):
        xpos = argmin(abs(event.xdata-self.minimumsForFibre))
        if event.button==1:
            self.fibreIndex = xpos

        elif event.button==3:
            self.fibreIndex=''
        plt.close()

    ## Определения углов наклона переднего и заднего фронтов спайка
    #
    #  На участках от максимума до минимума и от минимума до максимума находим
    #  точки соответствующие 20% и 80% от амплитуды (вернее от разницы
    #  напряжения в максимуме и минимуме) и возвращаем тангинсы угол наклона прямых
    #  проведенных через эти точки.
    #
    def getSpikeAngles(self, sample):
        sampleMin = min(sample)
        try:
            minPoint = where(sample==sampleMin)[0][0]
        except:
            minPoint = where(sample==sampleMin)[0]
        max1 = sample[0]
        max2 = sample[-1]
        h1 = max1-sampleMin
        point1 = where(sample[:minPoint]<(max1-h1*0.2))[0][0]
        point2 = where(sample[:minPoint]<(max1-h1*0.8))[0][0]
        h2 = max2-sampleMin
        point3 = where(sample[minPoint:]>(sampleMin+h2*0.2))[0][0]
        point4 = where(sample[minPoint:]>(sampleMin+h2*0.8))[0][0]

        if point2-point1 > 0:
            angle1 = (sample[point1]-sample[point2])/(point2-point1)
        else:
            angle1 = sample[point1]-sample[point2]
        if point4-point3 > 0:
            angle2 = (sample[point4]-sample[point3])/(point4-point3)
        else:
            angle2 = sample[point4]-sample[point3]
        return angle1*1000.0/self.frequency,-angle2*1000.0/self.frequency

    ## Определяем длинну спайка
    #
    #  Для того чтобы исключить ошибку определения связанную с пологим выходом
    #  графика в районе максимумов, смотрим расстояние между серединами спуска
    #  и подъема.
    #
    def getSpikeLength(self, max1, min1, max2):
        h1 = self.result[max1]-self.result[min1]
        h1Part = self.result[max1]-h1*(0.5)#50% of first spike front
        h2 = self.result[max2]-self.result[min1]
        h2Part = self.result[max2]-h2*(0.5)#50% of first spike front
        try:
            firstPoint = where(self.result[max1:min1] < h1Part)[0][0]
            secondPoint = where(self.result[min1:max2] > h2Part)[0][0]
        except:
            try:
                firstPoint = where(self.result[max1:min1] < h1Part)[0]
                secondPoint = where(self.result[min1:max2] > h2Part)[0]
            except:
                firstPoint=(min1-max1)/2
                secondPoint=(max2-min1)/2
        length=(secondPoint+(min1-(max1+firstPoint)))*2
        logger.info("getSpikeLength # firstPoint: {0}, secondPoint: {1}, length {2}".format(firstPoint, secondPoint, length))
        return length

    ## Определяем длинну группы спайков
    def responsLength(self):
        """
        The function for calculation the response length - the distance between the stimuli and the moment of potential returning to baseline
        """
        responsMatrix = zeros((max(self.clusters), 2), dtype = int)#[[start1, stop1],[start2, stop2]]
        length = len(self.result)
        smallFrame = self.defaultFrame/10
        logger.warn("responsLength # len(unique(self.clusters)): {0}, len(self.clusters): {1}".format(len(unique(self.clusters)), len(self.clusters)))
        for i in unique(self.clusters):
            try:
                lastSpike = self.spikeDict.values()[list(self.clusters).index(i+1)-1]
            except:
                lastSpike = self.spikeDict.values()[-1]
            start = self.stimuli[0][i-1]
            baseLevel = self.result[start-smallFrame*2:start].mean()
            tmpObject = getattr(self, lastSpike)
            lastMax = tmpObject.spikeMax2
            k = lastMax
            std2 = self.result[start-smallFrame*2:start].std()
            try:
                while((abs(self.result[k:k+smallFrame*4].mean()-baseLevel) > std2/4 or self.result[k:k+smallFrame*4].std() > std2/4) and (k < length-smallFrame*4 and k < self.stimuli[0][i])):
                    k += smallFrame
            except:
                logger.warn("responsLength # finding end of last response")
                k = lastMax
                if k > length-smallFrame*4:
                    k = length-1
                else:
                    while(abs(self.result[k:k+smallFrame*4].mean()-baseLevel) > std2/6 or self.result[k:k+smallFrame*4].std() > std2/6):
                        k += smallFrame
                        if k > length-smallFrame*5:
                            k = length-1
                            break
                stop = k
                """
                Shift the response end to left for long tail preventing
                """
                difference = self.result[lastMax]-self.result[stop]
                threshold = self.result[lastMax]-0.9*difference
                if difference > 0:
                    while self.result[stop] < threshold:
                        stop -= 1
                if difference < 0:
                    while self.result[stop] > threshold:
                        stop -= 1
                logger.warn("responsLength # lastMax: {0}, stop: {1}, length{2}".format(lastMax, stop, length))
                try:
                    """
                    Calculate response end precisely using polynomial smoothing
                    """
                    sampleLen = stop-lastMax
                    logger.warn("responsLength # End sample length: {0}".format(sampleLen))
                    if sampleLen > 0:
                        arFit = polyfit(array(range(sampleLen)), self.result[lastMax:stop], 2)
                        sample = polyval(arFit, array(range(sampleLen)))
                        extrem = where(diff(sample)==0)[0]
                        logger.warn("responsLength # number of extremums in respons length curve: {0}".format(len(extrem)))
                        if len(extrem) > 0:
                            lastExtremum = extrem[-1]
                            if sample[lastExtremum] > sample[lastExtremum+1]:
                                realStop = stop
                            else:
                                realStop = lastExtremum
                        else:
                            if sample[0] > sample[1]:
                                shift = where(diff(sample)>-0.000001)[0]
                                if len(shift) > 0:
                                    realStop = lastMax+shift[0]
                                else:
                                    realStop = stop
                            else:
                                realStop = stop
                        responsMatrix[i-1] = start, realStop
                    else:
                        responsMatrix[i-1] = start, stop
                except:
                    responsMatrix[i-1] = start, stop
                    logger.error("responsLength # Error: {0}".format(sys.exc_info()))
        return responsMatrix

    def responsAnalysis(self):
        """
        Main function for response(fEPSP and all spikes induced by one stimulus)
        The following functions are called from there:

            self.checkForFibrePotential - is the first "spike" a real spike or fibre potential
            self.getResponsLength - get the length of response in ADC points (20% to 20% of fEPSP amplitude)
            self.setSpikeDelays - calculate the time delay between stimulus and spike`s minimum
            self.epspReconstructor - reconstruct the shape of fEPSP
            self.epileptStd - rouge estimate the "epileptiform activity"
            self.spikeArea - calculation of area between signal curve and fEPSP for one spike
            self.epspArea - calculation of area between signal and fEPSP for all spikes

        """
        def getResponsLength(sample):
            h1 = sample[0]-max(sample)
            h1Part = h1*0.2#20% of first spike front
            h2 = sample[-1]-max(sample)
            h2Part = h2*0.2
            try:
                firstPoint = where(sample > h1Part)[0][0]
                secondPoint = where(sample.revers() > h2Part)[0][0]
            except:
                try:
                    firstPoint = where(sample > h1Part)[0]
                    secondPoint = where(sample.revers() > h2Part)[0]
                except:
                    firstPoint = 0
                    secondPoint = 0
            length = len(sample)-firstPoint-secondPoint
            return length

        rMatrix = self.responsMatrix
        self.epsp = array([[],[]])
        for i in unique(self.clusters):
            index = len(self.responseDict)
            self.responseDict[index]="r"+str(i)
            setattr(self, self.responseDict[index], Response())
            tmpObject = getattr(self, self.responseDict[index])
            try:
                try:
                    tmpObject.spikes = array(self.spikeDict.values())[self.clusters==i]
                    tmpObject.responseStart = rMatrix[i-1][0]
                    tmpObject.responseEnd = rMatrix[i-1][1]
                    tmpObject.length = getResponsLength(self.result[rMatrix[i-1][0]:rMatrix[i-1][1]])*1000.0/self.frequency
                    tmpObject.response_top = max(self.result[rMatrix[i-1][0]:rMatrix[i-1][1]])
                    tmpObject.response_bottom = min(self.result[rMatrix[i-1][0]:rMatrix[i-1][1]])
                    tmpObject.baselevel = self.result[rMatrix[i-1][0]-self.defaultFrame/2:rMatrix[i-1][0]].mean()
                    tmpObject.responsNumber = i
                    tmpObject.epsp = round(tmpObject.response_top-tmpObject.baselevel, 1)
                except:
                    logger.error("Unexpected error wile fill response properties: {0}".format(sys.exc_info()))
                try:
                    self.setSpikeDelays(tmpObject.spikes, tmpObject.responseStart)
                except:
                    logger.error("Unexpected error wile setSpikeDelays: {0}".format(sys.exc_info()))
                if self.argDict["manual"]:
                    self.interactiveFibreSearch(self.responseDict[index])
                else:
                    self.checkForFibrePotential(self.responseDict[index])
                self.spikeNumberShift(tmpObject)
            except:
                logger.error("Unexpected error wile checkForFibrePotential: {0}".format(sys.exc_info()))
        logger.info(self.fileName.split('/')[-1], self.responseDict)

    def spikeNumberShift(self, tmpObject):
        tmpObject2 = getattr(self, tmpObject.spikes[0])
        if tmpObject2.spikeNumber==0 and tmpObject2.fibre!=1:
            logger.warn("spike number shift")
            for i in tmpObject.spikes:
                tmpObject2 = getattr(self, i)
                tmpObject2.spikeNumber += 1

    def setSpikeDelays(self, spikeDict, startPoint):
        for i in spikeDict:
            tmpObject = getattr(self, i)
            tmpObject.spikeDelay=(tmpObject.spikeMin-startPoint)*1000.0/self.frequency

    def writeData(self):
        if self.argDict["write"]:
            try:
                self.mysql_writer.dbWriteNumberOfResponses(len(self.responseDict.values()))
            except:
                logger.error("Unexpected error wile dbWriteNumberOfResponses: {0}".format(sys.exc_info()))
            for i in self.responseDict.values():
                tmpObject = getattr(self, i)
                self.mysql_writer.dbWriteResponse(tmpObject)

                try:
                    for j in tmpObject.spikes:
                        tmpObject2 = getattr(self, j)
                        self.mysql_writer.dbWriteSpike(tmpObject2)
                except:
                    logger.error("Unexpected error wile dbWriteSpike: {0}".format(sys.exc_info()))
            self.mysql_writer.dbCommit()
