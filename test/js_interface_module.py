#!/usr/bin/env python

from PyQt5 import uic, QtGui, QtCore, Qt
from PyQt5.QtCore import QFile, QIODevice, Qt, QTextStream, QUrl
from PyQt5.QtWidgets import (QAction, QApplication, QLineEdit, QMainWindow,
        QSizePolicy, QStyle, QTextEdit)
from PyQt5.QtNetwork import QNetworkProxyFactory, QNetworkRequest
from PyQt5.QtWebKitWidgets import QWebPage, QWebView

import json


class SetupScene:
    webview = None

    @staticmethod
    def init(wv):
        SetupScene.webview = wv.page().mainFrame()

    @staticmethod
    def apply_callback( name, parent):
        SetupScene.webview.addToJavaScriptWindowObject(name, parent)

    @staticmethod
    def translate_mesh_by_id(id, x, y, z):
        SetupScene.webview.evaluateJavaScript(
            "translateMeshByID('" + id + "', " +
            str(x) + ", " + str(y) + ", " + str(z) + " );")

    @staticmethod
    def rotate_mesh_by_id(id, angle_x, angle_y, angle_z):
        SetupScene.webview.evaluateJavaScript(
            "rotateMeshByID('" + id + "', " +
            str(angle_x) + ", " + str(angle_y) + ", " + str(angle_z) + " );")

    @staticmethod
    def scale_mesh_by_id(id, factor_x, factor_y, factor_z):
        SetupScene.webview.evaluateJavaScript(
            "scaleMeshByID('" + id + "', " +
            str(factor_x) + ", " + str(factor_y) + ", " +
            str(factor_z) + " );")

    @staticmethod
    def add_mesh(data, mesh_id, images={}):
        SetupScene.webview.evaluateJavaScript(
            "addMesh(" + data + ",'" + mesh_id + "'," + json.dumps(images) + ");")

    @staticmethod
    def highlight_mesh(mesh_id):
        SetupScene.webview.evaluateJavaScript(
            "highlight('" + mesh_id + "');")

    @staticmethod
    def remove_highlight_from_mesh(mesh_id):
        SetupScene.webview.evaluateJavaScript(
            "removeHighlight('" + mesh_id + "');")

    @staticmethod
    def set_mesh_position(mesh_id, x, y, z):
        SetupScene.webview.evaluateJavaScript(
            "setMeshPosition('" + mesh_id + "', " +
            str(x) + ", " + str(y) + ", " + str(z) + ");")

    @staticmethod
    def get_translation_rotation_scale(mesh_id):
        SetupScene.webview.evaluateJavaScript(
            "getTranslationRotationScale('" + mesh_id + "');"
        )


def deserialize_list(js_list_as_string):
    l = []
    s = ''

    for c in list(js_list_as_string):
        if c != ',':
            s += c
        else:
            l.append(float(s))
            s = ''

    l.append(float(s))

    return l