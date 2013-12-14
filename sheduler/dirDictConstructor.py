'''
Created on 16.10.2012

@author: pilat
'''
from os import listdir
import os
'''
dictionary constructing of all directories with .dat files within prefix
'''

def dirDict(prefix,initialTag):
    '''
    Constructor
    input: prefix
    output:
    dict{path1:list(tag1,tag2),path2:list(tag2,tag3),...}
    '''
    dict1={}
    dict1=recursSearch(prefix,initialTag,dict1)
    return dict1
        
def recursSearch(path,tagList,dict1):
    tmp=path.split("/")
    if tmp[-1]=="":
        newTag=tmp[-2]
    else:
        newTag=tmp[-1]
    resultTag="%s,%s" % (tagList,newTag)
    for dirs in listdir(path):
        newPath="%s/%s" % (path,dirs)
        if os.path.isdir(newPath):
            try:
                fileList=listdir(newPath)
                if all((any([".dat" in i for i in fileList]),any([".ins" in i for i in fileList]))):
                    dict1[newPath]=resultTag
                else:
                    dict1=recursSearch(newPath,resultTag,dict1)
            except:
                pass
        else:
            pass
    return dict1    