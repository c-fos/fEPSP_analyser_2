## @package dbModel Модуль описания структуры БД
# на самом деле не помню что это за файл,
# видимо служебный для сбора в БД информации о работе самой программы
# и для последующей доработки на основе этих данных
# нигде сейчас не используется, но может содержать полезный код
'''
Created on 21.11.2013

@author: Ilya Malakhin (pilat1988@gmail.com)
'''
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Date, Time, Boolean, Float, Column,Integer, String, Table, PickleType
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

## Определяем необходимые глобальные переменные
Base = declarative_base()
## Настраиваем подключение к БД
engine = create_engine('mysql://fepsp_user:filter123@localhost/fepsp_db')

## Создаем дескриптор сессии
def createSession():
    return sessionmaker(bind=engine)

## Промежуточная таблица обеспечивающая связь many-to-many между экспериментами и тэгами
experiment_tag = Table('experiment_tag', Base.metadata,
    Column('experiment_id', Integer, ForeignKey('experiment.id')),
    Column('tag_id', Integer, ForeignKey('exptag.id')),
    mysql_engine='InnoDB',
    mysql_charset='utf8'   )

## Промежуточная таблица обеспечивающая связь many-to-many между записями и тэгами
record_tag = Table('record_tag', Base.metadata,
    Column('record_id', Integer, ForeignKey('record.id')),
    Column('tag_id', Integer, ForeignKey('rectag.id')),
    mysql_engine='InnoDB',
    mysql_charset='utf8')

## Таблица тэгов для описания эксперимента
class expTag(Base):
    __tablename__ = 'exptag'
    __table_args__ = {'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(String(40))  # Тэг
    desc = Column(String(1000))  # Описание тэга

    def __init__(self, name, desc = "Without description"):
        self.name = name
        self.desc = desc

## Таблица тэгов для описания записи
class recTag(Base):
    __tablename__ = 'rectag'
    __table_args__ = {'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(String(40))  # Тэг
    desc = Column(String(1000))  # Описание тэга

    def __init__(self, name, desc = "Without description"):
        self.name = name
        self.desc = desc

## Таблица для описания эксперимента
class Experiment(Base):
    __tablename__ = 'experiment'
    __table_args__ = {'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    name = Column(String(200))  # Имя эксперимента
    date = Column(Date)  # Дата эксперимента
    mask = Column(Boolean)  # Исключить эксперимент из расчета
    tag = relationship(expTag, secondary=experiment_tag, backref=backref('experiment', cascade="all, delete"))

    def __init__(self, name, date, mask = 0):
        self.name = name
        self.date = date
        self.mask = mask

## Таблица для описания записи
class Record(Base):
    __tablename__ = 'record'
    __table_args__ = {'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    experiment = Column(Integer, ForeignKey('experiment.id'))
    exp_rel = relationship(Experiment, backref=backref('record', cascade='all, delete,all, delete-orphan'))
    filename = Column(String(200))
    time = Column(Time)
    frequency = Column(Integer)
    source = Column(PickleType)
    numberofresponses = Column(Integer)
    hardError = Column(Boolean)
    softError = Column(Boolean)
    tag = relationship(recTag, secondary=record_tag, backref=backref('record',cascade='all, delete'))

    def __init__(self, exp, name, time, numOfResp = 0, hError = False, sError = False):
        self.experiment = exp
        self.filename = name
        self.time = time
        self.numberofresponses = numOfResp
        self.hardError = hError
        self.softError = sError

## Таблица для описания служебной ниформации использованой при анализе
#
#  В таблице хранятся значения переменных и коеффициентов использовынных при
#  анализе в привязке к записям
#
class TechInfo(Base):
    __tablename__ = 'techInfo'
    __table_args__ = {'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    defFrame = Column(Integer)
    stimDuration = Column(Integer)
    mainLevel = Column(Integer)
    pwr2Std = Column(Float)
    treshold = Column(Float)
    std = Column(Float)
    clean_std = Column(Float)
    SD = Column(Float)
    snr = Column(Float)
    ptp = Column(Float)

    record = Column(Integer, ForeignKey('record.id'))
    record_rel = relationship(Record, uselist=False,
                              backref=backref("techInfo",
                                              cascade="all, delete,all, delete-orphan"))

    def __init__(self,record, defFrame, stimDuration):
        self.record = record
        self.defFrame = defFrame
        self.stimDuration = stimDuration

## Таблица для описания характеристик электрических стимулов( или шумов)
#  Используется для обучения нейронной сети. данные хранятся в привязке к
#  записи.
class StimProp(Base):
    __tablename__ = 'stimProp'
    __table_args__ = {'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    length = Column(Float)
    ptp_1 = Column(Float)
    ptp_2 = Column(Float)
    std_1 = Column(Float)
    std_2 = Column(Float)
    median_1 = Column(Float)
    median_2 = Column(Float)
    mean_1 = Column(Float)
    mean_2 = Column(Float)
    median_diff_1 = Column(Float)
    median_diff_2 = Column(Float)
    std_diff = Column(Float)
    ptp_diff = Column(Float)
    stim = Column(Boolean)
    auto = Column(Boolean)
    techInfo = Column(Integer, ForeignKey('techInfo.id'))
    techInfo_rel = relationship(TechInfo, backref=backref("stimProp",
                                                          cascade="all, delete,all, delete-orphan"))

    def __init__(self, number, length, ptp_1, ptp_2, std_1, std_2, median_1,
                 median_2, mean_1, mean_2, median_diff_1, median_diff_2,
                 std_diff, ptp_diff, stim, auto, techInfo):
        self.number = number
        self.length = length
        self.ptp_1 = ptp_1
        self.ptp_2 = ptp_2
        self.std_1 = std_1
        self.std_2 = std_2
        self.median_1 = median_1
        self.median_2 = median_2
        self.mean_1 = mean_1
        self.mean_2 = mean_2
        self.median_diff_1 = median_diff_1
        self.median_diff_2 = median_diff_2
        self.std_diff = std_diff
        self.ptp_diff = ptp_diff
        self.stim = stim
        self.auto = auto
        self.techInfo = techInfo

## Таблица для описания характеристик фильтров отдельных уровней вейвлет разложения
#
#  Используется для совершенствования алгоритма. данные хранятся в привязке в
#  записи.
class WaveLevel(Base):
    __tablename__ = 'waveLevel'
    __table_args__ = {'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    level = Column(Integer)
    minSD = Column(Float)
    maxSD = Column(Float)
    smoothCoef = Column(Float)
    smooth = Column(Integer)

    techInfo = Column(Integer, ForeignKey('techInfo.id'))
    techInfo_rel = relationship(TechInfo, uselist=False,
                                backref=backref("waveLevel",
                                                cascade="all, delete,all, delete-orphan"))

    def __init__(self, tech, smooth, level, minSD, maxSD, smoothCoef):
        self.techInfo = tech
        self.level = level
        self.minSD = minSD
        self.maxSD = maxSD
        self.smooth = smooth
        self.smoothCoef = smoothCoef



## Таблица для описания группы спайков в ответ на один стимул
class Response(Base):
    __tablename__ = 'response'
    __table_args__ = {'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    record = Column(Integer, ForeignKey('record.id'))
    record_rel = relationship(Record, backref=backref("response",
                                                      cascade="all, delete,all, delete-orphan"))
    number = Column(Integer)
    numberofspikes = Column(Integer)
    length = Column(Float)
    epsp = Column(Float)
    epspFront = Column(Float)
    epspBack = Column(Float)
    epileptStd = Column(Float)

    def __init__(self, record, number, numofspikes, length, epsp, epspFront, epspBack, epilept):
        self.record = record
        self.number = number
        self.numberofspikes = numofspikes
        self.length = length
        self.epsp = epsp
        self.epspFront = epspFront
        self.epspBack = epspBack
        self.epileptStd = epilept


## Таблица для описания отдельного спайка
class Spike(Base):
    __tablename__ = 'spike'
    __table_args__ = {'mysql_charset': 'utf8', 'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    response = Column(Integer, ForeignKey('response.id'))
    response_rel = relationship(Response, backref=backref("spike",
                                                          cascade="all, delete,all, delete-orphan"))
    ampl = Column(Float)
    number = Column(Integer)
    length = Column(Float)
    maxDiff = Column(Float)
    angle1 = Column(Float)
    angle2 = Column(Float)
    delay = Column(Float)
    maxtomin = Column(Float)
    area = Column(Float)
    fibre = Column(Boolean)
    manual = Column(Boolean)

    def __init__(self, response, ampl, number, length, maxDiff, angle1, angle2,
                 delay, maxtomin, area, fibre, manual):
        self.response = response
        self.ampl = ampl
        self.number = number
        self.length = length
        self.maxDiff = maxDiff
        self.angle1 = angle1
        self.angle2 = angle2
        self.delay = delay
        self.maxtomin = maxtomin
        self.area = area
        self.fibre = fibre
        self.manual = manual

## Служебная операция создающая таблицы в пустой БД
#  Не имеет интерфейса из программы, запускается вручную непосредственно из
#  интерпритатора.
def createDB():
    Base.metadata.create_all(engine)

## Служебная операция полного удаления Таблиц со всей информацией из БД.
#  Не имеет интерфейса из программы, запускается вручную непосредственно из
#  интерпритатора.
def dropAll():
    Base.metadata.drop_all(engine)

