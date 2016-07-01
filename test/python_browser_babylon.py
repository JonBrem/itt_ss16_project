#!/usr/bin/env python


from PyQt5.QtCore import QFile, QIODevice, Qt, QTextStream, QUrl
from PyQt5.QtWidgets import (QAction, QApplication, QLineEdit, QMainWindow,
        QSizePolicy, QStyle, QTextEdit)
from PyQt5.QtNetwork import QNetworkProxyFactory, QNetworkRequest
from PyQt5.QtWebKitWidgets import QWebPage, QWebView

import time


class MainWindow(QMainWindow):
    def __init__(self, url):
        super(MainWindow, self).__init__()

        self.progress = 0

        QNetworkProxyFactory.setUseSystemConfiguration(True)

        self.view = QWebView(self)

        self.view.load(url)

        self.view.titleChanged.connect(self.adjustTitle)
        self.view.loadProgress.connect(self.setProgress)
        self.view.loadFinished.connect(self.finishLoading)

        self.setCentralWidget(self.view)

    def viewSource(self):
        accessManager = self.view.page().networkAccessManager()
        request = QNetworkRequest(self.view.url())
        reply = accessManager.get(request)
        reply.finished.connect(self.slotSourceDownloaded)

    def slotSourceDownloaded(self):
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
            self.setWindowTitle(self.view.title())

    def setProgress(self, p):
        self.progress = p
        self.adjustTitle()

    def finishLoading(self):
        self.progress = 100
        self.adjustTitle()

        self.view.page().mainFrame().evaluateJavaScript(open('jquery-2.2.4.min.js').read())
        self.view.page().mainFrame().evaluateJavaScript(open('babylon.2.4.max.js').read())
        self.view.page().mainFrame().evaluateJavaScript(open('babylon.objFileLoader.js').read())
        self.view.page().mainFrame().evaluateJavaScript(open('setup_scene.js').read())
        mesh_file = open('assets/box.babylon');

        data = '('
        for line in mesh_file:
            data += "'" + line[:-1] + "' + \n"
        mesh_file.close()
        data += "'')"
        print(data)

        self.view.page().mainFrame().evaluateJavaScript("add_mesh(" + data + ");");


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    url = QUrl('file:///home/jon/Desktop/pyqt3d/index.html')

    browser = MainWindow(url)
    browser.show()

    sys.exit(app.exec_())
