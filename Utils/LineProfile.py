# -*- coding: utf-8 -*-
"""
Discription: Preferences Window
Author(s): M. Fränzl
Data: 19/06/11
"""

import numpy as np

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi

import pyqtgraph as pg


class LineProfileWindow(QWidget):
    
    closed = QtCore.pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        loadUi('Utils/LineProfileWindow.ui', self)
        
        gLayout = pg.GraphicsLayoutWidget()  
        self.layout.addWidget(gLayout)   
        self.p = gLayout.addPlot()
        self.p.showAxis('top')
        self.p.showAxis('right')
        self.p.setLabels(left='Intensity', bottom='px')
        self.p.getAxis('top').setStyle(showValues=False)
        self.p.getAxis('right').setStyle(showValues=False)
        self.p.getAxis('top').setHeight(10)
        self.p.getAxis('right').setWidth(15)
        
    def closeEvent(self, e):
        self.closed.emit()
        e.accept()
        