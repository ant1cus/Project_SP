# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
import os


class Button(QtWidgets.QLineEdit):

	def __init__(self, parent):
		super(Button, self).__init__(parent)

		self.setAcceptDrops(True)

	def dragEnterEvent(self, e):

		if e.mimeData().hasUrls():
			e.accept()
		else:
			super(Button, self).dragEnterEvent(e)

	def dragMoveEvent(self, e):

		super(Button, self).dragMoveEvent(e)

	def dropEvent(self, e):

		if e.mimeData().hasUrls():
			for url in e.mimeData().urls():
				self.setText(os.path.normcase(url.toLocalFile()))
				e.accept()
		else:
			super(Button, self).dropEvent(e)


class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        mainWindow.setObjectName("mainWindow")
        mainWindow.resize(792, 577)
        font = QtGui.QFont()
        font.setPointSize(10)
        mainWindow.setFont(font)
        self.centralwidget = QtWidgets.QWidget(mainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.pushButton_open_load_asu_file = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_open_load_asu_file.setObjectName("pushButton_open_load_asu_file")
        self.gridLayout.addWidget(self.pushButton_open_load_asu_file, 1, 4, 1, 1)
        self.label_load_asu = QtWidgets.QLabel(self.centralwidget)
        self.label_load_asu.setObjectName("label_load_asu")
        self.gridLayout.addWidget(self.label_load_asu, 1, 0, 1, 1)
        self.checkBox_name_gk = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox_name_gk.setObjectName("checkBox_name_gk")
        self.gridLayout.addWidget(self.checkBox_name_gk, 2, 0, 1, 1)
        self.pushButton_open_material_sp_dir = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_open_material_sp_dir.setObjectName("pushButton_open_material_sp_dir")
        self.gridLayout.addWidget(self.pushButton_open_material_sp_dir, 0, 4, 1, 1)
        self.checkBox_name_complect = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox_name_complect.setObjectName("checkBox_name_complect")
        self.gridLayout.addWidget(self.checkBox_name_complect, 3, 0, 1, 1)
        self.lineEdit_name_complect = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_name_complect.setEnabled(False)
        self.lineEdit_name_complect.setObjectName("lineEdit_name_complect")
        self.gridLayout.addWidget(self.lineEdit_name_complect, 3, 1, 1, 4)
        self.label_material_sp = QtWidgets.QLabel(self.centralwidget)
        self.label_material_sp.setObjectName("label_material_sp")
        self.gridLayout.addWidget(self.label_material_sp, 0, 0, 1, 1)
        self.lineEdit_path_material_sp = Button(self.centralwidget)
        self.lineEdit_path_material_sp.setObjectName("lineEdit_path_material_sp")
        self.gridLayout.addWidget(self.lineEdit_path_material_sp, 0, 1, 1, 3)
        self.lineEdit_path_load_asu = Button(self.centralwidget)
        self.lineEdit_path_load_asu.setObjectName("lineEdit_path_load_asu")
        self.gridLayout.addWidget(self.lineEdit_path_load_asu, 1, 1, 1, 3)
        self.lineEdit_name_gk = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_name_gk.setEnabled(False)
        self.lineEdit_name_gk.setObjectName("lineEdit_name_gk")
        self.gridLayout.addWidget(self.lineEdit_name_gk, 2, 1, 1, 4)
        self.pushButton_start = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_start.setObjectName("pushButton_start")
        self.gridLayout.addWidget(self.pushButton_start, 4, 1, 1, 3)
        mainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(mainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 792, 24))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        mainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(mainWindow)
        self.statusbar.setObjectName("statusbar")
        mainWindow.setStatusBar(self.statusbar)
        self.action = QtWidgets.QAction(mainWindow)
        self.action.setObjectName("action")
        self.menu.addAction(self.action)
        self.menubar.addAction(self.menu.menuAction())

        self.retranslateUi(mainWindow)
        self.checkBox_name_gk.toggled['bool'].connect(self.lineEdit_name_gk.setEnabled) # type: ignore
        self.checkBox_name_complect.toggled['bool'].connect(self.lineEdit_name_complect.setEnabled) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(mainWindow)

    def retranslateUi(self, mainWindow):
        _translate = QtCore.QCoreApplication.translate
        mainWindow.setWindowTitle(_translate("mainWindow", "Главное окно"))
        self.pushButton_open_load_asu_file.setText(_translate("mainWindow", "Открыть"))
        self.label_load_asu.setText(_translate("mainWindow", "Файл выгрузки с АСУ"))
        self.checkBox_name_gk.setText(_translate("mainWindow", "Наименование ГК"))
        self.pushButton_open_material_sp_dir.setText(_translate("mainWindow", "Открыть"))
        self.checkBox_name_complect.setText(_translate("mainWindow", "Наименование к-та"))
        self.label_material_sp.setText(_translate("mainWindow", "Папка с материалами"))
        self.pushButton_start.setText(_translate("mainWindow", "Старт"))
        self.menu.setTitle(_translate("mainWindow", "Настройки"))
        self.action.setText(_translate("mainWindow", "Настройки по умолчанию"))