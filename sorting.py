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
        self.path_for_default = incoming_data['path_for_default']
        self.event = threading.Event()

    def run(self):
        try:
            current_progress = 0
            self.logging.info('\n******************************Новый прогон******************************\n')
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
                        if self.pause_threading():
                            return
                        path_dir = pathlib.Path(self.path_finish_folder, name_finish_folder,
                                                name_set[row], str(serial_num) + ' В')
                        # try:
                        #     os.makedirs(path_dir)
                        # except FileExistsError:
                        #     self.logging.info('Такая папка уже есть ' + str(path_dir))
                        os.makedirs(path_dir, exist_ok=True)
                        for device in range(1, number_device):
                            os.makedirs(pathlib.Path(path_dir, str(device), 'photo'), exist_ok=True)
                            os.makedirs(pathlib.Path(path_dir, str(device), 'rentgen'), exist_ok=True)
                            # try:
                            #     os.makedirs(pathlib.Path(path_dir, str(device), 'photo'))
                            # except FileExistsError:
                            #     self.logging.info('Такая папка уже есть ' + str(pathlib.Path(path_dir,
                            #                                                                  str(device), 'photo')))
                            # try:
                            #     os.makedirs(pathlib.Path(path_dir, str(device), 'rentgen'))
                            # except FileExistsError:
                            #     self.logging.info('Такая папка уже есть ' + str(pathlib.Path(path_dir,
                            #                                                                  str(device), 'rentgen')))
                    df.columns = name_for_df
                    df.reset_index(drop=True, inplace=True)
                    size = df.shape
                    percent += (size[0] - 1) * (number_device - 1)
                    list_df.append(df)
                    self.logging.info('Файл ' + file_load_asu + ' обработан')
                except BaseException as error:
                    self.logging.error(error)
                    self.logging.error(traceback.format_exc())
                    self.status.emit('Что-то не так с файлом ' + file_load_asu)
            percent = 100 / percent
            name_info = 'Инфо'
            name_spk = 'СПК'
            self.logging.info('Бежим по файлам СП')
            self.status.emit('Начинаем сортировку указанных файлов СП')
            for name_device in os.listdir(self.path_material_sp):
                if self.pause_threading():
                    return
                if name_device.lower() == 'инфо':
                    name_info = name_device
                elif name_device.lower() == 'спк':
                    name_spk = name_device
                else:
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
                                        self.logging.info(str(path_photo) +
                                                          ' - почему то такого пути для фото нет, создаём')
                                        errors.append(str(path_photo) +
                                                      ' - почему то такого пути для фото нет, создаём')
                                        path_photo.mkdir(parents=True)
                                    if pathlib.Path(path_rentgen).is_dir() is False:
                                        self.logging.info(str(path_rentgen) +
                                                          ' - почему то такого пути для рентгена нет, создаём')
                                        errors.append(str(path_rentgen) +
                                                      ' - почему то такого пути для рентгена нет, создаём')
                                        path_rentgen.mkdir(parents=True)
                        file_in_finish = [str(file) for file in os.listdir(pathlib.Path(self.path_material_sp,
                                                                                        name_device, str(sn_device)))]
                        self.logging.info('Копируемые файлы: ' + ', '.join(file_in_finish))
                        exist_file = [str(file) for file in file_in_finish
                                      if file in os.listdir(pathlib.Path(path_rentgen))
                                      or file in os.listdir(pathlib.Path(path_photo))]
                        replace = True
                        if exist_file:
                            self.logging.info('Файлы, присутствующие в папке ' + str(path_rentgen.parent)
                                              + ': ' + ', '.join(exist_file))
                            self.logging.info('Спрашиваем что делать')
                            replace = self.pause_threading(exist_file, str(path_rentgen.parent))
                        if replace:
                            for file in os.listdir(pathlib.Path(self.path_material_sp, name_device, str(sn_device))):
                                if file in exist_file and replace is False:
                                    continue
                                if str(file).endswith('.tif') or str(file).endswith('.tiff') \
                                        or str(file).endswith('.png') or str(file).endswith('.jpeg'):
                                    pathlib.Path(self.path_material_sp, name_device,
                                                 str(sn_device), str(file)).replace(
                                        pathlib.Path(path_rentgen, str(file)))
                                else:
                                    pathlib.Path(self.path_material_sp, name_device,
                                                 str(sn_device), str(file)).replace(pathlib.Path(path_photo, str(file)))
                        current_progress += percent
                        self.progress.emit(int(current_progress))

            def info_spk_copy(path_info_spk, name_info_spk):
                for file_info_spk in os.listdir(path_info_spk):
                    sn_file = str(file_info_spk).partition('_')[2].rpartition('.')[0]
                    sn_file = sn_file + ' В'
                    for finish_set in os.listdir(pathlib.Path(self.path_finish_folder,
                                                              name_finish_folder)):
                        replace_info_spk = True
                        if sn_file in os.listdir(pathlib.Path(self.path_finish_folder,
                                                              name_finish_folder, str(finish_set))):
                            self.logging.info('Перемещаем\n' + str(pathlib.Path(self.path_material_sp,
                                                                                file_info_spk,
                                                                                str(file_info_spk)))
                                              + '\nв\n' +
                                              str(pathlib.Path(self.path_finish_folder,
                                                               name_finish_folder, str(finish_set), sn_file,
                                                               file_info_spk))
                                              )
                            if pathlib.Path(self.path_finish_folder, name_finish_folder, str(finish_set),
                                            sn_file, file_info_spk).is_file():
                                self.logging.info('Файл ' + str(pathlib.Path(self.path_finish_folder,
                                                                             name_finish_folder,
                                                                             str(finish_set),
                                                                             sn_file,
                                                                             file_info_spk))
                                                  + 'уже есть в папке.')
                                self.logging.info('Спрашиваем что делать')
                                replace_info_spk = self.pause_threading(file_info_spk,
                                                                        str(pathlib.Path(self.path_finish_folder,
                                                                                         name_finish_folder,
                                                                                         str(finish_set),
                                                                                         sn_file,
                                                                                         file_info_spk)))
                            if replace_info_spk:
                                pathlib.Path(self.path_material_sp, name_info_spk,
                                             str(file_info_spk)).replace(pathlib.Path(self.path_finish_folder,
                                                                                      name_finish_folder,
                                                                                      str(finish_set),
                                                                                      sn_file,
                                                                                      file_info_spk))

            if pathlib.Path(self.path_material_sp, name_info).is_dir():
                info_spk_copy(pathlib.Path(self.path_material_sp, name_info), name_info)
            if pathlib.Path(self.path_material_sp, name_spk).is_dir():
                info_spk_copy(pathlib.Path(self.path_material_sp, name_spk), name_spk)

            self.logging.info('Готово')
            self.logging.info('\n******************************Конец работы******************************\n')
            self.status.emit('Готово')
            self.progress.emit(100)
            os.chdir(self.path_for_default)
            return
        except BaseException as error:
            self.logging.error(error)
            self.logging.error(traceback.format_exc())
            self.logging.info('\n******************************Конец работы******************************\n')
            self.progress.emit(0)
            self.status.emit('Ошибка!')
            os.chdir(self.path_for_default)
            return

    def pause_threading(self, data=None, folder=None):
        user_pause = False if self.queue.empty() else self.queue.get_nowait()
        if data:
            if len(data) == 1:
                self.messageChanged.emit('Вопрос?', 'В папке "' + folder + '" уже есть файл '
                                         + data[0] + ' Заменить файл?')
            else:
                self.messageChanged.emit('Вопрос?', 'В папке "' + folder + '" уже есть файлы ('
                                         + str(len(data)) + ') с такими же именами.'
                                                            ' Заменить файлы?')
            self.event.wait()
            self.event.clear()
            return True if self.queue.get_nowait() else False
        elif user_pause:
            self.messageChanged.emit('Пауза', 'Проверка остановлена пользователем. Нажмите «Да» для продолжения'
                                              ' или «Нет» для прерывания')
            self.event.wait()
            self.event.clear()
            if self.queue.get_nowait():
                self.status.emit('Прервано пользователем')
                self.progress.emit(0)
                return True
        return False
