# -*- coding: utf-8 -*-
"""
Discription: Module for Connected-Component Labeling similar to the 
            "Particle Analysis.vi" in the LabVIEW Vision Development Module.
Author(s):   M. Fränzl
Data:        20/01/20
"""

import numpy as np

import skimage
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
        self.minAreaSpinBox.valueChanged.connect(self.updated.emit)  
        self.maxAreaSpinBox.valueChanged.connect(self.updated.emit)
        self.invertCheckBox.stateChanged.connect(self.updated.emit)
        self.maxFeaturesSpinBox.valueChanged.connect(self.updated.emit)
        
           
    def attach(self, plot):
        self.p = plot
        self.pc1 = pg.PlotCurveItem(pen=pg.mkPen('b', width=3), brush=pg.mkBrush(None), pxMode=False)
        self.pc2 = pg.PlotCurveItem(pen=pg.mkPen('r', width=3), brush=pg.mkBrush(None), pxMode=False)
        self.p.addItem(self.pc1)
        self.p.addItem(self.pc2)
        ini.loadSettings(self.iniFile, self.widget)   
        
        
    def detach(self):
        self.p.removeItem(self.pc1)
        self.p.removeItem(self.pc2)
        ini.saveSettings(self.iniFile, self.widget)
        

    def findFeatures(self, frame, imageItem):
            
        threshold = self.thresholdSpinBox.value()
        min_area = self.minAreaSpinBox.value()
        max_area = self.maxAreaSpinBox.value()
        max_features = self.maxFeaturesSpinBox.value()
        invert = self.invertCheckBox.checkState()

        features = pd.DataFrame()           
        intensityImage = imageItem.image
        thresholdImage = (intensityImage > threshold).astype(int) # Threshold image
        if invert:
            thresholdImage = 1 - thresholdImage
        labelImage = skimage.measure.label(thresholdImage)
        regions = skimage.measure.regionprops(label_image = labelImage, intensity_image = intensityImage) # http://scikit-image.org/docs/dev/api/skimage.measure.html
        j = 0
        for region in regions:
            # Area filter first 
            if region.area < min_area or region.area > max_area:  # Do not add feature
                continue
            if j >= max_features: # Do not add feature
                continue 
            features = features.append([{'y': region.centroid[0], 
                                         'x': region.centroid[1],
                                         'y_weighted': region.weighted_centroid[0],
                                         'x_weighted': region.weighted_centroid[1],
                                         'orientation': region.orientation,
                                         'minor_axis_length': region.minor_axis_length,
                                         'major_axis_length': region.major_axis_length,
                                         'eccentricity': region.eccentricity,
                                         'area': region.area,
                                         'equivalent_diameter': region.equivalent_diameter,
                                         'filled_area': region.filled_area,
                                         'max_intensity': region.max_intensity,
                                         'mean_intensity': region.mean_intensity,
                                         #'bbox': region.bbox,
                                         'frame': frame,}])
            j += 1 # feature added
        features.reset_index(drop=True, inplace = True)
        
        imageItem.setImage(thresholdImage)
        
        # Draw overlay
        if features.size > 0:
            drawOverlay.ellipses(features.x.values, features.y.values, features.minor_axis_length.values, features.major_axis_length.values, features.orientation.values, self.pc1, self.pc2)
            self.numberOfFeatures.setText(str(features.shape[0]))
        else:
            self.numberOfFeatures.setText('0')
            self.pc1.setData() 
            self.pc2.setData()
            
   
        return features
