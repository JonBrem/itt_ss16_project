#!/usr/bin/env python

import wiimote as wm
from PyQt5 import QtCore
import time
import utility_module as um
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

        self.notification = 'Wiimote Init'

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
                # print('No Wiimote Connected')
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

            self.__allow_button_press_once_('A', self.a_button_clicked)
            self.__allow_button_hold_('B', self.b_button_clicked,
                                      self.b_button_released)

            self.__allow_button_press_once_('Plus', self.plus_button_clicked)
            self.__allow_button_press_once_('Minus', self.minus_button_clicked)
            self.__allow_button_press_once_('One', self.one_button_clicked)
            self.__allow_button_press_once_('Two', self.two_button_clicked)

            # add more buttons as seen fit

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

        if self.is_ir_initial:
            self.is_ir_initial = pl.all(pl.array(points) == 1023)
            return

        x_values, y_values = \
            self.__get_moving_averages_points(um.sort_points(points))

        sx1, sy1 = x_values[0], y_values[0]  # tl
        sx2, sy2 = x_values[1], y_values[1]  # bl
        sx3, sy3 = x_values[2], y_values[2]  # br
        sx4, sy4 = x_values[3], y_values[3]  # tr

        source_points_123 = pl.matrix([[sx1, sx2, sx3],
                                       [sy1, sy2, sy3],
                                       [1, 1, 1]])
        source_point_4 = [[sx4],
                          [sy4],
                          [1]]

        scale_to_source = pl.solve(source_points_123, source_point_4)

        l, m, t = [float(x) for x in scale_to_source]

        unit_to_source = pl.matrix([[l * sx1, m * sx2, t * sx3],
                                    [l * sy1, m * sy2, t * sy3],
                                    [l, m, t]])

        dx1, dy1 = 0, 0
        dx2, dy2 = 0, self.monitor_height
        dx3, dy3 = self.monitor_width, self.monitor_height
        dx4, dy4 = self.monitor_width, 0

        dest_points_123 = pl.matrix([[dx1, dx2, dx3],
                                     [dy1, dy2, dy3],
                                     [1, 1, 1]])

        dest_point_4 = pl.matrix([[dx4],
                                  [dy4],
                                  [1]])

        scale_to_dest = pl.solve(dest_points_123, dest_point_4)

        l, m, t = [float(x) for x in scale_to_dest]

        unit_to_dest = pl.matrix([[l * dx1, m * dx2, t * dx3],
                                  [l * dy1, m * dy2, t * dy3],
                                  [l, m, t]])

        source_to_unit = pl.inv(unit_to_source)

        source_to_dest = unit_to_dest @ source_to_unit

        x, y, z = [float(w) for w in (source_to_dest @ pl.matrix([
            [self.width/2],
            [self.height/2],
            [1]]))]

        x /= z
        y /= z

        y = self.height - y

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



