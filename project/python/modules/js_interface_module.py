#!/usr/bin/env python

from PyQt5 import uic, QtGui, QtCore, Qt
from PyQt5.QtCore import QFile, QIODevice, Qt, QTextStream, QUrl
from PyQt5.QtWidgets import (QAction, QApplication, QLineEdit, QMainWindow,
                             QSizePolicy, QStyle, QTextEdit)
from PyQt5.QtNetwork import QNetworkProxyFactory, QNetworkRequest
from PyQt5.QtWebKitWidgets import QWebPage, QWebView

import json


class SetupScene:
    """ Contains calls to the JS component.

        Our .js file is called "setup_scene.js", hence the name of this class.
        This helps to keep all JS parts of the python system in one place.
    """
    webview = None

    @staticmethod
    def init(wv):
        SetupScene.webview = wv.page().mainFrame()

    @staticmethod
    def apply_callback(name, parent):
        SetupScene.webview.addToJavaScriptWindowObject(name, parent)

    @staticmethod
    def translate_mesh_by_id(id_, x, y, z):
        SetupScene.webview.evaluateJavaScript(
            "translateMeshByID('" + id_ + "', " +
            str(x) + ", " + str(y) + ", " + str(z) + " );")

    @staticmethod
    def rotate_mesh_by_id(id_, angle_x, angle_y, angle_z):
        SetupScene.webview.evaluateJavaScript(
            "rotateMeshByID('" + id_ + "', " +
            str(angle_x) + ", " + str(angle_y) + ", " + str(angle_z) + " );")

    @staticmethod
    def scale_mesh_by_id(id_, factor_x, factor_y, factor_z, keep_y_bottom=True):
        method = "scaleMeshByID"
        if not keep_y_bottom:
            method = "scaleMeshByIDBasic"

        SetupScene.webview.evaluateJavaScript(
            method + "('" + id_ + "', " +
            str(factor_x) + ", " + str(factor_y) + ", " +
            str(factor_z) + " );")

    @staticmethod
    def add_mesh(data, mesh_id, images={}, mesh_type="box",
                 transform="null", mesh_file=""):
        SetupScene.webview.evaluateJavaScript(
            "addMesh(" + data + ",'" + mesh_id + "'," + json.dumps(images) +
            ",'" + mesh_type + "'," + transform + ",'" + mesh_file + "');")

    @staticmethod
    def duplicate_mesh(mesh_id_original, new_id):
        SetupScene.webview.evaluateJavaScript(
            "duplicateMesh('" + mesh_id_original + "', '" + new_id + "');")

    @staticmethod
    def highlight_mesh(mesh_id, from_click):
        SetupScene.webview.evaluateJavaScript(
            "highlight('" + mesh_id + "'," + str(from_click).lower() + ");")

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
            "getTranslationRotationScale('" + mesh_id + "');")

    @staticmethod
    def save_state(identifier="no identifier"):
        SetupScene.webview.evaluateJavaScript(
            "saveScene('" + identifier + "');")

    @staticmethod
    def remove_mesh(mesh_id):
        SetupScene.webview.evaluateJavaScript("removeMesh('" + mesh_id + "');")

    @staticmethod
    def set_selected_plane(which):
        SetupScene.webview.evaluateJavaScript("selectPlane('" + which + "');")

    @staticmethod
    def on_scale_end():
        SetupScene.webview.evaluateJavaScript("onScaleEnd();")

    @staticmethod
    def set_camera_to_default():
        SetupScene.webview.evaluateJavaScript("setCameraToDefault();")

    @staticmethod
    def target_camera_to_plane(plane):
        SetupScene.webview.evaluateJavaScript("targetCameraToPlane('" + plane +
                                              "');")

    @staticmethod
    def create_new_scene(x, y):
        SetupScene.webview.evaluateJavaScript("createScene('" + str(x / 100) +
                                              "', '" + str(y / 100) + "');")

    @staticmethod
    def set_texture(type_, texture_name, texture_data, file_name):
        SetupScene.webview.evaluateJavaScript(
            "setTextureData('" + type_ + "'," +
            "'" + texture_name + "',\"" +
            texture_data + "\",'" + file_name + "');")

    @staticmethod
    def remove_texture(type_):
        SetupScene.webview.evaluateJavaScript(
            "removeTextureData('" + type_ + "');")

    @staticmethod
    def redo_scene(x, y):
        SetupScene.webview.evaluateJavaScript("redoScene('" + str(x) + "', '" +
                                              str(y) + "')")


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
