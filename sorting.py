import os
import threading
import traceback
import pandas as pd
import math
import pathlib
import PySimpleGUI as sg
import time

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
            self.logging.info('Начинаем процедуру сортировки файлов')
            self.status.emit('Старт')
            self.progress.emit(current_progress)
            percent = 1
            errors = []
            name_finish_folder = self.name_gk if self.name_gk else 'Номер ГК'
            try:
                os.mkdir(pathlib.Path(self.path_finish_folder, name_finish_folder))
            except FileExistsError:
                self.logging.info('Такая папка уже есть ' + str(pathlib.Path(self.path_finish_folder,
                                                                             name_finish_folder)))
            self.logging.info('Создаём структуру папок')
            self.status.emit('Создаём структуру папок')
            list_df = []
            for file_load_asu in os.listdir(self.path_load_asu):
                try:
                    self.logging.info('Считываем файл выгрузки ' + file_load_asu)
                    df = pd.read_excel(self.path_load_asu + '\\' + file_load_asu, sheet_name=0, header=None)
                    index_string = -100
                    for index, item in df.iloc[0].items():
                        if math.isnan(item):
                            df.iloc[0, index] = index_string
                            index_string += 1
                    number_device = df.shape[1] - (100 + index_string) + 1
                    df.sort_values(0, axis=1, inplace=True)
                    name_for_df = df.iloc[1]
                    df = df.drop(labels=[1], axis=0)
                    name_set = df[2].to_numpy().tolist()
                    self.logging.info('Создаём структуру для ' + file_load_asu)
                    for row, serial_num in enumerate(df[3].to_numpy().tolist()[1:], start=1):
                        path_dir = pathlib.Path(self.path_finish_folder, name_finish_folder,
                                                name_set[row], str(serial_num) + ' В')
                        try:
                            os.makedirs(path_dir)
                        except FileExistsError:
                            self.logging.info('Такая папка уже есть ' + str(path_dir))
                        # os.makedirs(path_dir)
                        for device in range(1, number_device):
                            try:
                                os.makedirs(pathlib.Path(path_dir, str(device), 'photo'))
                            except FileExistsError:
                                self.logging.info('Такая папка уже есть ' + str(pathlib.Path(path_dir,
                                                                                             str(device), 'photo')))
                            try:
                                os.makedirs(pathlib.Path(path_dir, str(device), 'rentgen'))
                            except FileExistsError:
                                self.logging.info('Такая папка уже есть ' + str(pathlib.Path(path_dir,
                                                                                             str(device), 'rentgen')))
                    df.columns = name_for_df
                    df.reset_index(drop=True, inplace=True)
                    size = df.shape
                    percent += (size[0] - 1)*(number_device - 1)
                    list_df.append(df)
                    self.logging.info('Файл ' + file_load_asu + ' обработан')
                except BaseException as error:
                    self.logging.error(error)
                    self.logging.error(traceback.format_exc())
                    self.status.emit('Что-то не так с файлом ' + file_load_asu)
            percent = 100/percent
            self.logging.info('Бежим по файлам СП')
            self.status.emit('Начинаем сортировку указанных файлов СП')
            for name_device in os.listdir(self.path_material_sp):
                self.logging.info('Бежим по ' + str(name_device))
                for sn_device in os.listdir(pathlib.Path(self.path_material_sp, name_device)):
                    self.logging.info('Бежим по ' + str(sn_device))
                    self.status.emit('Сортируем устройства с sn ' + str(sn_device))
                    for device in list_df:
                        if name_device in device:
                            if device[name_device].isin([sn_device]).any():
                                row = device.index[device[name_device] == sn_device].tolist()[0]
                                column = device.loc[0, name_device]
                                path_photo = pathlib.Path(self.path_finish_folder, name_finish_folder,
                                                          device.iloc[row, 2], device.iloc[row, 3] + ' В',
                                                          str(column), 'photo')
                                path_rentgen = pathlib.Path(self.path_finish_folder, name_finish_folder,
                                                            device.iloc[row, 2], device.iloc[row, 3] + ' В',
                                                            str(column), 'rentgen')
                                if pathlib.Path(path_photo).is_dir() is False:
                                    self.logging.info('Почему то такого пути для фото нет, создаём')
                                    path_photo.mkdir(parents=True)
                                if pathlib.Path(path_rentgen).is_dir() is False:
                                    self.logging.info('Почему то такого пути для рентгена нет, создаём')
                                    path_rentgen.mkdir(parents=True)
                    for file in os.listdir(pathlib.Path(self.path_material_sp, name_device, str(sn_device))):
                        if str(file).endswith('.tif') or str(file).endswith('.tiff') or str(file).endswith('.png'):
                            pathlib.Path(self.path_material_sp, name_device,
                                         str(sn_device), str(file)).rename(pathlib.Path(path_rentgen, str(file)))
                        else:
                            pathlib.Path(self.path_material_sp, name_device,
                                         str(sn_device), str(file)).rename(pathlib.Path(path_photo, str(file)))
                    sg.one_line_progress_meter('Перенос файлов', current_progress, 100, '')
                    current_progress += percent
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
            self.logging.info('Готово')
            self.status.emit('Готово')
            return
        except BaseException as error:
            self.logging.error(error)
            self.logging.error(traceback.format_exc())
            self.progress.emit(0)
            self.status.emit('Ошибка!')
            os.chdir('C:\\')
            return

