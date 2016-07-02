#!/usr/bin/env python

import wiimote as wm
from PyQt5 import QtCore
import time


class Thread(QtCore.QThread):
    update_trigger = QtCore.pyqtSignal()

    def __init__(self, frequency):
        super(Thread, self).__init__()
        self.is_running = True
        self.frequency = frequency

    def run(self):
        while self.is_running:
            time.sleep(1.0 / self.frequency)
            self.update_trigger.emit()


class Wiimote(QtCore.QObject):
    values_trigger = QtCore.pyqtSignal()

    def __init__(self):
        super(Wiimote, self).__init__()
        self.wm = None

        self.thread = Thread(50)
        self.thread.update_trigger.connect(self.__update_loop_)
        self.thread.start()
        self.accelerometer_data = None
        self.notification = 'Wiimote Init'

    def connect(self, address):
        try:
            self.wm = wm.connect(address)
        except Exception:
            print('Connection Failed')
            self.wm = None

    def __update_loop_(self):
        if self.wm is None:
                print('No Wiimote Connected')
        else:
            self.accelerometer_data = self.wm.accelerometer

            # filter accelerometer_data here

            self.values_trigger.emit()


