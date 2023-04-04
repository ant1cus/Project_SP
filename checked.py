import os
import re
import pathlib

import psutil
from openpyxl import load_workbook


def check(n, e):
    f = True
    for el in e:
        if n == el:
            f = False
            return f
    return f


def checked_sorting_file(le_path_material_sp, le_path_load_asu):

    for proc in psutil.process_iter():
        if proc.name() == 'WINWORD.EXE':
            return ['УПС!', 'Закройте все файлы Word!']
    path_material_sp = le_path_material_sp.text().strip()
    if not path_material_sp:
        return ['УПС!', 'Путь к материалам СП пуст']
    if os.path.isfile(path_material_sp):
        return ['УПС!', 'Укажите папку с материалами СП (указан файл)']
    path_load_asu = le_path_load_asu.text().strip()
    if not path_load_asu:
        return ['УПС!', 'Путь к файлу выгрузки с АСУ пуст']
    if os.path.isdir(path_load_asu):
        return ['УПС!', 'Укажите файл с выгрузкой из АСУ (указана папка)']
    else:
        if path_load_asu.endswith('.xlsx') is False:
            return ['УПС!', 'Файл с выгрузкой из АСУ не формата ".xlsx"']

    return {'path_material_sp': path_material_sp, 'path_load_asu': path_load_asu}
