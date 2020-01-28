# -*- coding: utf-8 -*-
"""
Discription: Module for Connected-Component Labeling. 
Author(s):   M. Fränzl
Date:        18/09/18
"""

import numpy as np

from skimage.feature import blob_dog
import pandas as pd

import os

from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtWidgets
import pyqtgraph as pg

from .utils import drawOverlay, ini


class Module(QtWidgets.QWidget):

    updated = pyqtSignal()
        
    def __init__(self):
        super().__init__(None)
        
        moduleName = os.path.splitext(os.path.basename(__file__))[0]
        loadUi('Modules/' + moduleName + '.ui', self)
        self.iniFile = 'Modules/' + moduleName + '.ini'
        
        self.thresholdSpinBox.valueChanged.connect(self.updated.emit)
        self.maxSigmaSpinBox.valueChanged.connect(self.updated.emit)
        
           
    def attach(self, plot):
        self.p = plot
        self.pc = pg.PlotCurveItem(pen=pg.mkPen('r', width=3), brush=pg.mkBrush(None), pxMode=False)
        self.p.addItem(self.pc)  
        ini.loadSettings(self.iniFile, self.widget)   
        
        
    def detach(self):
        self.p.removeItem(self.pc) 
        ini.saveSettings(self.iniFile, self.widget)
       

    def findFeatures(self, frame, imageItem):
        
        threshold = self.thresholdSpinBox.value()
        maxSigma = self.maxSigmaSpinBox.value()

        image = imageItem.image
        mlist = blob_dog(image/image.max(), max_sigma=maxSigma, threshold=threshold/100)
        radii = mlist[:, 2]*np.sqrt(2)
    
        features = pd.DataFrame()
        x, y = np.meshgrid(np.arange(0, image.shape[0], 1), np.arange(0, image.shape[1], 1))
        if mlist.size > 0:
            for j in range(mlist.shape[0]):
                mask = (((x - mlist[j, 1])**2 + (y - mlist[j, 0])**2) < (mlist[j, 2]*np.sqrt(2))**2).astype(int)
                features = features.append([{'y': mlist[j, 0],
                                             'x': mlist[j, 1],
                                             'max_intensity': image[mask==1].max(),
                                             'area': 2*np.pi*mlist[j, 2]**2,
                                             'frame': frame,}])
        
        imageItem.setImage(image)
        
        if features.size > 0:
            drawOverlay.circles(features.x.values, features.y.values, radii, self.pc)
        else:
            self.pc.setData() 

        return features
