#!/usr/bin/env python

from PyQt5 import uic, QtGui, QtCore, Qt
from PyQt5.QtCore import QFile, QIODevice, Qt, QTextStream, QUrl
from PyQt5.QtWidgets import (QAction, QApplication, QLineEdit, QMainWindow,
        QSizePolicy, QStyle, QTextEdit)
from PyQt5.QtNetwork import QNetworkProxyFactory, QNetworkRequest
from PyQt5.QtWebKitWidgets import QWebPage, QWebView


class SetupScene:
    @staticmethod
    def apply_callback(webview, name, parent):
        webview.page().mainFrame().addToJavaScriptWindowObject(name, parent)

    @staticmethod
    def translate_mesh_by_id(webview, id, x, y, z):
        webview.page().mainFrame().evaluateJavaScript(
            "translateMeshByID('" + id + "', " +
            str(x) + ", " + str(y) + ", " + str(z) + " );")

    @staticmethod
    def rotate_mesh_by_id(webview, id, angle_x, angle_y, angle_z):
        webview.page().mainFrame().evaluateJavaScript(
            "rotateMeshByID('" + id + "', " +
            str(angle_x) + ", " + str(angle_y) + ", " + str(angle_z) + " );")

    @staticmethod
    def scale_mesh_by_id(webview, id, factor_x, factor_y, factor_z):
        webview.page().mainFrame().evaluateJavaScript(
            "scaleMeshByID('" + id + "', " +
            str(factor_x) + ", " + str(factor_y) + ", " +
            str(factor_z) + " );")

    @staticmethod
    def add_mesh(webview, data, mesh_id):
        webview.page().mainFrame().evaluateJavaScript(
            "addMesh(" + data + ",'" + mesh_id + "');")

    @staticmethod
    def highlight_mesh(webview, mesh_id):
        webview.page().mainFrame().evaluateJavaScript(
            "highlight('" + mesh_id + "');")

    @staticmethod
    def remove_highlight_from_mesh(webview, mesh_id):
        webview.page().mainFrame().evaluateJavaScript(
            "removeHighlight('" + mesh_id + "');")

    @staticmethod
    def set_mesh_position(webview, mesh_id, x, y, z):
        webview.page().mainFrame().evaluateJavaScript(
            "setMeshPosition('" + mesh_id + "', " +
            str(x) + ", " + str(y) + ", " + str(z) + ");")
