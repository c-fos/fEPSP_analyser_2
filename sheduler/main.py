'''
Created on 16.10.2012

@author: pilat
'''
from root.fEPSPanalyser import fepspAnalyser
from sheduler.dirDictConstructor import dirDict
from sys import exc_info
def shedule(path,initTags,frequ='200000'):
    dict1=dirDict(path,initTags)
    for i in dict1.keys():
        print(i)
        try:
            analyserObject=fepspAnalyser([0,i,frequ,"data","1",dict1[i],0,1,0,0])
            del analyserObject
            #print((0,i,frequ,"data","1",dict1[i],0,1,0))
        except:
            print "fepspAnalyser error:", exc_info()
            #del analyserObject