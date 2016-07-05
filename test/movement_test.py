#!/usr/bin/env python

import os

from PyQt5 import uic, QtGui, QtCore, Qt, QtWidgets, QtWebKit
from PyQt5.QtCore import QFile, QIODevice, Qt, QTextStream, QUrl
from PyQt5.QtWidgets import (QAction, QApplication, QLineEdit, QMainWindow,
        QSizePolicy, QStyle, QTextEdit)
from PyQt5.QtNetwork import QNetworkProxyFactory, QNetworkRequest
from PyQt5.QtWebKitWidgets import QWebPage, QWebView

import numpy as np
import json
import undo_utility as undo
import base64

import js_interface_module as js
import wiimote_interface_module as wii
import blend_model_picker as model_table


class Window(QMainWindow):
    def __init__(self, url, app):
        super(Window, self).__init__()
        self.progress = 0
        self.app = app

        self.monitor_width = 1920
        self.monitor_height = 1080

        QNetworkProxyFactory.setUseSystemConfiguration(True)

        self.win = uic.loadUi('room_design.ui')
        self.wv = QWebView(self.win)

        js.SetupScene.init(self.wv)

        self.wv.setGeometry(10, 10, 1000, 650)
        js.SetupScene.apply_callback('python_callback', self)

        self.wv.load(url)
        self.wv.titleChanged.connect(self.adjustTitle)
        self.wv.loadFinished.connect(self.finishLoading)

        self.translate_btn = self.win.btn_translate
        self.rotate_btn = self.win.btn_rotate
        self.scale_btn = self.win.btn_scale

        self.list_widget = self.win.list_widget
        self.mesh_select_table = None
        self.model_table = None

        self.setup_ui()

        self.meshes = []
        self.selected_mesh = None
        self.mesh_translation = []
        self.mesh_rotation = []
        self.mesh_scale = []

        self.is_first_b_button_callback = True

        self.address_line_edit = self.win.line_edit_address
        self.connect_btn = self.win.btn_connect

        self.connect_btn.clicked.connect(self.connect_wiimote)

        self.initial_accelerometer_data = None

        self.wiimote = wii.Wiimote(50, self.monitor_width, self.monitor_height)
        self.setup_wiimote()

        self.last_angle_y_rotation = 0.0
        self.last_scale_factor = 1.0

        self.win.show()

        self.undo_utility = undo.UndoUtility()

    def setup_wiimote(self):
        self.wiimote.a_button_clicked.connect(
            lambda: self.on_wm_a_button_press(self.wiimote.accelerometer_data))

        self.wiimote.b_button_clicked.connect(
            lambda: self.on_wm_b_button_press(self.wiimote.accelerometer_data))

        self.wiimote.ir_data_updated.connect(
            lambda: self.on_wm_ir_data_update(self.wiimote.pointer_location))

        self.wiimote.b_button_released.connect(self.on_wm_b_button_release)

        self.wiimote.plus_button_clicked.connect(self.on_wm_plus_button_press)
        self.wiimote.minus_button_clicked.connect(self.on_wm_minus_button_press)

        self.wiimote.one_button_clicked.connect(self.request_undo)
        self.wiimote.two_button_clicked.connect(self.redo)

    def on_wm_ir_data_update(self, data):
        x, y = data

        self.set_cursor_position(x, y, True)

    def on_wm_a_button_press(self, data):
        if self.selected_mesh is not None:
            self.initial_accelerometer_data = data

    def on_wm_b_button_press(self, data):
        if self.is_first_b_button_callback:
            js.SetupScene.save_state("wiimote_transform")
            self.initial_accelerometer_data = data
            self.is_first_b_button_callback = False

        if self.selected_mesh is not None:
            js.SetupScene.get_translation_rotation_scale(self.selected_mesh)
            self.handle_mesh_scaling_fine(data)
            self.handle_mesh_rotation_y(data)

    def on_wm_plus_button_press(self):
        js.SetupScene.save_state("wiimote_scale_up")
        if self.selected_mesh is not None:
            js.SetupScene.get_translation_rotation_scale(self.selected_mesh)

            self.last_scale_factor = self.mesh_scale[0]

            js.SetupScene.scale_mesh_by_id(self.selected_mesh,
                                           self.last_scale_factor * 1.1,
                                           self.last_scale_factor * 1.1,
                                           self.last_scale_factor * 1.1)

    def on_wm_minus_button_press(self):
        js.SetupScene.save_state("wiimote_scale_down")
        if self.selected_mesh is not None:
            js.SetupScene.get_translation_rotation_scale(self.selected_mesh)

            self.last_scale_factor = self.mesh_scale[0]

            js.SetupScene.get_translation_rotation_scale(self.selected_mesh)

            js.SetupScene.scale_mesh_by_id(self.selected_mesh,
                                           self.last_scale_factor * 0.9,
                                           self.last_scale_factor * 0.9,
                                           self.last_scale_factor * 0.9)

    def handle_mesh_scaling_fine(self, data):
        scale_step = (512 - 407) / 10000

        scale = ((self.initial_accelerometer_data[1]-data[1]) * scale_step)

        if data[2] > 511:
            js.SetupScene.scale_mesh_by_id(self.selected_mesh,
                                           scale + self.last_scale_factor,
                                           scale + self.last_scale_factor,
                                           scale + self.last_scale_factor)

    def handle_mesh_rotation_y(self, data):
        angle_step = (512 - 407) / 90 * np.pi / 180

        angle = (self.initial_accelerometer_data[0]-data[0]) * angle_step/1.3

        if data[2] > 506:
            js.SetupScene.rotate_mesh_by_id(self.selected_mesh, 0, angle +
                                            self.last_angle_y_rotation, 0)
        '''
        elif data[2] < 507:
            js.SetupScene.rotate_mesh_by_id(self.selected_mesh, 0, (angle +
                                            self.last_angle_y_rotation) * -1, 0)
        '''

    def on_wm_b_button_release(self):
        if len(self.mesh_rotation) != 0:
            self.last_angle_y_rotation = self.mesh_rotation[1]

        if len(self.mesh_scale) != 0:
            self.last_scale_factor = self.mesh_scale[0]

            if self.mesh_scale[0] < 0.1:
                js.SetupScene.scale_mesh_by_id(self.selected_mesh,
                                               0.1,
                                               0.1,
                                               0.1)

                self.last_scale_factor = 0.1

        self.is_first_b_button_callback = True

    def connect_wiimote(self):
        address = self.address_line_edit.text()
        self.wiimote.connect(address)

    def perform_action_of_child_element(self):
        item = self.tree_widget.currentItem()
        if item.childCount() == 0:
            print(item.text(0) + ' selected')

    def setup_ui(self):
        self.translate_btn.clicked.connect(self.translate)
        self.rotate_btn.clicked.connect(self.rotate)
        self.scale_btn.clicked.connect(self.scale)

        self.win.btn_duplicate.clicked.connect(self.duplicate)

        self.list_widget.selectionModel().selectionChanged.connect(
            self.mesh_selection_changed)

        self.mesh_select_table = model_table.CategoryPickerTable(self,
                                                                 self.win)
        self.mesh_select_table.setGeometry(10 + 500,
                                           610 + model_table.TABLE_ITEM_SIZE,
                                           0, model_table.TABLE_ITEM_SIZE)

        self.read_mesh_data("assets/models_info.json")

        # @TODO: should do this for all buttons etc. except the mesh table
        self.wv.installEventFilter(self)
        self.win.installEventFilter(self)

    def read_mesh_data(self, file_path):
        with open(file_path, 'r') as mesh_data_file:
            mesh_data = json.loads(mesh_data_file.read())
            for category in mesh_data['categories']:
                self.mesh_select_table.add_item(category)

    def request_add_mesh(self, mesh_file_name, type_, name=None, transform="null", from_load=False):
        if not from_load:
            js.SetupScene.save_state("add_mesh")

        if name is None:
            name = type_
        original_name = name
        index = 1
        while name in self.meshes:
            name = original_name + str(index)
            index += 1

        mesh_file = open(mesh_file_name)
        only_json = ""

        data = '('
        for line in mesh_file:
            data += "'" + line[:-1] + "' + \n"
            only_json += line
        mesh_file.close()
        data += "'')"

        images = {}
        # pre-load any jpeg data for js:
        json_data = json.loads(only_json)
        if "materials" in json_data:
            for material in json_data["materials"]:
                if "diffuseTexture" in material:
                    if "name" in material["diffuseTexture"]:
                        file_name = "assets/models/" + material["diffuseTexture"]["name"]
                        if os.path.isfile(file_name):
                            jpeg_file = "data:image/jpg;base64," +\
                                str(base64.b64encode(open(file_name, "rb").read()))[2:]
                            images[material["diffuseTexture"]["name"]] = jpeg_file

        js.SetupScene.add_mesh(data, name, images, type_, transform, mesh_file_name)

    def duplicate(self, b=None):
        if self.selected_mesh is not None:
            self.request_duplicate_mesh(self.selected_mesh)

    def request_duplicate_mesh(self, mesh_id):
        js.SetupScene.save_state("duplicate_mesh")
        name = original_name = mesh_id + "_copy"
        index = 1
        while name in self.meshes:
            name = original_name + str(index)
            index += 1
        js.SetupScene.duplicate_mesh(mesh_id, name)

    def translate(self):
        js.SetupScene.save_state("translate_button")
        if self.selected_mesh is not None:
            js.SetupScene.translate_mesh_by_id(self.selected_mesh,
                                               1, 0, 0)

    def rotate(self):
        js.SetupScene.save_state("rotate_button")
        if self.selected_mesh is not None:
            angle = str((np.pi / 8))
            js.SetupScene.rotate_mesh_by_id(self.selected_mesh,
                                            0, 0, angle)

    def scale(self):
        js.SetupScene.save_state("scale_button")
        if self.selected_mesh is not None:
            js.SetupScene.scale_mesh_by_id(self.selected_mesh, 2, 1, 1)

    def viewSource(self):
        """
        never called?
        :return:
        """
        accessManager = self.wv.page().networkAccessManager()
        request = QNetworkRequest(self.wv.url())
        reply = accessManager.get(request)
        reply.finished.connect(self.slotSourceDownloaded)

    def slotSourceDownloaded(self):
        """
        never called?
        :return:
        """
        reply = self.sender()
        self.textEdit = QTextEdit()
        self.textEdit.setAttribute(Qt.WA_DeleteOnClose)
        self.textEdit.show()
        self.textEdit.setPlainText(QTextStream(reply).readAll())
        self.textEdit.resize(600, 400)
        reply.deleteLater()

    def adjustTitle(self):
        if 0 < self.progress < 100:
            pass
            # self.setWindowTitle("%s (%s%%)" % (self.view.title(), self.progress))
        else:
            self.setWindowTitle(self.wv.title())

    def finishLoading(self):
        self.progress = 100
        self.adjustTitle()

        """mesh_file = open('assets/box.babylon')

        data = '('
        for line in mesh_file:
            data += "'" + line[:-1] + "' + \n"
        mesh_file.close()
        data += "'')"

        js.SetupScene.add_mesh(data, 'my_cube')
        js.SetupScene.add_mesh(data, 'my_other_cube')"""

    def mesh_selection_changed(self, b=0):
        selected = self.list_widget.selectedIndexes()
        if len(selected) > 0:
            self.select_mesh(self.meshes[selected[0].row()], False)
        else:
            self.de_select_meshes(False)

    def select_mesh(self, obj_id, update_list=True):
        was_selected = self.selected_mesh == obj_id

        self.selected_mesh = obj_id
        for mesh in self.meshes:
            if mesh == obj_id:
                continue

            js.SetupScene.remove_highlight_from_mesh(mesh)

        if update_list and not was_selected:
            if obj_id in self.meshes:
                # remove any selection:
                selection_model = self.list_widget.selectionModel()
                selection_model.clear()
                # add new selection:
                selected_index = self.meshes.index(obj_id)
                new_selection = self.list_widget.indexFromItem(
                    self.list_widget.item(selected_index))
                selection_model.select(new_selection,
                                       QtCore.QItemSelectionModel.Select)

        js.SetupScene.highlight_mesh(obj_id)

    def de_select_meshes(self, from_js=True):
        # @todo: do we ever need that param??
        if from_js:
            selection_model = self.list_widget.selectionModel()
            selection_model.clear()
        self.selected_mesh = None

        for mesh in self.meshes:
            js.SetupScene.remove_highlight_from_mesh(mesh)

    def set_cursor_position(self, x, y, absolute=True):
        if absolute:
            self.cursor().setPos(x, y)
        else:
            self.cursor().setPos(self.win.centralWidget.pos().x() + x,
                                 self.win.centralWidget.pos().y() + y)

    def get_cursor_position(self, absolute=True):
        if absolute:
            return self.cursor().pos()
        else:
            cursor_pos = self.cursor().pos()
            # trial and error
            y_fix = self.win.style().pixelMetric(QtWidgets.QStyle.PM_TitleBarHeight) * 1.5 + 1
            return QtCore.QPoint(cursor_pos.x() - self.win.pos().x(),
                                 cursor_pos.y() - self.win.pos().y() - y_fix)

    def simulate_click(self):
        rel_cursor = self.get_cursor_position(False)
        abs_cursor = self.get_cursor_position(True)

        clicked_child = self.win.childAt(rel_cursor)
        if clicked_child is None:
            clicked_child = self.win
        for ev_type in (QtGui.QMouseEvent.MouseButtonPress,
                        QtGui.QMouseEvent.MouseButtonRelease):
            global_child_coords = clicked_child.mapToGlobal(QtCore.QPoint(0, 0))
            pos = QtCore.QPoint(abs_cursor.x() - global_child_coords.x(),
                                abs_cursor.y() - global_child_coords.y())
            event = QtGui.QMouseEvent(ev_type,
                                      pos,
                                      abs_cursor,
                                      QtCore.Qt.LeftButton,
                                      QtCore.Qt.LeftButton,
                                      QtCore.Qt.NoModifier)
            self.app.postEvent(clicked_child, event)

    @QtCore.pyqtSlot(str)
    def js_mesh_loaded(self, mesh_name):
        self.list_widget.addItem(mesh_name)  # maybe map binding to object ?
        self.meshes.append(mesh_name)
        self.select_mesh(mesh_name)

    @QtCore.pyqtSlot(str, str)
    def js_mesh_load_error(self, mesh_name, error):
        print(mesh_name, error)

    @QtCore.pyqtSlot(str, str, str, str, str)
    def on_js_object_manipulation_performed(self, mesh_id, action, x, y, z):
        s = ''

        if x != '':
            s += (x + ', ')

        if y != '':
            s += (y + ', ')

        if z != '':
            s += z

    @QtCore.pyqtSlot(str)
    def on_object_clicked(self, obj_id):
        if obj_id in self.meshes:
            self.select_mesh(obj_id)
        elif len(obj_id) == 0:  # == None; None does not work from JS
            self.de_select_meshes()

    @QtCore.pyqtSlot(str)
    def on_js_console_log(self, log):
        """
        function for debugging purposes
        probably the most important one :P

        :param log:
        :return:
        """
        print(log)

    @QtCore.pyqtSlot(str, str, str)
    def on_translation_rotation_scale_request(self, trans, rot, scale):
        self.get_mesh_properties(trans, 'trans')
        self.get_mesh_properties(rot, 'rot')
        self.get_mesh_properties(scale, 'scale')

    def get_mesh_properties(self, data, mode):

        if mode == 'trans':
            self.mesh_translation = js.deserialize_list(data)

        if mode == 'rot':
            self.mesh_rotation = js.deserialize_list(data)

        if mode == 'scale':
            self.mesh_scale = js.deserialize_list(data)

    @QtCore.pyqtSlot(str, str)
    def save_state_result(self, scene_json, identifier):
        if identifier == "undo":
            self.undo_utility.set_first_state_at_undo(scene_json)
            self.undo()
        else:
            self.undo_utility.add_action(identifier, scene_json)

    def load_state(self, scene_json):
        self.clear_all()
        as_data = json.loads(scene_json)
        for mesh in as_data["meshes"]:
            self.request_add_mesh(mesh["fileName"], mesh["type"], mesh["id"], json.dumps({
                "pos": mesh["pos"],
                "rot": mesh["rot"],
                "scale": mesh["scale"]
                }), True)

    def clear_all(self):
        while self.list_widget.count() > 0:
            self.list_widget.takeItem(0)

        for mesh in self.meshes:
            js.SetupScene.remove_mesh(mesh)

        self.meshes = []
        self.selected_mesh = None

    def delete_mesh(self, mesh_id):
        self.selected_mesh = None
        if mesh_id in self.meshes:
            index = self.meshes.index(mesh_id)
            del self.meshes[index]
            self.list_widget.takeItem(index)
        js.SetupScene.remove_mesh(mesh_id)

    def request_undo(self):
        js.SetupScene.save_state("undo")

    def undo(self):
        undone_state = self.undo_utility.undo()
        if undone_state is not None:
            print("undoing: " + undone_state["action"])
            self.load_state(undone_state["state"])

    def redo(self):
        redone_state = self.undo_utility.redo()
        if redone_state is not None:
            print("redoing: " + redone_state["action"])
            self.load_state(redone_state["state"])

    # event filter that causes mesh selection table to lose focus
    # (if it has focus)
    def eventFilter(self, source, event):
        if event.type() == QtGui.QMouseEvent.MouseButtonPress:
            self.mesh_select_table.lose_focus()
        elif event.type() == QtGui.QKeyEvent.KeyRelease:
            if event.key() == 67:  # c[lear]
                self.clear_all()
            elif event.key() == 82:  # r[emove]
                if self.selected_mesh is not None:
                    self.delete_mesh(self.selected_mesh)
            elif event.key() == 75:  # [clic]k
                self.simulate_click()
            # z (undo if with ctrl)
            elif (event.key() == 90 and
                  int(event.modifiers()) == QtCore.Qt.ControlModifier):
                self.request_undo()
            # y (redo if with ctrl)
            elif (event.key() == 89 and
                  int(event.modifiers()) == QtCore.Qt.ControlModifier):
                self.redo()
            elif event.key() == 49:  # 1
                self.set_cursor_position(100.0, 100.0, True)
            elif event.key() == 50:  # 1
                self.set_cursor_position(100.0, 200.0, True)
            elif event.key() == 51:  # 1
                self.set_cursor_position(200.0, 200.0, True)
            elif event.key() == 52:  # 1
                self.set_cursor_position(200.0, 100.0, True)
            else:
                print(event.key(), int(event.modifiers()))
        return super(Window, self).eventFilter(source, event)


def main():
    app = QApplication(sys.argv)
    url = QUrl('file:///' + os.path.dirname(os.path.realpath(__file__)) + '/index.html')

    win = Window(url, app)

    sys.exit(app.exec_())

    pass


if __name__ == '__main__':
    import sys

    main()
