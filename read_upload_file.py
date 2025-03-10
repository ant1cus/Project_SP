import os
import traceback
from pathlib import Path

import pandas as pd


def read_upload_file(incoming_data):
    logging = incoming_data['logging']
    try:
        name_finish_folder = incoming_data['name_gk'] if incoming_data['name_gk'] else 'Номер ГК'
        try:
            df = pd.read_csv(Path(incoming_data['path_load_man']), header=None)
        except BaseException as error:
            logging.error(error)
            logging.error(traceback.format_exc())
            logging.info(f"Файл {incoming_data['path_load_man'].name} не обработан из-за непредвиденной ошибки")
            return
        # Отловить permission denied
        logging.info('Считываем файл выгрузки ' + incoming_data['path_load_man'].name)
        name_set = df.iloc[1, 1]
        number_device = sorted(set(df.iloc[0, 2:].values.tolist()))
        df = df.drop(labels=[0], axis=1)
        df = df.drop(labels=[1], axis=0)
        logging.info(f"Создаём структуру для {incoming_data['path_load_man'].name}")
        sn_device = df[0].to_numpy().tolist()[1:]
        for serial_num in sn_device:
            # if window_check.stop_threading:
            #     return {'error': False, 'text': 'cancel', 'trace': ''}
            path_dir = Path(incoming_data['path_finish_folder'], name_finish_folder, str(name_set), str(serial_num))
            os.makedirs(path_dir, exist_ok=True)
            for device in number_device:
                os.makedirs(Path(path_dir, str(device), 'photo'), exist_ok=True)
                os.makedirs(Path(path_dir, str(device), 'rentgen'), exist_ok=True)
        df = df.drop(labels=[0], axis=1)
        for column in list(df):
            sn_list = df[column].to_numpy().tolist()[1:]
        # df = df.drop(labels=[0], axis=1)
        # df = df.drop(labels=[1], axis=0)

        errors = []
        if errors:
            logging.info('Отправляем ошибки')
            return {'error': False, 'text': '\n'.join(errors), 'trace': ''}
        else:
            return {'error': False, 'text': '', 'trace': ''}
    except BaseException as error:
        return {'error': True, 'text': error, 'trace': traceback.format_exc()}