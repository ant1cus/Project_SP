import datetime
import os
import logging
import json
import re
import time
import traceback
from pathlib import Path

from PyQt5.QtWidgets import QFileDialog, QMessageBox

from Default import DefaultWindow

# Подумать как перезаписывать настройки и сделать одну функцию. Добавить обратную совместимость
# def rewrite_settings(path, data, widget=False, visible=False, order=False):
#     if widget:
#         dict_load = data
#     else:
#         name = visible if visible else order
#         with open(Path(path, 'Настройки.txt'), "r", encoding='utf-8-sig') as f:  # Открываем
#             dict_load = json.load(f)  # Загружаем данные
#             dict_load['gui_settings'][name] = data
#     with open(Path(path, 'Настройки.txt'), 'w', encoding='utf-8-sig') as f:  # Пишем в файл
#         json.dump(dict_load, f, ensure_ascii=False, sort_keys=True, indent=4)


def rewrite_settings(path: Path, data: dict or False = False) -> dict:
    """Создаёт файл настроек при первом запуске или если его удалили в процессе, открывает или перезаписывает его"""
    try:
        if data:
            with open(Path(path, 'Настройки.txt'), 'w', encoding='utf-8-sig') as f:  # Пишем в файл
                json.dump(data, f, ensure_ascii=False, sort_keys=True, indent=4)
                answer = data
        else:
            with open(Path(path, 'Настройки.txt'), "r", encoding='utf-8-sig') as f:
                answer = json.load(f)
    except FileNotFoundError:
        with open(Path(path, 'Настройки.txt'), "w", encoding='utf-8-sig') as f:
            data_insert = data if data else {"widget_settings": {}, 'gui_settings': {}}
            json.dump(data_insert, f, ensure_ascii=False, sort_keys=True, indent=4)
            answer = data_insert
    if 'widget_settings' not in answer:
        answer['widget_settings'] = {}
    if 'gui_settings' not in answer:
        answer['gui_settings'] = {}
    return answer


def default_data(incoming_data, lines):
    for element in lines:
        if element in incoming_data:
            if 'checkBox' in element or 'groupBox' in element:
                lines[element][1].setChecked(True) if incoming_data[element] else lines[element][1].setChecked(False)
            elif 'radioButton' in element:
                for radio, button in zip(incoming_data[element], lines[element][1]):
                    if radio:
                        button.setChecked(True)
                    else:
                        button.setAutoExclusive(False)
                        button.setChecked(False)
                    button.setAutoExclusive(True)
            elif 'doubleSpinBox' in element:
                lines[element][1].setValue(float(incoming_data[element]))
            else:
                lines[element][1].setText(incoming_data[element])  # Помещаем значение


def browse(self, sender, line_edit, path) -> None:
    """Выбор открытия диалога папки или файла и запись в переданный лайн выбранное значение"""
    try:
        if 'dir' in sender.objectName():
            directory = QFileDialog.getExistingDirectory(self, "Открыть папку", str(path))
        else:
            directory = QFileDialog.getOpenFileName(self, "Открыть файл", str(path))
        if directory and isinstance(directory, tuple):
            if directory[0]:
                line_edit.setText(directory[0])
        elif directory and isinstance(directory, str):
            line_edit.setText(directory)
    except BaseException as es:
        print(es)
    return


def default_settings(self, default_path: Path, lines: dict) -> None:
    """Закрывает главное окно и выводит окно с настройками по умолчанию"""
    self.close()
    # Дополнительно передаем функцию для перезаписи дефолтных значений
    window_add = DefaultWindow(self, default_path, lines, default_data, browse, rewrite_settings)
    window_add.show()
    return


def logging_file(name: str, logging_dict: dict) -> list:
    """Создает файлы для логов и возвращает названия для текущего и общего лога"""
    filename_now = str(datetime.datetime.today().timestamp()) + '_logs.log'
    filename_all = str(datetime.date.today()) + '_logs.log'
    os.makedirs(Path('logs', name), exist_ok=True)
    logging_dict[filename_now] = logging.getLogger(filename_now)
    logging_dict[filename_now].setLevel(logging.DEBUG)
    name_log = logging.FileHandler(Path('logs', name, filename_now))
    basic_format = logging.Formatter("%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s")
    name_log.setFormatter(basic_format)
    logging_dict[filename_now].addHandler(name_log)
    return [filename_now, filename_all]


def start_thread(incoming: dict, logging_dict: dict, thread_dict: dict, self, check_func, run_func) -> None:
    """Запускает поток для выполнения. Включает проверку входящих данных,
     взаимодействие с основным потоком и вывод ошибок."""

    mode_name = incoming['mode_name']
    file_name = logging_file(mode_name, logging_dict)
    logging_dict[file_name[0]].info(f"----------------Запускаем {mode_name}----------------")
    logging_dict[file_name[0]].info('Проверка данных')
    try:
        answer = check_func(incoming)
        if answer['error']:
            logging_dict[file_name[0]].warning(answer['data'])
            logging_dict[file_name[0]].warning('Ошибки в заполнении формы, программа не запущена в работу')
            on_message_changed(self, 'УПС!', answer['data'])
            finished_thread(mode_name, logging_dict, thread_dict,
                            name_all=str(Path('logs', mode_name, file_name[1])),
                            name_now=str(Path('logs', mode_name, file_name[0])))
            return
        else:
            sending_data = answer['data']
        # Если всё прошло запускаем поток
        logging_dict[file_name[0]].info('Заполняем недостающие значения')
        sending_data['name_dir'] = Path(sending_data['name_dir']).name
        sending_data['title'] = f"{sending_data['mode_description'][mode_name]['title']} «{sending_data['name_dir']}»"

        def replace_name_dir(key_val):
            for val in key_val:
                sending_data[val] = re.sub('name_dir', sending_data['name_dir'],
                                           sending_data['mode_description'][mode_name][val])

        replace_name_dir(['cancel', 'exception', 'success', 'error'])
        sending_data['logging'], sending_data['move'] = logging_dict[file_name[0]], len(thread_dict[mode_name])
        sending_data['log_all'], sending_data['log_now'] = file_name[1], file_name[0]
        logging_dict[file_name[0]].info('Запуск на выполнение')
        thread = run_func(sending_data)
        thread.status_finish.connect(finished_thread)
        thread.status.connect(self.statusBar().showMessage)
        thread_dict[mode_name][str(thread)] = {'log_all': file_name[1],
                                               'log_now': file_name[0]}
        thread.start()
        time.sleep(0.1)  # Не удалять, не успевает отработать окно при сборке exe
    except BaseException as exception:
        logging_dict[file_name[0]].error(f"Ошибка при старте {mode_name}")
        logging_dict[file_name[0]].error(exception)
        logging_dict[file_name[0]].error(traceback.format_exc())
        on_message_changed(self, 'УПС!', 'Неизвестная ошибка, обратитесь к разработчику')
        finished_thread('sorting', logging_dict, thread_dict,
                        name_all=str(Path('logs', mode_name, file_name[1])),
                        name_now=str(Path('logs', mode_name, file_name[0])))
        return


def finished_thread(method, logging_dict: dict, thread_dict: dict, thread: str = '', name_all: str = '',
                    name_now: str = '') -> None:
    """После завершения потока записывает данные из текущего лога в общий"""
    if thread:
        file_all = Path('logs', method, thread_dict[method][thread]['log_all'])
        file_now = Path('logs', method, thread_dict[method][thread]['log_now'])
    else:
        file_all, file_now = Path(name_all), Path(name_now)
    filemode = 'a' if file_all.is_file() else 'w'
    with open(file_now, mode='r') as f:
        file_data = f.readlines()
    logging.shutdown()
    os.remove(file_now)
    logging_dict.pop(file_now.name)
    with open(file_all, mode=filemode) as f:
        f.write(''.join(file_data))
    if thread:
        thread_dict[method].pop(thread, None)
    return


def on_message_changed(self, title, description) -> None:
    """Функция для вывода сообщения. По заголовку определяет нужный формат и выводит описание."""
    if title == 'УПС!':
        QMessageBox.critical(self, title, description)
    elif title == 'Внимание!':
        QMessageBox.warning(self, title, description)
    elif title == 'Вопрос?':
        self.statusBar().clearMessage()
        ans = QMessageBox.question(self, title, description, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ans == QMessageBox.No:
            self.thread.queue.put(True)
        else:
            self.thread.queue.put(False)
        self.thread.event.set()
    return
