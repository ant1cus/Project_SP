import os
import threading
import time

from PyQt5.QtCore import QThread, pyqtSignal

from DoingWindow import ProcessWindow


class CancelException(Exception):
    pass


class StartThreading(QThread):
    """Запуск потока для выполнения. Заполняем общие данные, работаем с окном прогресса и выводим сообщения
     об успешном или провальном выполнении программы. Ловим исключения."""
    status_finish = pyqtSignal(str, dict, dict, str, str, str)
    progress_value = pyqtSignal(int)
    info_value = pyqtSignal(str, str, str or None)
    status = pyqtSignal(str)
    line_progress = pyqtSignal(str)
    line_doing = pyqtSignal(str)

    def __init__(self, incoming_data):  # Список переданных элементов.
        QThread.__init__(self)
        self.incoming_data = incoming_data
        self.start_function = incoming_data['start_function']
        self.mode_name = incoming_data['mode_name']
        self.logging = incoming_data['logging']
        self.default_path = incoming_data['default_path']
        self.name_dir = incoming_data['name_dir']
        self.cancel = incoming_data['cancel']
        self.exception = incoming_data['exception']
        self.success = incoming_data['success']
        self.error = incoming_data['error']
        self.event = threading.Event()
        self.event.set()
        self.now_doc = 0
        self.all_doc = incoming_data['all_doc']
        # self.percent = incoming_data['percent']
        self.current_progress = 0
        self.window_check = ProcessWindow(self.default_path, self.event, incoming_data['move'], incoming_data['title'])
        self.progress_value.connect(self.window_check.progressBar.setValue)
        self.line_progress.connect(self.window_check.lineEdit_progress.setText)
        self.line_doing.connect(self.window_check.lineEdit_doing.setText)
        self.info_value.connect(self.window_check.info_message)
        self.window_check.show()

    def run(self):
        self.logging.info('Запустили run')
        self.line_progress.emit(f'Выполнено 0 %')
        self.progress_value.emit(0)
        answer = self.start_function(self.incoming_data, self.current_progress, self.now_doc, self.all_doc,
                                     self.line_doing, self.line_progress, self.progress_value, self.event,
                                     self.window_check, self.info_value)
        self.line_progress.emit(f'Выполнено 100 %')
        self.progress_value.emit(100)
        if answer['status'] == 'error':
            self.logging.error(answer['text'])
            self.logging.error(answer['trace'])
            self.info_value.emit('УПС!', 'Работа программы завершена из-за непредвиденной ошибки', None)
            self.finish_thread(self.exception)
        elif answer['status'] == 'cancel':
            self.finish_thread(self.cancel)
        elif answer['status'] == 'warning':
            self.logging.info('\n'.join(answer['text']))
            self.info_value.emit('Внимание!', '\n'.join(answer['text']), self.error)
            self.finish_thread(self.error)
        elif answer['status'] == 'success':
            self.finish_thread(self.success)
        else:
            self.logging.error('Отсутствует статус завершения потока')
            self.info_value.emit('УПС!', 'Работа программы завершена из-за непредвиденной ошибки', None)
            self.finish_thread(self.exception)

    def finish_thread(self, text: str) -> None:
        self.logging.info(text)
        self.status.emit(text)
        self.status_finish.emit(self.mode_name, self.incoming_data['logging_dict'], self.incoming_data['thread_dict'],
                                str(self), self.incoming_data['log_all'], self.incoming_data['log_now'])
        time.sleep(0.5)  # Не удалять, не успевает отработать emit status_finish. Может потом
        os.chdir(self.default_path)
        self.window_check.close()
        return

