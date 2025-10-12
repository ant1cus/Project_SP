import pathlib
import queue
import sys
import Main

from PyQt5.QtCore import QTranslator, QLocale, QLibraryInfo, QObject
from PyQt5.QtWidgets import QMainWindow, QApplication

from small_function import browse, default_settings, default_data, rewrite_settings, start_thread
from checked import checked_sorting_file, checked_form_file, check_unloading_file
from read_asu_file import copy_from_asu_file
from read_manufacture_file import copy_from_manufacture
from form_file import form_file
from change_unloading_file import change_unloading_file
from sp_asu_files import create_sp_sorting_file
from manufacture_asu_files import create_manufacture_asu_file
from StartThread import StartThreading


class MainWindow(QMainWindow, Main.Ui_mainWindow):  # Главное окно

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.default_path = pathlib.Path.cwd()
        self.mode_description = {'sorting': {'mode_name': 'sorting', 'title': 'Сортировка файлов в папке «name_dir»',
                                             'cancel': 'Поиск файлов в папке «name_dir» отменён пользователем',
                                             'exception': 'Поиск файлов в папке «name_dir» не завершён из-за ошибки',
                                             'success': 'Поиск файлов в папке «name_dir» успешно завершён',
                                             'error': 'Поиск файлов в папке «name_dir» завершён с ошибками'
                                             },
                                 'form': {'mode_name': 'form', 'title': 'Формирование файла в папке «name_dir»',
                                          'cancel': 'Формирование файла в папке «name_dir» отменено пользователем',
                                          'exception': 'Формирование файла в папке «name_dir» не завершено'
                                                       ' из-за ошибки',
                                          'success': 'Формирование файла в папке «name_dir» успешно завершено',
                                          'error': 'Формирование файла в папке «name_dir» завершено с ошибками'
                                          },
                                 'change': {'mode_name': 'change',
                                            'title': 'Изменение файла выгрузки в папке «name_dir»',
                                            'cancel': 'Изменение файла выгрузки в «name_dir» отменено пользователем',
                                            'exception': 'Изменение файла выгрузки в папке «name_dir» не завершено'
                                                         ' из-за ошибки',
                                            'success': 'Изменение файла выгрузки в папке «name_dir» успешно завершено',
                                            'error': 'Изменение файла выгрузки в папке «name_dir» завершено с ошибками'
                                            }
                                 }
        self.widget_name = {
            'sorting': {'grid': 'gridLayout_sorting', 'frame': 'groupBox_sorting',
                        'action': 'action_sorting_file', 'tab': 'sorting'},
            'form': {'grid': 'gridLayout_form', 'frame': 'groupBox_form',
                     'action': 'action_form_file', 'tab': 'form'},
            'change': {'grid': 'gridLayout_change', 'frame': 'groupBox_change',
                       'action': 'action_change_unloading', 'tab': 'change'},
                           }
        self.pushButton_open_unformat_file.clicked.connect((lambda: browse(self, self.pushButton_open_unformat_file,
                                                                           self.lineEdit_path_file_unformat_file,
                                                                           self.default_path)))
        self.pushButton_open_check_material_dir.clicked.connect((lambda: browse(self,
                                                                                self.pushButton_open_check_material_dir,
                                                                                self.lineEdit_path_dir_check_material,
                                                                                self.default_path)))
        self.pushButton_open_material_sp_dir.clicked.connect((lambda: browse(self, self.pushButton_open_material_sp_dir,
                                                                             self.lineEdit_path_dir_material_sp,
                                                                             self.default_path)))
        self.pushButton_open_load_asu_file.clicked.connect((lambda: browse(self, self.pushButton_open_load_asu_file,
                                                                           self.lineEdit_path_load_asu_file,
                                                                           self.default_path)))
        self.pushButton_open_load_manufacture_file.clicked.connect(
            (lambda: browse(self, self.pushButton_open_load_manufacture_file, self.lineEdit_path_file_manufacture,
                            self.default_path)))
        self.pushButton_open_path_finish_dir.clicked.connect((lambda: browse(self, self.pushButton_open_path_finish_dir,
                                                                             self.lineEdit_path_dir_finish,
                                                                             self.default_path)))
        self.pushButton_open_start_unloading_dir.clicked.connect(
            (lambda: browse(self, self.pushButton_open_start_unloading_dir,
                            self.lineEdit_path_dir_start_unloading_files, self.default_path)))
        self.pushButton_open_finish_unloading_dir.clicked.connect(
            (lambda: browse(self, self.pushButton_open_finish_unloading_dir,
                            self.lineEdit_path_dir_finish_unloading_files, self.default_path)))
        self.pushButton_sorting_file_SP.clicked.connect(self.sorting_file)
        self.pushButton_sorting_file_manufacture.clicked.connect(self.sorting_file)
        self.pushButton_form_file.clicked.connect(self.form_file)
        self.pushButton_change_unloading_file.clicked.connect(self.change_unloading_file)
        self.action_form_file.triggered.connect(lambda: self.add_tab(self.action_form_file))
        self.action_sorting_file.triggered.connect(lambda: self.add_tab(self.action_sorting_file))
        self.action_change_unloading.triggered.connect(lambda: self.add_tab(self.action_change_unloading))
        self.lines = {
            'form-lineEdit_path_file_unformat_file': ['Путь к неподготовленному файлу',
                                                      self.lineEdit_path_file_unformat_file],
            'form-lineEdit_path_dir_check_material': ['Путь к материалам для проверки',
                                                      self.lineEdit_path_dir_check_material],
            'sorting-lineEdit_path_dir_material_sp': ['Путь к папке с материалами', self.lineEdit_path_dir_material_sp],
            'sorting-radioButton_group1': ['Тип выгрузки', [self.radioButton_load_asu,
                                                            self.radioButton_load_manufacture]],
            'sorting-lineEdit_path_load_asu_file': ['Файл выгрузки «.xlsx»', self.lineEdit_path_load_asu_file],
            'sorting-lineEdit_path_file_manufacture': ['Файл выгрузки «.csv»', self.lineEdit_path_file_manufacture],
            'sorting-lineEdit_path_dir_finish': ['Путь к конечной папке', self.lineEdit_path_dir_finish],
            'sorting-checkBox_name_gk': ['Включить ГК', self.checkBox_name_gk],
            'sorting-lineEdit_name_gk': ['Наименование ГК', self.lineEdit_name_gk],
            'sorting-checkBox_name_set': ['Включить комплект', self.checkBox_name_set],
            'sorting-lineEdit_name_set': ['Наименование комплекта', self.lineEdit_name_set],
            'change-lineEdit_path_dir_start_unloading_files': ['Исходные файлы выгрузки',
                                                               self.lineEdit_path_dir_start_unloading_files],
            'change-lineEdit_path_dir_finish_unloading_files': ['Конечная папка',
                                                               self.lineEdit_path_dir_finish_unloading_files]
                      }
        self.action_default_window.triggered.connect((lambda: default_settings(self, self.default_path, self.lines,
                                                                               self.widget_name)))
        self.default_data = rewrite_settings(self.default_path)
        self.data = self.default_data["widget_settings"]
        self.tab_order = self.default_data['gui_settings']['tab_order']
        self.tab_visible = self.default_data['gui_settings']['tab_visible']
        default_data(self.data, self.lines)
        # Управление табами в виджете
        self.start_index = False
        self.start_name = False
        self.tabWidget.tabBar().tabMoved.connect(self.tab_)
        self.tabWidget.tabBarClicked.connect(self.tab_click)
        self.tabWidget.tabCloseRequested.connect(lambda index: self.tabWidget.removeTab(index))
        self.tab_for_paint = {}
        for tab in range(0, self.tabWidget.tabBar().count()):
            self.tab_for_paint[self.tabWidget.widget(tab).objectName()] = {}
            if self.tabWidget.widget(tab).objectName() not in self.tab_order.values():
                self.tab_order[str(len(self.tab_order))] = self.tabWidget.widget(tab).objectName()
                rewrite_settings(self.default_path, self.tab_order, 'tab_order')
                self.tab_visible[str(self.tabWidget.widget(tab).objectName())] = True
                rewrite_settings(self.default_path, self.tab_visible, 'tab_visible')
            self.tab_for_paint[self.tabWidget.widget(tab).objectName()]['widget'] = self.tabWidget.widget(tab)
            self.tab_for_paint[self.tabWidget.widget(tab).objectName()]['name'] = self.tabWidget.tabText(tab)
        self.tabWidget.clear()
        for tab in self.tab_order:
            if self.tab_visible[self.tab_order[tab]]:
                action = self.findChild(QObject, self.widget_name[self.tab_order[tab]]['action'])
                action.setChecked(True)
                self.tabWidget.addTab(self.tab_for_paint[self.tab_order[tab]]['widget'],
                                      self.tab_for_paint[self.tab_order[tab]]['name'])
        self.tabWidget.tabBar().setCurrentIndex(0)
        # Для каждого потока свой лог. Потом сливаем в один и удаляем
        self.logging_dict = {}
        # Для сдвига окна при появлении
        self.thread_dict = {self.mode_description[i]['mode_name']: {} for i in self.mode_description}
        self.default_dict = {'mode_description': self.mode_description, 'logging_dict': self.logging_dict,
                             'thread_dict': self.thread_dict, 'default_path': self.default_path,
                             'all_doc': 0, 'now_doc': 0}

    def tab_(self, index):
        for tab in self.tab_order.items():
            if tab[1] == self.start_name and tab[1] == self.tabWidget.currentWidget().objectName():
                self.tab_order[str(index)], self.tab_order[tab[0]] = self.tab_order[tab[0]], self.tab_order[str(index)]
                break
            elif tab[1] == self.tabWidget.currentWidget().objectName():
                self.tab_order[str(index)], self.tab_order[tab[0]] = self.tab_order[tab[0]], self.tab_order[str(index)]
                break
        rewrite_settings(self.default_path, self.tab_order, 'tab_order')

    def tab_click(self, index):
        try:
            self.start_name = self.tab_order[str(index)]
        except KeyError:
            pass

    def add_tab(self, widget_action):
        name_open_tab = {self.tabWidget.widget(ind).objectName(): ind for ind
                         in range(0, self.tabWidget.tabBar().count())}
        for tab in self.widget_name:
            action = self.findChild(QObject, self.widget_name[tab]['action'])
            if action == widget_action:
                if action.isChecked():
                    if tab not in name_open_tab:
                        self.tabWidget.addTab(self.tab_for_paint[tab]['widget'],
                                              self.tab_for_paint[tab]['name'])
                    if self.tab_visible[tab] is False:
                        self.tab_visible[tab] = True
                        rewrite_settings(self.default_path, self.tab_visible, 'tab_visible')
                else:
                    if self.tab_visible[tab]:
                        self.tab_visible[tab] = False
                        rewrite_settings(self.default_path, self.tab_visible, 'tab_visible')

    def form_file(self):
        queue_sorting_file = queue.Queue(maxsize=1)
        mode_name = self.mode_description['form']['mode_name']
        name_dir = self.lineEdit_path_file_unformat_file.text().strip()
        start_function = form_file
        data = {**self.default_dict,
                'queue': queue_sorting_file, 'mode_name': mode_name, 'name_dir': name_dir,
                'start_function': start_function,
                'unformat_file': self.lineEdit_path_file_unformat_file.text().strip(),
                'path_check_material': self.lineEdit_path_dir_check_material.text().strip(),
                }
        start_thread(data, self.logging_dict, self.thread_dict, self, checked_form_file, StartThreading)

    def sorting_file(self):
        queue_sorting_file = queue.Queue(maxsize=1)
        mode_name = self.mode_description['sorting']['mode_name']
        name_dir = self.lineEdit_path_dir_material_sp.text().strip()
        name_gk = self.lineEdit_name_gk.text().strip() if self.checkBox_name_gk.isChecked() else False
        name_set = self.lineEdit_name_set.text().strip() if self.checkBox_name_set.isChecked() else False
        func = create_sp_sorting_file if self.sender().text() == 'Преобразовать файлы СП' else create_manufacture_asu_file
        asu_man = True if self.radioButton_load_asu.isChecked() else False
        start_function = copy_from_asu_file if asu_man else copy_from_manufacture
        data = {**self.default_dict,
                'queue': queue_sorting_file, 'mode_name': mode_name, 'name_dir': name_dir,
                'start_function': start_function,
                'name_gk': name_gk, 'name_set': name_set, 'asu_man': asu_man,
                'function': func,
                'path_material_sp': self.lineEdit_path_dir_material_sp.text().strip(),
                'path_load_asu': self.lineEdit_path_load_asu_file.text().strip(),
                'path_load_man': self.lineEdit_path_file_manufacture.text().strip(),
                'path_finish_folder': self.lineEdit_path_dir_finish.text().strip()
                }
        start_thread(data, self.logging_dict, self.thread_dict, self, checked_sorting_file, StartThreading)

    def change_unloading_file(self):
        queue_unloading_file = queue.Queue(maxsize=1)
        mode_name = self.mode_description['change']['mode_name']
        name_dir = self.lineEdit_path_dir_start_unloading_files.text().strip()
        start_function = change_unloading_file
        data = {**self.default_dict,
                'queue': queue_unloading_file, 'mode_name': mode_name, 'name_dir': name_dir,
                'start_function': start_function,
                'start_path': self.lineEdit_path_dir_start_unloading_files.text().strip(),
                'finish_path': self.lineEdit_path_dir_finish_unloading_files.text().strip(),
                }
        start_thread(data, self.logging_dict, self.thread_dict, self, check_unloading_file, StartThreading)


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
