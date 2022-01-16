## @package rInterface_lib
#  Модуль доступа к функциям R для работы с нейронными сетями.
#
#  В перспективе следует заменить на более зрелый и гибкий PyBrain
#
'''
Created on 11.03.2012

@author: pilat
'''
import os

from rpy2.robjects.packages import importr
import rpy2.robjects as ro
from rpy2.rlike import container
import rpy2.robjects.numpy2ri
from numpy import array

libPath = '.libPaths("/home/pilat/R/x86_64-pc-linux-gnu-library/4.1")'

## Определение с помощью нейронной сети является или спайк реальным или это волоконный ответ.
def neuroCheck(maxtomin, delay, length, angle1, angle2):
    angles = angle1/angle2
    ro.r(libPath)  #
    nnet = importr("nnet")
    ro.r.load(os.getcwd()+"/main/.RneuroModel8")
    tmpMatrix = ro.r['data.frame'](ro.DataFrame(container.TaggedList([length, delay, maxtomin, angle1, angles],['length','delay','maxtomin','angle1','angles'])))
    result = ro.r.predict(ro.r['neuroModel'], tmpMatrix)
    return array(result)[0][0]

## Определени с помощью нейронной сети является ли резкий всплеск шумом или электрическим стимулом.
def stimNeuroCheck(length, ptp, base_ptp, std, median, mean, base_mean, base_median, base_std, diff_median, base_diff_median, sampleStdDiff, samplePtpDiff):
    median_baseMedian = median-base_median
    if base_ptp==0:
        base_ptp = 10**-16
    ptp_base_ptp = ptp/base_ptp
    med_ptp = abs(median_baseMedian)/base_ptp
    ro.r(libPath)
    nnet = importr("nnet")
    ro.r.load(os.getcwd()+"/main/.RStimNeuroModel11")
    rpy2.robjects.numpy2ri.activate()
    tmpMatrix = ro.r['data.frame'](ro.DataFrame(container.TaggedList([length, ptp, base_ptp, std, median, mean, base_mean, base_median, base_std, diff_median, base_diff_median, median_baseMedian, med_ptp, ptp_base_ptp, sampleStdDiff, samplePtpDiff],['length','ptp','base_ptp','std','median','mean','base_mean','base_median','base_std','diff_median','base_diff_median','median_baseMedian','med_ptp','ptp_base_ptp','sampleStdDiff','samplePtpDiff'])))
    result = ro.r.predict(ro.r['neuroModel'], tmpMatrix)
    return array(result)[0][0]
