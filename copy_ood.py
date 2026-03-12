import os
import re
import shutil
import traceback
from pathlib import Path
from datetime import datetime

import pandas as pd


def copy_files(incoming_data: dict, current_progress, now_doc, all_doc, line_doing, line_progress, progress_value,
			   event, window_check,info_value) -> dict:
	logging = incoming_data['logging']
	try:
		start_time = datetime.now()
		logging.info(f"время начала - {start_time}")
		errors = []
		name_finish_folder = incoming_data['name_gk'] if incoming_data['name_gk'] else 'Номер ГК'
		if Path(incoming_data['finish_path'], name_finish_folder).exists() is False:
			os.makedirs(Path(incoming_data['finish_path'], name_finish_folder))
		logging.info(f"Считываем файл выгрузки {Path(incoming_data['upload_file']).name}")
		df = pd.read_excel(Path(incoming_data['upload_file']), sheet_name=0, header=None)
		if incoming_data['name_set']:
			df.fillna(value={2: incoming_data['name_set']}, inplace=True)
		df[1] = df[1].astype(str)
		df[3] = df[3].astype(str)
		df['finish_folder'] = str(Path(incoming_data['finish_path'], name_finish_folder)) + '\\' + df[1] + '\\' + df[3]
		serial_nums = {}
		logging.info(f"загрузка excel - {datetime.now() - start_time}")
		# Для кол-ва копий можно будет потом расскоментировать
		# find_files = {}
		for index, item in df.iloc[0].items():
			if index == 'finish_folder':
				continue
			if re.findall(r'\d+', str(item)):
				folder = int(str(item).partition('-')[0]) if re.findall(r'\d+-\d+', str(item)) else int(item)
				# snapshot = int(str(item).partition('-')[2]) if re.findall(r'\d+-\d+', str(item)) else 1
				full_path = dict(zip(
					df[index].iloc[2:],
					[f"{i}\\{folder}" for i in df['finish_folder'].iloc[2:].to_numpy().tolist()]
				))
				# full_find = dict(zip(
				# 	df[index].iloc[2:],
				# 	[{'all': snapshot, **{i: False for i in range(1, snapshot + 1)}}]*(df.shape[1]-2)
				# ))
				serial_nums.update(full_path)
				# serial_snapshot.update(full_snapshot)
				# find_files.update(full_find)
		percent = 100 / len(serial_nums)
		logging.info(f"считывание excel - {datetime.now() - start_time}")
		for file in Path(incoming_data['start_path']).rglob('*.*'):
			if window_check.stop_threading:
				return {'status': 'cancel', 'trace': '', 'text': ''}
			file_sn = file.stem.partition('_')[2].partition('_')[2].partition('_')[0]
			if file_sn not in serial_nums:
				continue
			if Path(serial_nums[file_sn], 'photo', file.name).exists():
				continue
			if not Path(serial_nums[file_sn], 'photo').exists():
				os.makedirs(Path(serial_nums[file_sn], 'photo'))
			line_doing.emit(f'Копируем файл {file.name} ({now_doc} из {all_doc})')
			shutil.copy2(file, Path(serial_nums[file_sn], 'photo', file.name))
			now_doc += 1
			current_progress += percent
			line_progress.emit(f'Выполнено {int(current_progress)} %')
			progress_value.emit(int(current_progress))
		logging.info(f"конец программы - {datetime.now() - start_time}")
		return {'status': 'success', 'text': '', 'trace': ''}
	except BaseException as ex:
		return {'status': 'error', 'text': ex, 'trace': traceback.format_exc()}
