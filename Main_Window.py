# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Main_Window.ui'
#
# Created: Wed Oct 22 09:59:34 2014
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Main_Window(object):
    def setupUi(self, Main_Window):
        Main_Window.setObjectName(_fromUtf8("Main_Window"))
        Main_Window.setWindowModality(QtCore.Qt.WindowModal)
        Main_Window.resize(480, 283)
        self.centralwidget = QtGui.QWidget(Main_Window)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.btnEnd = QtGui.QPushButton(self.centralwidget)
        self.btnEnd.setGeometry(QtCore.QRect(170, 230, 75, 23))
        self.btnEnd.setObjectName(_fromUtf8("btnEnd"))
        self.btnStart = QtGui.QPushButton(self.centralwidget)
        self.btnStart.setGeometry(QtCore.QRect(170, 190, 75, 23))
        self.btnStart.setObjectName(_fromUtf8("btnStart"))
        self.groupBox = QtGui.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(10, 20, 431, 101))
        self.groupBox.setTitle(_fromUtf8(""))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.ButtonPathEin = QtGui.QPushButton(self.groupBox)
        self.ButtonPathEin.setGeometry(QtCore.QRect(339, 20, 75, 23))
        self.ButtonPathEin.setObjectName(_fromUtf8("ButtonPathEin"))
        self.lblPathEin = QtGui.QLabel(self.groupBox)
        self.lblPathEin.setGeometry(QtCore.QRect(30, 21, 117, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lblPathEin.setFont(font)
        self.lblPathEin.setObjectName(_fromUtf8("lblPathEin"))
        self.ButtonPathAus = QtGui.QPushButton(self.groupBox)
        self.ButtonPathAus.setGeometry(QtCore.QRect(339, 60, 75, 23))
        self.ButtonPathAus.setObjectName(_fromUtf8("ButtonPathAus"))
        self.lblPathAus = QtGui.QLabel(self.groupBox)
        self.lblPathAus.setGeometry(QtCore.QRect(30, 60, 121, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lblPathAus.setFont(font)
        self.lblPathAus.setObjectName(_fromUtf8("lblPathAus"))
        Main_Window.setCentralWidget(self.centralwidget)

        self.retranslateUi(Main_Window)
        QtCore.QMetaObject.connectSlotsByName(Main_Window)

    def retranslateUi(self, Main_Window):
        Main_Window.setWindowTitle(QtGui.QApplication.translate("Main_Window", "DKM Programm", None, QtGui.QApplication.UnicodeUTF8))
        self.btnEnd.setText(QtGui.QApplication.translate("Main_Window", "Ende", None, QtGui.QApplication.UnicodeUTF8))
        self.btnStart.setText(QtGui.QApplication.translate("Main_Window", "Start", None, QtGui.QApplication.UnicodeUTF8))
        self.ButtonPathEin.setText(QtGui.QApplication.translate("Main_Window", "Pfad Ändern", None, QtGui.QApplication.UnicodeUTF8))
        self.lblPathEin.setText(QtGui.QApplication.translate("Main_Window", "Pfad Eingangsdaten:", None, QtGui.QApplication.UnicodeUTF8))
        self.ButtonPathAus.setText(QtGui.QApplication.translate("Main_Window", "Pfad Ändern", None, QtGui.QApplication.UnicodeUTF8))
        self.lblPathAus.setText(QtGui.QApplication.translate("Main_Window", "Pfad Ausgangsdaten:", None, QtGui.QApplication.UnicodeUTF8))

