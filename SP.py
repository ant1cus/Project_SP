import pathlib
import queue
import sys

import Main

from PyQt5.QtCore import QTranslator, QLocale, QLibraryInfo
from PyQt5.QtWidgets import QMainWindow, QApplication

from small_function import browse, default_settings, default_data, rewrite_settings, start_thread
from checked import checked_sorting_file
from read_asu_file import read_asu
from StartThread import StartThreading


class MainWindow(QMainWindow, Main.Ui_mainWindow):  # Главное окно

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.default_path = pathlib.Path.cwd()
        # Словарь для создания отдельных модулей, если понадобится.
        # Принцип создания: добавляем как ключ название соответствующей функции, а в качестве значения - имя модуля
        # для логов, передачи в функции и т.п.
        # Создаю ещё один словарь для описаний. Нужен для универсализации окна запуска потока. Ключ и значения - так же,
        # как и в предыдущем
        self.mode_description = {'copy': {'mode_name': 'copy', 'title': 'Сортировка файлов в папке',
                                          'cancel': 'Поиск файлов в папке «name_dir» отменён пользователем',
                                          'exception': 'Поиск файлов в папке «name_dir» не завершён из-за ошибки',
                                          'success': 'Поиск файлов в папке «name_dir» успешно завершён',
                                          'error': 'Поиск файлов в папке «name_dir» завершён с ошибками'
                                          }}
        self.pushButton_open_material_sp_dir.clicked.connect((lambda: browse(self, self.pushButton_open_material_sp_dir,
                                                                             self.lineEdit_path_dir_material_sp,
                                                                             self.default_path)))
        self.pushButton_open_load_asu_dir.clicked.connect((lambda: browse(self, self.pushButton_open_load_asu_dir,
                                                                          self.lineEdit_path_dir_load_asu,
                                                                          self.default_path)))
        self.pushButton_open_load_manufacture_file.clicked.connect(
            (lambda: browse(self, self.pushButton_open_load_manufacture_file, self.lineEdit_path_file_manufacture,
                            self.default_path)))
        self.pushButton_open_path_finish_dir.clicked.connect((lambda: browse(self, self.pushButton_open_path_finish_dir,
                                                                             self.lineEdit_path_dir_finish,
                                                                             self.default_path)))
        self.pushButton_start.clicked.connect(self.sorting_file)
        self.lines = {'copy-lineEdit_path_dir_material_sp': ['Путь к папке с материалами',
                                                             self.lineEdit_path_dir_material_sp],
                      'copy-radioButton_group1': ['Тип выгрузки', [self.radioButton_load_asu,
                                                                   self.radioButton_load_manufacture]],
                      'copy-lineEdit_path_dir_load_asu': ['Путь к выгрузке АСУ', self.lineEdit_path_dir_load_asu],
                      'copy-lineEdit_path_file_manufacture': ['Путь к файлу выгрузки',
                                                              self.lineEdit_path_file_manufacture],
                      'copy-lineEdit_path_dir_finish': ['Путь к конечной папке', self.lineEdit_path_dir_finish],
                      'copy-checkBox_name_gk': ['Включить ГК', self.checkBox_name_gk],
                      'copy-lineEdit_name_gk': ['Наименование ГК', self.lineEdit_name_gk],
                      'copy-checkBox_name_set': ['Включить комплект', self.checkBox_name_set],
                      'copy-lineEdit_name_set': ['Наименование комплекта', self.lineEdit_name_set]
                      }
        self.action_default_window.triggered.connect((lambda: default_settings(self, self.default_path, self.lines)))
        self.default_data = rewrite_settings(self.default_path)
        self.data = self.default_data["widget_settings"]
        default_data(self.data, self.lines)
        # Для каждого потока свой лог. Потом сливаем в один и удаляем
        self.logging_dict = {}
        # Для сдвига окна при появлении
        self.thread_dict = {self.mode_description[i]['mode_name']: {} for i in self.mode_description}
        self.default_dict = {'mode_description': self.mode_description, 'logging_dict': self.logging_dict,
                             'thread_dict': self.thread_dict, 'default_path': self.default_path,
                             'all_doc': 0, 'now_doc': 0}

    def sorting_file(self):
        queue_sorting_file = queue.Queue(maxsize=1)
        mode_name = self.mode_description['copy']['mode_name']
        name_dir = self.lineEdit_path_dir_material_sp.text().strip()
        name_gk = self.lineEdit_name_gk.text().strip() if self.checkBox_name_gk.isChecked() else False
        name_set = self.lineEdit_name_set.text().strip() if self.checkBox_name_set.isChecked() else False
        asu_man = True if self.radioButton_load_asu.isChecked() else False
        data = {**self.default_dict,
                'queue': queue_sorting_file, 'mode_name': mode_name, 'name_dir': name_dir, 'start_function': read_asu,
                'name_gk': name_gk, 'name_set': name_set, 'asu_man': asu_man,
                'path_material_sp': self.lineEdit_path_dir_material_sp.text().strip(),
                'path_load_asu': self.lineEdit_path_dir_load_asu.text().strip(),
                'path_load_man': self.lineEdit_path_file_manufacture.text().strip(),
                'path_finish_folder': self.lineEdit_path_dir_finish.text().strip()
                }
        start_thread(data, self.logging_dict, self.thread_dict, self, checked_sorting_file, StartThreading)


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
