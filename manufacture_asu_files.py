import os
import shutil
import traceback
from pathlib import Path
import pandas as pd
from small_function import replace_object


def create_manufacture_asu_file(incoming_data: dict, documents: pd.DataFrame, name_finish_folder: str,
                                now_doc, all_doc,
                                current_progress, percent, logging, event, window_check, line_doing,
                                line_progress, progress_value, info_value) -> dict:
    try:
        errors = []
        for file in Path(incoming_data['path_material_sp']).rglob('*.*'):
            if window_check.stop_threading:
                return {'status': 'cancel', 'trace': '', 'text': ''}
            now_doc += 1
            current_progress += percent
            line_progress.emit(f'Выполнено {int(current_progress)} %')
            progress_value.emit(int(current_progress))
            index_file = documents.loc[documents['start_path'] == file].index.tolist()[0]
            if documents.loc[index_file, 'copy_files']:
                if documents.loc[index_file, 'sn_set'] == 0:
                    errors.append(f"Для файла {file.name} серийник не найден в выгрузке АСУ")
                    logging.warning(f"Для файла {file.name} серийник не найден в выгрузке АСУ")
                    continue
                parent_path = Path(incoming_data['path_finish_folder'], name_finish_folder,
                                   str(documents.loc[index_file, 'name_set']), str(documents.loc[index_file, 'sn_set']))
                if Path(parent_path).exists() is False:
                    os.makedirs(parent_path)
                finish_path = Path(incoming_data['path_finish_folder'], name_finish_folder, str(documents.loc[index_file, 'name_set']),
                                  str(documents.loc[index_file, 'sn_set']), file.name)
                replace = replace_object(finish_path, logging, info_value, event, window_check)
                if replace:
                    shutil.copy2(file, finish_path)
                    logging.info(f"Файл {finish_path} создан")
                continue
            line_doing.emit(f'Копируем файл {str(file.name)} ({now_doc} из {all_doc})')  
            path_dir = Path(incoming_data['path_finish_folder'], name_finish_folder,
                            str(documents.loc[index_file, 'name_set']), str(documents.loc[index_file, 'sn_set']),
                            str(int(documents.loc[index_file, 'folder_number'])))
            os.makedirs(path_dir, exist_ok=True)
            copy_file = Path(path_dir, file.name)
            replace = replace_object(copy_file, logging, info_value, event, window_check)
            if replace:
                shutil.copy2(file, copy_file)
                logging.info(f"Файл {copy_file} создан")
        return {'status': 'warning' if errors else 'success', 'text': errors, 'trace': ''}
    except BaseException as ex:
        return {'status': 'error', 'text': ex, 'trace': traceback.format_exc()}
