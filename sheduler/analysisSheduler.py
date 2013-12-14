'''
Created on 16.02.2012

@author: pilat
'''
print "Using:\nFirst step: `analysisSheduler create_list $DIR_NAME` where 'create_list' is a keyword and DIR_NAME name of the folder with experiment folders to be processing\n\
Second step: modify .dir_list file by inserting tags\n\
Third step: `analysisSheduler start` where 'start' is a keyword "

import sys
from glob import glob
from os.path import isdir
from os import remove
from root.fEPSPanalyser import fepspAnalyser

def addDir(path):
    if isdir(path):
        return "%s ''\n" % path
    
if sys.argv[1]=="create_list" and len(sys.argv)==3:
    dir_list=glob(sys.argv[2]+"/*")
    dir_list2=[addDir(i) for i in dir_list]
    #remove('.dir_list')
    with open('.dir_list', 'a') as f:
        [f.write(i) for i in dir_list2]
elif sys.argv[1]=="start" and len(sys.argv)==2:
    with open('.dir_list', 'r') as f:
        dir_list2=f.readlines()
    for i in dir_list2:
        path=i.split(' \'')[0].strip()
        tags=i.split(' \'')[1].strip('\'\n').strip()
        print tags,path
        try:
            analyserObject=fepspAnalyser([0,path,'200000',"data","1",tags,0,1,0])
            del analyserObject
        except:
            print "fepspAnalyser error:", sys.exc_info()
            del analyserObject

