#!/usr/bin/env python

from PyQt5 import QtCore
import time
from python.lib import wiimote as wm
from python.modules import utility_module as um
import pylab as pl


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

    ir_data_updated = QtCore.pyqtSignal()

    def __init__(self, frequency, monitor_width, monitor_height):
        super(Wiimote, self).__init__()
        self.wm = None
        self.num_samples = 32
        self.frequency = frequency
        self.monitor_width = monitor_width
        self.monitor_height = monitor_height

        # wiimote ir camera resolution

        self.width = 1024
        self.height = 768

        self.ring_x_values = um.RingArray(self.num_samples)
        self.ring_y_values = um.RingArray(self.num_samples)
        self.ring_z_values = um.RingArray(self.num_samples)

        self.ring_ir_sensor_samples = um.RingArray(self.num_samples)

        self.thread = Thread(self.frequency)
        self.thread.update_trigger.connect(self.__update_loop_)
        self.thread.start()
        self.accelerometer_data = None
        self.pointer_location = ()

        self.is_ir_initial = True

        self.button_states = dict.fromkeys(['A', 'B', 'Up', 'Down', 'Left',
                                            'Right', 'Home', 'Minus',
                                            'Plus', 'One', 'Two'], False)

    def connect(self, address):
        try:
            self.wm = wm.connect(address)
        except Exception:
            print('Connection Failed')
            self.wm = None

        if self.wm is not None:
            self.wm.ir.register_callback(self.__on_ir_sensor_data_)

    def __update_loop_(self):
        if self.wm is None:
            pass
        else:
            x, y, z = self.wm.accelerometer

            if x != 0 and y != 0 and z != 0:
                self.ring_x_values.append(x)
                self.ring_y_values.append(y)
                self.ring_z_values.append(z)

                ret_x = int(um.moving_average(self.ring_x_values,
                                              len(self.ring_x_values)))

                ret_y = int(um.moving_average(self.ring_y_values,
                                              len(self.ring_y_values)))

                ret_z = int(um.moving_average(self.ring_z_values,
                                              len(self.ring_z_values)))

                self.accelerometer_data = [ret_x, ret_y, ret_z]

            self.__allow_button_hold_('A', self.a_button_clicked,
                                      self.a_button_released)
            self.__allow_button_hold_('B', self.b_button_clicked,
                                      self.b_button_released)

            self.__allow_button_hold_('Up', self.up_button_clicked,
                                      self.up_button_released)

            self.__allow_button_hold_('Down', self.down_button_clicked,
                                      self.down_button_released)

            self.__allow_button_hold_('Left', self.left_button_clicked,
                                      self.left_button_released)

            self.__allow_button_hold_('Right', self.right_button_clicked,
                                      self.right_button_released)

            self.__allow_button_press_once_('Plus', self.plus_button_clicked)
            self.__allow_button_press_once_('Minus', self.minus_button_clicked)
            self.__allow_button_press_once_('One', self.one_button_clicked)
            self.__allow_button_press_once_('Two', self.two_button_clicked)
            self.__allow_button_press_once_('Home', self.home_button_clicked)

    def __allow_button_press_once_(self, btn, trigger):
        if self.wm.buttons[btn] and not self.button_states[btn]:
            self.button_states[btn] = True

            trigger.emit()
        elif not self.wm.buttons[btn] and self.button_states[btn]:
            self.button_states[btn] = False

    def __allow_button_hold_(self, btn, trigger_click, trigger_release):
        if self.wm.buttons[btn]:
            trigger_click.emit()
            self.button_states[btn] = True
        else:
            trigger_release.emit()
            self.button_states[btn] = False

    def __on_ir_sensor_data_(self, ir_data):
        if len(ir_data) != 4:
            return

        points = []
        [points.append([io['x'], io['y']]) for io in ir_data]

        # the ir sensor likes to initialize with 1023 for all coordinates
        # so we catch that case here

        if self.is_ir_initial:
            self.is_ir_initial = pl.all(pl.array(points) == 1023)
            return

        x_values, y_values = \
            self.__get_moving_averages_points(um.sort_points(points))

        x, y = um.get_projection_transformed_point(x_values, y_values,
                                                   self.monitor_width,
                                                   self.monitor_height,
                                                   self.width / 2,
                                                   self.height / 2)

        self.pointer_location = (x, y)

        self.ir_data_updated.emit()

    def __get_moving_averages_points(self, sorted_points):
        self.ring_ir_sensor_samples.append(sorted_points)

        temp_x_values = [0] * 4
        temp_y_values = [0] * 4

        for point_tuples in self.ring_ir_sensor_samples:
            for i in range(0, len(point_tuples)):
                temp_x_values[i] += (point_tuples[i][0] /
                                     len(self.ring_ir_sensor_samples))

                temp_y_values[i] += (point_tuples[i][1] /
                                     len(self.ring_ir_sensor_samples))

        return temp_x_values, temp_y_values
