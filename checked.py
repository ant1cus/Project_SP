import os


def checked_sorting_file(le_path_material_sp, le_path_load_asu, le_path_finish_folder, name_gk, name_set):

    denied_simbol = '/\:*?<>|'
    path_material_sp = le_path_material_sp.text().strip()
    if not path_material_sp:
        return ['УПС!', 'Путь к материалам СП пуст']
    if os.path.isfile(path_material_sp):
        return ['УПС!', 'Укажите папку с материалами СП (указан файл)']
    path_load_asu = le_path_load_asu.text().strip()
    if not path_load_asu:
        return ['УПС!', 'Путь к папке с выгрузками из АСУ пуст']
    if os.path.isfile(path_load_asu):
        return ['УПС!', 'Укажите папку с выгрузками из АСУ (указан файл)']
    else:
        for element in os.listdir(path_load_asu):
            error = []
            if element.endswith('.xlsx') is False:
                error.append(element)
            if error:
                return ['УПС!', 'Файл с выгрузкой из АСУ не формата ".xlsx"']
    path_finish_folder = le_path_finish_folder.text().strip()
    if not path_finish_folder:
        return ['УПС!', 'Путь к материалам СП пуст']
    if os.path.isfile(path_finish_folder):
        return ['УПС!', 'Укажите папку с материалами СП (указан файл)']
    for element in denied_simbol:
        if element in name_gk:
            return ['УПС!', 'Запрещённый символ в имени ГК: ' + element]
        if element in name_set:
            return ['УПС!', 'Запрещённый символ в наименовании комплекта: ' + element]

    return {'path_material_sp': path_material_sp, 'path_load_asu': path_load_asu,
            'path_finish_folder': path_finish_folder, 'name_gk': name_gk, 'name_set': name_set}
