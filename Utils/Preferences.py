# -*- coding: utf-8 -*-
"""
Discription: Preferences Window
Author(s): M. Fränzl
Data: 19/06/11
"""

import numpy as np

from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi

from pyqtgraph import QtCore, QtGui


class PreferencesWindow(QDialog):
    
    def __init__(self):
        super().__init__(None,  QtCore.Qt.WindowCloseButtonHint)
        
        loadUi('Utils/PreferencesWindow.ui', self)
        
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        