#!/usr/bin/python2
# -*- coding: utf-8 -*-
## @package dbAccess_lib
#  Модуль доступа к БД.
#
#  Задача данного модуля обеспечить чтение и запись в БД структурированных, подготовленных основным алгоритмом данных.
#
'''
Created on 05.12.2011

@author: pilat
'''
import datetime as dt
from os import stat
import sys, pickle
from numpy import median, diff
import dbModel as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Date, DateTime, Boolean, Float, Column, Integer, String, Table
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

## Класс, в методах которого реализованны необходимые обращения к БД.
#
#
class Mysql_writer:
    ## Конструктор
    #
    #  Загрузка настроек БД, подключение к БД, создание словарей тегов по
    #  которым следует различать файлы .dat, устанавливается коэффициент для
    #  перевода единиц АЦП в милливольты.
    def __init__(self):
        self.variables_global()
        self.dbConnect()
        self.rTagDict={"reox":"реоксигенация"
                       , "отмывка":"отмывка"
                       , "n2":"гипоксия"
                       , "epi":"эпилепт"
                       , "эпилепт":"эпилепт"
                       , "воздействие":"воздействие"
                       , "infl":"воздействие"
                       , "реокс":"реоксигенация"
                       , "гипокс":"гипоксия"
                       , "коф":"инкубация"
                       , "КОФ":"инкубация"
                       , "ФИЗ":"инкубация"
                       , "физ":"инкубация"
                       , "тета":"тетанизация"
                       , "инк":"инкубация"
                       , "teta":"тетанизация"}  # по ключевым словам в имени файлов устанавливать теги на записи о файле в БД.
        self.rTagMask = ["до", "перед", "макс"]  # Не устанавливать тэг, если в названии файла присутствуют эти слова
        self.koef = 1  # Коэффициент перевода делений АЦП в миливольты. По умолчанию 1, поскольку его изменение потребует переобучение нейронных сетей.
        self.responsNumber = 0
        self.filePath = ''
        self.responslength = 0
        self.numberofspikes = 0
        self.ampl = 0
        self.number = 0
        self.dbServerIp = 'localhost'
        self.userName = 'filteruser_local'
        self.userPassword = 'filter123'
        self.dbName = 'filterdb'
        self.time = 0

    ## Заполнение специфичных для эксперимента настроек
    #
    #  @param filePath Путь к файлу .dat
    #  @param tagString Строка с перечислением через запятую тэгов, которые экспериментатор указал во время запуска расчета.
    def loadExpInfo(self, filePath, tagString):
        self.filePath = filePath
        self.tagString = tagString
        self.date= dt.date.fromtimestamp(stat(filePath).st_mtime)
        print("loadExpInfo # Имя файла: {0}, строка тэгов: {1}, дата: {2}".format(self.filePath, self.tagString, self.date))

    ## Запись в БД тегов эксперимента и связывание тегов с экспериментом
    def tagWriter(self):
        tagList= self.tagString.split(',')
        print("tagWriter # tagList: {0}".format(tagList))
        if tagList:
            exp = self.session.query(db.Experiment).filter(db.Experiment.id == self.idExperiment).one()
            print("tagWriter # exp.id: {0}".format(exp.id))
            for i in tagList:
                print("tagWriter # Обрабатываем тэг {0}".format(i))
                tagInst = self.tagCheck(i, 'expTag')
                print("tagWriter # tagInst {0}".format(tagInst))
                exp.tag.append(tagInst)

    ## Функция возвращает id тэга, если такого тега нет, то предварительно создает его.
    #
    # @param tag Тэг, строковый тип.
    # @param table Название таблицы с тегами
    def tagCheck(self, tag, table):
        if table == 'expTag':
            tagExist = self.session.query(db.expTag).filter(db.expTag.name == tag).first()
            if not tagExist:
                print("there are no '{0}' tag. {1}".format(tag, sys.exc_info()))
                tagExist = db.expTag(tag)
                self.session.add(tagExist)
                self.session.commit()
        else:
            tagExist = self.session.query(db.recTag).filter(db.recTag.name == tag).first()
            if not tagExist:
                print("there are no '{0}' tag. {1}".format(tag, sys.exc_info()))
                tagExist = db.recTag(tag)
                self.session.add(tagExist)
                self.session.commit()
        return tagExist

    ## Загрузка настроек подключения к БД
    #
    # Из файла "dbConfig" загружаются адрес БД, имя ДБ, имя пользователя ДБ,
    # пароль пользователя ДБ.
    # Если файл не найден, загружается умолчательные значения.
    #
    #
    def variables_global(self):
        try:
            with open("dbConfig",'r') as fd:
                dbAccessVars = pickle.load(fd)
            self.dbServerIp = dbAccessVars[0]
            self.userName = dbAccessVars[2]
            self.userPassword = dbAccessVars[3]
            self.dbName = dbAccessVars[1]
        except:
            print("Load default database config")

    ## Загрузка значений переменных для записи в БД проанализированной информации.
    #
    # Осуществляется из реквизитов переданного процедуре объекта.
    # Предполагается что объект - представитель класса ...
    #
    def variables_local(self, tmpObject):
        self.responsNumber = tmpObject.responsNumber
        self.numberofspikes = tmpObject.allSpikes
        self.responslength = tmpObject.responseEnd - tmpObject.responseStart
        self.ampl = tmpObject.spikeAmpl
        self.number = tmpObject.spikeNumber

    ## Подключение к БД.
    #
    #  Необходимые настройки получаем из предварительно заполненных реквизитов
    #  класса.
    #
    def dbConnect(self):
        try:
            Session = db.createSession()
            self.session = Session()

        except:
            print("Db connect error: {0}. Exit!".format(sys.exc_info()))
            sys.exit(1)

    ## Сохранение информации об эксперименте.
    #
    #  Имя эксперимента получаем из имени папки содержащей обрабатываемый .dat файл.
    #  Дату с даты модификации первого попавшегося .dat файла в этой папке.
    #
    def dbWriteExperiment(self):
        experimentName = str(self.filePath.split('/')[-2])
        newExp = db.Experiment(experimentName, self.date)
        self.session.add(newExp)
        self.session.commit()
        self.idExperiment = newExp.id
        print("dbWriteExperiment # Создана запись в таблице Experiment, id={0}".format(self.idExperiment))

    ## Сохранение информации об отдельной записи (один .dat файл)
    #
    #  Сохраняется время модификации файла, имя файла, связь с экспериментом.
    #  В реквизит idRecord сохраняется id созданной записи.
    #
    def dbWriteRecord(self):
        fileName = self.filePath.split('/')[-1]
        newRecord = db.Record(self.idExperiment, fileName, self.time)
        self.session.add(newRecord)
        self.session.commit()
        self.idRecord = newRecord.id
        print("dbWriteRecord # Создана запись в таблице record, id={0}".format(self.idRecord))

    ## Добавление исходных данных в БД
    #
    #  в таблицу Record добавляем исходные данные: массив и частоту
    #
    def addSource(self, freq, data):
        record = self.session.query(db.Record).filter(db.Record.id == self.idRecord).one()
        record.source = data
        record.frequency = freq
        self.session.add(record)
        self.session.commit()

    ## Поиск в имени файла ключевых слов
    #
    #  Используется для того чтобы определить к какому этапу эксперимента
    #  относится анализируемая запись. Для работу требуется чтобы в имени файла
    #  было ключевое слово, позволяющее отнести запись к этапу эксперимента.
    #  @param tagString Название файла.
    #  @param tagDict Словарь разрешенных ключевых слов.
    #  @param tagMask Список запрещенных ключевых слов.
    #
    def findTags(self, tagString, tagDict, tagMask):
        tagList=[]
        for i in tagDict.keys():
            if (i in tagString) and (all([j not in tagString for j in tagMask])):
                tagList.append(tagDict[i])
        return tagList

    ## Получение полного списка проанализированных экспериментов.
    #
    #  Возвращает список всех проанализированных экспериментов и их id
    #
    def getExpNames(self):
        namesList = self.session.query(db.Experiment.name, db.Experiment.id).all()
        return namesList

    ## Получение таблицы с амплитудами спайков одного эксперимента для экспорта в файл
    def getDataToExport(self, _idExp, _spikeNum):
        exportData = self.session.query(db.Experiment.name,\
                                        db.Record.filename,\
                                        db.Response.number,\
                                        db.Record.time,\
                                        db.Spike.ampl).\
                                    filter(db.Spike.response==db.Response.id,\
                                           db.Response.record==db.Record.id,\
                                           db.Record.experiment==db.Experiment.id,\
                                           db.Response.number == 1,\
                                           db.Experiment.id == _idExp,\
                                           db.Spike.number == _spikeNum).\
                                    order_by(db.Record.time)
        print("getDataToExport # _idExp={0}, _spikeNum={1}, exportData.count()={2}".format(_idExp, _spikeNum, exportData.count()))
        return exportData.all()

    ## Сохранение тегов для этапов эксперимента и их связей с анализируемым файлом.
    #
    #  @param filename Имя анализируемого .dat файла.
    #
    def dbWriteRecordTags(self, filename):
        tagList = self.findTags(filename, (self.rTagDict), (self.rTagMask))
        if not tagList:
            tagList = ["-"]
        print("dbWriteRecordTags # tagList: {0}".format(tagList))
        rec = self.session.query(db.Record).filter(db.Record.id == self.idRecord).one()
        for i in tagList:
            rec.tag.append(db.recTag(i))
            #tagId = self.tagCheck(i, "recordTags", "idrecordTags")

    ## Сохранение информации о группе спайков в ответ на одиночный стимул
    #
    #  @param tmpObject Экземпляр класса Response
    #
    def dbWriteResponse(self, tmpObject):
        rNumber = tmpObject.responsNumber
        epsp = tmpObject.epsp*self.koef
        nOfSpikes = len(tmpObject.spikes)
        rLength = tmpObject.length
        epspArea = tmpObject.epspArea
        epspFront = tmpObject.epspFront
        epspBack = tmpObject.epspBack
        epilept = tmpObject.epspEpileptStd
        newRespons = db.Response(self.idRecord, rNumber, nOfSpikes, rLength,
                                  epsp, epspFront, epspBack, epilept)
        self.session.add(newRespons)
        self.session.commit()
        self.idResponse = newRespons.id
        print("dbWriteResponse # Создана запись в таблице response, id={0}".format(self.idResponse))

    ## Обновляет информацию о количестве групп спайков в записи
    #
    #  Запись об анализируемом файле создается еще до самого анализа, поэтому
    #  когда количество групп спайков определено, эта информация добавляется к
    #  записи о файле.
    #
    def dbWriteNumberOfResponses(self, number):
        record = self.session.query(db.Record).filter(db.Record.id == self.idRecord).one()
        record.numberofresponses = number
        self.session.add(record)

    ## Сохранение служебной информации о характере обрабатываемого сигнала
    #
    #  Используется для развития алгоритма обработки.
    #  Следует расширить данную таблицу и сохранять в неё всю возможную
    #  информацию о проводимом анализе.
    #
    #def dbWriteSignalProperties(self, ptp_, snr_, std_, mainLevel):
    #    newSigProp = db.SignalProp(snr_, std_, ptp_, mainLevel, self.idRecord )
    #    self.session.add(newSigProp)
    #    self.session.commit()

    ## Сохранение уровня возникшей в процессе выполнения анализа ошибки.
    #
    #  @param soft 1 - была не критическая ошибка, иначе 0
    #  @param hard 1 - была критическая ошибка, иначе 0
    #
    def dbWriteError(self, soft, hard):
        record = self.session.query(db.Record).filter(db.Record.id == self.idRecord).one()
        record.softError = soft
        record.hardError = hard
        self.session.add(record)

    ## Сохранение информации о спайке
    #
    #  @param tmpObject Экземпляр класса Spike
    #
    def dbWriteSpike(self, tmpObject):
        ampl = tmpObject.spikeAmpl*self.koef
        number = tmpObject.spikeNumber
        sLength = tmpObject.spikeLength  # must be changed to length at 80% or something like that
        maxdiff = (tmpObject.spikeMax2Val-tmpObject.spikeMax1Val)*self.koef
        angle1 = tmpObject.spikeFront
        angle2 = tmpObject.spikeBack
        delay = tmpObject.spikeDelay
        maxToMin = tmpObject.spikeMaxToMin*self.koef
        area = tmpObject.area
        fibre = tmpObject.fibre
        manual = tmpObject.manual

        newSpike = db.Spike(self.idResponse, ampl, number, sLength, maxdiff,
                            angle1, angle2, delay, maxToMin, area, fibre, manual)
        self.session.add(newSpike)

    ## Удаление эксперимента
    #
    # Удаление эксперимента целиком или очистка ответов и спайков
    def deleteExp(self, id, complete = True):
        exp = self.session.query(db.Experiment).filter(db.Experiment.id == id).first()
        if complete:
            self.session.delete(exp)
        else:
            responses = self.session.query(db.Response).filter(db.Response.record == db.Record.id, db.Record.experiment == id).all()
            for i in responses:
                self.session.delete(i)
        self.session.commit()


    ## Сделать коммит в БД
    def dbCommit(self):
        self.session.commit()

    ## Отключение от БД
    def dbDisconnect(self):
        self.session.close()

    ## Создаем запись в которую по ходу алгоритма записываем значения переменных и коефициентов
    def dbWriteTechInfo(self, frame, stimDur):
        tech = db.TechInfo(self.idRecord, frame, stimDur)
        self.session.add(tech)
        self.session.commit()
        self.idTech = tech.id

    ## Добавляем в техИнфо значения переменных для поиска стимулов
    def dbTechInfo_stim(self, p2s, treshold):
        tech = self.session.query(db.TechInfo).filter(db.TechInfo.id == self.idTech).one()
        tech.pwr2Std = p2s
        tech.treshold = treshold
        self.session.add(tech)

    ## Добавляем в техИнфо значения главного уровня вейвлет разложения и характеристики сигнала до фильтрации
    def dbTechInfo_level(self, _snr, _ptp, _std, mainLevel):
        tech = self.session.query(db.TechInfo).filter(db.TechInfo.id == self.idTech).one()
        tech.snr = _snr
        tech.ptp = _ptp
        tech.std = _std
        tech.mainLevel = mainLevel
        self.session.add(tech)

    ## Добавляем в техИнфо значения переменных для определения спайков
    def dbTechInfo_clean(self, _std, SD):
        tech = self.session.query(db.TechInfo).filter(db.TechInfo.id == self.idTech).one()
        tech.clean_std = _std
        tech.SD = SD
        self.session.add(tech)
        self.session.commit()

    ## Добавляем информацию о фильтрации уровня вейвлет разложения
    def dbWaveLevel_write(self, smooth, level, minSD, maxSD, smoothCoef):
        wLevel = db.WaveLevel(self.idTech, smooth, level, minSD, maxSD, smoothCoef)
        self.session.add(wLevel)

    ## Сохраняем информацию для поиска стимулов
    def dbStimProp_write(self, number, length, ptp_1, ptp_2, std_1, std_2, median_1, median_2, mean_1, mean_2, median_diff_1, median_diff_2, std_diff, ptp_diff, stim, auto):
        stim = db.StimProp(number, length, ptp_1, ptp_2, std_1, std_2, median_1, median_2, mean_1, mean_2, median_diff_1, median_diff_2, std_diff, ptp_diff, stim, auto, self.idTech)
        self.session.add(stim)

    ## Сохранение информации о характеристиках стимула
    #
    #  Используется для обучения нейронной сети отличать шум от стимулов.
    #
    #def dbWriteStim(self, base_sample, sample, length, number, status, freq, sampleStdDiff, samplePtpDiff):
    #    try:
    #        length = str(length*100000.0/freq)
    #        try:
    #            ptp = str(sample.ptp()*0.1)
    #        except:
    #            ptp = str(0)
    #        try:
    #            base_ptp = str(base_sample.ptp()*0.1)
    #        except:
    #            base_ptp = str(0)
    #        std = str(sample.std())
    #        median1 = str(median(sample)*0.1)
    #        mean = str(sample.mean()*0.1)
    #        base_mean = str(base_sample.mean()*0.1)
    #        base_median = str(median(base_sample)*0.1)
    #        base_std = str(base_sample.std())
    #        number = str(number)
    #        diff_median = str(median(diff(sample*1.0)))
    #        base_diff_median = str(median(diff(base_sample*1.0)))
    #    except:
    #        print("Unexpected error wile dbWriteStim configuration: {0}".format(sys.exc_info()))
    #    cursor = self.conn.cursor()
    #    try:
    #        cursor.execute("INSERT INTO stimProperties(length, ptp, base_ptp,\
    #                       std, median, mean, base_mean, base_median,\
    #                       base_std,\
    #                       number, status, diff_median, base_diff_median,\
    #                       sampleStdDiff, samplePtpDiff)\
    #                       VALUES({0},{1},{2},{3},\
    #                       {4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14});\
    #                       ".format(length, ptp, base_ptp, std, median1, mean,
    #                       base_mean, base_median, base_std, number, status,
    #                       diff_median, base_diff_median, sampleStdDiff, samplePtpDiff))
    #    except:
    #        print("Unexpected error wile dbWriteStim in dbAccess:", sys.exc_info())
    #    self.conn.commit()
    #    cursor.close()
