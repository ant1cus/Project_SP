import os
import threading
import traceback
import pandas as pd
import math
import pathlib

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
        self.path_finish_folder = incoming_data['path_finish_folder']
        self.name_gk = incoming_data['name_gk']
        self.name_set = incoming_data['name_set']
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
            name_finish_folder = self.name_gk if self.name_gk else 'Номер ГК'
            os.mkdir(pathlib.Path(self.path_finish_folder, name_finish_folder))
            for file_load_asu in os.listdir(self.path_load_asu):
                df = pd.read_excel(self.path_load_asu + '\\' + file_load_asu, sheet_name=0, header=None)
                index_string = -100
                for index, item in df.iloc[0].items():
                    if math.isnan(item):
                        df.iloc[0, index] = index_string
                        index_string += 1
                number_device = df.shape[1] - (100 + index_string) + 1
                df.sort_values(0, axis=1, inplace=True)
                df = df.drop(labels=[0, 1], axis=0)
                name_set = df[2].to_numpy().tolist()
                for row, serial_num in enumerate(df[3].to_numpy().tolist()):
                    path_dir = pathlib.Path(self.path_finish_folder, name_finish_folder,
                                            name_set[row], str(serial_num) + ' В')
                    os.makedirs(path_dir)
                    for device in range(1, number_device):
                        os.makedirs(pathlib.Path(path_dir, str(device), 'photo'))
                        os.makedirs(pathlib.Path(path_dir, str(device), 'rentgen'))
                # print(df)
                # print(df_values)
            # os.mkdir(self.path_finish_folder + '\\' + name_finish_folder)
            # if errors:
            #     self.logging.info("Выводим ошибки")
            #     self.queue.put({'errors': errors})
            #     self.errors.emit()
            #     self.status.emit('В файлах присутствуют ошибки')
            # else:
            #     self.logging.info("Конец работы программы")
            #     self.status.emit('Готово')
            # os.chdir('C:\\')
            self.status.emit('Готово')
            return
        except BaseException as es:
            self.logging.error(es)
            self.logging.error(traceback.format_exc())
            self.progress.emit(0)
            self.status.emit('Ошибка!')
            os.chdir('C:\\')
            return

