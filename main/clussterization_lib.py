#!/usr/bin/python2
# -*- coding: utf-8 -*-
## @package clussterization_lib
#  Модуль работы с большим количеством стимулов в записи.
#
#  Изначально был создан для анализа спантанной активности с помощью
#  класстерного анализа, но такой анализ не был реализован до конца и был
#  удален. Модуль используется, но скорее всего можен быть редуцирован до
#  небольшой функции и внесен в основной алгоритм
#
#  На данный момент используется вроде для определения к какому стимулу
#  относится тот или иной спайк
#

'''
Created on 15.02.2012

@author: pilat
'''

from numpy import array, where, zeros
import sys

def clusterization(fromObject, spikeDict, stimuli):
    if len(spikeDict) > 1:
        dictValues = array(spikeDict.values())
        listOfSpikes = []
        for i in dictValues:
            tmpObject = getattr(fromObject, i)
            listOfSpikes.append([tmpObject.spikeMin])
        ndarrayOfSpikes = array(listOfSpikes)
        rightClasterOrder = zeros(ndarrayOfSpikes.size, dtype = int)
        ndarrayOfSpikes.shape = (1, ndarrayOfSpikes.size)
        for i in range(len(stimuli[0])):
            rightClasterOrder[ndarrayOfSpikes[0] >= stimuli[0][i]]=i+1
        return (rightClasterOrder)
    else:
        return(array([1]))

def clusterAnalyser(fromObject, spikeDict, clusters):
    dictValues = array(spikeDict.values())
    for i in range(len(dictValues)):
        try:
            tmpObject = getattr(fromObject, dictValues[i])
            tmpObject.responsNumber = int(clusters[i])
            k = where(clusters == int(clusters[i]))[0][0]
            tmpObject.spikeNumber = int(i)-k
        except:
            print("clusterAnalyser # Error: {0}".format(sys.exc_info()))
