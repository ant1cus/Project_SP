import os
import threading
import time
import traceback
import pandas as pd
import pathlib
import shutil
from natsort import natsorted
from PyQt5.QtCore import QThread, pyqtSignal
from DoingWindow import ProcessWindow


class CancelException(Exception):
    pass


class SortingFile(QThread):
    status_finish = pyqtSignal(str, str)
    progress_value = pyqtSignal(int)
    info_value = pyqtSignal(str, str)
    status = pyqtSignal(str)
    line_progress = pyqtSignal(str)
    line_doing = pyqtSignal(str)

    def __init__(self, incoming_data):  # Список переданных элементов.
        QThread.__init__(self)
        self.path_material_sp = incoming_data['path_material_sp']
        self.path_load_asu = incoming_data['path_load_asu']
        self.path_finish_folder = incoming_data['path_finish_folder']
        self.name_gk = incoming_data['name_gk']
        self.name_set = incoming_data['name_set']
        self.logging = incoming_data['logging']
        self.queue = incoming_data['queue']
        self.default_path = incoming_data['default_path']
        self.event = threading.Event()
        self.event.set()
        self.now_doc = 0
        self.all_doc = 0
        self.percent_progress = 0
        self.move = incoming_data['move']
        self.name_dir = pathlib.Path(self.path_material_sp).name
        title = f'Сортировка файлов в папке «{self.name_dir}»'
        self.window_check = ProcessWindow(self.default_path, self.event, self.move, title)
        self.progress_value.connect(self.window_check.progressBar.setValue)
        self.line_progress.connect(self.window_check.lineEdit_progress.setText)
        self.line_doing.connect(self.window_check.lineEdit_doing.setText)
        self.info_value.connect(self.window_check.info_message)
        self.window_check.show()

    def run(self):
        try:
            incoming_errors = []
            current_progress = 0
            self.logging.info('Начинаем заполнение документов, читаем значения из файла')
            files = [file for file in os.listdir(self.start_path) if file.endswith('.xlsx') and '~' not in file]
            files = natsorted(files)
            self.all_doc = len(files)
            self.percent_progress = 100 / len(files)
            self.line_progress.emit(f'Выполнено {int(current_progress)} %')
            self.progress_value.emit(0)
            if self.unloading_file.endswith('.txt'):
                df = pd.read_csv(self.unloading_file, delimiter='|', encoding='ANSI',
                                 header=None, converters={0: str, 6: str, 11: str})
                df.drop([i for i in range(df.shape[1]) if i not in [0, 6, 11]], axis=1, inplace=True)
                df = df[[0, 11, 6]]
                df.columns = range(df.shape[1])
            else:
                df = pd.read_excel(self.unloading_file, converters={'B': str, 'C': str}, header=None)
                df.columns = range(df.shape[1])
            self.logging.info('DataFrame заполнен, начинаем переименование и перенос')
            for file in files:
                self.now_doc += 1
                self.line_doing.emit(f'Генерируем файлы для комплекта {file} ({self.now_doc} из {self.all_doc})')
                self.event.wait()
                if self.window_check.stop_threading:
                    raise CancelException()
                self.logging.info(f'Поиск файла {file} ({self.now_doc} из {self.all_doc})')
                set_index = df[df[1] == file.rpartition('.')[0]].index.tolist()
                device_index = df[df[2] == file.rpartition('.')[0]].index.tolist()
                if not set_index and not device_index:
                    self.logging.info(f'{file} не найден в выгрузке, продолжаем')
                    current_progress += self.percent_progress
                    self.line_progress.emit(f'Выполнено {int(current_progress)} %')
                    self.progress_value.emit(int(current_progress))
                    continue
                if len(set_index) > 0:
                    self.logging.info(f'Берем имя в номере комплекта')
                    new_name = str(df.iloc[set_index[0], 0])
                else:
                    self.logging.info(f'Берем имя в номере устройства')
                    new_name = str(df.iloc[device_index[0], 0])
                new_name = new_name.partition('.')[2] + '.xlsx'
                if new_name is False:
                    self.logging.info(f'Не удалось извлечь новое имя файла')
                    incoming_errors.append(f'Неверно указан номер комплекта у файла {file}'
                                           f'(отсутствует нужный разделитель «.»)')
                    current_progress += self.percent_progress
                    self.line_progress.emit(f'Выполнено {int(current_progress)} %')
                    self.progress_value.emit(int(current_progress))
                    continue
                try:
                    shutil.copy(pathlib.Path(self.start_path, file), pathlib.Path(self.finish_path, new_name))
                    self.logging.info(f'Скопировали файл в новую папку')
                except PermissionError:
                    self.logging.info(f'Не удалось скопировать файл')
                    incoming_errors.append(f'Не удалось скопировать файл {file}')
                    current_progress += self.percent_progress
                    self.line_progress.emit(f'Выполнено {int(current_progress)} %')
                    self.progress_value.emit(int(current_progress))
                    continue
                try:
                    os.remove(pathlib.Path(self.start_path, file))
                    self.logging.info(f'Удалили старый файл')
                except PermissionError:
                    self.logging.info(f'Не удалось удалить файл')
                    incoming_errors.append(f'Не удалось удалить файл {file}')
                current_progress += self.percent_progress
                self.line_progress.emit(f'Выполнено {int(current_progress)} %')
                self.progress_value.emit(int(current_progress))
            self.line_progress.emit(f'Выполнено 100 %')
            self.progress_value.emit(int(100))
            if incoming_errors:
                self.logging.info(f"Поиск файлов в папке «{self.name_dir}» завершён с ошибками")
                self.logging.info('\n'.join(incoming_errors))
                err = '\n' + '\n'.join(incoming_errors)
                self.info_value.emit('УПС!', f"Ошибки при работе программы:{err}")
                self.event.clear()
                self.event.wait()
                self.status.emit(f"Поиск файлов в папке «{self.name_dir}» завершён с ошибками")
                os.chdir(self.default_path)
                self.status_finish.emit('finding_files', str(self))
                time.sleep(1)  # Не удалять, не успевает отработать emit status_finish. Может потом
                self.window_check.close()
                return
            else:
                self.logging.info(f"Поиск файлов в папке «{self.name_dir}» успешно завершен")
                os.chdir(self.default_path)
                self.status.emit(f"Поиск файлов в папке «{self.name_dir}» успешно завершен")
                self.status_finish.emit('finding_files', str(self))
                time.sleep(1)  # Не удалять, не успевает отработать emit status_finish. Может потом
                self.window_check.close()
                # print(datetime.datetime.now() - start_time)
                return
        except CancelException:
            self.logging.warning(f"Поиск файлов в папке «{self.name_dir}» отменён пользователем")
            self.status.emit(f"Поиск файлов в папке «{self.name_dir}» отменён пользователем")
            os.chdir(self.default_path)
            self.status_finish.emit('finding_files', str(self))
            time.sleep(1)  # Не удалять, не успевает отработать emit status_finish. Может потом
            self.window_check.close()
            return
        except BaseException as es:
            self.logging.error(es)
            self.logging.error(traceback.format_exc())
            self.logging.warning(f"Поиск файлов в папке «{self.name_dir}» не завершён из-за ошибки")
            self.info_value.emit('УПС!', 'Работа программы завершена из-за непредвиденной ошибки')
            self.event.clear()
            self.event.wait()
            self.status.emit(f"Ошибка при поиске файлов в папке «{self.name_dir}»")
            os.chdir(self.default_path)
            self.status_finish.emit('finding_files', str(self))
            time.sleep(1)  # Не удалять, не успевает отработать emit status_finish. Может потом
            self.window_check.close()
            return
    # def run(self):
    #     try:
    #         current_progress = 0
    #         self.logging.info('\n******************************Новый прогон******************************\n')
    #         self.logging.info('Начинаем процедуру сортировки файлов')
    #         self.status.emit('Старт')
    #         self.progress.emit(current_progress)
    #         percent = 1
    #         errors = []
    #         name_finish_folder = self.name_gk if self.name_gk else 'Номер ГК'
    #         try:
    #             os.mkdir(pathlib.Path(self.path_finish_folder, name_finish_folder))
    #         except FileExistsError:
    #             self.logging.info('Такая папка уже есть ' + str(pathlib.Path(self.path_finish_folder,
    #                                                                          name_finish_folder)))
    #         self.logging.info('Создаём структуру папок')
    #         self.status.emit('Создаём структуру папок')
    #         list_df = []
    #         for file_load_asu in os.listdir(self.path_load_asu):
    #             try:
    #                 self.logging.info('Считываем файл выгрузки ' + file_load_asu)
    #                 df = pd.read_excel(self.path_load_asu + '\\' + file_load_asu, sheet_name=0, header=None)
    #                 index_string = -100
    #                 for index, item in df.iloc[0].items():
    #                     if math.isnan(item):
    #                         df.iloc[0, index] = index_string
    #                         index_string += 1
    #                 number_device = df.shape[1] - (100 + index_string) + 1
    #                 df.sort_values(0, axis=1, inplace=True)
    #                 name_for_df = df.iloc[1]
    #                 df = df.drop(labels=[1], axis=0)
    #                 if self.name_set:
    #                     df.fillna(value={2: self.name_set}, inplace=True)
    #                 name_set = df[2].to_numpy().tolist()
    #                 # name_set = df[2].to_numpy().tolist() if self.name_set is False else [self.name_set] * len(df)
    #                 self.logging.info('Создаём структуру для ' + file_load_asu)
    #                 for row, serial_num in enumerate(df[3].to_numpy().tolist()[1:], start=1):
    #                     if self.pause_threading():
    #                         return
    #                     path_dir = pathlib.Path(self.path_finish_folder, name_finish_folder,
    #                                             str(name_set[row]), str(serial_num) + ' В')
    #                     # if math.isnan(df.iloc[row, 2]):
    #                     #     df.iloc[row, 2] = str(name_set[row])
    #                     # try:
    #                     #     os.makedirs(path_dir)
    #                     # except FileExistsError:
    #                     #     self.logging.info('Такая папка уже есть ' + str(path_dir))
    #                     os.makedirs(path_dir, exist_ok=True)
    #                     for device in range(1, number_device):
    #                         os.makedirs(pathlib.Path(path_dir, str(device), 'photo'), exist_ok=True)
    #                         os.makedirs(pathlib.Path(path_dir, str(device), 'rentgen'), exist_ok=True)
    #                         # try:
    #                         #     os.makedirs(pathlib.Path(path_dir, str(device), 'photo'))
    #                         # except FileExistsError:
    #                         #     self.logging.info('Такая папка уже есть ' + str(pathlib.Path(path_dir,
    #                         #                                                                  str(device), 'photo')))
    #                         # try:
    #                         #     os.makedirs(pathlib.Path(path_dir, str(device), 'rentgen'))
    #                         # except FileExistsError:
    #                         #     self.logging.info('Такая папка уже есть ' + str(pathlib.Path(path_dir,
    #                         #                                                                  str(device), 'rentgen')))
    #                 df.columns = name_for_df
    #                 df.reset_index(drop=True, inplace=True)
    #                 size = df.shape
    #                 percent += (size[0] - 1) * (number_device - 1)
    #                 list_df.append(df)
    #                 self.logging.info('Файл ' + file_load_asu + ' обработан')
    #             except BaseException as error:
    #                 self.logging.error(error)
    #                 self.logging.error(traceback.format_exc())
    #                 self.status.emit('Что-то не так с файлом ' + file_load_asu)
    #         percent = 100 / percent
    #         name_info = 'Инфо'
    #         name_spk = 'СПК'
    #         self.logging.info('Бежим по файлам СП')
    #         self.status.emit('Начинаем сортировку указанных файлов СП')
    #         for name_device in [path for path in os.listdir(self.path_material_sp) if os.path.isdir(
    #                 pathlib.Path(self.path_material_sp, path))]:
    #             if self.pause_threading():
    #                 return
    #             if name_device.lower() == 'инфо':
    #                 name_info = name_device
    #             elif name_device.lower() == 'спк':
    #                 name_spk = name_device
    #             else:
    #                 self.logging.info('Бежим по ' + str(name_device))
    #                 for sn_device in [path for path in os.listdir(pathlib.Path(self.path_material_sp, name_device)) if
    #                                   os.path.isdir(pathlib.Path(self.path_material_sp, name_device, path))]:
    #                     self.logging.info('Бежим по ' + str(sn_device))
    #                     self.status.emit('Сортируем устройства с sn ' + str(sn_device))
    #                     path_photo = False
    #                     path_rentgen = False
    #                     for device in list_df:
    #                         if name_device in device:
    #                             if device[name_device].isin([sn_device]).any():
    #                                 row = device.index[device[name_device] == sn_device].tolist()[0]
    #                                 column = device.loc[0, name_device]
    #                                 path_photo = pathlib.Path(self.path_finish_folder, name_finish_folder,
    #                                                           str(device.iloc[row, 2]), str(device.iloc[row, 3]) + ' В',
    #                                                           str(column), 'photo')
    #                                 path_rentgen = pathlib.Path(self.path_finish_folder, name_finish_folder,
    #                                                             str(device.iloc[row, 2]), str(device.iloc[row, 3]) + ' В',
    #                                                             str(column), 'rentgen')
    #                                 if pathlib.Path(path_photo).is_dir() is False:
    #                                     self.logging.info(str(path_photo) +
    #                                                       ' - почему то такого пути для фото нет, создаём')
    #                                     errors.append(str(path_photo) +
    #                                                   ' - почему то такого пути для фото нет, создаём')
    #                                     path_photo.mkdir(parents=True)
    #                                 if pathlib.Path(path_rentgen).is_dir() is False:
    #                                     self.logging.info(str(path_rentgen) +
    #                                                       ' - почему то такого пути для рентгена нет, создаём')
    #                                     errors.append(str(path_rentgen) +
    #                                                   ' - почему то такого пути для рентгена нет, создаём')
    #                                     path_rentgen.mkdir(parents=True)
    #                     if path_photo is False or path_rentgen is False:
    #                         errors.append('Серийник ' + str(sn_device) + ' не найден в выгрузке АСУ')
    #                         self.logging.warning('Серийник ' + str(sn_device) + ' не найден в выгрузке АСУ')
    #                         continue
    #                     file_in_finish = [str(file) for file in os.listdir(pathlib.Path(self.path_material_sp,
    #                                                                                     name_device, str(sn_device)))]
    #                     self.logging.info('Копируемые файлы: ' + ', '.join(file_in_finish))
    #                     exist_file = [str(file) for file in file_in_finish
    #                                   if file in os.listdir(pathlib.Path(path_rentgen))
    #                                   or file in os.listdir(pathlib.Path(path_photo))]
    #                     replace = True
    #                     if exist_file:
    #                         self.logging.info('Файлы, присутствующие в папке ' + str(path_rentgen.parent)
    #                                           + ': ' + ', '.join(exist_file))
    #                         self.logging.info('Спрашиваем что делать')
    #                         replace = self.pause_threading(exist_file, str(path_rentgen.parent))
    #                     if replace:
    #                         for file in os.listdir(pathlib.Path(self.path_material_sp, name_device, str(sn_device))):
    #                             if file in exist_file and replace is False:
    #                                 continue
    #                             if str(file).endswith('.tif') or str(file).endswith('.tiff') \
    #                                     or str(file).endswith('.png') or str(file).endswith('.jpeg'):
    #                                 pathlib.Path(self.path_material_sp, name_device,
    #                                              str(sn_device), str(file)).replace(
    #                                     pathlib.Path(path_rentgen, str(file)))
    #                             else:
    #                                 pathlib.Path(self.path_material_sp, name_device,
    #                                              str(sn_device), str(file)).replace(pathlib.Path(path_photo, str(file)))
    #                     current_progress += percent
    #                     self.progress.emit(int(current_progress))
    #
    #         def info_spk_copy(path_info_spk, name_info_spk):
    #             for file_info_spk in os.listdir(path_info_spk):
    #                 sn_file = str(file_info_spk).partition('_')[2].rpartition('.')[0]
    #                 sn_file = sn_file + ' В'
    #                 for finish_set in os.listdir(pathlib.Path(self.path_finish_folder,
    #                                                           name_finish_folder)):
    #                     replace_info_spk = True
    #                     if sn_file in os.listdir(pathlib.Path(self.path_finish_folder,
    #                                                           name_finish_folder, str(finish_set))):
    #                         self.logging.info('Перемещаем\n' + str(pathlib.Path(self.path_material_sp,
    #                                                                             file_info_spk,
    #                                                                             str(file_info_spk)))
    #                                           + '\nв\n' +
    #                                           str(pathlib.Path(self.path_finish_folder,
    #                                                            name_finish_folder, str(finish_set), sn_file,
    #                                                            file_info_spk))
    #                                           )
    #                         if pathlib.Path(self.path_finish_folder, name_finish_folder, str(finish_set),
    #                                         sn_file, file_info_spk).is_file():
    #                             self.logging.info('Файл ' + str(pathlib.Path(self.path_finish_folder,
    #                                                                          name_finish_folder,
    #                                                                          str(finish_set),
    #                                                                          sn_file,
    #                                                                          file_info_spk))
    #                                               + ' уже есть в папке.')
    #                             self.logging.info('Спрашиваем что делать')
    #                             replace_info_spk = self.pause_threading(file_info_spk,
    #                                                                     str(pathlib.Path(self.path_finish_folder,
    #                                                                                      name_finish_folder,
    #                                                                                      str(finish_set),
    #                                                                                      sn_file,
    #                                                                                      file_info_spk)))
    #                         if replace_info_spk:
    #                             pathlib.Path(self.path_material_sp, name_info_spk,
    #                                          str(file_info_spk)).replace(pathlib.Path(self.path_finish_folder,
    #                                                                                   name_finish_folder,
    #                                                                                   str(finish_set),
    #                                                                                   sn_file,
    #                                                                                   file_info_spk))
    #
    #         if pathlib.Path(self.path_material_sp, name_info).is_dir():
    #             info_spk_copy(pathlib.Path(self.path_material_sp, name_info), name_info)
    #         if pathlib.Path(self.path_material_sp, name_spk).is_dir():
    #             info_spk_copy(pathlib.Path(self.path_material_sp, name_spk), name_spk)
    #         if errors:
    #             self.logging.info('Отправляем ошибки')
    #             self.messageChanged.emit('УПС!', '\n'.join(errors))
    #             self.status.emit('Готово с ошибками')
    #         else:
    #             self.status.emit('Готово')
    #         self.logging.info('Готово')
    #         self.logging.info('\n*****************************Конец работы*****************************\n')
    #         self.progress.emit(100)
    #         os.chdir(self.default_path)
    #         return
    #     except BaseException as error:
    #         self.logging.error(error)
    #         self.logging.error(traceback.format_exc())
    #         self.logging.info('\n*****************************Конец работы*****************************\n')
    #         self.progress.emit(0)
    #         self.status.emit('Ошибка!')
    #         os.chdir(self.default_path)
    #         return
    #
    # def pause_threading(self, data=None, folder=None):
    #     user_pause = False if self.queue.empty() else self.queue.get_nowait()
    #     if data:
    #         if len(data) == 1:
    #             self.messageChanged.emit('Вопрос?', 'В папке "' + folder + '" уже есть файл '
    #                                      + data[0] + ' Заменить файл?')
    #         else:
    #             self.messageChanged.emit('Вопрос?', 'В папке "' + folder + '" уже есть файлы ('
    #                                      + str(len(data)) + ') с такими же именами.'
    #                                                         ' Заменить файлы?')
    #         self.event.wait()
    #         self.event.clear()
    #         return True if self.queue.get_nowait() else False
    #     elif user_pause:
    #         self.messageChanged.emit('Пауза', 'Проверка остановлена пользователем. Нажмите «Да» для продолжения'
    #                                           ' или «Нет» для прерывания')
    #         self.event.wait()
    #         self.event.clear()
    #         if self.queue.get_nowait():
    #             self.status.emit('Прервано пользователем')
    #             self.progress.emit(0)
    #             return True
    #     return False
