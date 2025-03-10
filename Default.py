import os
import pathlib
import default_window

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLineEdit, QDialog, QButtonGroup, QLabel, QSizePolicy, QPushButton, QComboBox


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
    def __init__(self, parent, path, lines, default_data, browse, rewrite_settings):
        super().__init__()
        self.setupUi(self)
        self.path_for_default = path
        self.parent = parent
        self.lines = lines
        self.default_data = default_data
        self.browse = browse
        # Сюда добавляем все возможные группы и разметки модулей. Надо подумать как извлечь универсально
        self.name_box = [self.groupBox_copy_file]
        self.name_grid = [self.gridLayout_copy_file]
        self.rewrite_settings = rewrite_settings
        default = self.rewrite_settings(self.path_for_default)
        self.widget_settings = default['widget_settings']
        self.gui_settings = default['gui_settings']
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
        self.combo = {}  # Для combobox
        self.button = {}  # Для кнопки «изменить»
        self.button_clear = {}  # Для кнопки «очистить»
        self.button_open = {}  # Для кнопки «открыть»
        for i, el in enumerate(self.lines):  # Заполняем
            frame = False
            grid = False
            # Сюда добавляем все возможные имена модулей
            for j, n in enumerate(['copy']):
                if n in el.partition('-')[0]:
                    frame = self.name_box[j]
                    grid = self.name_grid[j]
                    break
            self.line[i] = QLabel(frame)  # Помещаем в фрейм
            self.line[i].setText(self.lines[el][0])  # Название элемента
            self.line[i].setFont(QFont("Times", 12, QFont.Light))  # Шрифт, размер
            self.line[i].setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # Размеры виджета
            self.line[i].setDisabled(True)  # Делаем неактивным, чтобы нельзя было просто так редактировать
            self.gridLayout_copy_file.addWidget(self.line[i], i, 0)  # Добавляем виджет
            if 'checkBox' in el or 'groupBox' in el:
                self.combo[i] = QComboBox(frame)  # Помещаем в фрейм
                self.combo[i].addItems(['Включён', 'Выключен'])
                self.combo[i].setCurrentIndex(0) if el in self.widget_settings and self.widget_settings[el] \
                    else self.combo[i].setCurrentIndex(1)
                self.combo[i].setFont(QFont("Times", 12, QFont.Light))  # Шрифт, размер
                self.combo[i].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Размеры виджета
                grid.addWidget(self.combo[i], i, 3)  # Помещаем в фрейм
            elif 'radioButton' in el:
                self.combo[i] = QComboBox(frame)  # Помещаем в фрейм
                name_radio = [radio.text() for radio in self.lines[el][1]]
                name_radio.insert(0, '')
                radio_index = 0
                if el in self.widget_settings:
                    for button, radio_check in enumerate(self.widget_settings[el]):
                        if radio_check:
                            radio_index = button + 1
                self.combo[i].addItems(name_radio)
                self.combo[i].setCurrentIndex(radio_index)
                self.combo[i].setFont(QFont("Times", 12, QFont.Light))  # Шрифт, размер
                self.combo[i].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Размеры виджета
                grid.addWidget(self.combo[i], i, 3)  # Помещаем в фрейм
            elif 'comboBox' in el:
                self.combo[i] = QComboBox(frame)  # Помещаем в фрейм
                name_combo = self.lines[el][2]
                radio_index = 0
                if el in self.widget_settings:
                    for button, radio_check in enumerate(self.widget_settings[el]):
                        if radio_check:
                            radio_index = button
                self.combo[i].addItems(name_combo)
                self.combo[i].setCurrentIndex(radio_index)
                self.combo[i].setFont(QFont("Times", 12, QFont.Light))  # Шрифт, размер
                self.combo[i].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Размеры виджета
                grid.addWidget(self.combo[i], i, 3)  # Помещаем в фрейм
            else:
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
                if el in self.widget_settings:
                    self.name[i].setText(self.widget_settings[el])
                self.name[i].setFont(QFont("Times", 12, QFont.Light))  # Шрифт, размер
                self.name[i].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Размеры виджета
                self.name[i].setStyleSheet("QLineEdit {"
                                           "border-style: solid;"
                                           "}")
                self.name[i].setDisabled(True)  # Неактивный
                grid.addWidget(self.name[i], i, 3)  # Помещаем в фрейм
                if 'dir' in self.lines[el][1].objectName() or 'file' in self.lines[el][1].objectName():
                    self.button_open[i] = QPushButton("Открыть", frame)  # Создаем кнопку
                    self.button_open[i].setFont(QFont("Times", 12, QFont.Light))  # Размер шрифта
                    self.button_open[i].setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Размеры виджета
                    self.button_open[i].setDisabled(True)  # Неактивный
                    self.buttongroup_open.addButton(self.button_open[i], i)  # Добавляем в группу
                    # Новое для универсальности. Присваиваем object name в зависимости от того, что нужно открыть
                    button_name = 'dir' if 'dir' in self.lines[el][1].objectName() else 'file'
                    self.button_open[i].setObjectName(f"{i}_{button_name}")
                    grid.addWidget(self.button_open[i], i, 4)  # Добавляем в фрейм по месту

    def open_button_clicked(self, number):  # Для кнопки открыть
        self.browse(self, self.button_open[number], self.name[number], self.path_for_default)

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
        for i, el in enumerate(self.lines):  # Пробегаем значения
            if 'checkBox' in el:
                self.widget_settings[el] = True if self.combo[i].currentIndex() == 0 else False
            elif 'radioButton' in el:
                self.widget_settings[el] = [True if self.lines[el][1].index(radio) + 1 == self.combo[i].currentIndex()
                                            else False for radio in self.lines[el][1]]
            else:
                if self.name[i].isEnabled():  # Если виджет активный (означает потенциальное изменение)
                    if self.name[i].text():  # Если внутри виджета есть текст, то помещаем внутрь базы
                        self.widget_settings[el] = self.name[i].text()
                    else:  # Если нет текста, то удаляем значение
                        self.widget_settings[el] = None
        data_insert = {"widget_settings": self.widget_settings, "gui_settings": self.gui_settings}
        self.rewrite_settings(self.path_for_default, data_insert)
        self.close()  # Закрываем

    def closeEvent(self, event):
        os.chdir(pathlib.Path.cwd())
        if self.sender() and self.sender().text() == 'Принять':
            event.accept()
            default = self.rewrite_settings(self.path_for_default)
            data = default['widget_settings']
            self.default_data(data, self.lines)
            self.parent.show()
        else:
            event.accept()
            self.parent.show()
