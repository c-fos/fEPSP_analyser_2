# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtCore, QtGui
from simple import Ui_MainWindow
from workFlow_lib import workFlow
from dbAccess_lib_2 import Mysql_writer
import pickle, codecs
import InOut_lib as ioLib

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class MyForm(QtGui.QMainWindow):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.db = Mysql_writer("mysql", self.ui.dbUserLine.text(), self.ui.dbPassLine.text(), self.ui.dbServerIpLine.text(), self.ui.dbNameLine.text())
        self.fsmodel = QtGui.QFileSystemModel()
        self.stmodel = QtGui.QStandardItemModel()
        self.root_index = self.fsmodel.setRootPath(self.ui.pathLine.text())
        QtCore.QObject.connect(self.ui.sourceList, QtCore.SIGNAL(_fromUtf8("doubleClicked(QModelIndex)")),\
         self.sourceListClicked)
        QtCore.QObject.connect(self.ui.pathLine, QtCore.SIGNAL(_fromUtf8("editingFinished()")),\
                 self.show_path)
        QtCore.QObject.connect(self.ui.fEPSP_button, QtCore.SIGNAL(_fromUtf8("clicked()")),\
                 self.fEPSP_start)
        QtCore.QObject.connect(self.ui.upButton, QtCore.SIGNAL(_fromUtf8("clicked()")),\
                 self.pathUp)
        QtCore.QObject.connect(self.ui.clearDbButton, QtCore.SIGNAL(_fromUtf8("clicked()")),\
                 self.rmDbConfig)
        QtCore.QObject.connect(self.ui.saveDbButton, QtCore.SIGNAL(_fromUtf8("clicked()")),\
                 self.mkDbConfig)
        QtCore.QObject.connect(self.ui.exportRefresh, QtCore.SIGNAL(_fromUtf8("clicked()")),\
                 self.expNameUpdate)
        QtCore.QObject.connect(self.ui.expToDeleteRefresh, QtCore.SIGNAL(_fromUtf8("clicked()")),\
                 self.delNameUpdate)
        QtCore.QObject.connect(self.ui.exportButton, QtCore.SIGNAL(_fromUtf8("clicked()")),\
                 self.export)
        QtCore.QObject.connect(self.ui.Delete, QtCore.SIGNAL(_fromUtf8("clicked()")),\
                 self.deleteExp)

        sourceList = self.ui.sourceList
        sourceList.setModel(self.fsmodel)
        sourceList.setRootIndex(self.root_index)
        sourceList.show()
        self.loadConfig()

    def rmDbConfig(self):
        print("this function has not implemented yet")

    def mkDbConfig(self):
        fd = open("dbConfig",'w')
        tmpList=[str(self.ui.dbServerIpLine.text()), str(self.ui.dbNameLine.text()), str(self.ui.dbUserLine.text()), str(self.ui.dbPassLine.text())]
        pickle.dump(tmpList, fd)
        fd.close()

    def loadConfig(self):
        try:
            fd = open("dbConfig",'r')
            dbAccessVars = pickle.load(fd)
            fd.close()
            self.ui.dbServerIpLine.setText(dbAccessVars[0])
            self.ui.dbNameLine.setText(dbAccessVars[1])
            self.ui.dbUserLine.setText(dbAccessVars[2])
            self.ui.dbPassLine.setText(dbAccessVars[3])
        except:
            pass

    def fEPSP_start(self):
        path = str(self.ui.pathLine.text())
        frequency = str(self.ui.frequency_line.text())
        substance = str(self.ui.substance_line.text())
        smooth = self.ui.smoothBox.value()
        if self.ui.debugBox.isChecked():
            debug = True
        else:
            debug = False
        if self.ui.database_checkBox.isChecked():
            write = True
        else:
            write = False
        if self.ui.manualFibreSearchBox.isChecked():
            manual = True
        else:
            manual = False
        argDict = {"input":path
                   ,"frequ":frequency
                   ,"smooth":smooth
                   ,"imgPath":path
                   ,"write":write
                   ,"tags":substance
                   ,"manual":manual
                   ,"debug":debug
                   ,"dbConf":{"dbType":"mysql"
                             ,"dbUser":self.ui.dbUserLine.text()
                             ,"dbPass":self.ui.dbPassLine.text()
                             ,"dbAdress":self.ui.dbServerIpLine.text()
                             ,"dbScheme":self.ui.dbNameLine.text()}}
        if debug=="1":
            print(argDict)
        workFlow(argDict)

    def show_path(self):
        path = self.ui.pathLine.text()#QtGui.QDesktopServices.storageLocati$
        print(path)
        self.root_index = self.fsmodel.setRootPath(path)
        self.ui.sourceList.setRootIndex(self.root_index)
        self.ui.sourceList.update()

    def pathUp(self):
        path = self.ui.pathLine.text()#QtGui.QDesktopServices.storageLocati$
        print(path)
        index = self.fsmodel.setRootPath(path)
        newPathIndex = self.fsmodel.parent(index)
        newPath = self.fsmodel.filePath(newPathIndex)
        self.ui.sourceList.setRootIndex(newPathIndex)
        self.ui.pathLine.setText(newPath)

    def sourceListClicked(self):
        curIndex = self.ui.sourceList.currentIndex()
        if self.fsmodel.isDir(curIndex):
            self.ui.pathLine.setText(self.fsmodel.filePath(curIndex))
            self.ui.sourceList.setRootIndex(curIndex)

    def getNames(self):
        expList = self.db.getExpNames()
        return expList

    def getExport(self, idExp, spikeNum):
        data = self.db.getDataToExport(idExp, spikeNum)
        return data

    def expNameUpdate(self):
        self.expNames = self.getNames()
        self.ui.exportExpName.clear()
        for line in self.expNames:
            print(line)
            self.ui.exportExpName.addItem(list(line)[0])

    def delNameUpdate(self):
        self.delNames = self.getNames()
        self.ui.expToDelete.clear()
        for line in self.delNames:
            print(line)
            self.ui.expToDelete.addItem(list(line)[0])

    def exportFileNameUpdate(self):
        name = "./exportFiles/{0}_spike-{1}.csv".format(self.ui.exportExpName.curentText(), self.ui.exportSpike.value())
        self.ui.exportFilename.text(name)

    def deleteExp(self):
        id =  self.delNames[self.ui.expToDelete.currentIndex()][1]
        delAll = self.ui.delComplete.isChecked()
        self.db.deleteExp(id, delAll)

    def export(self):
        id = self.expNames[self.ui.exportExpName.currentIndex()][1]
        print(id)
        spike = self.ui.exportSpike.value()
        print(spike)
        data = self.getExport(id, spike)
        fileName = self.ui.exportFilename.text()
        print(fileName)
        ioLib.writeExport(fileName, data)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())
