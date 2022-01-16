import sys
import pickle, codecs

from PyQt5 import QtCore, QtGui, QtWidgets

from main.simple import Ui_MainWindow
from main.workFlow_lib import workFlow
from main.dbAccess_lib_2 import DB_writer
import main.InOut_lib as ioLib

class MyForm(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.db = DB_writer("postgresql", self.ui.dbUserLine.text(), self.ui.dbPassLine.text(), self.ui.dbServerIpLine.text(), self.ui.dbNameLine.text())
        self.fsmodel = QtWidgets.QFileSystemModel()
        self.stmodel = QtGui.QStandardItemModel()
        self.root_index = self.fsmodel.setRootPath(self.ui.pathLine.text())
        self.ui.sourceList.doubleClicked[QtCore.QModelIndex].connect(\
         self.sourceListClicked)
        self.ui.pathLine.editingFinished.connect(self.show_path)
        self.ui.fEPSP_button.clicked.connect(self.fEPSP_start)
        self.ui.upButton.clicked.connect(self.pathUp)
        self.ui.clearDbButton.clicked.connect(self.rmDbConfig)
        self.ui.saveDbButton.clicked.connect(self.mkDbConfig)
        self.ui.exportRefresh.clicked.connect(self.expNameUpdate)
        self.ui.expToDeleteRefresh.clicked.connect(self.delNameUpdate)
        self.ui.exportButton.clicked.connect(self.export)
        self.ui.Delete.clicked.connect(self.deleteExp)

        sourceList = self.ui.sourceList
        sourceList.setModel(self.fsmodel)
        sourceList.setRootIndex(self.root_index)
        sourceList.show()
        self.loadConfig()

    def rmDbConfig(self):
        print("this function has not implemented yet")

    def mkDbConfig(self):
        with open("./main/dbConfig",'wb') as fd:
            tmpList=[str(self.ui.dbServerIpLine.text()), str(self.ui.dbNameLine.text()), str(self.ui.dbUserLine.text()), str(self.ui.dbPassLine.text())]
            pickle.dump(tmpList, fd)

    def loadConfig(self):
        try:
            with open("./main/dbConfig",'rb') as fd:
                dbAccessVars = pickle.load(fd)
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
                   ,"dbConf":{"dbType":"postgresql"
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
    app = QtWidgets.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())
