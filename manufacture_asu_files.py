import os
import re
import shutil
import traceback
from pathlib import Path
import pandas as pd
from small_function import replace_object


def create_manufacture_asu_file(incoming_data: dict, name_finish_folder: str, documents: pd.DataFrame,
                                now_doc, all_doc,
                                current_progress, percent, logging, event, window_check, line_doing,
                                line_progress, progress_value, info_value) -> dict:
    try:
        errors = []
        df = documents.loc[documents['sn_set'] != 0]
        all_doc = df.shape[0]
        # percent = 100/all_doc
        percent = 1
        for row in df.itertuples():
            if window_check.stop_threading:
                return {'status': 'cancel', 'trace': '', 'text': ''}
            now_doc += 1
            current_progress += percent
            line_progress.emit(f'Выполнено {int(current_progress)} %')
            progress_value.emit(int(current_progress))
            if row.copy_files:
                parent_path = Path(incoming_data['path_finish_folder'], name_finish_folder, str(row.name_set))
                if not Path(parent_path).exists():
                    os.makedirs(parent_path)
                finish_path = Path(incoming_data['path_finish_folder'], name_finish_folder, str(row.name_set), row.name)
                if finish_path.exists():
                    logging.info(f"Файл {finish_path.name} существует, пропускаем")
                    continue
                replace = replace_object(finish_path, logging, info_value, event, window_check)
                if replace:
                    shutil.copy2(row.start_path, finish_path)
                    logging.info(f"Файл {finish_path} создан")
                new_name = re.sub('SPK', 'СПК', row.name)
                if row.sn_set != row.rename_file:
                    new_name = re.sub(new_name.partition('_')[2].partition('.')[0], row.rename_file, str(new_name))
                rename_file = Path(finish_path.parent, new_name)
                finish_path.replace(rename_file)
                continue
            line_doing.emit(f'Копируем файл {str(row.name)} ({now_doc} из {all_doc})')
            path_dir = Path(incoming_data['path_finish_folder'], name_finish_folder,
                            str(row.name_set), str(int(row.folder_number)), 'photo')
            os.makedirs(path_dir, exist_ok=True)
            copy_file = Path(path_dir, row.name)
            if copy_file.exists():
                logging.info(f"Файл {copy_file.name} существует, пропускаем")
                continue
            replace = replace_object(copy_file, logging, info_value, event, window_check)
            if replace:
                shutil.copy2(row.start_path, copy_file)
                logging.info(f"Файл {copy_file} создан")
        return {'status': 'warning' if errors else 'success', 'text': errors, 'trace': ''}
    except BaseException as ex:
        return {'status': 'error', 'text': ex, 'trace': traceback.format_exc()}
