import os
from pathlib import Path


def checked_sorting_file(incoming: dict) -> dict:
    denied_symbol = '/\:*?<>|'
    if not incoming['path_material_sp']:
        return {'error': True, 'data': 'Путь к материалам СП пуст'}
    if os.path.isfile(incoming['path_material_sp']):
        return {'error': True, 'data': 'Укажите папку с материалами СП (указан файл)'}
    for file in Path(incoming['path_material_sp']).rglob("*.*"):
        if file.suffix.lower() in ['.tiff', '.tif', '.jpeg', 'png', '.jpg']:
            incoming['all_doc'] += 1
        elif file.parent.name.lower() == 'спк':
            incoming['all_doc'] += 1
        elif file.parent.name.lower() == 'инфо':
            incoming['all_doc'] += 1
    if incoming['all_doc'] == 0:
        return {'error': True, 'data': 'Нет файлов для копирования и сортировки'}
    incoming['percent'] = 100 / incoming['all_doc']
    if incoming['asu_man']:
        if not incoming['path_load_asu']:
            return {'error': True, 'data': 'Путь к папке с выгрузками из АСУ пуст'}
        if os.path.isfile(incoming['path_load_asu']):
            return {'error': True, 'data': 'Укажите папку с выгрузками из АСУ (указан файл)'}
        else:
            for element in os.listdir(incoming['path_load_asu']):
                error = []
                if element.endswith('.xlsx') is False:
                    error.append(element)
                if error:
                    return {'error': True, 'data': 'Файл с выгрузкой из АСУ не формата ".xlsx"'}
    else:
        if not incoming['path_load_man']:
            return {'error': True, 'data': 'Путь к файлу выгрузки пуст'}
        if os.path.isfile(incoming['path_load_man']):
            if incoming['path_load_man'].endswith('.csv') is False:
                return {'error': True, 'data': 'Файл с выгрузкой не формата ".csv"'}
        else:
            return {'error': True, 'data': 'Указанный файл с выгрузкой удалён или переименован'}
    if not incoming['path_finish_folder']:
        return {'error': True, 'data': 'Путь к материалам СП пуст'}
    if os.path.isfile(incoming['path_finish_folder']):
        return {'error': True, 'data': 'Укажите папку с материалами СП (указан файл)'}
    for element in denied_symbol:
        if incoming['name_gk'] and element in incoming['name_gk']:
            return {'error': True, 'data': 'Запрещённый символ в имени ГК: ' + element}
        if incoming['name_set'] and element in incoming['name_set']:
            return {'error': True, 'data': 'Запрещённый символ в наименовании комплекта: ' + element}
    return {'error': False, 'data': incoming}
