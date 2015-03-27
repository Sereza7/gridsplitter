# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gridSplitter_dialog_base.ui'
#
# Created: Fri Mar 27 14:45:40 2015
#      by: PyQt4 UI code generator 4.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_gridSplicerDialogBase(object):
    def setupUi(self, gridSplicerDialogBase):
        gridSplicerDialogBase.setObjectName(_fromUtf8("gridSplicerDialogBase"))
        gridSplicerDialogBase.resize(558, 545)
        self.button_box = QtGui.QDialogButtonBox(gridSplicerDialogBase)
        self.button_box.setGeometry(QtCore.QRect(210, 490, 341, 32))
        self.button_box.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.button_box.setObjectName(_fromUtf8("button_box"))
        self.tabWidget = QtGui.QTabWidget(gridSplicerDialogBase)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 551, 481))
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.layoutWidget = QtGui.QWidget(self.tab)
        self.layoutWidget.setGeometry(QtCore.QRect(20, 40, 501, 381))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.gridLayout = QtGui.QGridLayout(self.layoutWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.splicesXSpinBox = gui.QgsSpinBox(self.layoutWidget)
        self.splicesXSpinBox.setMinimum(1)
        self.splicesXSpinBox.setMaximum(9999)
        self.splicesXSpinBox.setProperty("value", 5)
        self.splicesXSpinBox.setObjectName(_fromUtf8("splicesXSpinBox"))
        self.gridLayout.addWidget(self.splicesXSpinBox, 3, 3, 1, 1)
        self.label_6 = QtGui.QLabel(self.layoutWidget)
        self.label_6.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout.addWidget(self.label_6, 5, 0, 1, 1)
        self.label_3 = QtGui.QLabel(self.layoutWidget)
        self.label_3.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.splicesYSpinBox = gui.QgsSpinBox(self.layoutWidget)
        self.splicesYSpinBox.setMinimum(1)
        self.splicesYSpinBox.setMaximum(9999)
        self.splicesYSpinBox.setProperty("value", 5)
        self.splicesYSpinBox.setObjectName(_fromUtf8("splicesYSpinBox"))
        self.gridLayout.addWidget(self.splicesYSpinBox, 4, 3, 1, 1)
        self.label_7 = QtGui.QLabel(self.layoutWidget)
        self.label_7.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.gridLayout.addWidget(self.label_7, 8, 0, 1, 1)
        self.cmdBrowseOutput = QtGui.QPushButton(self.layoutWidget)
        self.cmdBrowseOutput.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.cmdBrowseOutput.setObjectName(_fromUtf8("cmdBrowseOutput"))
        self.gridLayout.addWidget(self.cmdBrowseOutput, 5, 3, 1, 1)
        self.cmdBrowsetmp = QtGui.QPushButton(self.layoutWidget)
        self.cmdBrowsetmp.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.cmdBrowsetmp.setObjectName(_fromUtf8("cmdBrowsetmp"))
        self.gridLayout.addWidget(self.cmdBrowsetmp, 8, 3, 1, 1)
        self.OuptDir = QtGui.QLineEdit(self.layoutWidget)
        self.OuptDir.setObjectName(_fromUtf8("OuptDir"))
        self.gridLayout.addWidget(self.OuptDir, 5, 1, 1, 1)
        self.tempFile = QtGui.QLineEdit(self.layoutWidget)
        self.tempFile.setObjectName(_fromUtf8("tempFile"))
        self.gridLayout.addWidget(self.tempFile, 8, 1, 1, 1)
        self.inputRasterBox = gui.QgsMapLayerComboBox(self.layoutWidget)
        self.inputRasterBox.setFrame(True)
        self.inputRasterBox.setObjectName(_fromUtf8("inputRasterBox"))
        self.gridLayout.addWidget(self.inputRasterBox, 0, 1, 1, 1)
        self.label_4 = QtGui.QLabel(self.layoutWidget)
        self.label_4.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 3, 1, 1, 1)
        self.label_5 = QtGui.QLabel(self.layoutWidget)
        self.label_5.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 4, 1, 1, 1)
        self.prefixx = QtGui.QLineEdit(self.layoutWidget)
        self.prefixx.setObjectName(_fromUtf8("prefixx"))
        self.gridLayout.addWidget(self.prefixx, 6, 1, 1, 1)
        self.label_8 = QtGui.QLabel(self.layoutWidget)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.gridLayout.addWidget(self.label_8, 6, 0, 1, 1)
        self.addTiles = QtGui.QCheckBox(self.layoutWidget)
        self.addTiles.setObjectName(_fromUtf8("addTiles"))
        self.gridLayout.addWidget(self.addTiles, 7, 0, 1, 1)
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.label_2 = QtGui.QLabel(self.tab_2)
        self.label_2.setGeometry(QtCore.QRect(60, 430, 391, 16))
        self.label_2.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.layoutWidget1 = QtGui.QWidget(self.tab_2)
        self.layoutWidget1.setGeometry(QtCore.QRect(10, 13, 531, 381))
        self.layoutWidget1.setObjectName(_fromUtf8("layoutWidget1"))
        self.verticalLayout = QtGui.QVBoxLayout(self.layoutWidget1)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.layoutWidget1)
        self.label.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.label.setWordWrap(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.label_9 = QtGui.QLabel(self.layoutWidget1)
        self.label_9.setObjectName(_fromUtf8("label_9"))
        self.verticalLayout.addWidget(self.label_9)
        self.label_10 = QtGui.QLabel(self.layoutWidget1)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.verticalLayout.addWidget(self.label_10)
        self.label_11 = QtGui.QLabel(self.layoutWidget1)
        self.label_11.setWordWrap(True)
        self.label_11.setObjectName(_fromUtf8("label_11"))
        self.verticalLayout.addWidget(self.label_11)
        self.label_12 = QtGui.QLabel(self.layoutWidget1)
        self.label_12.setObjectName(_fromUtf8("label_12"))
        self.verticalLayout.addWidget(self.label_12)
        self.label_13 = QtGui.QLabel(self.layoutWidget1)
        self.label_13.setWordWrap(True)
        self.label_13.setObjectName(_fromUtf8("label_13"))
        self.verticalLayout.addWidget(self.label_13)
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))

        self.retranslateUi(gridSplicerDialogBase)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.button_box, QtCore.SIGNAL(_fromUtf8("accepted()")), gridSplicerDialogBase.accept)
        QtCore.QObject.connect(self.button_box, QtCore.SIGNAL(_fromUtf8("rejected()")), gridSplicerDialogBase.reject)
        QtCore.QMetaObject.connectSlotsByName(gridSplicerDialogBase)

    def retranslateUi(self, gridSplicerDialogBase):
        gridSplicerDialogBase.setWindowTitle(_translate("gridSplicerDialogBase", "Grid Splitter", None))
        self.label_6.setText(_translate("gridSplicerDialogBase", "Output Base Directory", None))
        self.label_3.setText(_translate("gridSplicerDialogBase", "Input Layer:", None))
        self.label_7.setText(_translate("gridSplicerDialogBase", "temporary file", None))
        self.cmdBrowseOutput.setText(_translate("gridSplicerDialogBase", "Browse", None))
        self.cmdBrowsetmp.setText(_translate("gridSplicerDialogBase", "Browse", None))
        self.tempFile.setText(_translate("gridSplicerDialogBase", "/tmp/tempshape.shp", None))
        self.label_4.setText(_translate("gridSplicerDialogBase", "number of tiles in X axis", None))
        self.label_5.setText(_translate("gridSplicerDialogBase", "number of tiles in Y axis", None))
        self.label_8.setText(_translate("gridSplicerDialogBase", "prefix for output files (otional):", None))
        self.addTiles.setText(_translate("gridSplicerDialogBase", "Add tiles to canvas", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("gridSplicerDialogBase", "Parameters", None))
        self.label_2.setText(_translate("gridSplicerDialogBase", "Version 0.2. Please report errors to maximilian.krambach@gmx.de", None))
        self.label.setText(_translate("gridSplicerDialogBase", "gridSplitter cuts your input layer into tilesX * tilesY pieces.\n"
"If it is a raster, it tries to keep the raster\'s resolution to avoid gaps and overlaps.\n"
"If the number of splices and the resolution don\'t match up, it cuts slightly larger tiles, resulting in the last tile having a bit of \"no Data\".\n"
"The output is stored in subdirectories in TIF file format.\n"
"Vector layers will be stored in shapefile format.", None))
        self.label_9.setText(_translate("gridSplicerDialogBase", "Input Layer: The Layer you want to process\n"
"", None))
        self.label_10.setText(_translate("gridSplicerDialogBase", "TilesX, TilesY: The number of tiles you want to create for this axis.", None))
        self.label_11.setText(_translate("gridSplicerDialogBase", "Output Base Directory: Where you want your output to be stored. gridSplitter will make subdirectories for each tile", None))
        self.label_12.setText(_translate("gridSplicerDialogBase", "Prefix for output files (optional): To give the ouput files a better name than [tileX]_[tiley]", None))
        self.label_13.setText(_translate("gridSplicerDialogBase", "Temporary file: a non-existing file to store temporary informations, as some algorithm doesn\'t seem to accept memory layers", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("gridSplicerDialogBase", "Info", None))

from qgis import gui
