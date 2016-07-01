#!/usr/bin/env python

import os

from PyQt5 import uic, QtGui, QtCore, Qt
from PyQt5.QtCore import QFile, QIODevice, Qt, QTextStream, QUrl
from PyQt5.QtWidgets import (QAction, QApplication, QLineEdit, QMainWindow,
        QSizePolicy, QStyle, QTextEdit)
from PyQt5.QtNetwork import QNetworkProxyFactory, QNetworkRequest
from PyQt5.QtWebKitWidgets import QWebPage, QWebView

import numpy as np


class Window(QMainWindow):
    def __init__(self, url):
        super(Window, self).__init__()
        self.progress = 0

        QNetworkProxyFactory.setUseSystemConfiguration(True)

        self.win = uic.loadUi('room_design.ui')
        self.wv = QWebView(self.win)

        self.wv.setGeometry(10, 10, 1000, 650)
        self.wv.page().mainFrame().addToJavaScriptWindowObject(
            "python_callback", self)

        self.wv.load(url)

        self.wv.titleChanged.connect(self.adjustTitle)
        self.wv.loadProgress.connect(self.setProgress)
        self.wv.loadFinished.connect(self.finishLoading)

        self.translate_btn = self.win.btn_translate
        self.rotate_btn = self.win.btn_rotate
        self.scale_btn = self.win.btn_scale

        self.translate_btn.clicked.connect(self.translate)
        self.rotate_btn.clicked.connect(self.rotate)
        self.scale_btn.clicked.connect(self.scale)

        self.list_widget = self.win.list_widget

        self.win.show()

    def translate(self):
        print('translate')

        self.wv.page().mainFrame().evaluateJavaScript(
            "translateMeshByID('my_cube', 1, 0, 0);")

    def rotate(self):
        print('rotate')

        angle = str((np.pi / 8))
        self.wv.page().mainFrame().evaluateJavaScript(
            "rotateMeshByID('my_cube', " + angle + ", 0, 0);")

    def scale(self):
        print('scale')

        self.wv.page().mainFrame().evaluateJavaScript(
            "scaleMeshByID('my_cube', 2, 1, 1);")

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

    def setProgress(self, p):
        self.progress = p
        self.adjustTitle()

    def finishLoading(self):
        self.progress = 100
        self.adjustTitle()

        mesh_file = open('assets/box.babylon');

        data = '('
        for line in mesh_file:
            data += "'" + line[:-1] + "' + \n"
        mesh_file.close()
        data += "'')"

        self.wv.page().mainFrame().evaluateJavaScript("addMesh(" + data + ", 'my_cube');");

    @QtCore.pyqtSlot(str)
    def js_mesh_loaded(self, mesh_name):
        print(mesh_name)
        self.list_widget.addItem(mesh_name)  # maybe map binding to object ?
        self.wv.page().mainFrame().evaluateJavaScript("setMeshPosition('my_cube', 1, 1, 0);");

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