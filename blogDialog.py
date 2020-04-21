# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'blogDialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.dummyBlogIDLabel = QtWidgets.QLabel(Dialog)
        self.dummyBlogIDLabel.setObjectName("dummyBlogIDLabel")
        self.gridLayout.addWidget(self.dummyBlogIDLabel, 0, 0, 1, 1)
        self.dummyBlogContentLabel = QtWidgets.QLabel(Dialog)
        self.dummyBlogContentLabel.setObjectName("dummyBlogContentLabel")
        self.gridLayout.addWidget(self.dummyBlogContentLabel, 1, 0, 1, 1)
        self.blogContentEdit = QtWidgets.QPlainTextEdit(Dialog)
        self.blogContentEdit.setObjectName("blogContentEdit")
        self.gridLayout.addWidget(self.blogContentEdit, 1, 1, 1, 1)
        self.IDLabel = QtWidgets.QLabel(Dialog)
        self.IDLabel.setObjectName("IDLabel")
        self.gridLayout.addWidget(self.IDLabel, 0, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 2)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.dummyBlogIDLabel.setText(_translate("Dialog", "ID"))
        self.dummyBlogContentLabel.setText(_translate("Dialog", "Content"))
        self.IDLabel.setText(_translate("Dialog", "TextLabel"))

