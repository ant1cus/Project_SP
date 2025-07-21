import os
import re
import shutil
import traceback
from pathlib import Path
from small_function import replace_object

import pandas as pd


def create_sp_sorting_file(incoming_data: dict, name_finish_folder: str, documents: pd.DataFrame,
                           now_doc, all_doc, current_progress, percent, logging, event, window_check,
                           line_doing, line_progress, progress_value, info_value) -> dict:
    try:
        errors = []
        for file in Path(incoming_data['path_material_sp']).rglob('*.*'):
            if window_check.stop_threading:
                return {'status': 'cancel', 'trace': '', 'text': ''}
            now_doc += 1
            current_progress += percent
            line_progress.emit(f'Выполнено {int(current_progress)} %')
            progress_value.emit(int(current_progress))
            line_doing.emit(f'Анализ файла {str(file.name)} ({now_doc} из {all_doc})')
            index_file = documents.loc[documents['start_path'] == file].index.tolist()[0]
            suffix = file.suffix
            if suffix in ['.tif', '.tiff', '.jpeg', '.png', '.jpg'] and documents.loc[index_file, 'sn_set'] == 0:
                errors.append(f"Серийник {documents.loc[index_file, 'parent_name']} не найден в выгрузке АСУ")
                logging.warning(f"Серийник {documents.loc[index_file, 'parent_name']} не найден в выгрузке АСУ")
                continue
            if documents.loc[index_file, 'copy_files']:
                if documents.loc[index_file, 'sn_set'] == 0:
                    errors.append(f"Для файла {file.name} серийник не найден в выгрузке АСУ")
                    logging.warning(f"Для файла {file.name} серийник не найден в выгрузке АСУ")
                    continue
                parent_path = Path(incoming_data['path_finish_folder'], name_finish_folder,
                                   str(documents.loc[index_file, 'name_set']),
                                   str(documents.loc[index_file, 'sn_set']) + ' В')
                if Path(parent_path).exists() is False:
                    os.makedirs(parent_path)
                finish_path = Path(incoming_data['path_finish_folder'], name_finish_folder,
                                   str(documents.loc[index_file, 'name_set']),
                                   str(documents.loc[index_file, 'sn_set']) + ' В', file.name)
                replace = replace_object(finish_path, logging, info_value, event, window_check)
                if replace:
                    shutil.copy2(file, finish_path)
                    logging.info(f"Файл {finish_path} создан")
                    if documents.loc[index_file, 'rename_file']:
                        new_name = re.sub(file.name.partition('_')[2].partition('.')[0],
                                          documents.loc[index_file, 'rename_file'],
                                          str(file.name))
                        new_name = re.sub('SPK', 'СПК', new_name)
                        rename_file = Path(finish_path.parent, new_name)
                        if rename_file.exists():
                            os.remove(rename_file)
                        finish_path.rename(rename_file)
                continue
            if len(documents.loc[index_file, 'name_set']) == 0:
                continue
            line_doing.emit(f'Копируем файл {str(file.name)} ({now_doc} из {all_doc})')
            path_x_ray = Path(incoming_data['path_finish_folder'], name_finish_folder,
                            str(documents.loc[index_file, 'name_set']), str(documents.loc[index_file, 'sn_set']) + ' В',
                            str(int(documents.loc[index_file, 'folder_number'])), 'rentgen')
            path_photo = Path(incoming_data['path_finish_folder'], name_finish_folder,
                            str(documents.loc[index_file, 'name_set']), str(documents.loc[index_file, 'sn_set']) + ' В',
                            str(int(documents.loc[index_file, 'folder_number'])), 'photo')
            if Path(path_x_ray).exists() is False:
                os.makedirs(path_x_ray)
            if Path(path_photo).exists() is False:
                os.makedirs(path_photo)
            type_path = path_x_ray if suffix in ['.tif', '.tiff', '.jpeg', '.png'] else path_photo
            finish_path = Path(type_path, file.name)
            replace = replace_object(finish_path, logging, info_value, event, window_check)
            if replace:
                shutil.copy2(file, finish_path)
                logging.info(f"Файл {finish_path} создан")
        return {'status': 'warning' if errors else 'success', 'text': errors, 'trace': ''}
    except BaseException as ex:
        return {'status': 'error', 'text': ex, 'trace': traceback.format_exc()}
