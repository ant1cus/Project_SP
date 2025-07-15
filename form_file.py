import traceback
import pandas as pd
import numpy as np
from openpyxl import load_workbook
from pathlib import Path
from openpyxl.utils import get_column_letter


def form_file(incoming_data: dict, current_progress: float, now_doc: int, all_doc: int, line_doing, line_progress,
              progress_value, event, window_check, info_value) -> dict:
    logging = incoming_data['logging']
    try:
        save_file_name = f"{Path(incoming_data['unformat_file']).stem}" \
                         f"_sort{Path(incoming_data['unformat_file']).suffix}"
        # Получаем ширину столбцов
        logging.info('Читаем файл')
        line_doing.emit(f"Читаем файл {Path(incoming_data['unformat_file']).name}")
        wb = load_workbook(incoming_data['unformat_file'])
        ws = wb.active
        column_sheet = [ws.column_dimensions[get_column_letter(col[0].column)].width for col in ws.iter_cols()]
        row_height = ws.row_dimensions[1].height
        df = pd.read_excel(incoming_data['unformat_file'], header=None)
        nan_col = df.columns[df.isna().all()].tolist()
        rows, cols = np.where(df.isna())
        errors = [f"Пропущено значение в ячейке {row + 1}{get_column_letter(col + 1)}"
                  for row, col in zip(rows, cols) if col not in nan_col]
        col_for_copy = [col for col in cols if col not in nan_col]
        for index, column in enumerate(col_for_copy):
            for col in df.columns:
                if not set(df[column]).isdisjoint(df[col]):
                    errors[index] = f"{errors[index]} (замена из колонки {get_column_letter(col + 1)})"
                    break
        current_progress += 25
        line_progress.emit(f'Выполнено {int(current_progress)} %')
        progress_value.emit(int(current_progress))
        line_doing.emit(f"Ищем уникальные колонки")
        column_name = df.iloc[0]
        df = df.iloc[1:]
        column_list = [df[column].to_numpy().tolist() for column in df.columns]
        uniq_column = {}
        columns = []
        for index, column in enumerate(column_list):
            str_list = [str(col) for col in column]
            if len(set(str_list)) == 1 and index > 3:
                continue
            string_col = ','.join(str_list)
            if string_col not in columns:
                columns.append(string_col)
                uniq_column[index] = [column_name[index], *column]
        df = pd.DataFrame(uniq_column)
        current_progress += 50
        line_progress.emit(f'Выполнено {int(current_progress)} %')
        progress_value.emit(int(current_progress))
        line_doing.emit(f"Заполняем новый файл {save_file_name}")
        df.dropna(axis=1, inplace=True)
        column_width = max([column_sheet[index] for index in list(uniq_column.keys())])
        writer = pd.ExcelWriter(Path(Path(incoming_data['unformat_file']).parent, save_file_name))
        df.to_excel(writer, sheet_name='sort', index=False, header=False, na_rep='NaN')
        for column in df:
            col_idx = df.columns.get_loc(column)
            writer.sheets['sort'].set_column(col_idx, col_idx, column_width)
        writer.sheets['sort'].set_row(0, row_height)
        workbook = writer.book
        worksheet = writer.sheets['sort']
        format_row = workbook.add_format({'text_wrap': True})
        worksheet.set_row(0, None, format_row)
        writer.close()
        current_progress += 25
        line_progress.emit(f'Выполнено {int(current_progress)} %')
        progress_value.emit(int(current_progress))
        return {'status': 'warning' if errors else 'success', 'text': errors, 'trace': ''}
    except BaseException as ex:
        return {'status': 'error', 'text': ex, 'trace': traceback.format_exc()}
