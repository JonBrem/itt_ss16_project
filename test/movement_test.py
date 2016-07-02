#!/usr/bin/env python

import os

from PyQt5 import uic, QtGui, QtCore, Qt, QtWidgets
from PyQt5.QtCore import QFile, QIODevice, Qt, QTextStream, QUrl
from PyQt5.QtWidgets import (QAction, QApplication, QLineEdit, QMainWindow,
        QSizePolicy, QStyle, QTextEdit)
from PyQt5.QtNetwork import QNetworkProxyFactory, QNetworkRequest
from PyQt5.QtWebKitWidgets import QWebPage, QWebView

import numpy as np

import js_interface_module as js

class Window(QMainWindow):
    def __init__(self, url):
        super(Window, self).__init__()
        self.progress = 0

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

        self.tree_widget = self.win.tree_widget

        item_chair = self.add_root_element_to_tree('Chairs')
        item_table = self.add_root_element_to_tree('Table')
        item_couch = self.add_root_element_to_tree('Couch')

        self.add_child_to_tree_element(item_chair, 'Chair1')
        self.add_child_to_tree_element(item_chair, 'Chair2')
        self.add_child_to_tree_element(item_table, 'Table1')
        self.add_child_to_tree_element(item_couch, 'Comfy Couch')
        self.add_child_to_tree_element(item_couch, 'Old Couch')
        self.add_child_to_tree_element(item_couch, "Deadpool's Couch. YUCK!")

        self.tree_widget.doubleClicked.connect(
            self.perform_action_of_child_element)

        self.setup_ui()

        self.meshes = []
        self.selected_mesh = None

        self.win.show()

    def perform_action_of_child_element(self):
        item = self.tree_widget.currentItem()
        if item.childCount() == 0:
            print(item.text(0) + ' selected')

    def add_root_element_to_tree(self, name):
        item = QtWidgets.QTreeWidgetItem(self.tree_widget)
        item.setText(0, name)

        return item

    def add_child_to_tree_element(self, parent, name):
        item = QtWidgets.QTreeWidgetItem()
        item.setText(0, name)
        parent.addChild(item)

        # return item

    def setup_ui(self):
        self.translate_btn.clicked.connect(self.translate)
        self.rotate_btn.clicked.connect(self.rotate)
        self.scale_btn.clicked.connect(self.scale)

        self.list_widget.selectionModel().selectionChanged.connect(
            self.mesh_selection_changed)

    def translate(self):
        if self.selected_mesh is not None:
            print('translate')
            js.SetupScene.translate_mesh_by_id(self.selected_mesh,
                                               1, 0, 0)

    def rotate(self):
        if self.selected_mesh is not None:
            print('rotate')

            angle = str((np.pi / 8))
            js.SetupScene.rotate_mesh_by_id(self.selected_mesh,
                                            angle, 0, 0)

    def scale(self):
        if self.selected_mesh is not None:
            print('scale')

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

        mesh_file = open('assets/box.babylon')

        data = '('
        for line in mesh_file:
            data += "'" + line[:-1] + "' + \n"
        mesh_file.close()
        data += "'')"

        js.SetupScene.add_mesh(data, 'my_cube')
        js.SetupScene.add_mesh(data, 'my_other_cube')

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

    @QtCore.pyqtSlot(str)
    def js_mesh_loaded(self, mesh_name):
        print(mesh_name)
        self.list_widget.addItem(mesh_name)  # maybe map binding to object ?
        self.meshes.append(mesh_name)
        if mesh_name == 'my_cube':
            js.SetupScene.set_mesh_position(mesh_name, 1, 1, 0)

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

        print(action + ' mesh: ' + mesh_id + ' in: ' + s)

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


def main():
    app = QApplication(sys.argv)
    url = QUrl('file:///' + os.path.dirname(os.path.realpath(__file__)) + '/index.html')

    win = Window(url)

    sys.exit(app.exec_())

    pass


if __name__ == '__main__':
    import sys

    main()
