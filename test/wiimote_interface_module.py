#!/usr/bin/env python

import wiimote as wm
from PyQt5 import QtCore
import time
import utility_module as um


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
        self.num_samples = 32

        self.ring_x_values = um.RingArray(self.num_samples)
        self.ring_y_values = um.RingArray(self.num_samples)
        self.ring_z_values = um.RingArray(self.num_samples)

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
                # print('No Wiimote Connected')
            pass
        else:
            x, y, z = self.wm.accelerometer

            if x != 0 and y != 0 and z != 0:
                self.ring_x_values.append(x)
                self.ring_y_values.append(y)
                self.ring_z_values.append(z)

                ret_x = int(um.moving_average(self.ring_x_values,
                                              self.num_samples))

                ret_y = int(um.moving_average(self.ring_y_values,
                                              self.num_samples))

                ret_z = int(um.moving_average(self.ring_z_values,
                                              self.num_samples))

                self.accelerometer_data = [ret_x, ret_y, ret_z]

                self.values_trigger.emit()
