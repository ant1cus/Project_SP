import json
import os
import pathlib
import default_window

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLineEdit, QDialog, QButtonGroup, QLabel, QSizePolicy, QPushButton, QFileDialog, QComboBox
from PyQt5.QtCore import QDir

from rewrite_settings import rewrite


class Button(QLineEdit):

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


class DefaultWindow(QDialog, default_window.Ui_Dialog):  # Настройки по умолчанию
    def __init__(self, parent, path):
        super().__init__()
        self.setupUi(self)
        self.path_for_default = path
        self.parent = parent
        # Имена
        self.name_list = {'copy-lineEdit_path_material_sp': 'Путь к дир. с материалами СП',
                          'copy-lineEdit_path_load_asu': 'Путь к дир. с выгрузками АСУ',
                          'copy-lineEdit_path_finish_folder': 'Путь к конечной дир.',
                          'copy-checkBox_name_gk': 'Включить "ГК"',
                          'copy-lineEdit_name_gk': 'Номер ГК',
                          'copy-checkBox_name_set': 'Включить "Имя комплекта"',
                          'copy-lineEdit_name_set': 'Имя комплекта'
                          }
        self.name_box = [self.groupBox_copy_file]
        self.name_grid = [self.gridLayout_copy_file]
        with open(pathlib.Path(self.path_for_default, 'Настройки.txt'), "r", encoding='utf-8-sig') as f:  # Открываем
            dict_load = json.load(f)  # Загружаем данные
            self.data = dict_load['widget_settings']
        self.buttongroup_add = QButtonGroup()
        self.buttongroup_add.buttonClicked[int].connect(self.add_button_clicked)
        self.buttongroup_clear = QButtonGroup()
        self.buttongroup_clear.buttonClicked[int].connect(self.clear_button_clicked)
        self.buttongroup_open = QButtonGroup()
        self.buttongroup_open.buttonClicked[int].connect(self.open_button_clicked)
        self.pushButton_accept.clicked.connect(self.accept)  # Принять
        self.pushButton_cancel.clicked.connect(lambda: self.close())  # Отмена
        self.line = {}  # Для имен
        self.name = {}  # Для значений
        self.combo = {}  # Для комбобоксов
        self.button = {}  # Для кнопки «изменить»
        self.button_clear = {}  # Для кнопки «очистить»
        self.button_open = {}  # Для кнопки «открыть»
        for i, el in enumerate(self.name_list):  # Заполняем
            frame = False
            grid = False
            for j, n in enumerate(['copy']):
                if n in el.partition('-')[0]:
                    frame = self.name_box[j]
                    grid = self.name_grid[j]
                    break
            self.line[i] = QLabel(frame)  # Помещаем в фрейм
            self.line[i].setText(self.name_list[el])  # Название элемента
            self.line[i].setFont(QFont("Times", 12, QFont.Light))  # Шрифт, размер
            self.line[i].setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # Размеры виджета
            self.line[i].setFixedWidth(350)
            self.line[i].setDisabled(True)  # Делаем неактивным, чтобы нельзя было просто так редактировать
            self.gridLayout_copy_file.addWidget(self.line[i], i, 0)  # Добавляем виджет
            if 'checkBox' not in el:
                self.button[i] = QPushButton("Изменить", frame)  # Создаем кнопку
                self.button[i].setFont(QFont("Times", 12, QFont.Light))  # Размер шрифта
                self.button[i].setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Размеры виджета
                self.buttongroup_add.addButton(self.button[i], i)  # Добавляем в группу
                grid.addWidget(self.button[i], i, 1)  # Добавляем в фрейм по месту
                self.button_clear[i] = QPushButton("Очистить", frame)  # Создаем кнопку
                self.button_clear[i].setFont(QFont("Times", 12, QFont.Light))  # Размер шрифта
                self.button_clear[i].setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Размеры виджета
                self.buttongroup_clear.addButton(self.button_clear[i], i)  # Добавляем в группу
                grid.addWidget(self.button_clear[i], i, 2)  # Добавляем в фрейм по месту

                self.name[i] = Button(frame)  # Помещаем в фрейм
                if el in self.data:
                    self.name[i].setText(self.data[el])
                self.name[i].setFont(QFont("Times", 12, QFont.Light))  # Шрифт, размер
                self.name[i].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Размеры виджета
                self.name[i].setStyleSheet("QLineEdit {"
                                           "border-style: solid;"
                                           "}")
                self.name[i].setDisabled(True)  # Неактивный
                grid.addWidget(self.name[i], i, 3)  # Помещаем в фрейм
                if 'Путь' in self.line[i].text():
                    self.button_open[i] = QPushButton("Открыть", frame)  # Создаем кнопку
                    self.button_open[i].setFont(QFont("Times", 12, QFont.Light))  # Размер шрифта
                    self.button_open[i].setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Размеры виджета
                    self.button_open[i].setDisabled(True)  # Неактивный
                    self.buttongroup_open.addButton(self.button_open[i], i)  # Добавляем в группу
                    grid.addWidget(self.button_open[i], i, 4)  # Добавляем в фрейм по месту
            else:
                self.combo[i] = QComboBox(frame)  # Помещаем в фрейм
                self.combo[i].addItems(['Включён', 'Выключен'])
                self.combo[i].setCurrentIndex(0) if el in self.data and self.data[el]\
                    else self.combo[i].setCurrentIndex(1)
                self.combo[i].setFont(QFont("Times", 12, QFont.Light))  # Шрифт, размер
                self.combo[i].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Размеры виджета
                grid.addWidget(self.combo[i], i, 3)  # Помещаем в фрейм

    def open_button_clicked(self, num):  # Для кнопки открыть
        file = False
        if 'дир.' in self.line[num].text():
            directory = QFileDialog.getExistingDirectory(self, "Открыть папку", QDir.currentPath())
        else:
            directory = QFileDialog.getOpenFileName(self, "Открыть файл", QDir.currentPath())
            file = True
        if directory:  # Если нажать кнопку отркыть в диалоге выбора
            if file:  # Если файлы
                if directory[0]:  # Если есть файл, чтобы не очищалось поле
                    self.name[num].setText(directory[0])
            else:  # Если директории
                self.name[num].setText(directory)

    def add_button_clicked(self, number):  # Если кликнули по кнопке
        self.name[number].setEnabled(True)  # Делаем активным для изменения
        if number in self.button_open:
            self.button_open[number].setEnabled(True)  # Неактивный
        self.name[number].setStyleSheet("QLineEdit {"
                                        "border-style: solid;"
                                        "border-width: 1px;"
                                        "border-color: black; "
                                        "}")

    def clear_button_clicked(self, number):
        self.name[number].clear()

    def accept(self):  # Если нажали кнопку принять
        for i, el in enumerate(self.name_list):  # Пробегаем значения
            if 'checkBox' in el:
                self.data[el] = True if self.combo[i].currentIndex() == 0 else False
            else:
                if self.name[i].isEnabled():  # Если виджет активный (означает потенциальное изменение)
                    if self.name[i].text():  # Если внутри виджета есть текст, то помещаем внутрь базы
                        self.data[el] = self.name[i].text()
                    else:  # Если нет текста, то удаляем значение
                        self.data[el] = None
        data_insert = {"widget_settings": self.data}
        rewrite(self.path_for_default, data_insert, widget=True)
        self.close()  # Закрываем

    def closeEvent(self, event):
        os.chdir(pathlib.Path.cwd())
        if self.sender() and self.sender().text() == 'Принять':
            event.accept()
            # Открываем и загружаем данные
            with open(pathlib.Path(self.path_for_default, 'Настройки.txt'), "r", encoding='utf-8-sig') as f:
                data = json.load(f)['widget_settings']
            self.parent.default_data(data)
            self.parent.show()
        else:
            event.accept()
            self.parent.show()
