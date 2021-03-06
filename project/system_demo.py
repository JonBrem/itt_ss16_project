#!/usr/bin/python3

import os
from PyQt5 import uic, QtGui, QtCore, Qt, QtWidgets
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow)
from PyQt5.QtNetwork import QNetworkProxyFactory
from PyQt5.QtWebKitWidgets import QWebView

import numpy as np
import json

from python.modules import undo_utility as undo
from python.modules import js_interface_module as js
from python.modules import wiimote_interface_module as wii
from python.modules import blend_model_picker as model_table
from python.modules import utility_module as um


class Window(QMainWindow):
    def __init__(self, url, app):
        super(Window, self).__init__()
        self.progress = 0
        self.app = app

        self.UI_FILE_PATH = 'ui/room_design.ui'
        self.CALLBACK = 'python_callback'
        self.MODELS_INFO = 'assets/models_info.json'
        self.TEXTURES_INFO = 'assets/textures_info.json'
        self.WIIMOTE_FREQUENCY = 50
        self.DEFAULT_SCALE = 1.0
        self.DEFAULT_ROTATION = 0.0
        self.PLANE_XZ = 'xz'
        self.PLANE_XY = 'xy'
        self.PLANE_YZ = 'yz'

        self.WIN_X = 30
        self.WIN_Y = 60
        self.WIN_WIDTH = 1000
        self.WIN_HEIGHT = 650

        self.WIIMOTE_DEFAULT_ACCEL_SENSOR_VALUE = 512
        self.WIIMOTE_MIN_ACCEL_SENSOR_VALUE = 407
        self.WIIMOTE_MAX_ACCEL_SENSOR_VALUE = 610
        self.WIIMOTE_SENSITIVITY = 10000

        self.MESH_SELECT_TABLE_X_LEFT = 250
        self.TEXTURE_SELECT_TABLE_X_LEFT = 50
        self.SELECT_TABLES_Y = 665

        screen_dimens = self.app.desktop().screenGeometry()
        self.url = url
        self.monitor_width = screen_dimens.width()
        self.monitor_height = screen_dimens.height()

        QNetworkProxyFactory.setUseSystemConfiguration(True)

        self.win = uic.loadUi(self.UI_FILE_PATH)
        self.wv = QWebView(self.win)

        js.SetupScene.init(self.wv)
        js.SetupScene.apply_callback(self.CALLBACK, self)

        self.wv.load(self.url)

        self.list_widget = self.win.list_widget
        self.mesh_select_table = None
        self.model_table = None
        self.texture_select_table = None

        self.setup_ui()

        self.meshes = []
        self.selected_mesh = None
        self.mesh_translation = []
        self.mesh_rotation = []
        self.mesh_scale = []

        self.is_first_b_button_callback = True
        self.wm_current_a_button_state = False

        self.address_line_edit = self.win.line_edit_address
        self.connect_btn = self.win.btn_connect

        self.connect_btn.clicked.connect(self.connect_wiimote)

        self.initial_accelerometer_data = None

        self.wiimote = wii.Wiimote(self.WIIMOTE_FREQUENCY, self.monitor_width,
                                   self.monitor_height)
        self.dpad_button_states = {}
        self.setup_wiimote()

        self.last_angle_y_rotation = self.DEFAULT_ROTATION
        self.last_scale_factor = self.DEFAULT_SCALE

        self.win.show()

        self.undo_utility = undo.UndoUtility()

        self.selected_plane = self.PLANE_XZ
        self.select_plane(self.selected_plane)

    # WIIMOTE BINDINGS & METHODS

    def setup_wiimote(self):
        self.wiimote.a_button_clicked.connect(
            lambda: self.on_wm_a_button_press(self.wiimote.accelerometer_data))
        self.wiimote.a_button_released.connect(self.on_wm_a_button_release)

        self.wiimote.b_button_clicked.connect(
            lambda: self.on_wm_b_button_press(self.wiimote.accelerometer_data))

        self.wiimote.ir_data_updated.connect(
            lambda: self.on_wm_ir_data_update(self.wiimote.pointer_location))

        self.wiimote.b_button_released.connect(self.on_wm_b_button_release)

        self.wiimote.plus_button_clicked.connect(self.on_wm_plus_button_press)
        self.wiimote.minus_button_clicked.connect(self.on_wm_minus_button_press)

        self.wiimote.one_button_clicked.connect(self.request_undo)
        self.wiimote.two_button_clicked.connect(self.redo)

        self.dpad_button_states = {
            Qt.Key_Up: False, Qt.Key_Down: False,
            Qt.Key_Left: False, Qt.Key_Right: False, }
        self.wiimote.up_button_clicked.connect(
            lambda: self.on_wm_dpad_button_press(Qt.Key_Up))
        self.wiimote.up_button_released.connect(
            lambda: self.on_wm_dpad_button_release(Qt.Key_Up))
        self.wiimote.down_button_clicked.connect(
            lambda: self.on_wm_dpad_button_press(Qt.Key_Down))
        self.wiimote.down_button_released.connect(
            lambda: self.on_wm_dpad_button_release(Qt.Key_Down))
        self.wiimote.left_button_clicked.connect(
            lambda: self.on_wm_dpad_button_press(Qt.Key_Left))
        self.wiimote.left_button_released.connect(
            lambda: self.on_wm_dpad_button_release(Qt.Key_Left))
        self.wiimote.right_button_clicked.connect(
            lambda: self.on_wm_dpad_button_press(Qt.Key_Right))
        self.wiimote.right_button_released.connect(
            lambda: self.on_wm_dpad_button_release(Qt.Key_Right))
        self.wiimote.home_button_clicked.connect(self.on_wm_home_button_clicked)

    def on_wm_ir_data_update(self, data):
        x, y = data
        self.set_cursor_position(x, y, True)

    def on_wm_a_button_press(self, data):
        if self.wm_current_a_button_state:
            return
        self.wm_current_a_button_state = True
        self.simulate_mouse_press()
        if self.selected_mesh is not None:
            self.initial_accelerometer_data = data

    def on_wm_a_button_release(self):
        if self.wm_current_a_button_state is False:
            return
        self.wm_current_a_button_state = False
        self.simulate_mouse_release()

    def on_wm_b_button_press(self, data):
        if self.is_first_b_button_callback:
            js.SetupScene.save_state("wiimote_transform")
            self.initial_accelerometer_data = data
            self.is_first_b_button_callback = False

        if self.selected_mesh is not None:
            js.SetupScene.get_translation_rotation_scale(self.selected_mesh)
            self.handle_mesh_scaling_fine(data)
            self.handle_mesh_rotation_y(data)

    def on_wm_dpad_button_press(self, button):
        self.dpad_button_states[button] = True
        self.simulate_camera_event(QtGui.QKeyEvent.KeyPress, button)

    def on_wm_dpad_button_release(self, button):
        if self.dpad_button_states[button]:  # = last frame: button was pressed
            self.simulate_camera_event(QtGui.QKeyEvent.KeyRelease, button)
        self.dpad_button_states[button] = False

    def on_wm_plus_button_press(self):
        if self.selected_mesh is not None:
            js.SetupScene.save_state("duplicate_mesh")
            if self.selected_mesh is not None:
                self.request_duplicate_mesh(self.selected_mesh)

    def on_wm_minus_button_press(self):
        if self.selected_mesh is not None:
            js.SetupScene.save_state("remove_mesh")
            self.delete_mesh(self.selected_mesh)

    def on_wm_home_button_clicked(self):
        js.SetupScene.set_camera_to_default()

    def on_wm_b_button_release(self):
        if len(self.mesh_rotation) != 0:
            self.last_angle_y_rotation = self.mesh_rotation[1]

        if len(self.mesh_scale) != 0:
            self.last_scale_factor = self.mesh_scale[0]

            if self.mesh_scale[0] < 0.1:
                js.SetupScene.scale_mesh_by_id(self.selected_mesh, 0.1, 0.1,
                                               0.1)

                self.last_scale_factor = 0.1

        js.SetupScene.on_scale_end()
        self.is_first_b_button_callback = True

    def connect_wiimote(self):
        address = self.address_line_edit.text()
        self.wiimote.connect(address)

    # UI SETUP

    def setup_ui(self):
        self.wv.setGeometry(self.WIN_X, self.WIN_Y, self.WIN_WIDTH,
                            self.WIN_HEIGHT)
        self.wv.installEventFilter(self)
        self.win.installEventFilter(self)

        self.list_widget.selectionModel().selectionChanged.connect(
            self.mesh_selection_changed)

        self.setup_selection_tables()

        self.win.explain_controls_btn.clicked.connect(self.explain_controls)

        self.win.x_y_plane_btn.clicked.connect(
            lambda: self.select_plane(self.PLANE_XY))
        self.win.x_z_plane_btn.clicked.connect(
            lambda: self.select_plane(self.PLANE_XZ))
        self.win.y_z_plane_btn.clicked.connect(
            lambda: self.select_plane(self.PLANE_YZ))

        self.win.x_y_plane_cam_btn.clicked.connect(
            lambda: self.target_cam_to_plane(self.PLANE_XY))
        self.win.x_z_plane_cam_btn.clicked.connect(
            lambda: self.target_cam_to_plane(self.PLANE_XZ))
        self.win.y_z_plane_cam_btn.clicked.connect(
            lambda: self.target_cam_to_plane(self.PLANE_YZ))

        self.win.btn_new.clicked.connect(self.on_new_action)
        self.win.btn_save.clicked.connect(self.on_save_action)
        self.win.btn_load.clicked.connect(self.on_load_action)

    def set_bt_address(self, address):
        self.win.line_edit_address.setText(address)

    # SELECTION TABLES

    def setup_selection_tables(self):
        """ Sets up the mesh_select_table and texture_select_table
        """
        # magic numbers = coordinates (the app is not responsive anyway)

        # mesh_select_table (for the models)
        self.mesh_select_table = model_table.ExpandableSelectionTable(
            self, 'Mesh', self.win)
        self.mesh_select_table.set_create_from_center(False)
        self.mesh_select_table.move(
            self.MESH_SELECT_TABLE_X_LEFT,
            self.SELECT_TABLES_Y + model_table.TABLE_ITEM_SIZE)
        self.mesh_select_table.itemSelectionChanged.connect(
            lambda: self.table_selection_changed(self.mesh_select_table))
        self.read_selection_table_data(self.MODELS_INFO,
                                       self.mesh_select_table)

        # texture_select_table (ground, wall textures)
        self.texture_select_table = model_table.ExpandableSelectionTable(
            self, 'Texture', self.win)
        self.texture_select_table.set_create_from_center(False)
        self.texture_select_table.move(
            self.TEXTURE_SELECT_TABLE_X_LEFT,
            self.SELECT_TABLES_Y + model_table.TABLE_ITEM_SIZE)
        self.texture_select_table.itemSelectionChanged.connect(
            lambda: self.table_selection_changed(self.texture_select_table))
        self.read_selection_table_data(self.TEXTURES_INFO,
                                       self.texture_select_table)

    def table_selection_changed(self, table):
        """ Callback method; simply de-selects the other table.
            "Table" refers to the mesh selection bar or the
            texture selection bar (which are, technically, tables).
        """
        other_table = None
        if table == self.mesh_select_table:
            other_table = self.texture_select_table
        else:
            other_table = self.mesh_select_table

        if len(table.selectedIndexes()) > 0:
            other_table.lose_focus()

    def read_selection_table_data(self, file_path, selection_table):
        """ Reads the data from the file (e.g. assets/models_info.json)
            and sets up the seletion_table, i.e., tells it what categories
            there are & what icons and subitems they have.
        """
        with open(file_path, 'r') as data_file:
            data = json.loads(data_file.read())
            for category in data['categories']:
                selection_table.add_item(category)

    # ADDING MESHES / SELECTING TEXTURES

    def request_add_mesh(self, mesh_file_name, type_, name=None,
                         transform="null", from_load=False):
        """ Tells the JS component to add a mesh (scene object).

            name: might be overwritten if it is already in use
            transform: location, rotation and scale (default="null" = at the
                       center of the scene, scale = 1 & rotation = 0, 0, 0)
            from_load: when this method is called to load another state (True),
                       no new "undo state" will be created. Default=False
        """
        if not from_load:
            js.SetupScene.save_state("add_mesh")

        name = um.get_name_for_new_mesh(name, type_, self.meshes)

        mesh_file = open(mesh_file_name)
        data, json_data = um.read_file_as_js_string(mesh_file, True)
        mesh_file.close()

        texture_images = um.load_images_as_base64(json_data)

        js.SetupScene.add_mesh(data, name, texture_images, type_, transform,
                               mesh_file_name)

    @QtCore.pyqtSlot(str)
    def js_mesh_loaded(self, mesh_name):
        """ Gets called when the JS component successfully created an object.
        """
        self.list_widget.addItem(mesh_name)
        self.meshes.append(mesh_name)
        self.select_mesh(mesh_name)

    @QtCore.pyqtSlot(str, str)
    def js_mesh_load_error(self, mesh_name, error):
        """ Gets called when the JS component failed to create an object. """
        print(mesh_name, error)

    def request_change_texture(self, file_name, name, type_,
                               create_undo_point=True):
        if create_undo_point:
            js.SetupScene.save_state("change_texture")

        base64data = um.load_single_img_as_base64(file_name)
        js.SetupScene.set_texture(type_, name, base64data, file_name)

    # PLANE / CAMERA BUTTONS ON THE SIDE

    def target_cam_to_plane(self, plane):
            js.SetupScene.target_camera_to_plane(plane)

    def select_plane(self, which):
        self.selected_plane = which

        data = {self.PLANE_XY: [False, True, True],
                self.PLANE_XZ: [True, False, True],
                self.PLANE_YZ: [True, True, False], }

        self.win.x_y_plane_btn.setEnabled(data[which][0])
        self.win.x_z_plane_btn.setEnabled(data[which][1])
        self.win.y_z_plane_btn.setEnabled(data[which][2])

        js.SetupScene.set_selected_plane(which)

    # OBJECT MANIPULATIONS

    def request_duplicate_mesh(self, mesh_id):
        js.SetupScene.save_state("duplicate_mesh")
        name = um.get_name_for_copy(mesh_id, self.meshes)
        js.SetupScene.duplicate_mesh(mesh_id, name)

    def handle_mesh_scaling_fine(self, data):
        scale_step = (self.WIIMOTE_DEFAULT_ACCEL_SENSOR_VALUE -
                      self.WIIMOTE_MIN_ACCEL_SENSOR_VALUE) / \
                     self.WIIMOTE_SENSITIVITY

        scale = ((self.initial_accelerometer_data[1]-data[1]) * scale_step)

        if data[2] > self.WIIMOTE_DEFAULT_ACCEL_SENSOR_VALUE - 1:
            js.SetupScene.scale_mesh_by_id(self.selected_mesh,
                                           scale + self.last_scale_factor,
                                           scale + self.last_scale_factor,
                                           scale + self.last_scale_factor)

    def handle_mesh_rotation_y(self, data):
        right_angle = 90
        angle_step_smoothing = 1.3
        sensor_data_smoothing = 6

        angle_step = (self.WIIMOTE_DEFAULT_ACCEL_SENSOR_VALUE -
                      self.WIIMOTE_MIN_ACCEL_SENSOR_VALUE) / \
            right_angle * np.pi / (right_angle * 2)

        angle = (self.initial_accelerometer_data[0]-data[0]) * angle_step / \
            angle_step_smoothing

        if data[2] > self.WIIMOTE_DEFAULT_ACCEL_SENSOR_VALUE - \
                sensor_data_smoothing:
            js.SetupScene.rotate_mesh_by_id(self.selected_mesh, 0, angle +
                                            self.last_angle_y_rotation, 0)

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

    # dragging happens in JS, Python is notified when it starts to enable Undo:

    @QtCore.pyqtSlot(str)
    def on_js_obj_drag_start(self, mesh_id):
        js.SetupScene.save_state("js_drag_translate")

    # DELETING / RESETTING

    def clear_all(self):
        """ Resets the entire scene & the undo utility. """
        while self.list_widget.count() > 0:
            self.list_widget.takeItem(0)

        for mesh in self.meshes:
            js.SetupScene.remove_mesh(mesh)

        js.SetupScene.remove_texture("walls")
        js.SetupScene.remove_texture("carpet")
        self.meshes = []
        self.selected_mesh = None
        self.undo_utility.reset()

    def delete_mesh(self, mesh_id):
        self.selected_mesh = None
        if mesh_id in self.meshes:
            index = self.meshes.index(mesh_id)
            del self.meshes[index]
            self.list_widget.takeItem(index)
        js.SetupScene.remove_mesh(mesh_id)

    # MESH SELECTION

    def mesh_selection_changed(self, b=0):
        """ Callback for when the selection in the list of scene objects
            changes.
        """
        selected = self.list_widget.selectedIndexes()
        if len(selected) > 0:
            self.select_mesh(self.meshes[selected[0].row()], False)
        else:
            self.de_select_meshes(False)

    def select_mesh(self, obj_id, update_list=True, from_click=False):
        """ Sets the mesh as selected in the scene (gives it an outine)
            & in the list of objects.

            update_list: if the selection change came from the list widget,
                         it should not be updated redundantly (=False)
        """
        was_selected = self.selected_mesh == obj_id
        # = short for "the item that was selected was the item that was already
        # selected"

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

        js.SetupScene.highlight_mesh(obj_id, from_click)

    def de_select_meshes(self, from_js=True):
        if from_js:
            selection_model = self.list_widget.selectionModel()
            selection_model.clear()
        self.selected_mesh = None

        for mesh in self.meshes:
            js.SetupScene.remove_highlight_from_mesh(mesh)

    @QtCore.pyqtSlot(str)
    def on_object_clicked(self, obj_id):
        if obj_id in self.meshes:
            self.select_mesh(obj_id, True, True)
        else:  # == None; None does not work from JS
            self.de_select_meshes()

    @QtCore.pyqtSlot(str, str, str)
    def on_mesh_highlighted(self, obj_id, scale, y_rotation):
        self.last_scale_factor = float(scale)
        self.last_angle_y_rotation = float(y_rotation)

        self.mesh_rotation = [0, float(y_rotation), 0]
        self.mesh_scale = [float(scale), float(scale), float(scale)]

    # CURSOR AND CLICKS

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
            y_fix = self.win.style().pixelMetric(
                QtWidgets.QStyle.PM_TitleBarHeight) * 1.5 + 1
            return QtCore.QPoint(cursor_pos.x() - self.win.pos().x(),
                                 cursor_pos.y() - self.win.pos().y() - y_fix)

    def simulate_click(self):
        rel_cursor = self.get_cursor_position(False)
        abs_cursor = self.get_cursor_position(True)

        for ev_type in (QtGui.QMouseEvent.MouseButtonPress,
                        QtGui.QMouseEvent.MouseButtonRelease):
            self.simulate_left_mouse_event(ev_type, rel_cursor, abs_cursor)

    def simulate_mouse_press(self):
        rel_cursor = self.get_cursor_position(False)
        abs_cursor = self.get_cursor_position(True)

        self.simulate_left_mouse_event(QtGui.QMouseEvent.MouseButtonPress,
                                       rel_cursor, abs_cursor)

    def simulate_mouse_release(self):
        rel_cursor = self.get_cursor_position(False)
        abs_cursor = self.get_cursor_position(True)

        self.simulate_left_mouse_event(QtGui.QMouseEvent.MouseButtonRelease,
                                       rel_cursor, abs_cursor)

    def simulate_left_mouse_event(self, ev_type, rel_cursor, abs_cursor):
        clicked_child = self.win.childAt(rel_cursor)
        if clicked_child is None:
            clicked_child = self.win
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

    def simulate_camera_event(self, type_, key):
        event = QtGui.QKeyEvent(type_, key, QtCore.Qt.NoModifier)

        self.app.postEvent(self.wv, event)

    # NEW, SAVE, LOAD, UNDO, REDO

    def on_new_action(self):
        x, y, ok = um.InputDialog.get_new_room_xz_dimensions()

        if ok:
            self.clear_all()
            js.SetupScene.create_new_scene(x, y)

    def on_save_action(self):
        js.SetupScene.save_state("save")

    def on_load_action(self):
        scene_json = um.FileDialog.load_json_from_file()

        if scene_json != '':
            self.load_state(scene_json)

    @QtCore.pyqtSlot(str, str)
    def save_state_result(self, scene_json, identifier):
        """ Callback for when JS successfully saved the scene.

            identifier: same string that was given to the JS component
                        to mark why the state was saved. E.g., if it is
                        "undo", that means it was created to be able to
                        redo the scene & it should not be added to the
                        undo list.
        """
        scene_obj = json.loads(scene_json)

        scene_obj["selection"] = self.selected_mesh if \
            (self.selected_mesh is not None) else "None"

        scene_json = json.dumps(scene_obj)

        if identifier == "undo":
            self.undo_utility.set_first_state_at_undo(scene_json)
            self.undo()
        elif identifier == "save":
            um.FileDialog.save_json_to_file(scene_json)
        else:
            self.undo_utility.add_action(identifier, scene_json)

    def load_state(self, scene_json):
        """ Load the state in scene_json (JSON String) while completely
            discarding the current state. Cannot be undone.
        """
        self.clear_all()
        as_data = json.loads(scene_json)

        js.SetupScene.redo_scene(as_data["room"]["x"], as_data["room"]["y"])

        for mesh in as_data["meshes"]:
            self.request_add_mesh(mesh["fileName"], mesh["type"], mesh["id"],
                                  json.dumps({
                                    "pos": mesh["pos"],
                                    "rot": mesh["rot"],
                                    "scale": mesh["scale"]
                                    }), True)

        self.load_selection(as_data)

        self.load_floor_and_walls(as_data)

    def load_changed_state(self, current_state, next_state):
        """ Loads the "next_state" (JSON Object / dicts and lists) from the
            current state. Is faster than load_state & can be undone; use this
            method for "undo" and "redo" (when there are likely to be few
            changes between the states & undo must be possible).
        """

        # delete meshes if they are not in the next state
        for mesh in current_state["meshes"]:
            found_mesh = False
            for other_mesh in next_state["meshes"]:
                if other_mesh["id"] == mesh["id"]:
                    found_mesh = True
                    break
            if not found_mesh:
                self.delete_mesh(mesh["id"])

        # transform meshes for the next state / create them, if they don't
        # exist yet
        for mesh in next_state["meshes"]:
            found_mesh = False
            for previous_state in current_state["meshes"]:
                if previous_state["id"] == mesh["id"]:
                    found_mesh = True
                    self.load_transformations_for_mesh(mesh, previous_state)
                    break

            if not found_mesh:
                self.request_add_mesh(mesh["fileName"], mesh["type"],
                                      mesh["id"], json.dumps({
                                        "pos": mesh["pos"],
                                        "rot": mesh["rot"],
                                        "scale": mesh["scale"]
                                      }), True)

        self.load_selection(next_state)

        self.load_floor_and_walls(next_state)

    def load_selection(self, next_state):
        if next_state["selection"] is not "None":
            self.select_mesh(next_state["selection"])
        else:
            self.de_select_meshes()

    def load_floor_and_walls(self, next_state):
        for texture_type in ("walls", "floor"):
            if texture_type in next_state:
                self.request_change_texture(
                    next_state[texture_type]["fileName"],
                    next_state[texture_type]["textureName"],
                    next_state[texture_type]["type"], False)
            else:
                if texture_type == "floor":
                    js.SetupScene.remove_texture("carpet")
                else:
                    js.SetupScene.remove_texture(texture_type)

    def load_transformations_for_mesh(self, mesh, previous_state):
        pos_data_new = mesh["pos"]
        pos_data_old = previous_state["pos"]
        js.SetupScene.translate_mesh_by_id(
            mesh["id"], pos_data_new[0] - pos_data_old[0],
            pos_data_new[1] - pos_data_old[1],
            pos_data_new[2] - pos_data_old[2])

        rot_data = mesh["rot"]
        js.SetupScene.rotate_mesh_by_id(mesh["id"], rot_data[0], rot_data[1],
                                        rot_data[2])

        scale_data = mesh["scale"]
        js.SetupScene.scale_mesh_by_id(
            mesh["id"], scale_data[0], scale_data[1], scale_data[2], False)

    def request_undo(self):
        js.SetupScene.save_state("undo")

    def undo(self):
        undone_state = self.undo_utility.undo()
        current_state = self.undo_utility.current_state(True)
        if undone_state is not None:
            # self.load_state(undone_state["state"])
            self.load_changed_state(json.loads(current_state["state"]),
                                    json.loads(undone_state["state"]))

    def redo(self):
        redone_state = self.undo_utility.redo()
        current_state = self.undo_utility.current_state(False)
        if redone_state is not None:
            # self.load_state(redone_state["state"])
            self.load_changed_state(json.loads(current_state["state"]),
                                    json.loads(redone_state["state"]))

    # MISCELLANY

    @QtCore.pyqtSlot(str)
    def on_js_console_log(self, log):
        """
        function for debugging purposes

        :param log:
        :return:
        """
        print(log)

    def explain_controls(self):
        msg_box = QtWidgets.QMessageBox()
        pixmap = QtGui.QPixmap()
        pixmap.load("assets/img/wiimote_explain.png")
        # some 2:3 ratio that fits on most screens...
        pixmap = pixmap.scaled(534, 801)
        msg_box.setWindowTitle("WiiMote Controls - Info")
        msg_box.setIconPixmap(pixmap)
        msg_box.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msg_box.show()
        msg_box.exec_()

    def eventFilter(self, source, event):
        """ Causes selection tables to lose focus (if they have the focus)
            and handles ctrl+z & ctrl+y
        """
        if event.type() == QtGui.QMouseEvent.MouseButtonPress:
            self.mesh_select_table.lose_focus()
            self.texture_select_table.lose_focus()
        elif event.type() == QtGui.QKeyEvent.KeyRelease:
            if event.key() == 75:
                self.simulate_click()
            # z (undo if with ctrl)
            elif (source == self.win and event.key() == 90 and
                  int(event.modifiers()) == QtCore.Qt.ControlModifier):
                self.request_undo()
            # y (redo if with ctrl)
            elif (source == self.win and event.key() == 89 and
                  int(event.modifiers()) == QtCore.Qt.ControlModifier):
                self.redo()
            else:
                pass
                #  print(event.key(), int(event.modifiers()))
        return super(Window, self).eventFilter(source, event)


def main():
    app = QApplication(sys.argv)
    url = QUrl('file:///' + os.path.dirname(os.path.realpath(__file__)) +
               '/html/index.html')

    win = Window(url, app)

    if len(sys.argv) > 1:
        win.set_bt_address(sys.argv[1])

    sys.exit(app.exec_())

    pass


if __name__ == '__main__':
    import sys

    main()
