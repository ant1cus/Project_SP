import os
import threading
import traceback
import pandas as pd

from PyQt5.QtCore import QThread, pyqtSignal


class SortingFile(QThread):
    progress = pyqtSignal(int)  # Сигнал для прогресс бара
    status = pyqtSignal(str)  # Сигнал для статус бара
    messageChanged = pyqtSignal(str, str)
    errors = pyqtSignal()

    def __init__(self, incoming_data):  # Список переданных элементов.
        QThread.__init__(self)
        self.path_material_sp = incoming_data['path_material_sp']
        self.path_load_asu = incoming_data['path_load_asu']
        self.group_file = incoming_data['name_gk']
        self.no_freq_lim = incoming_data['name_set']
        self.logging = incoming_data['logging']
        self.queue = incoming_data['queue']
        self.event = threading.Event()

    def run(self):
        try:
            current_progress = 0
            self.logging.info('Начинаем парсить файлы')
            self.status.emit('Старт')
            self.progress.emit(current_progress)
            percent = 1
            errors = []
            df = pd.read_excel(self.path_load_asu, sheet_name=0, header=None)
            # if errors:
            #     self.logging.info("Выводим ошибки")
            #     self.queue.put({'errors': errors})
            #     self.errors.emit()
            #     self.status.emit('В файлах присутствуют ошибки')
            # else:
            #     self.logging.info("Конец работы программы")
            #     self.status.emit('Готово')
            # os.chdir('C:\\')
            print(df)
            return
        except BaseException as es:
            self.logging.error(es)
            self.logging.error(traceback.format_exc())
            self.progress.emit(0)
            self.status.emit('Ошибка!')
            os.chdir('C:\\')
            return

