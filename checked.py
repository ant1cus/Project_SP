import os
import re
from pathlib import Path

import psutil
from openpyxl import load_workbook
import pandas as pd


def checked_sorting_file(incoming: dict) -> dict:
    denied_symbol = '/\\:*?<>|'
    if not incoming['path_material_sp']:
        return {'error': True, 'data': 'Путь к материалам СП пуст'}
    if os.path.isfile(incoming['path_material_sp']):
        return {'error': True, 'data': 'Укажите папку с материалами СП (указан файл)'}
    if not os.path.isdir(incoming['path_material_sp']):
        return {'error': True, 'data': 'Указанная папка с материалами СП удалена или переименована'}
    copy_file = pd.DataFrame(columns=['path', 'sn1', 'sn2', 'suffix', 'info', 'rename_file', 'new_name'])
    for file in Path(incoming['path_material_sp']).rglob("*.*"):
        file_info = [file, '', '', file.suffix, False, False, False]
        if re.findall(r'\w+_(\w+)\.\w+\b', file.name):
            file_info[1] = re.findall(r'\w+_(\w+)\.\w+\b', file.name)[0]
        if re.findall(r'\w+_(\w+)_\w+\.\w+\b', file.name):
            file_info[2] = re.findall(r'\w+_(\w+)_\w+\.\w+\b', file.name)[0]
        if file.suffix.lower() in ['.tiff', '.tif', '.jpeg', 'png', '.jpg']:
            copy_file.loc[len(copy_file)] = file_info
        elif file.parent.name.lower() == 'спк' or file.parent.name.lower() == 'инфо':
            file_info[4] = True
            file_info[5] = file.stem.partition('_')[2]
            copy_file.loc[len(copy_file)] = file_info
    if len(copy_file) == 0:
        return {'error': True, 'data': 'Нет файлов для копирования и сортировки'}
    incoming['all_file'] = copy_file
    incoming['all_doc'] = len(copy_file)
    incoming['percent'] = 100 / incoming['all_doc']
    if incoming['asu_man']:
        if not incoming['path_load_asu']:
            return {'error': True, 'data': 'Путь к файлу выгрузки «.xlsx» пуст'}
        if os.path.isdir(incoming['path_load_asu']):
            return {'error': True, 'data': 'Файл выгрузки «.xlsx» удалён или переименован'}
        if incoming['path_load_asu'].endswith('.xlsx') is False:
            return {'error': True, 'data': 'Файл выгрузки «.xlsx» не формата ".xlsx"'}
        wb = load_workbook(str(Path(incoming['path_load_asu'])))
        try:
            wb.save(str(Path(incoming['path_load_asu'])))
        except PermissionError:
            return {'error': True, 'data': f"Закройте файл выгрузки {Path(incoming['path_load_asu']).name}"}
    else:
        if not incoming['path_load_man']:
            return {'error': True, 'data': 'Путь к файлу выгрузки «.csv» пуст'}
        if os.path.isdir(incoming['path_load_man']):
            return {'error': True, 'data': 'Указанный файл выгрузки «.csv» удалён или переименован'}
        if incoming['path_load_man'].endswith('.csv') is False:
            return {'error': True, 'data': 'Файл выгрузки «.csv» не формата «.csv»'}
    if not incoming['path_finish_folder']:
        return {'error': True, 'data': 'Путь к конечной папке пуст'}
    if os.path.isfile(incoming['path_finish_folder']):
        return {'error': True, 'data': 'Укажите директорию для копирования (указан файл)'}
    if not os.path.isdir(incoming['path_finish_folder']):
        return {'error': True, 'data': 'Указанная конечная папка удалена или переименована'}
    for element in denied_symbol:
        if incoming['name_gk'] and element in incoming['name_gk']:
            return {'error': True, 'data': 'Запрещённый символ в имени ГК: ' + element}
        if incoming['name_set'] and element in incoming['name_set']:
            return {'error': True, 'data': 'Запрещённый символ в наименовании комплекта: ' + element}
    return {'error': False, 'data': incoming}


def checked_form_file(incoming: dict) -> dict:
    if not incoming['unformat_file']:
        return {'error': True, 'data': 'Путь к неподготовленному файлу выгрузки пуст'}
    if os.path.isfile(incoming['unformat_file']):
        if incoming['unformat_file'].endswith('.xlsx') is False:
            return {'error': True, 'data': 'Файл с неподготовленной выгрузкой не формата ".xlsx"'}
    else:
        return {'error': True, 'data': 'Указанный файл с неподготовленной выгрузкой удалён или переименован'}
    if not incoming['path_check_material']:
        return {'error': True, 'data': 'Путь к проверяемым материалам пуст'}
    if not os.path.isdir(incoming['path_check_material']):
        return {'error': True, 'data': 'Указанный путь к проверяемым материалам удалён или переименован'}
    incoming['name_dir'] = Path(incoming['name_dir']).parent
    return {'error': False, 'data': incoming}


def check_unloading_file(incoming: dict) -> dict:
    for proc in psutil.process_iter():
        if proc.name() == 'WINWORD.EXE':
            return {'error': True, 'data': 'Закройте все файлы Word!'}
    if not incoming['start_path']:
        return {'error': True, 'data': 'Путь к исходным выгрузкам пуст'}
    if not os.path.isdir(incoming['start_path']):
        return {'error': True, 'data': 'Путь к исходным выгрузкам удалён или переименован'}
    if not len(os.listdir(incoming['start_path'])):
        return {'error': True, 'data': 'В указанном пути к исходным выгрузкам нет документов для преобразования'}
    if not incoming['finish_path']:
        return {'error': True, 'data': 'Путь к конечной папке пуст'}
    if not os.path.isdir(incoming['finish_path']):
        return {'error': True, 'data': 'Путь к конечной папке удалён или переименован'}
    if len(os.listdir(incoming['finish_path'])) > 0:
        return {'error': True, 'data': 'Конечная папка не пуста, очистите директорию'}
    for file in Path(incoming['start_path']).rglob('*.*'):
        if file.suffix == '.docx' and '~' not in file.name:
            incoming['all_doc'] += 1
    return {'error': False, 'data': incoming}
