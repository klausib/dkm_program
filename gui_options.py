# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui_options.ui'
#
# Created: Wed Jan 22 08:52:08 2014
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_frmOptions(object):
    def setupUi(self, frmOptions):
        frmOptions.setObjectName(_fromUtf8("frmOptions"))
        frmOptions.resize(349, 191)
        self.ButtonSave = QtGui.QPushButton(frmOptions)
        self.ButtonSave.setGeometry(QtCore.QRect(110, 140, 101, 23))
        self.ButtonSave.setObjectName(_fromUtf8("ButtonSave"))
        self.layoutWidget = QtGui.QWidget(frmOptions)
        self.layoutWidget.setGeometry(QtCore.QRect(40, 20, 269, 61))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.ckCRS = QtGui.QCheckBox(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.ckCRS.setFont(font)
        self.ckCRS.setObjectName(_fromUtf8("ckCRS"))
        self.verticalLayout.addWidget(self.ckCRS)
        self.ckEncoding = QtGui.QCheckBox(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.ckEncoding.setFont(font)
        self.ckEncoding.setObjectName(_fromUtf8("ckEncoding"))
        self.verticalLayout.addWidget(self.ckEncoding)
        self.ButtonPath = QtGui.QPushButton(frmOptions)
        self.ButtonPath.setGeometry(QtCore.QRect(230, 100, 81, 23))
        self.ButtonPath.setObjectName(_fromUtf8("ButtonPath"))
        self.lblPath = QtGui.QLabel(frmOptions)
        self.lblPath.setGeometry(QtCore.QRect(40, 90, 181, 37))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lblPath.setFont(font)
        self.lblPath.setObjectName(_fromUtf8("lblPath"))

        self.retranslateUi(frmOptions)
        QtCore.QMetaObject.connectSlotsByName(frmOptions)

    def retranslateUi(self, frmOptions):
        frmOptions.setWindowTitle(QtGui.QApplication.translate("frmOptions", "VOGIS - Menü Einstellungen", None, QtGui.QApplication.UnicodeUTF8))
        self.ButtonSave.setText(QtGui.QApplication.translate("frmOptions", "OK", None, QtGui.QApplication.UnicodeUTF8))
        self.ckCRS.setText(QtGui.QApplication.translate("frmOptions", "Koordinatenbezugssystem aus Projektdatei", None, QtGui.QApplication.UnicodeUTF8))
        self.ckEncoding.setText(QtGui.QApplication.translate("frmOptions", "Codierung Shapefiles aus Projektdatei", None, QtGui.QApplication.UnicodeUTF8))
        self.ButtonPath.setText(QtGui.QApplication.translate("frmOptions", "Pfad Ändern", None, QtGui.QApplication.UnicodeUTF8))
        self.lblPath.setText(QtGui.QApplication.translate("frmOptions", "Path", None, QtGui.QApplication.UnicodeUTF8))

