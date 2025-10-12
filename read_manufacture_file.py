import os
import re
import shutil
import traceback
from pathlib import Path

import pandas as pd


def copy_from_manufacture(incoming_data: dict, current_progress: float, now_doc: int, all_doc: int, line_doing,
                          line_progress, progress_value, event, window_check, info_value) -> dict:
    logging = incoming_data['logging']
    errors = []
    try:
        line_doing.emit(f'Считываем файл выгрузки')
        name_finish_folder = incoming_data['name_gk'] if incoming_data['name_gk'] else 'Номер ГК'
        try:
            df = pd.read_csv(Path(incoming_data['path_load_man']), header=None, delimiter=';', encoding='ANSI')
        except BaseException as error:
            logging.error(error)
            logging.error(traceback.format_exc())
            logging.info(f"Файл {Path(incoming_data['path_load_man']).name} не обработан из-за непредвиденной ошибки")
            return {'status': 'error', 'text': error, 'trace': traceback.format_exc()}
        # Отловить permission denied
        logging.info(f"Считываем файл выгрузки {Path(incoming_data['path_load_man']).name}")
        name_set = df.iloc[1, 1]
        number_device = sorted(set(df.iloc[0, 2:].values.tolist()))
        df = df.drop(labels=[0], axis=1)
        df = df.drop(labels=[1], axis=0)
        logging.info(f"Создаём структуру для {Path(incoming_data['path_load_man']).name}")
        line_doing.emit(f'Создаём структуру папок')
        sn_device = df[1].to_numpy().tolist()[1:]
        for serial_num in sn_device:
            if window_check.stop_threading:
                return {'status': 'cancel', 'trace': '', 'text': ''}
            path_dir = Path(incoming_data['path_finish_folder'], name_finish_folder, str(name_set), str(serial_num))
            os.makedirs(path_dir, exist_ok=True)
            for device in number_device:
                os.makedirs(Path(path_dir, str(device), 'photo'), exist_ok=True)
                os.makedirs(Path(path_dir, str(device), 'rentgen'), exist_ok=True)
        df = df.drop(labels=[1], axis=1)
        # Отдельно копируем все файлы с инфо и спк
        info_df = incoming_data['all_file'].loc[incoming_data['all_file']['info']]
        logging.info(f"Копируем документы")
        for column in list(df):
            sn_list = df[column].to_numpy().tolist()[1:]
            number_folder = df.loc[0, column]
            logging.info(f"Копируем столбец {column}")
            copy_number = 0
            for device, sn in zip(sn_device, sn_list):
                if window_check.stop_threading:
                    return {'status': 'cancel', 'trace': '', 'text': ''}
                find_1_sn = incoming_data['all_file'].loc[incoming_data['all_file']['sn1'] == sn]
                find_2_sn = incoming_data['all_file'].loc[incoming_data['all_file']['sn2'] == sn]
                info_index_sn1 = info_df.loc[(info_df['sn1'].str.contains(sn, case=False)) |
                                             (info_df['sn1'].str.contains('00' + sn, case=False))].index.to_list()
                info_index_sn2 = info_df.loc[(info_df['sn2'].str.contains(sn, case=False)) |
                                             (info_df['sn2'].str.contains('00' + sn, case=False))].index.to_list()
                if len(info_index_sn1) or len(info_index_sn2):
                    for ind in info_index_sn1:
                        info_df.loc[ind, 'new_name'] = device
                    for ind in info_index_sn2:
                        info_df.loc[ind, 'new_name'] = device
                find_file = pd.concat([find_1_sn, find_2_sn], ignore_index=True)
                for row in find_file.itertuples():
                    line_doing.emit(f'Копируем фото {row.path.name} ({now_doc} из {all_doc})')
                    folder = 'rentgen' if row.suffix in ['.tif', '.tiff', '.png', '.jpeg'] else 'photo'
                    finish_path = Path(incoming_data['path_finish_folder'], name_finish_folder, name_set, device,
                                       number_folder, folder, row.path.name)
                    if finish_path.exists():
                        errors.append(
                            f"Файл {finish_path.name} уже существует, повторное копирование"
                            f" из {row.path} не произведено")
                    else:
                        shutil.copy2(row.path, finish_path)
                        # row.path.replace(finish_path)
                    copy_number += 1
                    now_doc += 1
                    current_progress += incoming_data['percent']
                    line_progress.emit(f'Выполнено {int(current_progress)} %')
                    progress_value.emit(int(current_progress))
            logging.info(f"Скопировано {copy_number}")
        logging.info(f"Копируем файлы СПК и ИНФО если возможно")
        for row in info_df.itertuples():
            finish_path = Path(incoming_data['path_finish_folder'], name_finish_folder, name_set,
                               row.sn1, row.path.name)
            if finish_path.parent.exists():
                logging.info(f"Копируем {row.path}")
                shutil.copy2(row.path, finish_path)
                new_name = re.sub('SPK', 'СПК', row.path.name)
                if row.new_name:
                    new_name = re.sub(row.rename_file, row.new_name, row.path.name)
                rename_file = Path(finish_path.parent, new_name)
                finish_path.replace(rename_file)
                # if replace:
                #     shutil.copy2(file, finish_path)
                #     logging.info(f"Файл {finish_path} создан")
                #     if documents.loc[index_file, 'rename_file']:
                #         new_name = re.sub(file.name.partition('_')[2].partition('.')[0],
                #                           documents.loc[index_file, 'rename_file'],
                #                           str(file.name))
                #         new_name = re.sub('SPK', 'СПК', new_name)
                #         rename_file = Path(finish_path.parent, new_name)
                #         # if rename_file.exists():
                #         #     os.remove(rename_file)
                #         finish_path.replace(rename_file)
                # row.path.replace(finish_path)
        # text = '\n'.join(errors) if errors else ''
        return {'status': 'warning' if errors else 'success', 'text': errors, 'trace': ''}
    except BaseException as error:
        return {'status': 'error', 'text': error, 'trace': traceback.format_exc()}
