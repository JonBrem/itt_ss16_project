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
    a_button_clicked = QtCore.pyqtSignal()
    b_button_clicked = QtCore.pyqtSignal()
    up_button_clicked = QtCore.pyqtSignal()
    down_button_clicked = QtCore.pyqtSignal()
    left_button_clicked = QtCore.pyqtSignal()
    right_button_clicked = QtCore.pyqtSignal()
    minus_button_clicked = QtCore.pyqtSignal()
    plus_button_clicked = QtCore.pyqtSignal()
    home_button_clicked = QtCore.pyqtSignal()
    one_button_clicked = QtCore.pyqtSignal()
    two_button_clicked = QtCore.pyqtSignal()

    a_button_released = QtCore.pyqtSignal()
    b_button_released = QtCore.pyqtSignal()
    up_button_released = QtCore.pyqtSignal()
    down_button_released = QtCore.pyqtSignal()
    left_button_released = QtCore.pyqtSignal()
    right_button_released = QtCore.pyqtSignal()
    minus_button_released = QtCore.pyqtSignal()
    plus_button_released = QtCore.pyqtSignal()
    home_button_released = QtCore.pyqtSignal()
    one_button_released = QtCore.pyqtSignal()
    two_button_released = QtCore.pyqtSignal()

    def __init__(self, frequency):
        super(Wiimote, self).__init__()
        self.wm = None
        self.num_samples = 32
        self.frequency = frequency

        self.ring_x_values = um.RingArray(self.num_samples)
        self.ring_y_values = um.RingArray(self.num_samples)
        self.ring_z_values = um.RingArray(self.num_samples)

        self.thread = Thread(self.frequency)
        self.thread.update_trigger.connect(self.__update_loop_)
        self.thread.start()
        self.accelerometer_data = None
        self.is_a_pressed = False

        self.button_states = dict.fromkeys(['A', 'B', 'Up', 'Down', 'Left',
                                            'Right', 'Home', 'Minus',
                                            'Plus', 'One', 'Two'], False)

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

            self.allow_button_press_once('A')
            self.allow_button_hold('B', self.b_button_clicked,
                                   self.b_button_released)

            # add more buttons as seen fit

    def allow_button_press_once(self, btn):
        if self.wm.buttons[btn] and not self.button_states[btn]:
            self.button_states[btn] = True

            self.a_button_clicked.emit()
        elif not self.wm.buttons[btn] and self.button_states[btn]:
            self.button_states[btn] = False

    def allow_button_hold(self, btn, trigger_click, trigger_release):
        if self.wm.buttons[btn]:
            self.button_states[btn] = True
            trigger_click.emit()
        else:
            self.button_states[btn] = False
            trigger_release.emit()
