# -*- coding: utf-8 -*-
"""
Discription: Module for Connected-Component Labeling. 
Author(s):   M. Fränzl
Date:        18/09/18
"""

import numpy as np

from skimage.transform import hough_circle, hough_circle_peaks
from skimage.feature import canny
import pandas as pd

import os

from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtWidgets
import pyqtgraph as pg

from ..Utils import pgutils
from ..Utils.settings import saveSettings, restoreSettings


class Module(QtWidgets.QWidget):

    updated = pyqtSignal()
        
    def __init__(self):
        super().__init__(None)
        
        loadUi(os.path.splitext(os.path.relpath(__file__))[0] + '.ui', self)
        self.settingsFile = os.path.splitext(os.path.relpath(__file__))[0] + '.ini'
        
        self.sigmaSpinBox.valueChanged.connect(self.updated.emit)
        self.minRadiusSpinBox.valueChanged.connect(self.updated.emit)
        self.minRadiusSpinBox.valueChanged.connect(self.updated.emit)
        self.thresholdSpinBox.valueChanged.connect(self.updated.emit)
        self.showProcessedCheckBox.stateChanged.connect(self.updated.emit)
        self.showOverlayCheckBox.stateChanged.connect(self.updated.emit)

        
           
    def attach(self, plot):
        self.p = plot
        self.items = []
        restoreSettings(self.settingsFile, self.widget)
        
        
    def detach(self):
        for item in self.items:
            self.p.removeItem(item) 
        saveSettings(self.settingsFile, self.widget)
       

    def findFeatures(self, frame, imageItem):
                
        sigma = self.sigmaSpinBox.value()
        min_radius = self.minRadiusSpinBox.value()
        max_radius = self.maxRadiusSpinBox.value()
        threshold = self.thresholdSpinBox.value()
        
        image = imageItem.image
        
        edges = canny(image, sigma=sigma) # , low_threshold=80, high_threshold=150
        hough_radii = np.arange(min_radius, max_radius, 1) # np.linspace(20, 45, 50) 
        hough_transform = hough_circle(edges, hough_radii)

        # Select the most prominent circles
        _, x_centers, y_centers, radii = hough_circle_peaks(hough_transform, hough_radii, threshold=threshold)  
        
        features = pd.DataFrame()
        for x, y, r in zip(x_centers, y_centers, radii):
             features = features.append([{'x': x,
                                          'y': y,
                                          #'max_intensity': image[mask==1].max(),
                                          'radius': r,
                                          'frame': frame,}])
        
        if self.showProcessedCheckBox.checkState():
            imageItem.setImage(edges.astype('int'))
        
        for item in self.items:
            self.p.removeItem(item)          
        self.items = [] 
        
        if self.showOverlayCheckBox.checkState():
            for i, f in features.iterrows():
                self.items.append(pgutils.CircleItem([f.x+0.5, f.y+0.5], f.radius, color='r', width=2))
                self.p.addItem(self.items[-1]) 
        

        if features.size > 0:
            self.numberOfFeatures.setText(str(features.shape[0]))
        else:
            self.numberOfFeatures.setText('0')

        return features
