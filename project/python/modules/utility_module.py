#!/usr/bin/env python

from PyQt5 import QtCore, QtGui, Qt, QtWidgets
from collections import deque

import pylab as pl
import json
import os
import base64


class RingArray(deque):
    def __init__(self, max_length):
        super(RingArray, self).__init__(maxlen=max_length)

    def __repr__(self):
        """
        override

        :return:
        """

        l = []

        for i in self:
            l.append(i)

        return str(l)

    def append(self, *args, **kwargs):
        """
        override

        :param args:
        :param kwargs:
        :return:
        """

        if self.maxlen == len(self):
            self.rotate(-1)
            self.pop()
            super(RingArray, self).append(*args, **kwargs)
        else:
            super(RingArray, self).append(*args, **kwargs)


class InputDialog(Qt.QDialog):
    def __init__(self, parent):
        super(InputDialog, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout()

        self.setWindowTitle('Room Dimensions')

        self.line_edit_x = QtWidgets.QLineEdit()
        self.line_edit_y = QtWidgets.QLineEdit()

        self.label_x = QtWidgets.QLabel('x')
        self.label_y = QtWidgets.QLabel('y')

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(self.label_x)
        layout.addWidget(self.line_edit_x)
        layout.addWidget(self.label_y)
        layout.addWidget(self.line_edit_y)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_dimensions(self):
        if self.line_edit_x.text() is '' or self.line_edit_y.text() is '' or \
                        int(self.line_edit_x.text()) < 0 or \
                        int(self.line_edit_y.text()) < 0:
            return -1, -1

        return int(self.line_edit_x.text()), int(self.line_edit_y.text())

    @staticmethod
    def get_new_room_xz_dimensions(parent=None):
        dialog = InputDialog(parent)
        result = dialog.exec_()

        x, y = dialog.get_dimensions()

        if result == QtWidgets.QDialog.Rejected:
            return x, y, result == QtWidgets.QDialog.Accepted
        elif result == QtWidgets.QDialog.Accepted:
            if x == -1:
                return InputDialog.get_new_room_xz_dimensions()

            return x, y, result == QtWidgets.QDialog.Accepted


class FileDialog(QtWidgets.QFileDialog):
    def __init__(self, parent):
        super(FileDialog, self).__init__(parent)
        self.mode = mode

        if mode == 'save':
            self.setWindowTitle('Save as...')
        elif mode == 'load':
            self.setWindowTitle('Load from...')

    @staticmethod
    def save_json_to_file(scene_json):
        file_name, filter = FileDialog.getSaveFileName()

        if file_name != '':
            file = open(file_name, 'w')
            file.write(scene_json)
            file.close()

    @staticmethod
    def load_json_from_file():
        file_name, filter = FileDialog.getOpenFileName()

        if file_name != '':
            file = open(file_name, 'r')
            scene_json = file.read()
            file.close()

            return scene_json
        else:
            return ''



def moving_average(data, num_samples):
    return sum(data) / num_samples


def sort_points(points):
    """
    gets a list of points which are list themselves [x, y]
    it is expected that the list has the length 4

    calculates the top left, bottom left, bottom right and top right corners
    in that order (tl, bl, br, tr) and stores them in a list

    :param points: the unordered list of points with the length 4 (expected)

    :return: the sorted points in the order mentioned above
    """

    sorted_points = []

    x = float('inf')
    x2 = float('inf')
    y = 0
    y2 = 0

    for p in points:
        if p[0] < x:
            x = p[0]
            y = p[1]

            if x < x2:
                temp_x = x
                temp_y = y
                x = x2
                y = y2
                x2 = temp_x
                y2 = temp_y

    if y < y2:
        sorted_points.append([x, y])
        sorted_points.append([x2, y2])
    else:
        sorted_points.append([x2, y2])
        sorted_points.append([x, y])

    x = -1
    x2 = -1
    y = 0
    y2 = 0

    for p in points:
        if p[0] > x:
            x = p[0]
            y = p[1]

            if x > x2:
                temp_x = x
                temp_y = y
                x = x2
                y = y2
                x2 = temp_x
                y2 = temp_y

    if y < y2:
        sorted_points.append([x2, y2])
        sorted_points.append([x, y])
    else:
        sorted_points.append([x, y])
        sorted_points.append([x2, y2])

    return sorted_points


def get_projection_transformed_point(src_x_values, src_y_values, dest_width,
                                     dest_height, target_point_x,
                                     target_point_y):
    sx1, sy1 = src_x_values[0], src_y_values[0]  # tl
    sx2, sy2 = src_x_values[1], src_y_values[1]  # bl
    sx3, sy3 = src_x_values[2], src_y_values[2]  # br
    sx4, sy4 = src_x_values[3], src_y_values[3]  # tr

    source_points_123 = pl.matrix([[sx1, sx2, sx3],
                                   [sy1, sy2, sy3],
                                   [1, 1, 1]])

    source_point_4 = [[sx4], [sy4], [1]]

    scale_to_source = pl.solve(source_points_123, source_point_4)

    l, m, t = [float(x) for x in scale_to_source]

    unit_to_source = pl.matrix([[l * sx1, m * sx2, t * sx3],
                                [l * sy1, m * sy2, t * sy3],
                                [l, m, t]])

    dx1, dy1 = 0, 0
    dx2, dy2 = 0, dest_height
    dx3, dy3 = dest_width, dest_height
    dx4, dy4 = dest_width, 0

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
        [target_point_x],
        [target_point_y],
        [1]]))]

    x /= z
    y /= z

    y = target_point_y * 2 - y

    return x, y


def get_name_for_new_mesh(name, type_, used_names):
    if name is None:
        name = type_
    # "original" = unadulterated name
    original_name = name
    index = 1
    while name in used_names:
        name = original_name + str(index)
        index += 1
    return name


def get_name_for_copy(orig_mesh_id, used_names):
    name = original_name = orig_mesh_id + "_copy"
    index = 1
    while name in used_names:
        name = original_name + str(index)
        index += 1
    return name


def read_file_as_js_string(file, regular_contents_as_well=False):
    for_js = '('
    regular_contents = ''
    for line in file:
        for_js += "'" + line[:-1] + "' + \n"
        if regular_contents_as_well:
            regular_contents += line
    for_js += "'')"

    if regular_contents_as_well:
        return for_js, regular_contents
    else:
        return for_js


def load_images_as_base64(mesh_json):
    """ Loads images (only for material diffuse textures) from jpeg
        files as base 64 strings.
        Returns a dict where the original file name (the one in the JSON)
        is the key and the base64 data is the value. Thus, the corresponding
        mesh data can easily be found in JS.

        Will just do nothing if there is an error. The Param is a JSON string,
        no JSON object.
    """
    images = {}
    mesh_json = json.loads(mesh_json)
    if "materials" in mesh_json:
        for material in mesh_json["materials"]:
            if "diffuseTexture" in material:
                if "name" in material["diffuseTexture"]:
                    file_name = "assets/models/" + \
                                material["diffuseTexture"]["name"]
                    if os.path.isfile(file_name):
                        jpeg_file = load_single_img_as_base64(file_name)
                        images[material["diffuseTexture"]["name"]] = \
                            jpeg_file
    return images


def load_single_img_as_base64(file_name):
    base64data = "data:image/jpg;base64," + \
        str(base64.b64encode(open(file_name, "rb").read()))[2:]
    return base64data
