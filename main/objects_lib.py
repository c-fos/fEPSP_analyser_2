## @package objects_lib
#
# Модуль для объявления классов используемых для хранения структур данных.
#
# Экземпляры данных классов генерируются в ходе анализа групп спайков и
# отдельных спайков, храня всю собранную информацию. После того как эти объекты
# уже не требуются для анализа, информация из них сохраняется в БД.
#
'''
Created on 05.12.2011

@author: pilat
'''

## Класс для описания отдельного спайка.
class Spike:

    ## Конструктор
    def __init__(self, frequency):
        #primary variables
        self.responseNumber = 0 #int
        self.responseStart = 0  #point
        self.responseEnd = 0    #point
        self.spikeNumber = 0    #int
        self.allSpikes = 0      #int
        self.spikeMax1 = 0      #point
        self.spikeMin = 0       #point
        self.spikeMax2 = 0      #point
        self.spikeAmpl = 0      #depend on input
        self.frequency = frequency
        #secondary variables
        self.spikeLength = 0    #msec
        self.spikeFrequency = 0 #hZ
        self.spikeFront = 0
        self.spikeBack = 0
        self.area = 0
        self.fibre = 0
        self.manual = 0
        self.spikeDelay = 0

## Класс для описания группы спайков в ответ на одинарный стимул
class Response:

    ## Конструктор
    def __init__(self):
        self.epspFront = 0
        self.epspBack = 0
        self.epspEpileptStd = 0
        self.fibre = 0
        self.epspArea = 0
