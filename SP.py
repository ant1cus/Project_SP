import json
import pathlib
import queue
import re
import sys

import Main
import logging

from PyQt5.QtCore import QTranslator, QLocale, QLibraryInfo, QDir
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox

from sorting import SortingFile
from checked import checked_sorting_file


class MainWindow(QMainWindow, Main.Ui_mainWindow):  # Главное окно

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.queue = queue.Queue(maxsize=1)
        logging.basicConfig(filename="my_log.log",
                            level=logging.DEBUG,
                            filemode="w",
                            format="%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s")
        self.pushButton_open_load_asu_file.clicked.connect((lambda: self.browse(self.lineEdit_path_load_asu)))
        self.pushButton_open_material_sp_dir.clicked.connect((lambda: self.browse(self.lineEdit_path_material_sp)))
        self.pushButton_open_path_finish_dir.clicked.connect((lambda: self.browse(self.lineEdit_path_finish_folder)))
        self.pushButton_start.clicked.connect(self.sorting_file)
        self.path_for_default = pathlib.Path.cwd()  # Путь для файла настроек

    def browse(self, line_edit):  # Для кнопки открыть
        if 'dir' in self.sender().objectName():
            directory = QFileDialog.getExistingDirectory(self, "Открыть папку", QDir.currentPath())
        else:
            directory = QFileDialog.getOpenFileName(self, "Открыть файл", QDir.currentPath())
        # name_line_edit = re.findall(r'\w+_open_(\w+)', self.sender().objectName().rpartition('_')[0])[0]
        if directory and isinstance(directory, tuple):
            if directory[0]:
                line_edit.setText(directory[0])
        elif directory and isinstance(directory, str):
            line_edit.setText(directory)

    def sorting_file(self):
        sending_data = checked_sorting_file(self.lineEdit_path_material_sp, self.lineEdit_path_load_asu,
                                            self.lineEdit_path_finish_folder)
        name_gk = self.lineEdit_name_gk.text().strip() if self.checkBox_name_gk.isChecked() else False
        name_set = self.lineEdit_name_set.text().strip() if self.checkBox_name_set.isChecked() else False
        if isinstance(sending_data, list):
            self.on_message_changed(sending_data[0], sending_data[1])
            return
        # Если всё прошло запускаем поток
        sending_data['name_gk'], sending_data['name_set'] = name_gk, name_set
        sending_data['logging'], sending_data['queue'] = logging, self.queue
        self.thread = SortingFile(sending_data)
        self.thread.status.connect(self.show_mess)
        self.thread.messageChanged.connect(self.on_message_changed)
        self.thread.start()

    def pause_thread(self):
        if self.queue.empty():
            self.statusBar().showMessage(self.statusBar().currentMessage() + ' (прерывание процесса, подождите...)')
            self.queue.put(True)

    def show_mess(self, value):  # Вывод значения в статус бар
        self.statusBar().showMessage(value)

    def on_message_changed(self, title, description):
        if title == 'УПС!':
            QMessageBox.critical(self, title, description)
        elif title == 'Внимание!':
            QMessageBox.warning(self, title, description)
        elif title == 'Вопрос?':
            self.statusBar().clearMessage()
            ans = QMessageBox.question(self, title, description, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ans == QMessageBox.No:
                self.thread.queue.put(True)
            else:
                self.thread.queue.put(False)
            self.thread.event.set()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    translator = QTranslator(app)
    locale = QLocale.system().name()
    path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    translator.load('qtbase_%s' % locale.partition('_')[0], path)
    app.installTranslator(translator)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
