import math
import os
import time
import traceback
from pathlib import Path

import pandas as pd


def read_asu(incoming_data: dict, current_progress: float, now_doc: int, all_doc: int, line_doing, line_progress,
             progress_value, event, window_check, info_value) -> dict:
    logging = incoming_data['logging']
    try:
        errors = []
        list_df = []
        percent = incoming_data['percent']
        if incoming_data['asu_man']:
            line_doing.emit("Считаем количество комплектов")
            name_finish_folder = incoming_data['name_gk'] if incoming_data['name_gk'] else 'Номер ГК'
            try:
                os.mkdir(Path(incoming_data['path_finish_folder'], name_finish_folder))
            except FileExistsError:
                logging.info(f"Такая папка уже есть {Path(incoming_data['path_finish_folder'], name_finish_folder)}")
            logging.info('Считываем файлы АСУ и создаем структуру каталога')
        else:
            name_finish_folder = incoming_data['name_gk'] if incoming_data['name_gk'] else 'Номер ГК'
            try:
                df = pd.read_csv(Path(incoming_data['path_load_man']), header=None, delimiter=';', encoding='ANSI')
            except BaseException as error:
                logging.error(error)
                logging.error(traceback.format_exc())
                logging.info(f"Файл {Path(incoming_data['path_load_man']).name} не обработан из-за непредвиденной ошибки")
                return {'error': True, 'text': error, 'trace': traceback.format_exc()}
            # Отловить permission denied
            logging.info(f"Считываем файл выгрузки {Path(incoming_data['path_load_man']).name}")
            name_set = df.iloc[1, 1]
            number_device = sorted(set(df.iloc[0, 2:].values.tolist()))
            df = df.drop(labels=[0], axis=1)
            df = df.drop(labels=[1], axis=0)
            logging.info(f"Создаём структуру для {Path(incoming_data['path_load_man']).name}")
            sn_device = df[1].to_numpy().tolist()[1:]
            for serial_num in sn_device:
                # if window_check.stop_threading:
                #     return {'error': False, 'text': 'cancel', 'trace': ''}
                path_dir = Path(incoming_data['path_finish_folder'], name_finish_folder, str(name_set), str(serial_num))
                os.makedirs(path_dir, exist_ok=True)
                for device in number_device:
                    os.makedirs(Path(path_dir, str(device), 'photo'), exist_ok=True)
                    os.makedirs(Path(path_dir, str(device), 'rentgen'), exist_ok=True)
            # df = df.drop(labels=[0], axis=1)
            for column in list(df):
                sn_list = df[column].to_numpy().tolist()[1:]
                # for sn in df[column].to_numpy().tolist()[1:]:
                #     # отсюда поиск по первой df серийника
                #     pass
        for file_load_asu in os.listdir(incoming_data['path_load_asu']):
            try:
                logging.info('Считываем файл выгрузки ' + file_load_asu)
                # Отловить permission denied
                df = pd.read_excel(Path(incoming_data['path_load_asu'], file_load_asu), sheet_name=0, header=None)
                index_string = -100
                for index, item in df.iloc[0].items():
                    if math.isnan(item):
                        df.iloc[0, index] = index_string
                        index_string += 1
                number_device = df.shape[1] - (100 + index_string) + 1
                df.sort_values(0, axis=1, inplace=True)
                name_for_df = df.iloc[1]
                df = df.drop(labels=[1], axis=0)
                if incoming_data['name_set']:
                    df.fillna(value={2: incoming_data['name_set']}, inplace=True)
                name_set = df[2].to_numpy().tolist()
                logging.info(f"Создаём структуру для {file_load_asu}")
                for row, serial_num in enumerate(df[3].to_numpy().tolist()[1:], start=1):
                    # event.wait()
                    if window_check.stop_threading:
                        return {'error': False, 'text': 'cancel', 'trace': ''}
                    path_dir = Path(incoming_data['path_finish_folder'], name_finish_folder,
                                    str(name_set[row]), str(serial_num) + ' В')
                    os.makedirs(path_dir, exist_ok=True)
                    for device in range(1, number_device):
                        os.makedirs(Path(path_dir, str(device), 'photo'), exist_ok=True)
                        os.makedirs(Path(path_dir, str(device), 'rentgen'), exist_ok=True)
                df.columns = name_for_df
                df.reset_index(drop=True, inplace=True)
                list_df.append(df)
                logging.info(f"Файл {file_load_asu} обработан")
            except BaseException as error:
                logging.error(error)
                logging.error(traceback.format_exc())
                logging.info(f"Файл {file_load_asu} не обработан из-за непредвиденной ошибки")

            name_info = ''
            name_spk = ''
            logging.info('Бежим по файлам СП')
            name_device_list = [path for path in os.listdir(incoming_data['path_material_sp'])
                                if os.path.isdir(Path(incoming_data['path_material_sp'], path))]
            for name_device in name_device_list:
                # time.sleep(1)
                if window_check.stop_threading:
                    return {'error': False, 'text': 'cancel', 'trace': ''}
                if name_device.lower() == 'инфо':
                    name_info = name_device
                    continue
                elif name_device.lower() == 'спк':
                    name_spk = name_device
                    continue
                logging.info('Бежим по ' + str(name_device))
                sn_device_list = [path for path in os.listdir(Path(incoming_data['path_material_sp'], name_device))
                                  if os.path.isdir(Path(incoming_data['path_material_sp'], name_device, path))]
                for sn_device in sn_device_list:
                    logging.info('Бежим по ' + str(sn_device))
                    line_doing.emit(f'Сортируем устройства с sn {sn_device} ({now_doc} из {all_doc})')
                    path_photo = False
                    path_xray = False
                    for device in list_df:
                        if name_device in device:
                            if device[name_device].isin([sn_device]).any():
                                row = device.index[device[name_device] == sn_device].tolist()[0]
                                column = device.loc[0, name_device]
                                # 3
                                path_photo = Path(incoming_data['path_finish_folder'], name_finish_folder,
                                                  str(device.iloc[row, 2]), str(device.iloc[row, 3]) + ' В',
                                                  str(column), 'photo')
                                path_xray = Path(incoming_data['path_finish_folder'], name_finish_folder,
                                                 str(device.iloc[row, 2]), str(device.iloc[row, 3]) + ' В',
                                                 str(column), 'rentgen')
                                if Path(path_photo).is_dir() is False:
                                    logging.info(f"{path_photo} - почему то пути для фото нет, создаём")
                                    errors.append(f"{path_photo} - почему то пути для фото нет, создаём")
                                    path_photo.mkdir(parents=True)
                                if Path(path_xray).is_dir() is False:
                                    logging.info(f"{path_xray} - почему то пути для рентгена нет, создаём")
                                    errors.append(f"{path_xray} - почему то пути для рентгена нет, создаём")
                                    path_xray.mkdir(parents=True)
                                # /3
                    if path_photo is False or path_xray is False:
                        errors.append(f"Серийник {sn_device} не найден в выгрузке АСУ")
                        logging.warning(f"Серийник {sn_device} не найден в выгрузке АСУ")
                        continue
                    file_in_finish = [str(file) for file in os.listdir(Path(incoming_data['path_material_sp'],
                                                                            name_device, str(sn_device)))]
                    logging.info('Копируемые файлы: ' + ', '.join(file_in_finish))
                    exist_file = [str(file) for file in file_in_finish
                                  if file in os.listdir(Path(path_xray))
                                  or file in os.listdir(Path(path_photo))]
                    replace = True
                    # 2
                    if exist_file:
                        logging.info(f"Файлы, присутствующие в папке {path_xray.parent}: {', '.join(exist_file)}")
                        logging.info('Спрашиваем что делать')
                        if len(exist_file) == 1:
                            text = f"В папке «{path_xray.parent}» уже есть файл {exist_file[0]}. Заменить файл?"
                        else:
                            text = f"В папке «{path_xray.parent}» уже есть файлы ({len(exist_file)})" \
                                   f" с такими же именами. Заменить файлы?"
                        info_value.emit("Вопрос?", text)
                        event.clear()
                        event.wait()
                        replace = window_check.answer
                    # /2
                    if replace:
                        # 1
                        for file in os.listdir(Path(incoming_data['path_material_sp'], name_device, str(sn_device))):
                            now_doc += 1
                            if file in exist_file and replace is False:
                                continue
                            if str(file).endswith('.tif') or str(file).endswith('.tiff') \
                                    or str(file).endswith('.png') or str(file).endswith('.jpeg'):
                                Path(incoming_data['path_material_sp'], name_device,
                                     str(sn_device), str(file)).replace(
                                    Path(path_xray, str(file)))
                            else:
                                Path(incoming_data['path_material_sp'], name_device,
                                     str(sn_device), str(file)).replace(Path(path_photo, str(file)))
                        # /1
                            current_progress += percent
                            line_progress.emit(f'Выполнено {int(current_progress)} %')
                            progress_value.emit(int(current_progress))
                        logging.info('Файл заменён')
                    else:
                        current_progress += percent*len(exist_file)
                        line_progress.emit(f'Выполнено {int(current_progress)} %')
                        progress_value.emit(int(current_progress))

            def info_spk_copy(path_info_spk: Path, name_info_spk: str, now_doc_: int, cur_prog: float) -> dict:
                for file_info_spk in os.listdir(path_info_spk):
                    time.sleep(1)
                    now_doc_ += 1
                    line_doing.emit(f'Сортируем устройства с sn {sn_device} ({now_doc_} из {all_doc})')
                    cur_prog += percent
                    line_progress.emit(f'Выполнено {int(cur_prog)} %')
                    progress_value.emit(int(cur_prog))
                    sn_file = str(file_info_spk).partition('_')[2].rpartition('.')[0]
                    sn_file = sn_file + ' В'
                    for finish_set in os.listdir(Path(incoming_data['path_finish_folder'], name_finish_folder)):
                        replace_info_spk = True
                        if sn_file in os.listdir(Path(incoming_data['path_finish_folder'],
                                                      name_finish_folder, str(finish_set))):
                            logging.info('Перемещаем\n' + str(Path(incoming_data['path_material_sp'],
                                                                   file_info_spk,
                                                                   str(file_info_spk)))
                                         + '\nв\n' +
                                         str(Path(incoming_data['path_finish_folder'],
                                                  name_finish_folder, str(finish_set), sn_file, file_info_spk)))
                            if Path(incoming_data['path_finish_folder'], name_finish_folder, str(finish_set),
                                    sn_file, file_info_spk).is_file():
                                file_path = Path(incoming_data['path_finish_folder'], name_finish_folder,
                                                 str(finish_set), sn_file, file_info_spk)
                                text_info = f"Файл {file_info_spk} уже есть в папке {file_path}"
                                logging.info(text_info)
                                logging.info('Спрашиваем что делать')
                                info_value.emit("Вопрос?", text_info + " Заменить файл?")
                                event.clear()
                                event.wait()
                                replace_info_spk = window_check.answer
                            if replace_info_spk:
                                Path(incoming_data['path_material_sp'], name_info_spk,
                                     str(file_info_spk)).replace(Path(incoming_data['path_finish_folder'],
                                                                      name_finish_folder, str(finish_set),
                                                                      sn_file, file_info_spk))
                return {"now_doc": now_doc_, "current_progress": cur_prog}
            if Path(incoming_data['path_material_sp'], name_info).is_dir():
                answer = info_spk_copy(Path(incoming_data['path_material_sp'], name_info), name_info, now_doc, current_progress)
                now_doc, current_progress = answer['now_doc'], answer['current_progress']
            if Path(incoming_data['path_material_sp'], name_spk).is_dir():
                info_spk_copy(Path(incoming_data['path_material_sp'], name_spk), name_spk, now_doc, current_progress)
                # now_doc, current_progress = answer['now_doc'], answer['current_progress']
            if errors:
                logging.info('Отправляем ошибки')
                return {'error': False, 'text': '\n'.join(errors), 'trace': ''}
            else:
                return {'error': False, 'text': '', 'trace': ''}
    except BaseException as error:
        return {'error': True, 'text': error, 'trace': traceback.format_exc()}
